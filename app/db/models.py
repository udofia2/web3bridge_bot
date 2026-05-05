from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GroupSetting(Base):
    __tablename__ = "group_settings"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    welcome: Mapped[bool] = mapped_column(Boolean, default=True)
    antiflood: Mapped[bool] = mapped_column(Boolean, default=True)
    badwords: Mapped[bool] = mapped_column(Boolean, default=True)
    antilinks: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_msg: Mapped[str] = mapped_column(String(500), default="Welcome to the group, {name}!")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WarningRecord(Base):
    __tablename__ = "warnings"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "user_id", name="pk_warnings"),)

    chat_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicSetting(Base):
    __tablename__ = "topic_settings"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "thread_id", name="pk_topic_settings"),)

    chat_id: Mapped[int] = mapped_column(BigInteger)
    thread_id: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(30), default="normal")
    topic_name: Mapped[str] = mapped_column(String(200), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicWhitelist(Base):
    __tablename__ = "topic_whitelist"
    __table_args__ = (
        PrimaryKeyConstraint("chat_id", "thread_id", "user_id", name="pk_topic_whitelist"),
    )

    chat_id: Mapped[int] = mapped_column(BigInteger)
    thread_id: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), default="")
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
