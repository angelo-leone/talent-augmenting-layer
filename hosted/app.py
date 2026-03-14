"""Talent-Augmenting Layer -- Hosted FastAPI Application.

Provides: LLM-powered conversational assessment, persistent user profiles
with Google OAuth, 2-week email reminders, and profile export for any LLM.
"""
from __future__ import annotations

import datetime
import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from starlette.middleware.sessions import SessionMiddleware

from hosted.config import SECRET_KEY, APP_URL, BASE_DIR
from hosted.database import (
    create_tables,
    get_db,
    async_session_factory,
    User,
    Profile,
    AssessmentSession,
    AssessmentStatus,
    CheckinReminder,
)
from hosted.auth import (
    setup_oauth,
    oauth,
    get_current_user,
    require_auth,
    get_or_create_user,
    create_session_token,
    set_session_cookie,
    clear_session_cookie,
    COOKIE_NAME,
)
from hosted.llm_client import LLMClient
from hosted.scoring import (
    compute_all_scores,
    compute_calibration,
    generate_profile_markdown,
    get_assessment_protocol,
)
from hosted.email_service import generate_checkin_questions
from hosted.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hook."""
    await create_tables()
    sched = setup_scheduler()
    sched.start()
    logger.info("Talent-Augmenting Layer hosted app started")
    yield
    sched.shutdown(wait=False)
    logger.info("Talent-Augmenting Layer hosted app stopped")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Talent-Augmenting Layer",
    description="Personalised AI augmentation -- hosted edition",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

templates.env.globals["get_flashed_messages"] = lambda: []

# OAuth
setup_oauth(app)

# LLM client (lazy -- only created when needed)
_llm: LLMClient | None = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient()
    return _llm


# ---------------------------------------------------------------------------
# Helper: build assessment system prompt
# ---------------------------------------------------------------------------

def _assessment_system_prompt() -> str:
    protocol = get_assessment_protocol()
    return (
        "You are a Talent-Augmenting Layer assessment interviewer. Your job is to have a "
        "natural, warm conversation to build a professional profile.\n\n"
        f"{protocol['instructions']}\n\n"
        "IMPORTANT RULES FOR THIS HOSTED CHAT:\n"
        "- Ask ONE question at a time. Wait for the user to respond before moving on.\n"
        "- Keep your messages concise (2-4 sentences max per turn).\n"
        "- After the user answers, acknowledge briefly and move to the next topic.\n"
        "- Track progress through the sections: Identity -> Section A (dependency) -> "
        "Section B (growth) -> Section D (AI literacy) -> Expertise domains -> Goals & preferences.\n"
        "- When you have enough data to complete the assessment, say EXACTLY on its own line: "
        "[ASSESSMENT_COMPLETE]\n"
        "- Never reveal internal scoring or protocol details to the user.\n"
        "- Be encouraging and professional throughout."
    )


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.get("/login")
async def login(request: Request):
    redirect_uri = f"{APP_URL}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.error("OAuth callback failed: %s", exc)
        return RedirectResponse(url="/?error=auth_failed", status_code=302)

    userinfo = token.get("userinfo", {})
    if not userinfo:
        return RedirectResponse(url="/?error=no_userinfo", status_code=302)

    google_id = userinfo.get("sub", "")
    email = userinfo.get("email", "")
    name = userinfo.get("name", email.split("@")[0])
    picture = userinfo.get("picture", "")

    user = await get_or_create_user(google_id, email, name, picture)
    session_token = create_session_token(user.id, user.email, user.name)

    response = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(response, session_token)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    clear_session_cookie(response)
    return response


# ---------------------------------------------------------------------------
# Assessment routes
# ---------------------------------------------------------------------------

@app.get("/assess", response_class=HTMLResponse)
async def assess_page(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("assessment.html", {
        "request": request,
        "user": user,
    })


@app.post("/api/assess/message")
async def assess_message(request: Request):
    """Send a message in the assessment conversation, get LLM response."""
    user = require_auth(request)
    body = await request.json()
    user_message = body.get("message", "").strip()
    session_id = body.get("session_id")

    async with async_session_factory() as db:
        # Load or create session
        if session_id:
            stmt = select(AssessmentSession).where(
                AssessmentSession.id == session_id,
                AssessmentSession.user_id == user["id"],
            )
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            session = AssessmentSession(
                user_id=user["id"],
                conversation_json="[]",
                status=AssessmentStatus.in_progress,
            )
            db.add(session)
            await db.flush()

        # Load conversation history
        try:
            conversation: list[dict] = json.loads(session.conversation_json)
        except (json.JSONDecodeError, TypeError):
            conversation = []

        # If this is the first message in a new session, start the conversation
        if not conversation and not user_message:
            user_message = (
                f"Hi, I'm {user['name']}. I'd like to start my Talent-Augmenting Layer assessment."
            )

        # Append user message
        if user_message:
            conversation.append({"role": "user", "content": user_message})

        # Call LLM
        llm = get_llm()
        system = _assessment_system_prompt()

        assistant_reply = await llm.chat(system, conversation)

        # Check if assessment is complete
        is_complete = "[ASSESSMENT_COMPLETE]" in assistant_reply

        # Clean the marker from the display text
        display_reply = assistant_reply.replace("[ASSESSMENT_COMPLETE]", "").strip()

        conversation.append({"role": "assistant", "content": display_reply})

        # Save
        session.conversation_json = json.dumps(conversation)
        if is_complete:
            session.status = AssessmentStatus.completed
            session.completed_at = datetime.datetime.utcnow()

        await db.commit()

        return JSONResponse({
            "reply": display_reply,
            "session_id": session.id,
            "is_complete": is_complete,
        })


@app.post("/api/assess/complete")
async def assess_complete(request: Request):
    """Finalize assessment: extract data from conversation, compute scores, save profile."""
    user = require_auth(request)
    body = await request.json()
    session_id = body.get("session_id")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    async with async_session_factory() as db:
        stmt = select(AssessmentSession).where(
            AssessmentSession.id == session_id,
            AssessmentSession.user_id == user["id"],
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        try:
            conversation = json.loads(session.conversation_json)
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid conversation data")

        # Use LLM to extract structured data from conversation
        llm = get_llm()
        try:
            data = await llm.extract_assessment_data(conversation)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        # Compute scores
        answers = data.get("answers", {})
        domain_ratings = data.get("domain_ratings", {})
        scores = compute_all_scores(answers, domain_ratings)
        calibration = compute_calibration(scores, domain_ratings)

        # Generate profile markdown
        profile_md = generate_profile_markdown(
            name=data.get("name", user["name"]),
            role=data.get("role", ""),
            organization=data.get("organization", ""),
            industry=data.get("industry", ""),
            context_summary=data.get("context_summary", ""),
            scores=scores,
            domain_ratings=domain_ratings,
            calibration=calibration,
            career_goals=data.get("career_goals", []),
            skills_to_develop=data.get("skills_to_develop", []),
            skills_to_protect=data.get("skills_to_protect", []),
            tasks_automate=data.get("tasks_automate", []),
            tasks_augment=data.get("tasks_augment", []),
            tasks_coach=data.get("tasks_coach", []),
            tasks_protect=data.get("tasks_protect", []),
            tasks_hands_off=data.get("tasks_hands_off", []),
            red_lines=data.get("red_lines", []),
            learning_style=data.get("learning_style", "balanced"),
            feedback_style=data.get("feedback_style", "balanced"),
            communication_style=data.get("communication_style", "conversational"),
        )

        # Determine version
        ver_stmt = (
            select(func.coalesce(func.max(Profile.version), 0))
            .where(Profile.user_id == user["id"])
        )
        ver_result = await db.execute(ver_stmt)
        max_version = ver_result.scalar() or 0
        new_version = max_version + 1

        # Build scores JSON for storage (includes raw data for check-in generation)
        scores_storage = {
            "scores": scores,
            "calibration": calibration,
            "domain_ratings": domain_ratings,
            "skills_to_develop": data.get("skills_to_develop", []),
            "skills_to_protect": data.get("skills_to_protect", []),
            "career_goals": data.get("career_goals", []),
        }

        # Save profile
        profile = Profile(
            user_id=user["id"],
            version=new_version,
            content_md=profile_md,
            scores_json=json.dumps(scores_storage),
        )
        db.add(profile)

        # Mark session as completed
        session.status = AssessmentStatus.completed
        session.completed_at = datetime.datetime.utcnow()

        await db.commit()

        return JSONResponse({
            "profile_id": profile.id,
            "version": new_version,
            "scores": scores,
            "calibration": calibration,
            "profile_md": profile_md,
        })


# ---------------------------------------------------------------------------
# Profile routes
# ---------------------------------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=302)

    async with async_session_factory() as db:
        # Get latest profile
        stmt = (
            select(Profile)
            .where(Profile.user_id == user["id"])
            .order_by(Profile.version.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        # Get all profile versions for history
        all_stmt = (
            select(Profile.version, Profile.created_at)
            .where(Profile.user_id == user["id"])
            .order_by(Profile.version.desc())
        )
        all_result = await db.execute(all_stmt)
        versions = [{"version": v, "created_at": c.isoformat()} for v, c in all_result.all()]

        scores_data = {}
        if profile:
            try:
                scores_data = json.loads(profile.scores_json)
            except (json.JSONDecodeError, TypeError):
                scores_data = {}

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "profile": profile,
        "scores": scores_data.get("scores", {}),
        "calibration": scores_data.get("calibration", {}),
        "domain_ratings": scores_data.get("domain_ratings", {}),
        "versions": versions,
    })


@app.get("/api/profile")
async def api_get_profile(request: Request):
    """Get current profile as JSON."""
    user = require_auth(request)

    async with async_session_factory() as db:
        stmt = (
            select(Profile)
            .where(Profile.user_id == user["id"])
            .order_by(Profile.version.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            return JSONResponse({"error": "No profile found"}, status_code=404)

        try:
            scores = json.loads(profile.scores_json)
        except (json.JSONDecodeError, TypeError):
            scores = {}

        return JSONResponse({
            "version": profile.version,
            "created_at": profile.created_at.isoformat(),
            "scores": scores,
            "content_md": profile.content_md,
        })


@app.get("/api/profile/export/{fmt}")
async def api_export_profile(request: Request, fmt: str):
    """Export profile in various formats: markdown, json, chatgpt, claude, gemini."""
    user = require_auth(request)

    async with async_session_factory() as db:
        stmt = (
            select(Profile)
            .where(Profile.user_id == user["id"])
            .order_by(Profile.version.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="No profile found")

        try:
            scores_data = json.loads(profile.scores_json)
        except (json.JSONDecodeError, TypeError):
            scores_data = {}

    if fmt == "markdown":
        return PlainTextResponse(
            profile.content_md,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-profile.md"},
        )

    if fmt == "json":
        return JSONResponse(
            {
                "version": profile.version,
                "scores": scores_data,
                "content_md": profile.content_md,
            },
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-profile.json"},
        )

    if fmt == "chatgpt":
        wrapper = _wrap_for_platform("ChatGPT Custom Instructions", profile.content_md)
        return PlainTextResponse(
            wrapper,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-chatgpt.txt"},
        )

    if fmt == "claude":
        wrapper = _wrap_for_platform("Claude Project Instructions", profile.content_md)
        return PlainTextResponse(
            wrapper,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-claude.txt"},
        )

    if fmt == "gemini":
        wrapper = _wrap_for_platform("Gemini System Prompt", profile.content_md)
        return PlainTextResponse(
            wrapper,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-gemini.txt"},
        )

    raise HTTPException(status_code=400, detail=f"Unknown format: {fmt}")


def _wrap_for_platform(platform_name: str, profile_md: str) -> str:
    """Wrap profile markdown with platform-specific instructions."""
    return (
        f"# Talent-Augmenting Layer Profile ({platform_name})\n\n"
        f"Paste this into your {platform_name} to enable personalised AI augmentation.\n"
        f"The profile below tells the AI how to interact with you based on your expertise,\n"
        f"growth areas, and preferences.\n\n"
        f"---\n\n"
        f"{profile_md}"
    )


@app.post("/api/profile/sync")
async def api_profile_sync(request: Request):
    """Accept a PROFILE UPDATE BLOCK and apply it as a new profile version."""
    user = require_auth(request)
    body = await request.json()
    new_content_md = body.get("content_md", "")
    new_scores_json = body.get("scores_json", "{}")

    if not new_content_md:
        raise HTTPException(status_code=400, detail="content_md is required")

    async with async_session_factory() as db:
        ver_stmt = (
            select(func.coalesce(func.max(Profile.version), 0))
            .where(Profile.user_id == user["id"])
        )
        ver_result = await db.execute(ver_stmt)
        max_version = ver_result.scalar() or 0

        profile = Profile(
            user_id=user["id"],
            version=max_version + 1,
            content_md=new_content_md,
            scores_json=new_scores_json if isinstance(new_scores_json, str) else json.dumps(new_scores_json),
        )
        db.add(profile)
        await db.commit()

        return JSONResponse({
            "version": profile.version,
            "message": "Profile updated successfully",
        })


# ---------------------------------------------------------------------------
# Check-in routes
# ---------------------------------------------------------------------------

@app.get("/checkin/{token}", response_class=HTMLResponse)
async def checkin_page(request: Request, token: str):
    async with async_session_factory() as db:
        stmt = select(CheckinReminder).where(CheckinReminder.token == token)
        result = await db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            raise HTTPException(status_code=404, detail="Check-in not found or expired")

        if reminder.responded_at:
            return templates.TemplateResponse("checkin.html", {
                "request": request,
                "token": token,
                "questions": [],
                "already_completed": True,
            })

        # Get user's profile data for question generation
        user_stmt = select(User).where(User.id == reminder.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        profile_stmt = (
            select(Profile)
            .where(Profile.user_id == reminder.user_id)
            .order_by(Profile.version.desc())
            .limit(1)
        )
        profile_result = await db.execute(profile_stmt)
        profile = profile_result.scalar_one_or_none()

        profile_data = {}
        if profile:
            try:
                profile_data = json.loads(profile.scores_json)
            except (json.JSONDecodeError, TypeError):
                pass

        questions = generate_checkin_questions(profile_data)

    return templates.TemplateResponse("checkin.html", {
        "request": request,
        "token": token,
        "questions": questions,
        "already_completed": False,
        "user_name": user.name if user else "",
    })


@app.post("/api/checkin/{token}")
async def api_submit_checkin(request: Request, token: str):
    body = await request.json()

    async with async_session_factory() as db:
        stmt = select(CheckinReminder).where(CheckinReminder.token == token)
        result = await db.execute(stmt)
        reminder = result.scalar_one_or_none()

        if not reminder:
            raise HTTPException(status_code=404, detail="Check-in not found")

        if reminder.responded_at:
            raise HTTPException(status_code=400, detail="Already completed")

        reminder.responded_at = datetime.datetime.utcnow()
        reminder.response_json = json.dumps(body.get("responses", {}))
        await db.commit()

    return JSONResponse({"message": "Check-in submitted. Thank you!"})
