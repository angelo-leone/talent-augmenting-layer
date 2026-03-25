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
    Float,
    Boolean,
    Enum,
    ForeignKey,
    UniqueConstraint,
    func,
    select,
    case,
    text,
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


class PilotGroup(str, enum.Enum):
    control = "control"
    treatment = "treatment"


class SurveyTimepoint(str, enum.Enum):
    baseline = "baseline"          # Day 0
    midpoint = "midpoint"          # Day 10
    endline = "endline"            # Day 21
    followup = "followup"          # Day 35 (2-week post)


class TaskCategory(str, enum.Enum):
    automate = "automate"
    augment = "augment"
    coach = "coach"
    protect = "protect"
    hands_off = "hands_off"


class EngagementLevel(str, enum.Enum):
    passive = "passive"
    active = "active"
    critical = "critical"


class SkillSignal(str, enum.Enum):
    growth = "growth"
    stable = "stable"
    atrophy = "atrophy"
    none = "none"


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

    # ── Vanguard Pilot fields ──
    pilot_group = Column(Enum(PilotGroup), nullable=True)
    pilot_participant_id = Column(String(32), unique=True, nullable=True, index=True)

    # ── Toggle Off: automation-only mode ──
    automation_mode = Column(Boolean, default=False, nullable=False, server_default="0")

    profiles = relationship("Profile", back_populates="user", order_by="Profile.version.desc()")
    sessions = relationship("AssessmentSession", back_populates="user", order_by="AssessmentSession.created_at.desc()")
    reminders = relationship("CheckinReminder", back_populates="user", order_by="CheckinReminder.sent_at.desc()")
    surveys = relationship("PilotSurvey", back_populates="user", order_by="PilotSurvey.recorded_at.desc()")
    chat_logs = relationship("ChatLog", back_populates="user", order_by="ChatLog.created_at.desc()")


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
# Vanguard Pilot: Survey & Assessment Scores
# ---------------------------------------------------------------------------

class PilotSurvey(Base):
    """Stores per-user, per-timepoint RCT survey/assessment scores.

    Metrics from Experimental Design:
      - TAAQ: Talent Augmenting Assessment Questionnaire (composite)
      - M_CSR: Cold Start Refactor score (can user solve without AI?)
      - M_HT: Hallucination Trap Detection score (does user catch errors?)
      - E_gap: Explainability Gap (can user explain AI-assisted decisions?)
      - NASA-TLX: Subjective workload (6 sub-scales, 0-100 each)
    """
    __tablename__ = "pilot_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    timepoint = Column(Enum(SurveyTimepoint), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False)

    # TAAQ composite (0-10 scale, same as TALRI)
    taaq_score = Column(Float, nullable=True)
    taaq_subscores_json = Column(Text, nullable=True)  # {"adr": 4, "gp": 7, "ali": 6, "esa_mean": 3.5}

    # Cold Start Refactor M_CSR (0-100, task performance without AI)
    m_csr_score = Column(Float, nullable=True)
    m_csr_details_json = Column(Text, nullable=True)  # {"task_id": "...", "time_s": 120, "correctness": 0.85}

    # Hallucination Trap Detection M_HT (0-100, error detection rate)
    m_ht_score = Column(Float, nullable=True)
    m_ht_details_json = Column(Text, nullable=True)  # {"traps_presented": 5, "traps_caught": 3, "false_positives": 1}

    # Explainability Gap E_gap (0-100, explanation quality)
    e_gap_score = Column(Float, nullable=True)
    e_gap_details_json = Column(Text, nullable=True)  # {"explanation_quality": 72, "reasoning_depth": 3}

    # NASA-TLX subjective workload (0-100 per sub-scale)
    nasa_tlx_mental = Column(Float, nullable=True)
    nasa_tlx_physical = Column(Float, nullable=True)
    nasa_tlx_temporal = Column(Float, nullable=True)
    nasa_tlx_performance = Column(Float, nullable=True)
    nasa_tlx_effort = Column(Float, nullable=True)
    nasa_tlx_frustration = Column(Float, nullable=True)
    nasa_tlx_composite = Column(Float, nullable=True)  # Weighted average

    # Raw responses JSON for auditing
    raw_responses_json = Column(Text, nullable=True)

    user = relationship("User", back_populates="surveys")

    __table_args__ = (
        UniqueConstraint("user_id", "timepoint", name="uq_user_timepoint"),
    )


# ---------------------------------------------------------------------------
# Vanguard Pilot: Chat Session Telemetry
# ---------------------------------------------------------------------------

class ChatLog(Base):
    """Per-interaction telemetry captured from <tal_log> blocks.

    Each row = one LLM interaction turn with structured metadata
    for computing R_passive and tracking skill signals over time.
    """
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(128), nullable=True, index=True)  # Groups turns within a conversation
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Structured telemetry from <tal_log>
    task_category = Column(Enum(TaskCategory), nullable=True)
    domain = Column(String(255), nullable=True)
    engagement_level = Column(Enum(EngagementLevel), nullable=True)
    skill_signal = Column(Enum(SkillSignal), nullable=True)
    notes = Column(Text, nullable=True)

    # Whether the user accepted AI output without critical editing
    accepted_without_edit = Column(Boolean, nullable=True)

    # The mode the AI used (automation_only when toggle-off is active)
    ai_mode = Column(String(64), nullable=True)  # "standard" | "automation_only"

    # Full turn payload for audit trail
    turn_payload_json = Column(Text, nullable=True)

    user = relationship("User", back_populates="chat_logs")


async def compute_passive_ratio(db: AsyncSession, user_id: int, days: int | None = None) -> float:
    """Compute Engagement Passive Ratio (R_passive) for a user.

    R_passive = count(engagement_level == 'passive') / count(all logged interactions)

    Args:
        db: Async database session
        user_id: User to compute for
        days: If set, only consider the last N days. None = all time.

    Returns:
        Float 0.0–1.0. Returns 0.0 if no interactions logged.
    """
    filters = [ChatLog.user_id == user_id]
    if days is not None:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        filters.append(ChatLog.created_at >= cutoff)

    total_stmt = select(func.count(ChatLog.id)).where(*filters)
    passive_stmt = select(func.count(ChatLog.id)).where(
        *filters,
        ChatLog.engagement_level == EngagementLevel.passive,
    )

    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    if total == 0:
        return 0.0

    passive_result = await db.execute(passive_stmt)
    passive = passive_result.scalar() or 0
    return passive / total


# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables() -> None:
    """Create all tables if they don't exist, and add any missing columns."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Migrate existing tables: add columns that may be missing.
        # CREATE_ALL only creates new tables; it won't ALTER existing ones.
        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS pilot_group VARCHAR(50)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS pilot_participant_id VARCHAR(32)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS automation_mode BOOLEAN NOT NULL DEFAULT FALSE",
        ]
        for stmt in migrations:
            await conn.execute(text(stmt))


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
