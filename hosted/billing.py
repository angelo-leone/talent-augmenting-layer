"""Stripe billing scaffold (feature-flagged).

This module is a skeleton. It is NOT wired into hosted/app.py unless
ENABLE_BILLING=true is set in config. When disabled, imports from here
still succeed (the module compiles), but no routes are registered.

To activate:
  1. Set ENABLE_BILLING=true, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET,
     STRIPE_PRICE_PRO, STRIPE_PRICE_TEAM in the environment.
  2. Call register_billing_routes(app) from hosted/app.py's startup.
  3. Create Stripe Products + Prices in the Stripe dashboard; copy the
     price IDs into STRIPE_PRICE_PRO and STRIPE_PRICE_TEAM.
  4. Configure a webhook in the Stripe dashboard pointing at
     {APP_URL}/api/billing/webhook with events checkout.session.completed,
     customer.subscription.updated, and customer.subscription.deleted.

The billing columns on the User table (stripe_customer_id, plan_tier,
subscription_status) are created regardless of this flag, so flipping it
on later does not require a migration.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select

from hosted.config import (
    APP_URL,
    ENABLE_BILLING,
    STRIPE_PRICE_PRO,
    STRIPE_PRICE_TEAM,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)
from hosted.database import PlanTier, User, async_session_factory
from hosted.auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter()


def _stripe_client():
    """Lazy import so the module is loadable without the stripe package."""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    try:
        import stripe  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="stripe package not installed. `pip install stripe` to enable.",
        ) from exc
    stripe.api_key = STRIPE_SECRET_KEY
    return stripe


def _price_for_tier(tier: str) -> Optional[str]:
    return {
        "pro": STRIPE_PRICE_PRO,
        "team": STRIPE_PRICE_TEAM,
    }.get(tier)


@router.post("/api/billing/checkout")
async def create_checkout_session(request: Request) -> JSONResponse:
    """Create a Stripe Checkout Session for the authenticated user."""
    user = require_auth(request)
    body = await request.json()
    tier = body.get("tier", "pro")
    price_id = _price_for_tier(tier)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Unknown tier: {tier}")

    stripe = _stripe_client()

    async with async_session_factory() as db:
        stmt = select(User).where(User.id == user["id"])
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        if not db_user.stripe_customer_id:
            customer = stripe.Customer.create(email=db_user.email, name=db_user.name or None)
            db_user.stripe_customer_id = customer.id
            await db.commit()
        customer_id = db_user.stripe_customer_id

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{APP_URL}/dashboard?billing=success",
        cancel_url=f"{APP_URL}/pricing?billing=cancelled",
        allow_promotion_codes=True,
    )
    return JSONResponse({"checkout_url": session.url})


@router.get("/api/billing/portal")
async def create_portal_session(request: Request) -> RedirectResponse:
    """Redirect the user to the Stripe customer portal (cancel / update card)."""
    user = require_auth(request)
    stripe = _stripe_client()

    async with async_session_factory() as db:
        stmt = select(User).where(User.id == user["id"])
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()
        if not db_user or not db_user.stripe_customer_id:
            raise HTTPException(status_code=404, detail="No Stripe customer for this user")

    session = stripe.billing_portal.Session.create(
        customer=db_user.stripe_customer_id,
        return_url=f"{APP_URL}/dashboard",
    )
    return RedirectResponse(url=session.url, status_code=302)


@router.post("/api/billing/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Handle Stripe webhook events. Updates plan_tier / subscription_status."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    stripe = _stripe_client()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Rejecting Stripe webhook: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    event_type = event["type"]
    data = event["data"]["object"]
    customer_id = data.get("customer")
    if not customer_id:
        return JSONResponse({"ok": True, "ignored": "no customer"})

    async with async_session_factory() as db:
        stmt = select(User).where(User.stripe_customer_id == customer_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return JSONResponse({"ok": True, "ignored": "user not found"})

        if event_type in ("checkout.session.completed", "customer.subscription.updated"):
            user.subscription_status = data.get("status") or "active"
            # Map Stripe price id back to a tier
            items = data.get("items", {}).get("data", [])
            if items:
                price_id = items[0].get("price", {}).get("id")
                if price_id == STRIPE_PRICE_PRO:
                    user.plan_tier = PlanTier.pro
                elif price_id == STRIPE_PRICE_TEAM:
                    user.plan_tier = PlanTier.team
        elif event_type == "customer.subscription.deleted":
            user.plan_tier = PlanTier.free
            user.subscription_status = "canceled"

        await db.commit()

    return JSONResponse({"ok": True})


def register_billing_routes(app: Any) -> None:
    """Attach billing routes to the FastAPI app, iff ENABLE_BILLING is on."""
    if not ENABLE_BILLING:
        logger.info("ENABLE_BILLING is off; billing routes not mounted.")
        return
    app.include_router(router)
    logger.info("Stripe billing routes mounted.")
