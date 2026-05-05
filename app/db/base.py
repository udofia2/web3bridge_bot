from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def init_engine(database_url: str) -> None:
    global _ENGINE, _SESSION_FACTORY

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    _ENGINE = create_engine(database_url, connect_args=connect_args, future=True)
    _SESSION_FACTORY = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)


def get_engine() -> Engine:
    if _ENGINE is None:
        raise RuntimeError("Database engine is not initialized")
    return _ENGINE


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if _SESSION_FACTORY is None:
        raise RuntimeError("Database session factory is not initialized")

    session = _SESSION_FACTORY()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all() -> None:
    Base.metadata.create_all(bind=get_engine())
