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
    PilotSurvey,
    SurveyTimepoint,
    ChatLog,
    TaskCategory,
    EngagementLevel,
    SkillSignal,
    compute_passive_ratio,
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
    compute_esa,
    generate_profile_markdown,
    get_assessment_protocol,
)
from hosted.email_service import generate_checkin_questions
from hosted.scheduler import setup_scheduler
from hosted.mcp_sse_handler import (
    handle_sse_get,
    handle_sse_post,
    get_sse_config,
)

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

_ASSESSMENT_MAX_TURNS = 40  # Hard ceiling to prevent infinite loops


def _assessment_system_prompt(turn_count: int = 0) -> str:
    protocol = get_assessment_protocol()

    # Dynamic urgency instruction based on turn count
    pacing = ""
    if turn_count >= 30:
        pacing = (
            "\n\n⚠️ CRITICAL: You have used most of the allocated turns. "
            "You MUST wrap up NOW. Summarise what you have, thank the user, "
            "and output [ASSESSMENT_COMPLETE] on its own line immediately. "
            "Do NOT ask any more questions.\n"
        )
    elif turn_count >= 22:
        pacing = (
            "\n\nURGENT PACING: You are running long. Skip any remaining sections "
            "that haven't been covered and move directly to wrap-up. Ask at most "
            "ONE more question, then output [ASSESSMENT_COMPLETE].\n"
        )
    elif turn_count >= 16:
        pacing = (
            "\n\nPACING REMINDER: You are past the halfway point. Make sure you have "
            "covered the most important sections. Start wrapping up the current section "
            "and move toward completion.\n"
        )

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
        "- DOMAIN LIMIT: When collecting expertise domains, ask for their TOP 3-5 domains "
        "ONLY. After 5 domains, stop asking and move on to Goals & preferences. Do NOT keep "
        "asking 'any other domains?' in a loop.\n"
        "- You have a HARD LIMIT of approximately 20 assistant turns total. Plan accordingly.\n"
        "- When you have enough data to complete the assessment, say EXACTLY on its own line: "
        "[ASSESSMENT_COMPLETE]\n"
        "- If you are running low on turns, prioritise the most important data and wrap up.\n"
        "- Never reveal internal scoring or protocol details to the user.\n"
        "- Be encouraging and professional throughout."
        f"{pacing}"
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
    return templates.TemplateResponse(name="login.html", request=request)


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
    return templates.TemplateResponse(name="assessment.html", request=request, context={
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

        # Count assistant turns for pacing / hard limit
        assistant_turn_count = sum(1 for m in conversation if m["role"] == "assistant")

        # Hard ceiling: auto-complete if too many turns
        if assistant_turn_count >= _ASSESSMENT_MAX_TURNS:
            is_complete = True
            display_reply = (
                "Thank you for going through the assessment! I have all the information "
                "I need to build your profile. Click the button below to generate it."
            )
            conversation.append({"role": "assistant", "content": display_reply})
            session.conversation_json = json.dumps(conversation)
            session.status = AssessmentStatus.completed
            session.completed_at = datetime.datetime.utcnow()
            await db.commit()
            return JSONResponse({
                "reply": display_reply,
                "session_id": session.id,
                "is_complete": True,
            })

        # Call LLM with turn-aware system prompt
        llm = get_llm()
        system = _assessment_system_prompt(turn_count=assistant_turn_count)

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

        # Get automation mode
        auto_stmt = select(User.automation_mode).where(User.id == user["id"])
        auto_result = await db.execute(auto_stmt)
        automation_mode = bool(auto_result.scalar_one_or_none())

    return templates.TemplateResponse(name="dashboard.html", request=request, context={
        "user": user,
        "profile": profile,
        "scores": scores_data.get("scores", {}),
        "calibration": scores_data.get("calibration", {}),
        "domain_ratings": scores_data.get("domain_ratings", {}),
        "versions": versions,
        "automation_mode": automation_mode,
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

        # Check automation mode
        user_row = (await db.execute(select(User).where(User.id == user["id"]))).scalar_one_or_none()
        auto_mode = user_row.automation_mode if user_row else False

        try:
            scores_data = json.loads(profile.scores_json)
        except (json.JSONDecodeError, TypeError):
            scores_data = {}

    content_md = profile.content_md
    if auto_mode:
        content_md += "\n\n<mode>automation_only</mode>\n"

    if fmt == "markdown":
        return PlainTextResponse(
            content_md,
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-profile.md"},
        )

    if fmt == "json":
        return JSONResponse(
            {
                "version": profile.version,
                "scores": scores_data,
                "content_md": content_md,
                "automation_mode": auto_mode,
            },
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-profile.json"},
        )

    if fmt == "chatgpt":
        wrapper = _wrap_for_platform("ChatGPT Custom Instructions", content_md)
        return PlainTextResponse(
            wrapper,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-chatgpt.txt"},
        )

    if fmt == "claude":
        wrapper = _wrap_for_platform("Claude Project Instructions", content_md)
        return PlainTextResponse(
            wrapper,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=talent-augmenting-layer-claude.txt"},
        )

    if fmt == "gemini":
        wrapper = _wrap_for_platform("Gemini System Prompt", content_md)
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


@app.post("/api/profile/evolve")
async def api_profile_evolve(request: Request):
    """Incrementally evolve a user's profile based on accumulated chat telemetry.

    Called periodically (e.g. after N interactions) by the MCP server or a cron job.
    Reads the latest profile + recent ChatLog entries, computes skill signal
    deltas, and creates a new profile version with updated domain ratings.
    """
    user = require_auth(request)

    async with async_session_factory() as db:
        # Get latest profile
        prof_stmt = (
            select(Profile)
            .where(Profile.user_id == user["id"])
            .order_by(Profile.version.desc())
            .limit(1)
        )
        prof_result = await db.execute(prof_stmt)
        profile = prof_result.scalar_one_or_none()

        if not profile:
            raise HTTPException(status_code=404, detail="No profile to evolve — run assessment first")

        try:
            scores_data = json.loads(profile.scores_json)
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=500, detail="Corrupt profile scores")

        domain_ratings = scores_data.get("domain_ratings", {})

        # Aggregate skill signals from recent chat logs (since last profile version)
        log_stmt = (
            select(ChatLog)
            .where(
                ChatLog.user_id == user["id"],
                ChatLog.created_at >= profile.created_at,
                ChatLog.skill_signal.isnot(None),
            )
            .order_by(ChatLog.created_at)
        )
        log_result = await db.execute(log_stmt)
        logs = log_result.scalars().all()

        if not logs:
            return JSONResponse({"message": "No new signals — profile unchanged", "version": profile.version})

        # Aggregate signals per domain
        domain_signals: dict[str, list[str]] = {}
        for log in logs:
            d = log.domain or "general"
            if d not in domain_signals:
                domain_signals[d] = []
            if log.skill_signal:
                domain_signals[d].append(log.skill_signal.value)

        # Compute deltas: net growth vs atrophy signals per domain
        changes_made = False
        for domain, signals in domain_signals.items():
            growth_count = signals.count("growth")
            atrophy_count = signals.count("atrophy")
            net = growth_count - atrophy_count

            if domain in domain_ratings and abs(net) >= 3:
                old_rating = domain_ratings[domain]
                if net >= 3:
                    domain_ratings[domain] = min(5, old_rating + 1)
                elif net <= -3:
                    domain_ratings[domain] = max(1, old_rating - 1)
                if domain_ratings[domain] != old_rating:
                    changes_made = True

        if not changes_made:
            return JSONResponse({"message": "Signals insufficient for rating change", "version": profile.version})

        # Recompute scores with updated domain ratings
        answers = scores_data.get("scores", {})
        raw_answers = {}
        for section in ("adr", "gp", "ali"):
            if section in answers and "raw" in answers[section]:
                # Reconstruct approximate raw answers from stored raw averages
                pass
        # Use existing section scores directly — only domain ratings changed
        new_scores = scores_data.get("scores", {})
        new_scores["esa"] = compute_esa(domain_ratings)
        new_calibration = compute_calibration(new_scores, domain_ratings)

        scores_data["scores"] = new_scores
        scores_data["calibration"] = new_calibration
        scores_data["domain_ratings"] = domain_ratings

        # Create new version
        ver_stmt = (
            select(func.coalesce(func.max(Profile.version), 0))
            .where(Profile.user_id == user["id"])
        )
        ver_result = await db.execute(ver_stmt)
        max_version = ver_result.scalar() or 0

        # Regenerate profile markdown
        new_profile_md = generate_profile_markdown(
            name=user.get("name", ""),
            role=scores_data.get("role", ""),
            organization=scores_data.get("organization", ""),
            industry=scores_data.get("industry", ""),
            context_summary=scores_data.get("context_summary", ""),
            scores=new_scores,
            domain_ratings=domain_ratings,
            calibration=new_calibration,
            career_goals=scores_data.get("career_goals", []),
            skills_to_develop=scores_data.get("skills_to_develop", []),
            skills_to_protect=scores_data.get("skills_to_protect", []),
            tasks_automate=scores_data.get("tasks_automate", []),
            tasks_augment=scores_data.get("tasks_augment", []),
            tasks_coach=scores_data.get("tasks_coach", []),
            tasks_protect=scores_data.get("tasks_protect", []),
            tasks_hands_off=scores_data.get("tasks_hands_off", []),
            red_lines=scores_data.get("red_lines", []),
        )

        new_profile = Profile(
            user_id=user["id"],
            version=max_version + 1,
            content_md=new_profile_md,
            scores_json=json.dumps(scores_data),
        )
        db.add(new_profile)
        await db.commit()

        return JSONResponse({
            "version": new_profile.version,
            "changes": {d: domain_ratings[d] for d in domain_signals if d in domain_ratings},
            "message": "Profile evolved based on interaction signals",
        })


# ---------------------------------------------------------------------------
# Telemetry & Pilot API routes
# ---------------------------------------------------------------------------

@app.post("/api/telemetry/chat-log")
async def api_ingest_chat_log(request: Request):
    """Ingest a structured chat log entry from <tal_log> blocks.

    Accepts a JSON payload with telemetry fields and stores it in the
    ChatLog table. Called by the MCP server after parsing <tal_log>.
    """
    user = require_auth(request)
    body = await request.json()

    task_cat = body.get("task_category")
    engagement = body.get("engagement_level")
    skill_sig = body.get("skill_signal")

    async with async_session_factory() as db:
        log_entry = ChatLog(
            user_id=user["id"],
            session_id=body.get("session_id"),
            task_category=TaskCategory(task_cat) if task_cat and task_cat in TaskCategory.__members__ else None,
            domain=body.get("domain"),
            engagement_level=EngagementLevel(engagement) if engagement and engagement in EngagementLevel.__members__ else None,
            skill_signal=SkillSignal(skill_sig) if skill_sig and skill_sig in SkillSignal.__members__ else None,
            notes=body.get("notes"),
            accepted_without_edit=body.get("accepted_without_edit"),
            ai_mode=body.get("ai_mode", "standard"),
            turn_payload_json=json.dumps(body) if body else None,
        )
        db.add(log_entry)
        await db.commit()

        return JSONResponse({"id": log_entry.id, "status": "logged"})


@app.post("/api/telemetry/chat-log/batch")
async def api_ingest_chat_log_batch(request: Request):
    """Ingest multiple chat log entries at once."""
    user = require_auth(request)
    body = await request.json()
    entries = body.get("entries", [])

    if not entries:
        raise HTTPException(status_code=400, detail="entries array required")

    async with async_session_factory() as db:
        ids = []
        for entry in entries:
            task_cat = entry.get("task_category")
            engagement = entry.get("engagement_level")
            skill_sig = entry.get("skill_signal")

            log_entry = ChatLog(
                user_id=user["id"],
                session_id=entry.get("session_id"),
                task_category=TaskCategory(task_cat) if task_cat and task_cat in TaskCategory.__members__ else None,
                domain=entry.get("domain"),
                engagement_level=EngagementLevel(engagement) if engagement and engagement in EngagementLevel.__members__ else None,
                skill_signal=SkillSignal(skill_sig) if skill_sig and skill_sig in SkillSignal.__members__ else None,
                notes=entry.get("notes"),
                accepted_without_edit=entry.get("accepted_without_edit"),
                ai_mode=entry.get("ai_mode", "standard"),
                turn_payload_json=json.dumps(entry),
            )
            db.add(log_entry)
            await db.flush()
            ids.append(log_entry.id)

        await db.commit()
        return JSONResponse({"ids": ids, "count": len(ids)})


@app.get("/api/telemetry/passive-ratio")
async def api_passive_ratio(request: Request):
    """Get the Engagement Passive Ratio (R_passive) for the current user."""
    user = require_auth(request)
    days_param = request.query_params.get("days")
    days = int(days_param) if days_param else None

    async with async_session_factory() as db:
        ratio = await compute_passive_ratio(db, user["id"], days=days)
        return JSONResponse({"r_passive": round(ratio, 4), "days": days})


@app.post("/api/pilot/survey")
async def api_submit_survey(request: Request):
    """Submit or update pilot survey scores for a timepoint."""
    user = require_auth(request)
    body = await request.json()

    timepoint_val = body.get("timepoint")
    if not timepoint_val or timepoint_val not in SurveyTimepoint.__members__:
        raise HTTPException(status_code=400, detail="Valid timepoint required: baseline, midpoint, endline, followup")

    async with async_session_factory() as db:
        # Upsert: check if survey already exists for this user+timepoint
        stmt = select(PilotSurvey).where(
            PilotSurvey.user_id == user["id"],
            PilotSurvey.timepoint == SurveyTimepoint(timepoint_val),
        )
        result = await db.execute(stmt)
        survey = result.scalar_one_or_none()

        if not survey:
            survey = PilotSurvey(
                user_id=user["id"],
                timepoint=SurveyTimepoint(timepoint_val),
            )
            db.add(survey)

        # Update fields from body
        if "taaq_score" in body:
            survey.taaq_score = body["taaq_score"]
        if "taaq_subscores" in body:
            survey.taaq_subscores_json = json.dumps(body["taaq_subscores"])
        if "m_csr_score" in body:
            survey.m_csr_score = body["m_csr_score"]
        if "m_csr_details" in body:
            survey.m_csr_details_json = json.dumps(body["m_csr_details"])
        if "m_ht_score" in body:
            survey.m_ht_score = body["m_ht_score"]
        if "m_ht_details" in body:
            survey.m_ht_details_json = json.dumps(body["m_ht_details"])
        if "e_gap_score" in body:
            survey.e_gap_score = body["e_gap_score"]
        if "e_gap_details" in body:
            survey.e_gap_details_json = json.dumps(body["e_gap_details"])

        # NASA-TLX sub-scales
        for tlx_key in ("mental", "physical", "temporal", "performance", "effort", "frustration"):
            field_name = f"nasa_tlx_{tlx_key}"
            if field_name in body:
                setattr(survey, field_name, body[field_name])

        if "nasa_tlx_composite" in body:
            survey.nasa_tlx_composite = body["nasa_tlx_composite"]

        if "raw_responses" in body:
            survey.raw_responses_json = json.dumps(body["raw_responses"])

        await db.commit()
        return JSONResponse({"survey_id": survey.id, "timepoint": timepoint_val})


@app.get("/api/pilot/surveys")
async def api_get_surveys(request: Request):
    """Get all pilot survey data for the current user."""
    user = require_auth(request)

    async with async_session_factory() as db:
        stmt = (
            select(PilotSurvey)
            .where(PilotSurvey.user_id == user["id"])
            .order_by(PilotSurvey.recorded_at)
        )
        result = await db.execute(stmt)
        surveys = result.scalars().all()

        data = []
        for s in surveys:
            data.append({
                "timepoint": s.timepoint.value,
                "recorded_at": s.recorded_at.isoformat() if s.recorded_at else None,
                "taaq_score": s.taaq_score,
                "m_csr_score": s.m_csr_score,
                "m_ht_score": s.m_ht_score,
                "e_gap_score": s.e_gap_score,
                "nasa_tlx_composite": s.nasa_tlx_composite,
            })

        return JSONResponse({"surveys": data})


# ---------------------------------------------------------------------------
# Settings routes
# ---------------------------------------------------------------------------

@app.post("/api/settings/automation-mode")
async def api_toggle_automation(request: Request):
    """Toggle Fast Automation mode on/off.

    When enabled, the system appends <mode>automation_only</mode> to the
    prompt, disabling pedagogical friction while keeping TAL telemetry active.
    """
    user = require_auth(request)
    body = await request.json()
    enabled = bool(body.get("enabled", False))

    async with async_session_factory() as db:
        stmt = select(User).where(User.id == user["id"])
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()
        if db_user:
            db_user.automation_mode = enabled
            await db.commit()

    return JSONResponse({"automation_mode": enabled})


@app.get("/api/settings/automation-mode")
async def api_get_automation_mode(request: Request):
    """Check whether automation mode is active for the current user."""
    user = require_auth(request)

    async with async_session_factory() as db:
        stmt = select(User.automation_mode).where(User.id == user["id"])
        result = await db.execute(stmt)
        mode = result.scalar_one_or_none()

    return JSONResponse({"automation_mode": bool(mode)})


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
            return templates.TemplateResponse(name="checkin.html", request=request, context={
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

    return templates.TemplateResponse(name="checkin.html", request=request, context={
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


# ───────────────────────────────────────────────────────────────────────────
# MCP Server via SSE (Remote Access)
# ───────────────────────────────────────────────────────────────────────────

@app.get("/mcp/sse")
async def mcp_sse_get(request: Request):
    """
    SSE endpoint for MCP clients to establish persistent connection.
    
    Connects to: GET /mcp/sse
    
    Returns a Server-Sent Events stream for bidirectional MCP communication.
    
    Example Claude Desktop config:
    {
      "mcpServers": {
        "talent-augmenting-layer": {
          "url": "https://proworker-hosted.onrender.com/mcp/sse"
        }
      }
    }
    """
    return await handle_sse_get(request)


@app.post("/mcp/sse")
async def mcp_sse_post(request: Request):
    """
    SSE endpoint for MCP clients (POST variant).
    
    Handles MCP protocol requests via HTTP POST.
    """
    return await handle_sse_post(request)


@app.get("/mcp/config")
async def mcp_config():
    """
    Return configuration for connecting to the remote MCP server.
    
    Endpoint: GET /mcp/config
    
    Returns a JSON object with the SSE URL and client configuration instructions.
    """
    return await get_sse_config()
