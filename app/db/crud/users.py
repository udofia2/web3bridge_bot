from sqlalchemy.orm import Session

from app.db.models import UserProfile


def upsert_user(session: Session, user_id: int, username: str | None, first_name: str | None) -> UserProfile:
    row = session.get(UserProfile, user_id)
    if row is None:
        row = UserProfile(user_id=user_id, username=username or "", first_name=first_name or "")
        session.add(row)
    else:
        row.username = username or row.username
        row.first_name = first_name or row.first_name
    session.flush()
    return row
