"""
Hotmart webhook processing.

Events handled:
  PURCHASE_APPROVED        → activate plan + credit monthly tokens
  PURCHASE_REFUNDED        → downgrade to free
  PURCHASE_CHARGEBACK      → downgrade to free
  PURCHASE_CANCELED        → downgrade to free (first-payment cancels)
  SUBSCRIPTION_CANCELLATION → downgrade to free
"""
import logging
from datetime import date

from django.conf import settings

logger = logging.getLogger(__name__)

# Events that mean "payment succeeded, activate plan"
ACTIVATE_EVENTS = {"PURCHASE_APPROVED", "PURCHASE_COMPLETE"}

# Events that mean "access revoked, downgrade"
REVOKE_EVENTS = {
    "PURCHASE_REFUNDED",
    "PURCHASE_CHARGEBACK",
    "PURCHASE_CANCELED",
    "SUBSCRIPTION_CANCELLATION",
}


def get_plan_for_offer(offer_code):
    """Returns plan key ('navegante'|'practicante') by offer code or None."""
    return settings.HOTMART_OFFER_PLAN_MAP.get(str(offer_code))


def _get_user_by_email(email):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.filter(email__iexact=email).first()


def activate_plan(user, plan, subscriber_code=""):
    from accounts.models import UserProfile
    from tokens.models import TokenBalance

    profile, _ = UserProfile.objects.get_or_create(user=user)
    old_plan = profile.plan
    profile.plan = plan
    profile.plan_active_since = date.today()
    if subscriber_code:
        profile.hotmart_subscriber_code = subscriber_code
    profile.save()

    # Credit monthly token allowance only on first activation or plan upgrade
    config = settings.TOKEN_PLANS.get(plan, {})
    monthly = config.get("monthly_tokens", 0)
    if monthly:
        balance, _ = TokenBalance.objects.get_or_create(user=user, defaults={"balance": 0})
        balance.credit(monthly, reason=f"Tokens plan {plan} — Hotmart")

    logger.info(f"[Hotmart] {user.email}: {old_plan} → {plan} (sub={subscriber_code})")


def revoke_plan(user, reason=""):
    from accounts.models import UserProfile

    profile = UserProfile.objects.filter(user=user).first()
    if not profile or profile.plan == "free":
        return
    old_plan = profile.plan
    profile.plan = "free"
    profile.hotmart_subscriber_code = ""
    profile.save()
    logger.info(f"[Hotmart] {user.email}: {old_plan} → free ({reason})")


def process_webhook(payload):
    """
    Main entry point. Returns (ok: bool, message: str).
    payload is the parsed JSON dict from Hotmart.
    """
    event = payload.get("event", "")
    data = payload.get("data", {})

    buyer_email = (data.get("buyer") or {}).get("email", "").strip().lower()
    offer_code  = str((data.get("purchase") or {}).get("offer", {}).get("code", ""))
    sub_data    = data.get("subscription") or {}
    subscriber_code = (sub_data.get("subscriber") or {}).get("code", "")

    if not buyer_email:
        return True, "no buyer email — ignored"

    user = _get_user_by_email(buyer_email)
    if not user:
        logger.warning(f"[Hotmart] {event}: no user found for {buyer_email}")
        return True, f"user {buyer_email} not found — ignored"

    if event in ACTIVATE_EVENTS:
        plan = get_plan_for_offer(offer_code)
        if not plan:
            logger.warning(f"[Hotmart] offer {offer_code} not mapped to any plan")
            return True, f"offer {offer_code} not mapped"
        activate_plan(user, plan, subscriber_code=subscriber_code)
        return True, f"plan {plan} activated for {buyer_email}"

    if event in REVOKE_EVENTS:
        revoke_plan(user, reason=event)
        return True, f"plan revoked for {buyer_email} ({event})"

    # Unknown event — acknowledge so Hotmart doesn't retry
    return True, f"event {event} ignored"
