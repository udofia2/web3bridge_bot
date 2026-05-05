from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import TopicSetting, TopicWhitelist


def upsert_topic_mode(
    session: Session,
    chat_id: int,
    thread_id: int,
    mode: str,
    topic_name: str,
) -> TopicSetting:
    row = session.get(TopicSetting, {"chat_id": chat_id, "thread_id": thread_id})
    if row is None:
        row = TopicSetting(chat_id=chat_id, thread_id=thread_id, mode=mode, topic_name=topic_name)
        session.add(row)
    else:
        row.mode = mode
        if topic_name:
            row.topic_name = topic_name
    session.flush()
    return row


def get_topic_mode(session: Session, chat_id: int, thread_id: int) -> str:
    row = session.get(TopicSetting, {"chat_id": chat_id, "thread_id": thread_id})
    return row.mode if row else "normal"


def get_topic_name(session: Session, chat_id: int, thread_id: int) -> str:
    row = session.get(TopicSetting, {"chat_id": chat_id, "thread_id": thread_id})
    if row and row.topic_name:
        return row.topic_name
    return f"Topic #{thread_id}"


def clear_topic_mode(session: Session, chat_id: int, thread_id: int) -> None:
    row = session.get(TopicSetting, {"chat_id": chat_id, "thread_id": thread_id})
    if row:
        session.delete(row)
        session.flush()


def add_whitelist_user(session: Session, chat_id: int, thread_id: int, user_id: int) -> None:
    row = session.get(TopicWhitelist, {"chat_id": chat_id, "thread_id": thread_id, "user_id": user_id})
    if row is None:
        session.add(TopicWhitelist(chat_id=chat_id, thread_id=thread_id, user_id=user_id))
        session.flush()


def remove_whitelist_user(session: Session, chat_id: int, thread_id: int, user_id: int) -> None:
    row = session.get(TopicWhitelist, {"chat_id": chat_id, "thread_id": thread_id, "user_id": user_id})
    if row:
        session.delete(row)
        session.flush()


def clear_whitelist(session: Session, chat_id: int, thread_id: int) -> None:
    rows = session.scalars(
        select(TopicWhitelist).where(
            TopicWhitelist.chat_id == chat_id,
            TopicWhitelist.thread_id == thread_id,
        )
    ).all()
    for row in rows:
        session.delete(row)


def is_user_whitelisted(session: Session, chat_id: int, thread_id: int, user_id: int) -> bool:
    row = session.get(TopicWhitelist, {"chat_id": chat_id, "thread_id": thread_id, "user_id": user_id})
    return row is not None


def get_whitelist_count(session: Session, chat_id: int, thread_id: int) -> int:
    return session.scalar(
        select(func.count()).select_from(TopicWhitelist).where(
            TopicWhitelist.chat_id == chat_id,
            TopicWhitelist.thread_id == thread_id,
        )
    ) or 0


def list_topic_modes(session: Session, chat_id: int) -> list[TopicSetting]:
    return session.scalars(select(TopicSetting).where(TopicSetting.chat_id == chat_id)).all()
