import logging

from app.bot.application import build_application, polling_allowed_updates
from app.config import Settings, load_settings
from app.db.base import create_all, init_engine
from app.logging import setup_logging

logger = logging.getLogger(__name__)


def bootstrap() -> tuple[Settings, object]:
    settings = load_settings()
    setup_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    init_engine(settings.database_url)
    if settings.auto_init_db:
        create_all()

    application = build_application(settings)
    return settings, application


def run_polling() -> None:
    _, application = bootstrap()
    logger.info("Starting bot in polling mode")
    application.run_polling(allowed_updates=polling_allowed_updates())
