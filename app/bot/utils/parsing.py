import logging
import re

from telegram import Message, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
_USERNAME_PATTERN = re.compile(r"@([A-Za-z0-9_]{5,32})")


def get_thread_id(update: Update) -> int | None:
    msg = update.effective_message
    return msg.message_thread_id if msg else None


def extract_mentions(message: Message) -> list[str]:
    usernames: list[str] = []
    if not message.entities or not message.text:
        logger.debug("extract_mentions: no entities or no text | text=%r entities=%r", message.text, message.entities)
        return usernames

    logger.debug("extract_mentions: text=%r entities=%r", message.text, message.entities)
    for entity in message.entities:
        if entity.type == "mention" and message.text:
            username = message.text[entity.offset + 1 : entity.offset + entity.length]
            usernames.append(username)

    logger.debug("extract_mentions: extracted=%r", usernames)
    return usernames


async def resolve_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg is None:
        logger.debug("resolve_target_user: no effective_message")
        return None

    logger.debug("resolve_target_user: text=%r entities=%r", msg.text, msg.entities)

    if msg.reply_to_message and msg.reply_to_message.from_user:
        logger.debug("resolve_target_user: reply target=%s", msg.reply_to_message.from_user.id)
        return msg.reply_to_message.from_user

    for ent in (msg.entities or []):
        if ent.type == "text_mention" and getattr(ent, "user", None):
            logger.debug("resolve_target_user: text_mention target=%s", ent.user.id)
            return ent.user
        if ent.type == "mention" and msg.text:
            username = msg.text[ent.offset + 1 : ent.offset + ent.length]
            try:
                chat = await context.bot.get_chat(f"@{username}")
                logger.debug("resolve_target_user: mention resolved username=@%s id=%s", username, getattr(chat, 'id', None))
                return chat
            except TelegramError as exc:
                logger.debug("resolve_target_user: mention lookup failed username=@%s error=%s", username, exc)
                continue

    parts = (msg.text or "").split()
    if len(parts) > 1 and parts[1].startswith("@"):
        try:
            chat = await context.bot.get_chat(parts[1])
            logger.debug("resolve_target_user: token fallback resolved username=%s id=%s", parts[1], getattr(chat, 'id', None))
            return chat
        except TelegramError as exc:
            logger.debug("resolve_target_user: token fallback failed username=%s error=%s", parts[1], exc)

    logger.debug("resolve_target_user: no target found")
    return None
