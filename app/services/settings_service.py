from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.crud.settings import (
    get_or_create_group_setting,
    update_group_setting,
    update_welcome_message,
)


@dataclass
class GroupSettingsDTO:
    welcome: bool
    antiflood: bool
    badwords: bool
    antilinks: bool
    welcome_msg: str


class SettingsService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get(self, session: Session, chat_id: int) -> GroupSettingsDTO:
        row = get_or_create_group_setting(
            session,
            chat_id,
            defaults={
                "welcome": self._settings.default_welcome_enabled,
                "antiflood": self._settings.default_antiflood_enabled,
                "badwords": self._settings.default_badwords_enabled,
                "antilinks": self._settings.default_antilinks_enabled,
                "welcome_msg": self._settings.default_welcome_message,
            },
        )
        return GroupSettingsDTO(
            welcome=row.welcome,
            antiflood=row.antiflood,
            badwords=row.badwords,
            antilinks=row.antilinks,
            welcome_msg=row.welcome_msg,
        )

    def toggle(self, session: Session, chat_id: int, key: str) -> GroupSettingsDTO:
        current = self.get(session, chat_id)
        new_value = not getattr(current, key)
        update_group_setting(session, chat_id, key, new_value)
        return self.get(session, chat_id)

    def set_welcome_message(self, session: Session, chat_id: int, message: str) -> GroupSettingsDTO:
        self.get(session, chat_id)
        update_welcome_message(session, chat_id, message)
        return self.get(session, chat_id)
