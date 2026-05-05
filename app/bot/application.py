from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.bot.handlers.admin import (
    cmd_ban,
    cmd_clearwarnings,
    cmd_kick,
    cmd_mute,
    cmd_pin,
    cmd_unban,
    cmd_unmute,
    cmd_unpin,
    cmd_warn,
    cmd_warnings,
)
from app.bot.handlers.members import on_member_update
from app.bot.handlers.misc import cmd_help
from app.bot.handlers.moderation import auto_moderate
from app.bot.handlers.settings import cmd_settings, cmd_setwelcome, on_settings_callback
from app.bot.handlers.topic import (
    cmd_topic_allow,
    cmd_topic_announce,
    cmd_topic_close,
    cmd_topic_disallow,
    cmd_topic_list,
    cmd_topic_normal,
    cmd_topic_open,
    cmd_topic_pin,
    cmd_topic_restrict,
)
from app.config import Settings
from app.services.moderation_service import FloodTracker
from app.services.settings_service import SettingsService
from app.services.topic_service import TopicService
from app.services.warning_service import WarningService


def build_application(settings: Settings) -> Application:
    app = Application.builder().token(settings.bot_token).build()

    app.bot_data["settings"] = settings
    app.bot_data["settings_service"] = SettingsService(settings)
    app.bot_data["topic_service"] = TopicService()
    app.bot_data["warning_service"] = WarningService(settings.max_warnings)
    app.bot_data["flood_tracker"] = FloodTracker(settings.flood_limit, settings.flood_window_secs)

    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, auto_moderate), group=1)
    app.add_handler(ChatMemberHandler(on_member_update, ChatMemberHandler.CHAT_MEMBER))

    for cmd, fn in [
        ("topicannounce", cmd_topic_announce),
        ("topicrestrict", cmd_topic_restrict),
        ("topicallow", cmd_topic_allow),
        ("topicdisallow", cmd_topic_disallow),
        ("topicnormal", cmd_topic_normal),
        ("topicclose", cmd_topic_close),
        ("topicopen", cmd_topic_open),
        ("topicpin", cmd_topic_pin),
        ("topiclist", cmd_topic_list),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    for cmd, fn in [
        ("ban", cmd_ban),
        ("unban", cmd_unban),
        ("kick", cmd_kick),
        ("mute", cmd_mute),
        ("unmute", cmd_unmute),
        ("warn", cmd_warn),
        ("warnings", cmd_warnings),
        ("clearwarnings", cmd_clearwarnings),
        ("pin", cmd_pin),
        ("unpin", cmd_unpin),
        ("setwelcome", cmd_setwelcome),
        ("settings", cmd_settings),
        ("help", cmd_help),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    app.add_handler(CallbackQueryHandler(on_settings_callback))
    return app


def polling_allowed_updates() -> list[str]:
    return Update.ALL_TYPES
