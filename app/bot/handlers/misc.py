from telegram import Update
from telegram.ext import ContextTypes


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message is None:
        return

    text = (
        "Group Admin Bot v2 - Commands\n\n"
        "Topic Moderation\n"
        "/topicannounce - Announcement-only (admins only)\n"
        "/topicrestrict [@user] - Restrict to whitelist\n"
        "/topicallow @user - Add to whitelist\n"
        "/topicdisallow @user - Remove from whitelist\n"
        "/topicnormal - Reset topic to open\n"
        "/topicclose - Close topic\n"
        "/topicopen - Reopen topic\n"
        "/topicpin - Pin a replied message in topic\n"
        "/topiclist - List all topic settings\n\n"
        "General Moderation\n"
        "/ban, /unban, /kick\n"
        "/mute [minutes], /unmute\n"
        "/warn [reason], /warnings, /clearwarnings\n"
        "/pin, /unpin\n"
        "/setwelcome <message>\n"
        "/settings\n"
        "/help\n"
    )
    await update.effective_message.reply_text(text)
