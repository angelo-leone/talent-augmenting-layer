"""Talent-Augmenting Layer -- Background scheduler for check-in reminders and Drive sync.

Uses APScheduler to run:
  - Daily 09:00 UTC: check-in reminders for overdue profile updates
  - Daily 02:00 UTC: anonymised export of chat transcripts/telemetry to Google Drive
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import logging
import os
import secrets

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, func

from hosted.config import CHECKIN_INTERVAL_DAYS
from hosted.database import (
    async_session_factory,
    User,
    Profile,
    CheckinReminder,
    ChatLog,
    PilotSurvey,
    compute_passive_ratio,
)
from hosted.email_service import send_checkin_reminder

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _check_and_send_reminders() -> None:
    """Daily job: find users whose last profile update is >= CHECKIN_INTERVAL_DAYS old
    and who haven't received a reminder in the last 7 days.  Send them a check-in email.
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=CHECKIN_INTERVAL_DAYS)
    recent_reminder_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)

    async with async_session_factory() as session:
        # Get all users who have at least one profile
        stmt = (
            select(User)
            .join(Profile, User.id == Profile.user_id)
            .group_by(User.id)
            .having(func.max(Profile.created_at) <= cutoff)
        )
        result = await session.execute(stmt)
        overdue_users = result.scalars().all()

        for user in overdue_users:
            # Check if we already sent a reminder recently
            recent_stmt = (
                select(CheckinReminder)
                .where(
                    CheckinReminder.user_id == user.id,
                    CheckinReminder.sent_at >= recent_reminder_cutoff,
                )
                .limit(1)
            )
            recent_result = await session.execute(recent_stmt)
            if recent_result.scalar_one_or_none() is not None:
                logger.debug("Skipping %s -- already reminded recently", user.email)
                continue

            # Get their latest profile scores for question generation
            profile_stmt = (
                select(Profile)
                .where(Profile.user_id == user.id)
                .order_by(Profile.version.desc())
                .limit(1)
            )
            profile_result = await session.execute(profile_stmt)
            latest_profile = profile_result.scalar_one_or_none()
            if not latest_profile:
                continue

            try:
                profile_data = json.loads(latest_profile.scores_json)
            except (json.JSONDecodeError, TypeError):
                profile_data = {}

            # Generate token and record the reminder
            token = secrets.token_urlsafe(48)
            reminder = CheckinReminder(
                user_id=user.id,
                token=token,
            )
            session.add(reminder)
            await session.flush()

            # Send the email
            success = await send_checkin_reminder(
                user_email=user.email,
                user_name=user.name or "there",
                profile_data=profile_data,
                checkin_token=token,
            )

            if success:
                logger.info("Check-in reminder sent to %s (token=%s)", user.email, token[:12])
            else:
                logger.warning("Failed to send check-in reminder to %s", user.email)

        await session.commit()


