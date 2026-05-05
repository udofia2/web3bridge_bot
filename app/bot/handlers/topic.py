from telegram import Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from app.bot.utils.parsing import extract_mentions, get_thread_id
from app.bot.utils.permissions import require_admin
from app.core.enums import TopicMode
from app.db.base import session_scope


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

        for username in extract_mentions(update.effective_message):
            try:
                user_obj = await context.bot.get_chat(f"@{username}")
                topic_service.allow_user(session, update.effective_chat.id, thread_id, user_obj.id)
                added.append(f"@{username}")
            except TelegramError:
                continue

    added_text = ", ".join(added) if added else "none yet"
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
        for username in extract_mentions(update.effective_message):
            try:
                user_obj = await context.bot.get_chat(f"@{username}")
                topic_service.allow_user(session, update.effective_chat.id, thread_id, user_obj.id)
                added.append(f"@{username}")
            except TelegramError:
                continue

    if added:
        await update.effective_message.reply_text(f"Added to whitelist: {', '.join(added)}")
    else:
        await update.effective_message.reply_text("Mention at least one user: /topicallow @username")


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
        for username in extract_mentions(update.effective_message):
            try:
                user_obj = await context.bot.get_chat(f"@{username}")
                topic_service.disallow_user(session, update.effective_chat.id, thread_id, user_obj.id)
                removed.append(f"@{username}")
            except TelegramError:
                continue

    if removed:
        await update.effective_message.reply_text(f"Removed from whitelist: {', '.join(removed)}")
    else:
        await update.effective_message.reply_text("Mention at least one user: /topicdisallow @username")


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
        await update.effective_message.reply_text("Topic closed. Use /topicopen to reopen.")
    except TelegramError as exc:
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
        await update.effective_message.reply_text("Topic reopened.")
    except TelegramError as exc:
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
        await update.effective_message.reply_text("Message pinned in this topic.")
    except TelegramError as exc:
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

    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
