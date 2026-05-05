import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    bot_token: str
    app_env: str
    runtime_mode: str
    webhook_url: str
    webhook_secret_token: str
    host: str
    port: int
    database_url: str
    log_level: str
    max_warnings: int
    flood_limit: int
    flood_window_secs: int
    mute_duration_min: int
    bad_words: set[str]
    default_welcome_enabled: bool
    default_antiflood_enabled: bool
    default_badwords_enabled: bool
    default_antilinks_enabled: bool
    default_welcome_message: str
    auto_init_db: bool


def load_settings() -> Settings:
    bad_words_raw = os.getenv("BAD_WORDS", "spam,scam,porn,xxx,drugs")
    bad_words = {word.strip().lower() for word in bad_words_raw.split(",") if word.strip()}

    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        app_env=os.getenv("APP_ENV", "development"),
        runtime_mode=os.getenv("RUNTIME_MODE", "polling").lower(),
        webhook_url=os.getenv("WEBHOOK_URL", ""),
        webhook_secret_token=os.getenv("WEBHOOK_SECRET_TOKEN", ""),
        host=os.getenv("HOST", "0.0.0.0"),
        port=_env_int("PORT", 8000),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./bot.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_warnings=_env_int("MAX_WARNINGS", 3),
        flood_limit=_env_int("FLOOD_LIMIT", 5),
        flood_window_secs=_env_int("FLOOD_WINDOW_SECS", 5),
        mute_duration_min=_env_int("MUTE_DURATION_MIN", 10),
        bad_words=bad_words,
        default_welcome_enabled=_env_bool("DEFAULT_WELCOME", True),
        default_antiflood_enabled=_env_bool("DEFAULT_ANTIFLOOD", True),
        default_badwords_enabled=_env_bool("DEFAULT_BADWORDS", True),
        default_antilinks_enabled=_env_bool("DEFAULT_ANTILINKS", False),
        default_welcome_message=os.getenv(
            "DEFAULT_WELCOME_MSG",
            "Welcome to the group, {name}! Please read the rules.",
        ),
        auto_init_db=_env_bool("AUTO_INIT_DB", True),
    )
