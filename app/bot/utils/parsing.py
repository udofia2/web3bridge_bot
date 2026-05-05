from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes


def get_thread_id(update: Update) -> int | None:
    msg = update.effective_message
    return msg.message_thread_id if msg else None


def extract_mentions(message: Message) -> list[str]:
    usernames: list[str] = []
    if not message.entities or not message.text:
        return usernames

    for entity in message.entities:
        if entity.type == "mention":
            username = message.text[entity.offset + 1 : entity.offset + entity.length]
            usernames.append(username)
    return usernames


async def resolve_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg is None:
        return None

    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user

    for username in extract_mentions(msg):
        try:
            chat_obj = await context.bot.get_chat(f"@{username}")
            return chat_obj
        except TelegramError:
            continue
    return None
