from sqlalchemy.orm import Session

from app.core.enums import TopicMode
from app.db.crud.topics import (
    add_whitelist_user,
    clear_topic_mode,
    clear_whitelist,
    get_topic_mode,
    get_topic_name,
    get_whitelist_count,
    is_user_whitelisted,
    list_topic_modes,
    remove_whitelist_user,
    upsert_topic_mode,
)


class TopicService:
    def set_mode(
        self,
        session: Session,
        chat_id: int,
        thread_id: int,
        mode: TopicMode,
        topic_name: str,
    ) -> None:
        upsert_topic_mode(session, chat_id, thread_id, mode.value, topic_name)

    def clear_mode(self, session: Session, chat_id: int, thread_id: int) -> None:
        clear_topic_mode(session, chat_id, thread_id)
        clear_whitelist(session, chat_id, thread_id)

    def get_mode(self, session: Session, chat_id: int, thread_id: int) -> TopicMode:
        mode_value = get_topic_mode(session, chat_id, thread_id)
        return TopicMode(mode_value)

    def allow_user(self, session: Session, chat_id: int, thread_id: int, user_id: int) -> None:
        add_whitelist_user(session, chat_id, thread_id, user_id)

    def disallow_user(self, session: Session, chat_id: int, thread_id: int, user_id: int) -> None:
        remove_whitelist_user(session, chat_id, thread_id, user_id)

    def is_allowed(self, session: Session, chat_id: int, thread_id: int, user_id: int) -> bool:
        return is_user_whitelisted(session, chat_id, thread_id, user_id)

    def list_settings(self, session: Session, chat_id: int) -> list[dict]:
        rows = list_topic_modes(session, chat_id)
        output: list[dict] = []
        for row in rows:
            output.append(
                {
                    "thread_id": row.thread_id,
                    "mode": row.mode,
                    "name": row.topic_name or get_topic_name(session, chat_id, row.thread_id),
                    "whitelist_count": get_whitelist_count(session, chat_id, row.thread_id),
                }
            )
        return output
