import logging

from fastapi import FastAPI

from app.api.dependencies import get_application, get_settings, set_runtime
from app.api.routes.webhook import router as webhook_router
from app.bot.application import build_application
from app.config import load_settings
from app.db.base import create_all, init_engine
from app.logging import setup_logging

api = FastAPI(title="Telegram Admin Bot API")
api.include_router(webhook_router)

logger = logging.getLogger(__name__)


@api.get("/health")
async def health_check():
    return {"status": "ok"}


@api.on_event("startup")
async def startup_event() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required")
    if not settings.webhook_url:
        raise RuntimeError("WEBHOOK_URL is required in webhook mode")

    init_engine(settings.database_url)
    if settings.auto_init_db:
        create_all()

    application = build_application(settings)
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret_token or None,
    )

    set_runtime(application, settings)
    logger.info("Webhook server started")


@api.on_event("shutdown")
async def shutdown_event() -> None:
    try:
        settings = get_settings()
        application = get_application()
    except RuntimeError:
        return

    await application.bot.delete_webhook(drop_pending_updates=False)
    await application.stop()
    await application.shutdown()
    logger.info("Webhook server stopped (%s)", settings.app_env)
