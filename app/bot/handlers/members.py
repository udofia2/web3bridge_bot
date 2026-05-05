from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

from app.db.base import session_scope


async def on_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if result is None or update.effective_chat is None:
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user
    chat_id = update.effective_chat.id

    settings_service = context.bot_data["settings_service"]

    if old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED) and new_status == ChatMemberStatus.MEMBER:
        with session_scope() as session:
            cfg = settings_service.get(session, chat_id)

        if cfg.welcome:
            msg = cfg.welcome_msg.format(
                name=user.first_name,
                username=f"@{user.username}" if user.username else user.first_name,
            )
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Rules", callback_data=f"rules_{chat_id}")]]
            )
            await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=keyboard)

    elif old_status == ChatMemberStatus.MEMBER and new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
        await context.bot.send_message(chat_id=chat_id, text=f"{user.first_name} has left the group.")
