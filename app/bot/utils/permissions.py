from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes


async def is_admin(chat_id: int, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat is None or update.effective_user is None or update.effective_message is None:
        return False

    ok = await is_admin(update.effective_chat.id, context, update.effective_user.id)
    if not ok:
        await update.effective_message.reply_text("This command is for admins only.")
    return ok
