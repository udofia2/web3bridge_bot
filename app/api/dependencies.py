from telegram.ext import Application

from app.config import Settings

_APP: Application | None = None
_SETTINGS: Settings | None = None


def set_runtime(application: Application, settings: Settings) -> None:
    global _APP, _SETTINGS
    _APP = application
    _SETTINGS = settings


def get_application() -> Application:
    if _APP is None:
        raise RuntimeError("Telegram application is not initialized")
    return _APP


def get_settings() -> Settings:
    if _SETTINGS is None:
        raise RuntimeError("Settings not initialized")
    return _SETTINGS