async def _export_pilot_data_to_drive() -> None:
    """Export anonymised pilot telemetry/survey data to a shared Google Drive folder.

    Runs at 02:00 UTC daily.  Uses OAuth 2.0 user credentials (refresh token)
    so the app uploads files as the folder owner — no service account sharing
    required.  Writes a single JSONL file per day named
    ``pilot-export-YYYY-MM-DD.jsonl`` into the Drive folder specified by
    ``GDRIVE_FOLDER_ID``.

    Each row is keyed by ``pilot_participant_id`` (a randomised opaque ID set
    during group assignment) — no email/name fields are exported.
    """
    from hosted.config import (
        GDRIVE_OAUTH_CLIENT_ID,
        GDRIVE_OAUTH_CLIENT_SECRET,
        GDRIVE_OAUTH_REFRESH_TOKEN,
        GDRIVE_FOLDER_ID,
        PILOT_EXPORT_ENABLED,
    )

    if not PILOT_EXPORT_ENABLED:
        return
    if not all([GDRIVE_OAUTH_CLIENT_ID, GDRIVE_OAUTH_CLIENT_SECRET,
                GDRIVE_OAUTH_REFRESH_TOKEN, GDRIVE_FOLDER_ID]):
        logger.warning("Drive export enabled but OAuth credentials/folder not configured — skipping")
        return

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
    except ImportError:
        logger.error("google-api-python-client / google-auth not installed — Drive export skipped")
        return

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    start_dt = datetime.datetime.combine(yesterday, datetime.time.min)
    end_dt = datetime.datetime.combine(today, datetime.time.min)

    rows: list[dict] = []
    async with async_session_factory() as session:
        # --- chat logs from yesterday -------------------------------------------------
        chat_stmt = (
            select(ChatLog, User.pilot_participant_id, User.pilot_group)
            .join(User, ChatLog.user_id == User.id)
            .where(ChatLog.created_at >= start_dt, ChatLog.created_at < end_dt)
            .order_by(ChatLog.created_at)
        )
        chat_result = await session.execute(chat_stmt)
        for log, pid, group in chat_result.all():
            if not pid:
                continue  # skip non-pilot users
            rows.append({
                "type": "chat_log",
                "participant_id": pid,
                "group": group.value if group else None,
                "session_id": log.session_id,
                "task_category": log.task_category.value if log.task_category else None,
                "domain": log.domain,
                "engagement_level": log.engagement_level.value if log.engagement_level else None,
                "skill_signal": log.skill_signal.value if log.skill_signal else None,
                "accepted_without_edit": log.accepted_without_edit,
                "ai_mode": log.ai_mode,
                "notes": log.notes,
                "timestamp": log.created_at.isoformat(),
            })

        # --- survey scores from yesterday --------------------------------------------
        survey_stmt = (
            select(PilotSurvey, User.pilot_participant_id, User.pilot_group)
            .join(User, PilotSurvey.user_id == User.id)
            .where(PilotSurvey.recorded_at >= start_dt, PilotSurvey.recorded_at < end_dt)
            .order_by(PilotSurvey.recorded_at)
        )
        survey_result = await session.execute(survey_stmt)
        for survey, pid, group in survey_result.all():
            if not pid:
                continue
            rows.append({
                "type": "survey",
                "participant_id": pid,
                "group": group.value if group else None,
                "timepoint": survey.timepoint.value if survey.timepoint else None,
                "taaq_score": survey.taaq_score,
                "m_csr_score": survey.m_csr_score,
                "m_ht_score": survey.m_ht_score,
                "e_gap_score": survey.e_gap_score,
                "nasa_mental": survey.nasa_tlx_mental,
                "nasa_physical": survey.nasa_tlx_physical,
                "nasa_temporal": survey.nasa_tlx_temporal,
                "nasa_performance": survey.nasa_tlx_performance,
                "nasa_effort": survey.nasa_tlx_effort,
                "nasa_frustration": survey.nasa_tlx_frustration,
                "nasa_composite": survey.nasa_tlx_composite,
                "timestamp": survey.recorded_at.isoformat(),
            })

        # --- passive ratios -----------------------------------------------------------
        pilot_users_stmt = (
            select(User)
            .where(User.pilot_participant_id.isnot(None))
        )
        pilot_result = await session.execute(pilot_users_stmt)
        for user in pilot_result.scalars().all():
            r_passive = await compute_passive_ratio(session, user.id)
            if r_passive is not None:
                rows.append({
                    "type": "passive_ratio",
                    "participant_id": user.pilot_participant_id,
                    "group": user.pilot_group.value if user.pilot_group else None,
                    "r_passive": r_passive,
                    "computed_date": today.isoformat(),
                })

    if not rows:
        logger.info("Drive export: no pilot data from %s — nothing to upload", yesterday)
        return

    # Build JSONL file in memory
    buf = io.BytesIO()
    for row in rows:
        buf.write((json.dumps(row, default=str) + "\n").encode())
    buf.seek(0)

    # Authenticate with OAuth user credentials and upload
    try:
        creds = Credentials(
            token=None,
            refresh_token=GDRIVE_OAUTH_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GDRIVE_OAUTH_CLIENT_ID,
            client_secret=GDRIVE_OAUTH_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        service = build("drive", "v3", credentials=creds, cache_discovery=False)

        file_name = f"pilot-export-{yesterday.isoformat()}.jsonl"
        file_metadata = {
            "name": file_name,
            "parents": [GDRIVE_FOLDER_ID],
            "mimeType": "application/jsonl",
        }
        media = MediaIoBaseUpload(buf, mimetype="application/jsonl", resumable=False)
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name",
        ).execute()
        logger.info("Drive export: uploaded %s (%d rows) — file id %s",
                     file_name, len(rows), uploaded.get("id"))
    except Exception:
        logger.exception("Drive export failed")


def setup_scheduler() -> AsyncIOScheduler:
    """Configure and return the scheduler. Call ``scheduler.start()`` from app startup."""
    scheduler.add_job(
        _check_and_send_reminders,
        trigger=CronTrigger(hour=9, minute=0),  # 09:00 UTC daily
        id="checkin_reminders",
        name="Send 2-week check-in reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        _export_pilot_data_to_drive,
        trigger=CronTrigger(hour=2, minute=0),  # 02:00 UTC daily
        id="pilot_drive_export",
        name="Export anonymised pilot data to Google Drive",
        replace_existing=True,
    )
    return scheduler
