"""Talent-Augmenting Layer -- Database models and session management.

SQLAlchemy 2.0 async style with aiosqlite for local dev.
"""
from __future__ import annotations

import datetime
import enum
from typing import AsyncGenerator

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from hosted.config import DATABASE_URL


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AssessmentStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False)
    name = Column(String(255), nullable=False, default="")
    picture = Column(String(1024), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    profiles = relationship("Profile", back_populates="user", order_by="Profile.version.desc()")
    sessions = relationship("AssessmentSession", back_populates="user", order_by="AssessmentSession.created_at.desc()")
    reminders = relationship("CheckinReminder", back_populates="user", order_by="CheckinReminder.sent_at.desc()")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    content_md = Column(Text, nullable=False, default="")
    scores_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="profiles")

    __table_args__ = (
        UniqueConstraint("user_id", "version", name="uq_user_version"),
    )


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_json = Column(Text, nullable=False, default="[]")
    status = Column(Enum(AssessmentStatus), nullable=False, default=AssessmentStatus.in_progress)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")


class CheckinReminder(Base):
    __tablename__ = "checkin_reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sent_at = Column(DateTime, server_default=func.now(), nullable=False)
    responded_at = Column(DateTime, nullable=True)
    response_json = Column(Text, nullable=True)
    token = Column(String(128), unique=True, nullable=False, index=True)

    user = relationship("User", back_populates="reminders")


# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables() -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
