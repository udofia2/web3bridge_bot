import logging
import re

from telegram import Update, Message
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.bot.utils.parsing import get_thread_id
from app.bot.utils.permissions import require_admin
from app.core.enums import TopicMode
from app.db.base import session_scope

logger = logging.getLogger(__name__)
_USERNAME_PATTERN = re.compile(r"@([A-Za-z0-9_]{5,32})")
_COMMAND_PATTERN = re.compile(r"^/\w+(?:@\w+)?\s*(.*)$", re.DOTALL)


def _describe_user(user) -> str:
    username = f"@{user.username}" if getattr(user, "username", None) else "(no username)"
    first_name = getattr(user, "first_name", "") or ""
    last_name = getattr(user, "last_name", "") or ""
    full_name = " ".join(part for part in [first_name, last_name] if part)
    return f"id={getattr(user, 'id', 'unknown')} name={full_name or '(unknown)'} username={username}"


def _describe_entities(message: Message) -> str:
    entities = message.entities or []
    if not entities:
        return "[]"
    parts: list[str] = []
    for ent in entities:
        parts.append(f"{ent.type}@{ent.offset}:{ent.length}")
    return "[" + ", ".join(parts) + "]"


async def _extract_users_from_message(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    command_user_id: int | None = None,
) -> list[tuple[int, str]]:
    """Extract user IDs and display names from a topic command message."""
    users: list[tuple[int, str]] = []
    text = message.text or ""
    logger.debug("topic user extraction: text=%r entities=%r", text, message.entities)

    if (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id != command_user_id
    ):
        user = message.reply_to_message.from_user
        display = f"@{user.username}" if user.username else user.first_name
        users.append((user.id, display))
        logger.debug(
            "topic user extraction: reply target -> id=%s display=%s",
            user.id,
            display,
        )
    elif message.reply_to_message and message.reply_to_message.from_user:
        logger.debug(
            "topic user extraction: ignored self-reply target -> id=%s",
            message.reply_to_message.from_user.id,
        )

    # Parse raw usernames from the command text itself, independent of Telegram entities.
    command_tail = text
    command_match = _COMMAND_PATTERN.match(text)
    if command_match:
        command_tail = command_match.group(1)

    raw_usernames = _USERNAME_PATTERN.findall(command_tail)
    if raw_usernames:
        logger.debug("topic user extraction: raw usernames from command tail=%r", raw_usernames)
        resolved_usernames: list[str] = []
        skipped_usernames: list[str] = []
        for username in raw_usernames:
            try:
                user_obj = await context.bot.get_chat(f"@{username}")
                users.append((user_obj.id, f"@{username}"))
                resolved_usernames.append(username)
                logger.debug("topic user extraction: raw username resolved -> @%s id=%s", username, user_obj.id)
            except TelegramError as exc:
                skipped_usernames.append(username)
                logger.debug("topic user extraction: raw username lookup failed @%s error=%s", username, exc)

    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and getattr(ent, "user", None):
                user = ent.user
                display = f"@{user.username}" if user.username else user.first_name
                users.append((user.id, display))
                logger.debug("topic user extraction: text_mention -> id=%s display=%s", user.id, display)
            elif ent.type == "mention" and text:
                username = text[ent.offset + 1 : ent.offset + ent.length]
                if username in raw_usernames:
                    # Already attempted via raw text above.
                    continue
                try:
                    user_obj = await context.bot.get_chat(f"@{username}")
                    users.append((user_obj.id, f"@{username}"))
                    logger.debug("topic user extraction: mention -> @%s id=%s", username, user_obj.id)
                except TelegramError as exc:
                    logger.debug("topic user extraction: mention lookup failed @%s error=%s", username, exc)

    if not users and text:
        logger.debug("topic user extraction: entity pass found no users, trying regex fallback")
        for username in _USERNAME_PATTERN.findall(text):
            try:
                user_obj = await context.bot.get_chat(f"@{username}")
                users.append((user_obj.id, f"@{username}"))
                logger.debug("topic user extraction: regex fallback -> @%s id=%s", username, user_obj.id)
            except TelegramError as exc:
                logger.debug("topic user extraction: regex fallback failed @%s error=%s", username, exc)

    logger.debug("topic user extraction: final users=%r", users)
    return users


async def cmd_topic_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    message = update.effective_message
    thread_id = get_thread_id(update)
    reply_target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        reply_target = _describe_user(message.reply_to_message.from_user)

    extracted = await _extract_users_from_message(
        message,
        context,
        update.effective_user.id if update.effective_user else None,
    )
    extracted_text = "\n".join(f"- {user_id} | {display}" for user_id, display in extracted) or "- none"

    lines = [
        "Topic Debug",
        f"chat_id: {update.effective_chat.id}",
        f"thread_id: {thread_id}",
        f"text: {message.text or '(no text)'}",
        f"entities: {_describe_entities(message)}",
        f"reply_target: {reply_target or 'none'}",
        "extracted_users:",
        extracted_text,
    ]

    logger.debug(
        "cmd_topic_debug: chat_id=%s thread_id=%s text=%r entities=%r extracted=%r reply_target=%r",
        update.effective_chat.id,
        thread_id,
        message.text,
        message.entities,
        extracted,
        reply_target,
    )

    await message.reply_text("\n".join(lines))


