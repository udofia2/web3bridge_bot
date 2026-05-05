from datetime import datetime, timedelta

from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes

from app.bot.utils.parsing import resolve_target_user
from app.bot.utils.permissions import require_admin
from app.db.base import session_scope


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.effective_message.reply_html(f"{target.mention_html()} has been <b>banned</b>.")


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.effective_message.reply_html(f"{target.mention_html()} has been <b>unbanned</b>.")


async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await context.bot.unban_chat_member(update.effective_chat.id, target.id)
    await update.effective_message.reply_html(f"{target.mention_html()} has been <b>kicked</b>.")


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

    until = datetime.utcnow() + timedelta(minutes=minutes)
    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until,
    )
    await update.effective_message.reply_html(
        f"{target.mention_html()} muted for <b>{minutes} minutes</b>."
    )


async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    target = await resolve_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user message or mention @username.")
        return

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        target.id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        ),
    )
    await update.effective_message.reply_html(f"{target.mention_html()} has been <b>unmuted</b>.")


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
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_html(
            f"{target.mention_html()} has been <b>banned</b> after {max_warnings} warnings."
        )
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

    await context.bot.pin_chat_message(update.effective_chat.id, reply.message_id)
    await update.effective_message.reply_text("Message pinned.")


async def cmd_unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    await context.bot.unpin_all_chat_messages(update.effective_chat.id)
    await update.effective_message.reply_text("All messages unpinned.")
