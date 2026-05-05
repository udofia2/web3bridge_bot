from datetime import datetime, timedelta

from telegram import ChatPermissions, Update
from telegram.error import TelegramError
from telegram.constants import ChatMemberStatus
import logging
from telegram.ext import ContextTypes

from app.bot.utils.parsing import resolve_target_user
from app.bot.utils.permissions import require_admin
from app.db.base import session_scope

logger = logging.getLogger(__name__)


async def _bot_member(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    me = await context.bot.get_me()
    return await context.bot.get_chat_member(chat_id, me.id)


async def _ensure_bot_can_restrict(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str | None]:
    try:
        bm = await _bot_member(chat_id, context)
    except TelegramError as e:
        logger.exception("Failed to fetch bot member status: %s", e)
        return False, "Could not verify bot permissions."

    if bm.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return False, "I am not an admin in this chat. Promote me and grant appropriate rights."
    if not getattr(bm, "can_restrict_members", False):
        return False, "I don't have permission to restrict/ban members."
    return True, None


async def _ensure_bot_can_pin(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str | None]:
    try:
        bm = await _bot_member(chat_id, context)
    except TelegramError as e:
        logger.exception("Failed to fetch bot member status: %s", e)
        return False, "Could not verify bot permissions."

    if bm.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return False, "I am not an admin in this chat. Promote me and grant appropriate rights."
    if not getattr(bm, "can_pin_messages", False):
        return False, "I don't have permission to pin messages."
    return True, None


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    ok, reason = await _ensure_bot_can_restrict(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_html(f"{target.mention_html()} has been <b>banned</b>.")
    except TelegramError as e:
        logger.exception("Failed to ban user: %s", e)
        await update.effective_message.reply_text(f"Could not ban user: {e}")


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    ok, reason = await _ensure_bot_can_restrict(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_html(f"{target.mention_html()} has been <b>unbanned</b>.")
    except TelegramError as e:
        logger.exception("Failed to unban user: %s", e)
        await update.effective_message.reply_text(f"Could not unban user: {e}")


async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    ok, reason = await _ensure_bot_can_restrict(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_html(f"{target.mention_html()} has been <b>kicked</b>.")
    except TelegramError as e:
        logger.exception("Failed to kick user: %s", e)
        await update.effective_message.reply_text(f"Could not kick user: {e}")


async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    app_settings = context.bot_data["settings"]
    minutes = app_settings.mute_duration_min
    if context.args and context.args[0].isdigit():
        minutes = int(context.args[0])


    ok, reason = await _ensure_bot_can_restrict(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return

    until = datetime.utcnow() + timedelta(minutes=minutes)
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await update.effective_message.reply_html(
            f"{target.mention_html()} muted for <b>{minutes} minutes</b>."
        )
    except TelegramError as e:
        logger.exception("Failed to mute user: %s", e)
        await update.effective_message.reply_text(f"Could not mute user: {e}")


async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    ok, reason = await _ensure_bot_can_restrict(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await update.effective_message.reply_html(f"{target.mention_html()} has been <b>unmuted</b>.")
    except TelegramError as e:
        logger.exception("Failed to unmute user: %s", e)
        await update.effective_message.reply_text(f"Could not unmute user: {e}")


async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    reason = " ".join(context.args) if context.args else "no reason given"
    warning_service = context.bot_data["warning_service"]

    with session_scope() as session:
        count, should_ban = warning_service.increment(session, update.effective_chat.id, target.id)

    max_warnings = context.bot_data["settings"].max_warnings
    if should_ban:
        ok, reason = await _ensure_bot_can_restrict(update.effective_chat.id, context)
        if not ok:
            await update.effective_message.reply_text(reason)
            return
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            await update.effective_message.reply_html(
                f"{target.mention_html()} has been <b>banned</b> after {max_warnings} warnings."
            )
        except TelegramError as e:
            logger.exception("Failed to ban user after warnings: %s", e)
            await update.effective_message.reply_text(f"Could not ban user: {e}")
    else:
        await update.effective_message.reply_html(
            f"{target.mention_html()} warning <b>{count}/{max_warnings}</b> - {reason}."
        )


async def cmd_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    warning_service = context.bot_data["warning_service"]
    with session_scope() as session:
        count = warning_service.get_count(session, update.effective_chat.id, target.id)

    max_warnings = context.bot_data["settings"].max_warnings
    await update.effective_message.reply_html(
        f"{target.mention_html()} has <b>{count}/{max_warnings}</b> warnings."
    )


async def cmd_clearwarnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    warning_service = context.bot_data["warning_service"]
    with session_scope() as session:
        warning_service.clear(session, update.effective_chat.id, target.id)

    await update.effective_message.reply_html(f"Warnings cleared for {target.mention_html()}.")


async def cmd_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    reply = update.effective_message.reply_to_message
    if not reply:
        await update.effective_message.reply_text("Reply to a message to pin it.")
        return

    ok, reason = await _ensure_bot_can_pin(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return
    try:
        await context.bot.pin_chat_message(update.effective_chat.id, reply.message_id)
        await update.effective_message.reply_text("Message pinned.")
    except TelegramError as e:
        logger.exception("Failed to pin message: %s", e)
        await update.effective_message.reply_text(f"Could not pin message: {e}")


async def cmd_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    ok, reason = await _ensure_bot_can_pin(update.effective_chat.id, context)
    if not ok:
        await update.effective_message.reply_text(reason)
        return
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await update.effective_message.reply_text("All messages unpinned.")
    except TelegramError as e:
        logger.exception("Failed to unpin messages: %s", e)
        await update.effective_message.reply_text(f"Could not unpin messages: {e}")
