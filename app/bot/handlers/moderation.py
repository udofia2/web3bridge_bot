from datetime import datetime, timedelta

from telegram import ChatPermissions, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.utils.messaging import safe_delete
from app.bot.utils.permissions import is_admin
from app.core.enums import TopicMode
from app.db.base import session_scope
from app.services.moderation_service import contains_bad_words, contains_blocked_links


async def _warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE, user, reason: str) -> None:
    if update.effective_chat is None:
        return

    warning_service = context.bot_data["warning_service"]
    max_warnings = context.bot_data["settings"].max_warnings

    with session_scope() as session:
        count, should_ban = warning_service.increment(session, update.effective_chat.id, user.id)

    if should_ban:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.send_message(
            update.effective_chat.id,
            f"{user.mention_html()} has been banned after {max_warnings} warnings.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            f"{user.mention_html()}, warning {count}/{max_warnings} - {reason}.",
            parse_mode=ParseMode.HTML,
        )


async def auto_moderate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg is None or update.effective_chat is None or msg.from_user is None:
        return

    chat_id = update.effective_chat.id
    user = msg.from_user
    text = msg.text or msg.caption or ""
    thread_id = msg.message_thread_id

    if await is_admin(chat_id, context, user.id):
        return

    topic_service = context.bot_data["topic_service"]
    settings_service = context.bot_data["settings_service"]
    warning_service = context.bot_data["warning_service"]
    flood_tracker = context.bot_data["flood_tracker"]
    app_settings = context.bot_data["settings"]

    with session_scope() as session:
        if thread_id is not None:
            mode = topic_service.get_mode(session, chat_id, thread_id)

            if mode == TopicMode.ANNOUNCEMENT:
                await safe_delete(msg)
                await context.bot.send_message(
                    chat_id,
                    f"{user.mention_html()}, this topic is <b>announcement-only</b>. Only admins can post here.",
                    parse_mode=ParseMode.HTML,
                    message_thread_id=thread_id,
                )
                return

            if mode == TopicMode.RESTRICTED and not topic_service.is_allowed(session, chat_id, thread_id, user.id):
                await safe_delete(msg)
                await context.bot.send_message(
                    chat_id,
                    f"{user.mention_html()}, you do not have permission to post in this topic.",
                    parse_mode=ParseMode.HTML,
                    message_thread_id=thread_id,
                )
                return

        cfg = settings_service.get(session, chat_id)

    if cfg.antiflood and flood_tracker.hit(chat_id, user.id):
        await safe_delete(msg)
        until = datetime.utcnow() + timedelta(minutes=app_settings.mute_duration_min)
        await context.bot.restrict_chat_member(
            chat_id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await context.bot.send_message(
            chat_id,
            f"{user.mention_html()} muted {app_settings.mute_duration_min} min for flooding.",
            parse_mode=ParseMode.HTML,
        )
        return

    if cfg.badwords and contains_bad_words(text, app_settings.bad_words):
        await safe_delete(msg)
        await _warn_user(update, context, user, reason="bad language")
        return

    if cfg.antilinks and contains_blocked_links(text):
        await safe_delete(msg)
        await _warn_user(update, context, user, reason="posting links")
        return
