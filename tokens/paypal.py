"""
PayPal integration — checkout y webhooks para pagos internacionales.

Flujo:
  1. Usuario elige pack + clickea "Pagar con PayPal"
  2. Vista crea orden vía PayPal API → redirect a PayPal
  3. Usuario paga en PayPal → vuelve a nuestra página
  4. Vista captura el pago → acredita fractones
  5. Webhook de PayPal como backup de confirmación

PayPal API v2: https://developer.paypal.com/api/rest/
"""
import base64
import logging
from decimal import Decimal

import requests
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

PP_BASE_URL = "https://api-m.paypal.com"          # producción
PP_SANDBOX_URL = "https://api-m.sandbox.paypal.com"  # sandbox


def _base_url():
    if settings.DEBUG:
        return PP_SANDBOX_URL
    return PP_BASE_URL


def _auth_header():
    """Basic auth con client_id + secret."""
    credentials = f"{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


def _access_token():
    """Obtiene access token de OAuth2."""
    try:
        resp = requests.post(
            f"{_base_url()}/v1/oauth2/token",
            headers={"Accept": "application/json", "Accept-Language": "en_US"},
            data={"grant_type": "client_credentials"},
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.RequestException as e:
        logger.error(f"[PP] Error obteniendo access token: {e}")
        return None


def _headers():
    token = _access_token()
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def create_order(pack, user, request=None):
    """
    Crea una orden de PayPal.
    Retorna (approval_url, order_id) o (None, None) en error.
    """
    headers = _headers()
    if not headers:
        return None, None

    ret_url = _return_url(request)

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": f"fracton_pack:{pack.slug}:user:{user.id}",
                "description": f"Pack {pack.name} — {pack.fractones} fractones Endonautas",
                "amount": {
                    "currency_code": "USD",
                    "value": str(pack.price_usd),
                },
                "custom_id": f"{pack.slug}:{user.id}",
            }
        ],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                    "brand_name": "Endonautas",
                    "locale": "es-CL",
                    "landing_page": "LOGIN",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW",
                    "return_url": ret_url + reverse("tokens:pp_return"),
                    "cancel_url": ret_url + reverse("tokens:pp_cancel"),
                }
            }
        },
    }

    try:
        resp = requests.post(
            f"{_base_url()}/v2/checkout/orders",
            json=payload,
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        order_id = data.get("id")
        # Extraer URL de aprobación
        approval_url = None
        for link in data.get("links", []):
            if link.get("rel") == "payer-action":
                approval_url = link.get("href")
                break
        logger.info(f"[PP] Orden creada: {order_id} para {user.email} — pack {pack.slug}")
        return approval_url, order_id
    except requests.RequestException as e:
        logger.error(f"[PP] Error creando orden: {e}")
        logger.error(f"[PP] Response: {getattr(e.response, 'text', 'no response')}")
        return None, None


def capture_order(order_id):
    """
    Captura el pago de una orden aprobada.
    Retorna (True, capture_data) o (False, error_msg).
    """
    headers = _headers()
    if not headers:
        return False, "No se pudo autenticar con PayPal"

    try:
        resp = requests.post(
            f"{_base_url()}/v2/checkout/orders/{order_id}/capture",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "")
        if status == "COMPLETED":
            return True, data
        else:
            return False, f"Status: {status}"
    except requests.RequestException as e:
        logger.error(f"[PP] Error capturando orden {order_id}: {e}")
        return False, str(e)


def process_webhook(payload, headers):
    """
    Procesa webhook de PayPal.
    PayPal envía eventos como PAYMENT.CAPTURE.COMPLETED, etc.
    Retorna (ok: bool, message: str).
    """
    event_type = payload.get("event_type", "")
    resource = payload.get("resource", {})

    logger.info(f"[PP] Webhook: {event_type}")

    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        return _process_capture(resource)

    if event_type == "CHECKOUT.ORDER.APPROVED":
        # El usuario aprobó pero aún no se capturó — la captura se hace en pp_return
        return True, "order approved — waiting for capture"

    if event_type in ("PAYMENT.CAPTURE.DENIED", "PAYMENT.CAPTURE.REFUNDED"):
        return _process_refund(resource)

    return True, f"event {event_type} ignored"


def _process_capture(resource):
    """Acredita fractones cuando el pago se capturó."""
    # Extraer info del purchase_unit
    purchase_units = resource.get("purchase_units", [])
    if not purchase_units:
        return True, "no purchase_units"

    custom_id = purchase_units[0].get("custom_id", "")
    reference_id = purchase_units[0].get("reference_id", "")

    # Parsear custom_id: "pack_slug:user_id"
    pack_slug, user_id = _parse_custom_id(custom_id)
    if not pack_slug:
        return True, f"custom_id no reconocido: {custom_id}"

    from django.contrib.auth import get_user_model
    from tokens.models import PayPalPurchase, TokenPack

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return True, f"user {user_id} not found"

    try:
        pack = TokenPack.objects.get(slug=pack_slug, active=True)
    except TokenPack.DoesNotExist:
        return True, f"pack {pack_slug} not found"

    capture_id = resource.get("id", "")

    # Buscar o crear PayPalPurchase
    purchase, created = PayPalPurchase.objects.get_or_create(
        pp_order_id=resource.get("supplementary", {}).get("related_ids", {}).get("order_id", capture_id),
        defaults={
            "user":       user,
            "pack":        pack,
            "pack_slug":   pack.slug,
            "fractones":   pack.fractones,
            "amount_usd":  pack.price_usd,
            "pp_raw":      resource,
        },
    )

    if purchase.status != "approved":
        purchase.status = "approved"
        purchase.pp_raw = resource
        purchase.save(update_fields=["status", "pp_raw", "updated_at"])
        _credit_fractones(user, pack, purchase)
        logger.info(f"[PP] {pack.fractones} fractones acreditados para {user.email}")
        return True, f"{pack.fractones} fractones credited to {user.email}"

    return True, "already approved — idempotent"


def _process_refund(resource):
    """Maneja reembolsos."""
    custom_id = resource.get("custom_id", "")
    pack_slug, user_id = _parse_custom_id(custom_id)
    if not pack_slug:
        return True, "custom_id no reconocido"

    from tokens.models import PayPalPurchase
    purchase = PayPalPurchase.objects.filter(
        pack_slug=pack_slug,
        status="approved",
    ).first()
    if purchase:
        purchase.status = "refunded"
        purchase.save(update_fields=["status", "updated_at"])
        logger.info(f"[PP] Compra reembolsada: {purchase}")
        return True, f"refunded {purchase}"

    return True, "no purchase found to refund"


def _credit_fractones(user, pack, purchase):
    """Acredita fractones al usuario."""
    from tokens.service import credit_pack
    credit_pack(user, pack.fractones, offer_code=f"paypal:{purchase.pp_order_id}")


def _parse_custom_id(custom_id):
    """Parsea 'pack_slug:user_id'."""
    if not custom_id:
        return None, None
    parts = str(custom_id).split(":")
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return None, None


def _return_url(request=None):
    """URL base para retornos."""
    if request:
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        return f"{scheme}://{host}"
    railway_domain = getattr(settings, "RAILWAY_PUBLIC_DOMAIN", "")
    if railway_domain:
        return f"https://{railway_domain}"
    return "https://app.endonautas.cl"
