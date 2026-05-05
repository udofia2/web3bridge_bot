from sqlalchemy.orm import Session

from app.db.models import WarningRecord


def get_warning_record(session: Session, chat_id: int, user_id: int) -> WarningRecord | None:
    return session.get(WarningRecord, {"chat_id": chat_id, "user_id": user_id})


def increment_warning(session: Session, chat_id: int, user_id: int) -> WarningRecord:
    row = get_warning_record(session, chat_id, user_id)
    if row is None:
        row = WarningRecord(chat_id=chat_id, user_id=user_id, count=0)
        session.add(row)
    row.count += 1
    session.flush()
    return row


def clear_warning_count(session: Session, chat_id: int, user_id: int) -> None:
    row = get_warning_record(session, chat_id, user_id)
    if row:
        row.count = 0
        session.flush()