async def cmd_topic_announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return

    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    topic_service = context.bot_data["topic_service"]
    with session_scope() as session:
        topic_service.set_mode(
            session,
            update.effective_chat.id,
            thread_id,
            TopicMode.ANNOUNCEMENT,
            f"Topic #{thread_id}",
        )

    logger.debug("cmd_topic_announce: set announcement mode chat_id=%s thread_id=%s", update.effective_chat.id, thread_id)
    await update.effective_message.reply_text(
        "This topic is now announcement-only. Only admins can post here.",
    )


async def cmd_topic_restrict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    topic_service = context.bot_data["topic_service"]
    added: list[str] = []

    with session_scope() as session:
        topic_service.set_mode(
            session,
            update.effective_chat.id,
            thread_id,
            TopicMode.RESTRICTED,
            f"Topic #{thread_id}",
        )

        users = await _extract_users_from_message(
            update.effective_message,
            context,
            update.effective_user.id if update.effective_user else None,
        )
        for user_id, display in users:
            topic_service.allow_user(session, update.effective_chat.id, thread_id, user_id)
            added.append(display)

    added_text = ", ".join(added) if added else "none yet"
    logger.debug("cmd_topic_restrict: added=%r chat_id=%s thread_id=%s", added, update.effective_chat.id, thread_id)
    await update.effective_message.reply_text(
        f"This topic is now restricted. Whitelisted: {added_text}. Use /topicallow @user to add more users.",
    )


async def cmd_topic_allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    topic_service = context.bot_data["topic_service"]
    added: list[str] = []
    with session_scope() as session:
        users = await _extract_users_from_message(
            update.effective_message,
            context,
            update.effective_user.id if update.effective_user else None,
        )
        for user_id, display in users:
            topic_service.allow_user(session, update.effective_chat.id, thread_id, user_id)
            added.append(display)

    logger.debug("cmd_topic_allow: added=%r chat_id=%s thread_id=%s", added, update.effective_chat.id, thread_id)
    if added:
        await update.effective_message.reply_text(f"Added to whitelist: {', '.join(added)}")
    else:
        await update.effective_message.reply_text(
            "Mention at least one user or reply to a user's message: /topicallow @username"
        )


async def cmd_topic_disallow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    topic_service = context.bot_data["topic_service"]
    removed: list[str] = []
    with session_scope() as session:
        users = await _extract_users_from_message(
            update.effective_message,
            context,
            update.effective_user.id if update.effective_user else None,
        )
        for user_id, display in users:
            topic_service.disallow_user(session, update.effective_chat.id, thread_id, user_id)
            removed.append(display)

    logger.debug("cmd_topic_disallow: removed=%r chat_id=%s thread_id=%s", removed, update.effective_chat.id, thread_id)
    if removed:
        await update.effective_message.reply_text(f"Removed from whitelist: {', '.join(removed)}")
    else:
        await update.effective_message.reply_text(
            "Mention at least one user or reply to a user's message: /topicdisallow @username"
        )


async def cmd_topic_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    topic_service = context.bot_data["topic_service"]
    with session_scope() as session:
        topic_service.clear_mode(session, update.effective_chat.id, thread_id)

    logger.debug("cmd_topic_normal: cleared mode chat_id=%s thread_id=%s", update.effective_chat.id, thread_id)
    await update.effective_message.reply_text("Topic reset to normal.")


async def cmd_topic_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    try:
        await context.bot.close_forum_topic(chat_id=update.effective_chat.id, message_thread_id=thread_id)
        logger.debug("cmd_topic_close: closed chat_id=%s thread_id=%s", update.effective_chat.id, thread_id)
        await update.effective_message.reply_text("Topic closed. Use /topicopen to reopen.")
    except TelegramError as exc:
        logger.exception("cmd_topic_close failed: %s", exc)
        await update.effective_message.reply_text(f"Could not close topic: {exc}")


async def cmd_topic_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    thread_id = get_thread_id(update)
    if not thread_id:
        await update.effective_message.reply_text("Use this command inside a topic thread.")
        return

    try:
        await context.bot.reopen_forum_topic(chat_id=update.effective_chat.id, message_thread_id=thread_id)
        logger.debug("cmd_topic_open: reopened chat_id=%s thread_id=%s", update.effective_chat.id, thread_id)
        await update.effective_message.reply_text("Topic reopened.")
    except TelegramError as exc:
        logger.exception("cmd_topic_open failed: %s", exc)
        await update.effective_message.reply_text(f"Could not reopen topic: {exc}")


async def cmd_topic_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a message inside this topic to pin it.")
        return

    try:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=reply.message_id,
            disable_notification=True,
        )
        logger.debug("cmd_topic_pin: pinned message_id=%s chat_id=%s thread_id=%s", reply.message_id, update.effective_chat.id, get_thread_id(update))
        await update.effective_message.reply_text("Message pinned in this topic.")
    except TelegramError as exc:
        logger.exception("cmd_topic_pin failed: %s", exc)
        await update.effective_message.reply_text(f"Could not pin message: {exc}")


async def cmd_topic_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    topic_service = context.bot_data["topic_service"]
    with session_scope() as session:
        rows = topic_service.list_settings(session, update.effective_chat.id)

    if not rows:
        await update.effective_message.reply_text("No topics have custom moderation settings yet.")
        return

    lines = ["Topic Moderation Settings", ""]
    for row in rows:
        icon = {"announcement": "ANN", "restricted": "RST"}.get(row["mode"], "NRM")
        line = f"[{icon}] {row['name']} - {row['mode']}"
        if row["mode"] == TopicMode.RESTRICTED.value:
            line += f" (whitelisted: {row['whitelist_count']})"
        lines.append(line)

    logger.debug("cmd_topic_list: chat_id=%s rows=%r", update.effective_chat.id, rows)
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
