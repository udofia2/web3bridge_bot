from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.bot.utils.permissions import is_admin, require_admin
from app.db.base import session_scope


def _build_settings_keyboard(chat_id: int, config) -> InlineKeyboardMarkup:
    def toggle_btn(label: str, key: str) -> InlineKeyboardButton:
        icon = "ON" if getattr(config, key) else "OFF"
        return InlineKeyboardButton(f"{icon} {label}", callback_data=f"toggle_{key}_{chat_id}")

    return InlineKeyboardMarkup(
        [
            [toggle_btn("Welcome", "welcome"), toggle_btn("Anti-Flood", "antiflood")],
            [toggle_btn("Bad Words", "badwords"), toggle_btn("Anti-Links", "antilinks")],
        ]
    )


async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    if not context.args:
        await update.effective_message.reply_text(
            "Usage: /setwelcome <message>. Use {name} and {username} placeholders."
        )
        return

    settings_service = context.bot_data["settings_service"]
    message = " ".join(context.args)

    with session_scope() as session:
        settings_service.set_welcome_message(session, update.effective_chat.id, message)

    await update.effective_message.reply_text("Welcome message updated.")


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_admin(update, context):
        return
    if update.effective_chat is None or update.effective_message is None:
        return

    settings_service = context.bot_data["settings_service"]
    with session_scope() as session:
        cfg = settings_service.get(session, update.effective_chat.id)

    await update.effective_message.reply_text(
        "Group Settings",
        reply_markup=_build_settings_keyboard(update.effective_chat.id, cfg),
    )


async def on_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data or ""
    if not data.startswith("toggle_"):
        if data.startswith("rules_"):
            await query.answer("No rules set yet. Ask an admin.", show_alert=True)
        return

    _, key, chat_id_str = data.split("_", 2)
    chat_id = int(chat_id_str)

    if not await is_admin(chat_id, context, query.from_user.id):
        await query.answer("Admins only.", show_alert=True)
        return

    settings_service = context.bot_data["settings_service"]
    with session_scope() as session:
        cfg = settings_service.toggle(session, chat_id, key)

    await query.edit_message_reply_markup(reply_markup=_build_settings_keyboard(chat_id, cfg))
