"""Talent-Augmenting Layer -- Background scheduler for check-in reminders.

Uses APScheduler to run a daily job that identifies users overdue for a
profile check-in and sends them a reminder email.
"""
from __future__ import annotations

import datetime
import json
import logging
import secrets

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, func

from hosted.config import CHECKIN_INTERVAL_DAYS
from hosted.database import async_session_factory, User, Profile, CheckinReminder
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


def setup_scheduler() -> AsyncIOScheduler:
    """Configure and return the scheduler. Call ``scheduler.start()`` from app startup."""
    scheduler.add_job(
        _check_and_send_reminders,
        trigger=CronTrigger(hour=9, minute=0),  # 09:00 UTC daily
        id="checkin_reminders",
        name="Send 2-week check-in reminders",
        replace_existing=True,
    )
    return scheduler
