from sqlalchemy.orm import Session

from app.db.models import GroupSetting


def get_or_create_group_setting(
    session: Session,
    chat_id: int,
    defaults: dict,
) -> GroupSetting:
    row = session.get(GroupSetting, chat_id)
    if row:
        return row

    row = GroupSetting(chat_id=chat_id, **defaults)
    session.add(row)
    session.flush()
    return row


def update_group_setting(session: Session, chat_id: int, key: str, value: bool) -> GroupSetting:
    row = session.get(GroupSetting, chat_id)
    if not row:
        raise ValueError("Group settings not found")
    setattr(row, key, value)
    session.flush()
    return row


def update_welcome_message(session: Session, chat_id: int, message: str) -> GroupSetting:
    row = session.get(GroupSetting, chat_id)
    if not row:
        raise ValueError("Group settings not found")
    row.welcome_msg = message
    session.flush()
    return row
