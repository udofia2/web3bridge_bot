from telegram import Message
from telegram.error import TelegramError


async def safe_delete(message: Message) -> None:
    try:
        await message.delete()
    except TelegramError:
        return
