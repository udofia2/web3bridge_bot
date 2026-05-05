from sqlalchemy.orm import Session

from app.db.crud.warnings import clear_warning_count, get_warning_record, increment_warning


class WarningService:
    def __init__(self, max_warnings: int) -> None:
        self.max_warnings = max_warnings

    def increment(self, session: Session, chat_id: int, user_id: int) -> tuple[int, bool]:
        row = increment_warning(session, chat_id, user_id)
        count = row.count
        should_ban = count >= self.max_warnings
        if should_ban:
            clear_warning_count(session, chat_id, user_id)
        return count, should_ban

    def get_count(self, session: Session, chat_id: int, user_id: int) -> int:
        row = get_warning_record(session, chat_id, user_id)
        return row.count if row else 0

    def clear(self, session: Session, chat_id: int, user_id: int) -> None:
        clear_warning_count(session, chat_id, user_id)
