from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.enums import TopicMode
from app.db.models import Base
from app.services.topic_service import TopicService


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_topic_mode_and_whitelist_cycle():
    service = TopicService()
    session = _session()

    service.set_mode(session, 10, 100, TopicMode.RESTRICTED, "VIP")
    assert service.get_mode(session, 10, 100) == TopicMode.RESTRICTED

    service.allow_user(session, 10, 100, 9)
    assert service.is_allowed(session, 10, 100, 9)

    service.disallow_user(session, 10, 100, 9)
    assert not service.is_allowed(session, 10, 100, 9)

    service.clear_mode(session, 10, 100)
    assert service.get_mode(session, 10, 100) == TopicMode.NORMAL
