"""Talent-Augmenting OS: Email service for 2-week check-in reminders.

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
            "Significant growth: I learnt or improved noticeably",
            "Some growth: small wins and steady progress",
            "Flat: no real change",
            "Decline: I feel less sharp than before",
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
                "A little: I've been working on it",
                "Not yet: haven't had the chance",
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
                "Partly: I used AI but stayed hands-on",
                "Mostly AI-driven: I reviewed but didn't do the core work",
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
                "Less reliant: I'm doing more independently",
                "About the same",
                "More reliant: I'm delegating more to AI",
                "Much more reliant: I'd struggle without AI now",
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

    subject = f"Talent-Augmenting OS: Your 2-week check-in, {user_name}"
    body_text = (
        f"Hi {user_name},\n\n"
        f"It's been two weeks since your last Talent-Augmenting OS profile update. "
        f"Take 2 minutes to reflect on your growth:\n\n"
        + "\n".join(question_lines)
        + f"\n\nComplete your check-in here:\n{checkin_url}\n\n"
        f"This helps keep your AI calibration accurate and tracks your skill development over time.\n\n"
        f"📝 If you're using the Talent-Augmenting OS with external platforms (Gemini, ChatGPT, Claude),\n"
        f"please also remember to upload your conversation transcripts to the team Drive folder.\n\n"
        f"-- Talent-Augmenting OS\n"
        f"Making workers better, not dependent."
    )
    body_html = (
        f"<div style='font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; "
        f"background: #1a1a2e; color: #eee; padding: 2rem; border-radius: 12px;'>"
        f"<h2 style='color: #e94560;'>Talent-Augmenting OS Check-in</h2>"
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
        f"<p style='color: #ccc; font-size: 0.9em; margin-top: 2em; padding-top: 1.5em; border-top: 1px solid #333;'>"
        f"<strong>📝 Transcript Upload Reminder:</strong><br>"
        f"If you're using the Talent-Augmenting OS prompt on external platforms (Google Gemini, ChatGPT, Claude),\n"
        f"please export and upload your conversation transcripts to the team Drive folder this week.\n"
        f"This helps us capture the full picture of your AI-augmented work.</p>"
        f"<p style='color: #999; font-size: 0.85em; margin-top: 1.5em;'>"
        f"Talent-Augmenting OS: Making workers better, not dependent.</p>"
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


async def send_invite_email(
    to_email: str,
    org_name: str,
    inviter_name: str,
    role: str,
    invite_url: str,
) -> bool:
    """Send an org-membership invite email.

    Returns True if sent via SendGrid (or logged when no API key configured).
    """
    subject = f"{inviter_name} invited you to {org_name} on Talent-Augmenting OS"
    body_text = (
        f"Hi,\n\n"
        f"{inviter_name} has invited you to join {org_name} on Talent-Augmenting OS "
        f"as a {role}.\n\n"
        f"Accept here (sign in with Google):\n{invite_url}\n\n"
        f"If you weren't expecting this invite, you can ignore this email.\n\n"
        f"-- Talent-Augmenting OS"
    )
    body_html = (
        f"<div style='font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; "
        f"background: #1a1a2e; color: #eee; padding: 2rem; border-radius: 12px;'>"
        f"<h2 style='color: #e94560; margin-top: 0;'>You've been invited</h2>"
        f"<p><strong>{inviter_name}</strong> invited you to join "
        f"<strong>{org_name}</strong> on Talent-Augmenting OS as a <strong>{role}</strong>.</p>"
        f"<p style='margin-top: 1.5em;'>"
        f"<a href='{invite_url}' style='display: inline-block; padding: 0.75rem 1.5rem; "
        f"background: #e94560; color: white; text-decoration: none; border-radius: 8px; "
        f"font-weight: 600;'>Accept invite</a></p>"
        f"<p style='color: #999; font-size: 0.85em; margin-top: 2em; padding-top: 1.5em; "
        f"border-top: 1px solid #333;'>"
        f"If you weren't expecting this, ignore this email.<br>"
        f"Talent-Augmenting OS : making workers better, not dependent.</p>"
        f"</div>"
    )
    if SENDGRID_API_KEY:
        return await _send_via_sendgrid(to_email, subject, body_text, body_html)
    logger.info(
        "Invite email (logged, no SendGrid key):\n  To: %s\n  Org: %s\n  URL: %s",
        to_email, org_name, invite_url,
    )
    return True


async def _send_via_sendgrid(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str,
    reply_to_email: str | None = None,
    reply_to_name: str | None = None,
) -> bool:
    """Send email through SendGrid API.

    ``reply_to_email`` sets the ``Reply-To`` header so a recipient hitting
    Reply lands on a different address than ``FROM_EMAIL`` (used by the
    feedback form: from = noreply, reply-to = submitter).
    """
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Content, ReplyTo

        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
        )
        message.add_content(Content("text/plain", body_text))
        message.add_content(Content("text/html", body_html))
        if reply_to_email:
            message.reply_to = ReplyTo(email=reply_to_email, name=reply_to_name)

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            logger.info("Email sent to %s (status %d)", to_email, response.status_code)
            return True
        else:
            logger.error("SendGrid error: status %d, body %s", response.status_code, response.body)
            return False
    except Exception:
        logger.exception("Failed to send email via SendGrid to %s", to_email)
        return False


# ---------------------------------------------------------------------------
# Feedback / contact form
# ---------------------------------------------------------------------------

FEEDBACK_INBOX = "angelo.leone@public.io"


def _html_escape(value: str) -> str:
    """Minimal HTML escape for user-supplied content in the email body."""
    import html
    return html.escape(value, quote=True)


async def send_feedback_email(
    submitter_name: str,
    submitter_email: str,
    topic: str,
    message: str,
    company: str = "",
    role: str = "",
    user_agent: str | None = None,
    ip: str | None = None,
) -> bool:
    """Send a feedback / contact-form submission to the FEEDBACK_INBOX.

    The submitter's email goes in ``Reply-To`` so hitting reply in any
    mail client lands a draft to them, not back to ``FROM_EMAIL``.
    Returns True on send-or-log success.
    """
    display_name = (submitter_name or "").strip() or "(name not provided)"
    company_line = (company or "").strip() or "(not provided)"
    role_line = (role or "").strip() or "(not provided)"
    topic_line = (topic or "general").strip() or "general"

    subject = f"[TAOS feedback / {topic_line}] from {display_name}"

    body_text = (
        f"New TAOS feedback submission\n\n"
        f"Topic: {topic_line}\n"
        f"Name: {display_name}\n"
        f"Email: {submitter_email}\n"
        f"Company: {company_line}\n"
        f"Role: {role_line}\n\n"
        f"Message:\n{message}\n\n"
        f"--\n"
        f"User-Agent: {user_agent or '(unknown)'}\n"
        f"IP: {ip or '(unknown)'}\n"
    )

    body_html = (
        "<div style='font-family: -apple-system, sans-serif; max-width: 640px; "
        "margin: 0 auto; color: #0F172A; padding: 1.5rem;'>"
        "<h2 style='color: #2D6A4F; margin: 0 0 1rem;'>New TAOS feedback</h2>"
        "<table style='border-collapse: collapse; margin-bottom: 1rem; font-size: 0.95rem;'>"
        f"<tr><td style='padding: 0.25rem 0.75rem 0.25rem 0; color: #64748B;'>Topic</td><td>{_html_escape(topic_line)}</td></tr>"
        f"<tr><td style='padding: 0.25rem 0.75rem 0.25rem 0; color: #64748B;'>Name</td><td>{_html_escape(display_name)}</td></tr>"
        f"<tr><td style='padding: 0.25rem 0.75rem 0.25rem 0; color: #64748B;'>Email</td>"
        f"<td><a href='mailto:{_html_escape(submitter_email)}'>{_html_escape(submitter_email)}</a></td></tr>"
        f"<tr><td style='padding: 0.25rem 0.75rem 0.25rem 0; color: #64748B;'>Company</td><td>{_html_escape(company_line)}</td></tr>"
        f"<tr><td style='padding: 0.25rem 0.75rem 0.25rem 0; color: #64748B;'>Role</td><td>{_html_escape(role_line)}</td></tr>"
        "</table>"
        "<div style='background: #F7F5EE; padding: 1rem; border-radius: 8px; "
        "white-space: pre-wrap; line-height: 1.55;'>"
        f"{_html_escape(message)}"
        "</div>"
        "<p style='color: #94A3B8; font-size: 0.78rem; margin-top: 1.5rem;'>"
        f"UA: {_html_escape(user_agent or '(unknown)')}<br>"
        f"IP: {_html_escape(ip or '(unknown)')}"
        "</p></div>"
    )

    if SENDGRID_API_KEY:
        return await _send_via_sendgrid(
            FEEDBACK_INBOX,
            subject,
            body_text,
            body_html,
            reply_to_email=submitter_email,
            reply_to_name=display_name,
        )

    logger.info(
        "Feedback email (logged, no SendGrid key):\n  To: %s\n  Subject: %s\n  From submitter: %s <%s>\n  Body:\n%s",
        FEEDBACK_INBOX,
        subject,
        display_name,
        submitter_email,
        body_text,
    )
    return True
