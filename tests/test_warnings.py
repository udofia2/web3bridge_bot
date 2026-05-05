from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base
from app.services.warning_service import WarningService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_warning_increment_and_autoban_threshold():
    service = WarningService(max_warnings=3)
    session = _session()

    count, should_ban = service.increment(session, chat_id=1, user_id=42)
    assert count == 1
    assert not should_ban

    count, should_ban = service.increment(session, chat_id=1, user_id=42)
    assert count == 2
    assert not should_ban

    count, should_ban = service.increment(session, chat_id=1, user_id=42)
    assert count == 3
    assert should_ban

    assert service.get_count(session, chat_id=1, user_id=42) == 0
