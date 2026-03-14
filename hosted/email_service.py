"""Talent-Augmenting Layer -- Email service for 2-week check-in reminders.

Uses SendGrid when SENDGRID_API_KEY is set; otherwise falls back to logging.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from hosted.config import SENDGRID_API_KEY, FROM_EMAIL, APP_URL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------

def generate_checkin_questions(profile_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate 3-5 targeted check-in questions from profile data.

    Focuses on coaching domains, protected skills, and growth trajectory.
    Each question is a dict with ``id``, ``text``, ``type`` (choice / text),
    and optional ``options`` list.
    """
    questions: list[dict[str, Any]] = []
    scores = profile_data.get("scores", {})
    esa = scores.get("esa", {})
    weak_domains = esa.get("weak_domains", [])
    strong_domains = esa.get("strong_domains", [])
    skills_to_protect = profile_data.get("skills_to_protect", [])
    skills_to_develop = profile_data.get("skills_to_develop", [])

    # Q1: General progress pulse
    questions.append({
        "id": "q_progress",
        "text": "Over the past two weeks, how would you rate your professional growth?",
        "type": "choice",
        "options": [
            "Significant growth -- I learnt or improved noticeably",
            "Some growth -- small wins and steady progress",
            "Flat -- no real change",
            "Decline -- I feel less sharp than before",
        ],
    })

    # Q2: Coaching domain focus
    if weak_domains:
        domain = weak_domains[0]
        questions.append({
            "id": "q_coaching_domain",
            "text": f"You flagged '{domain}' as a growth area. In the past two weeks, did you practice this skill independently (without AI doing it for you)?",
            "type": "choice",
            "options": [
                "Yes, multiple times",
                "Once or twice",
                "No, but I plan to",
                "No, and I've been relying on AI for it",
            ],
        })
    elif skills_to_develop:
        skill = skills_to_develop[0]
        questions.append({
            "id": "q_coaching_domain",
            "text": f"You want to develop '{skill}'. Have you made any progress on this in the past two weeks?",
            "type": "choice",
            "options": [
                "Yes, real progress",
                "A little -- I've been working on it",
                "Not yet -- haven't had the chance",
                "I've actually been delegating this to AI more",
            ],
        })

    # Q3: Protected skill check
    if skills_to_protect:
        skill = skills_to_protect[0]
        questions.append({
            "id": "q_protected_skill",
            "text": f"'{skill}' is a skill you want to protect from atrophy. Have you done this independently recently?",
            "type": "choice",
            "options": [
                "Yes, I did it myself this week",
                "Partly -- I used AI but stayed hands-on",
                "Mostly AI-driven -- I reviewed but didn't do the core work",
                "I haven't done this task recently",
            ],
        })

    # Q4: AI dependency self-check
    adr_score = scores.get("adr", {}).get("score", 5)
    if adr_score >= 5:
        questions.append({
            "id": "q_dependency_check",
            "text": "Compared to two weeks ago, how reliant on AI do you feel?",
            "type": "choice",
            "options": [
                "Less reliant -- I'm doing more independently",
                "About the same",
                "More reliant -- I'm delegating more to AI",
                "Much more reliant -- I'd struggle without AI now",
            ],
        })

    # Q5: Open reflection
    questions.append({
        "id": "q_open",
        "text": "Anything else to share? A win, a concern, or something you'd like your AI to adjust?",
        "type": "text",
    })

    return questions[:5]


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

async def send_checkin_reminder(
    user_email: str,
    user_name: str,
    profile_data: dict[str, Any],
    checkin_token: str,
) -> bool:
    """Send a 2-week check-in reminder email.

    Returns True if the email was sent (or logged) successfully.
    """
    questions = generate_checkin_questions(profile_data)
    checkin_url = f"{APP_URL}/checkin/{checkin_token}"

    # Build a simple text summary of questions for the email body
    question_lines = []
    for i, q in enumerate(questions, 1):
        question_lines.append(f"  {i}. {q['text']}")

    subject = f"Talent-Augmenting Layer -- Your 2-week check-in, {user_name}"
    body_text = (
        f"Hi {user_name},\n\n"
        f"It's been two weeks since your last Talent-Augmenting Layer profile update. "
        f"Take 2 minutes to reflect on your growth:\n\n"
        + "\n".join(question_lines)
        + f"\n\nComplete your check-in here:\n{checkin_url}\n\n"
        f"This helps keep your AI calibration accurate and tracks your skill development over time.\n\n"
        f"-- Talent-Augmenting Layer\n"
        f"Making workers better, not dependent."
    )
    body_html = (
        f"<div style='font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; "
        f"background: #1a1a2e; color: #eee; padding: 2rem; border-radius: 12px;'>"
        f"<h2 style='color: #e94560;'>Talent-Augmenting Layer Check-in</h2>"
        f"<p>Hi {user_name},</p>"
        f"<p>It's been two weeks since your last profile update. "
        f"Take 2 minutes to reflect on your growth:</p>"
        f"<ol style='padding-left: 1.2em;'>"
    )
    for q in questions:
        body_html += f"<li style='margin-bottom: 0.5em;'>{q['text']}</li>"
    body_html += (
        f"</ol>"
        f"<p style='margin-top: 1.5em;'>"
        f"<a href='{checkin_url}' style='display: inline-block; padding: 0.75rem 1.5rem; "
        f"background: #e94560; color: white; text-decoration: none; border-radius: 8px; "
        f"font-weight: 600;'>Complete Check-in</a></p>"
        f"<p style='color: #999; font-size: 0.85em; margin-top: 2em;'>"
        f"Talent-Augmenting Layer -- Making workers better, not dependent.</p>"
        f"</div>"
    )

    if SENDGRID_API_KEY:
        return await _send_via_sendgrid(user_email, subject, body_text, body_html)

    # Fallback: log the email
    logger.info(
        "Email (logged, no SendGrid key):\n  To: %s\n  Subject: %s\n  URL: %s",
        user_email,
        subject,
        checkin_url,
    )
    return True


async def _send_via_sendgrid(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str,
) -> bool:
    """Send email through SendGrid API."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Content

        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
        )
        message.add_content(Content("text/plain", body_text))
        message.add_content(Content("text/html", body_html))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info("Check-in email sent to %s (status %d)", to_email, response.status_code)
            return True
        else:
            logger.error("SendGrid error: status %d, body %s", response.status_code, response.body)
            return False
    except Exception:
        logger.exception("Failed to send email via SendGrid to %s", to_email)
        return False
