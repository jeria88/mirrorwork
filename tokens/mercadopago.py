"""
Mercado Pago integration.

Flujo:
  1. Usuario elige pack → vista crea preferencia MP → redirect a checkout MP
  2. MP procesa el pago → webhook notifica a nuestro endpoint
  3. Webhook valida, acredita fractones, actualiza MpPurchase

Docs: https://www.mercadopago.com.ar/developers/es/reference/preferences/_checkout_preferences/post
"""
import hashlib
import logging

import requests
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

MP_BASE_URL = "https://api.mercadopago.com"


def _headers():
    return {
        "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def create_checkout_preference(pack, user, request=None):
    """
    Crea una preferencia de checkout en Mercado Pago.
    Retorna (init_point, preference_id) o (None, None) en error.
    """
    if not settings.MP_ACCESS_TOKEN:
        logger.error("[MP] MP_ACCESS_TOKEN no configurado")
        return None, None

    # URL base para webhooks y retornos
    base_url = _base_url(request)

    payload = {
        "items": [
            {
                "title": f"Pack {pack.name} — {pack.fractones} fractones",
                "quantity": 1,
                "unit_price": pack.price_clp,
                "currency_id": "CLP",
            }
        ],
        "payer": {
            "email": user.email,
        },
        "external_reference": f"fracton_pack:{pack.slug}:user:{user.id}",
        "back_urls": {
            "success": base_url + reverse("tokens:mp_success"),
            "failure": base_url + reverse("tokens:mp_failure"),
            "pending": base_url + reverse("tokens:mp_pending"),
        },
        "auto_return": "approved",
        "notification_url": base_url + reverse("tokens:mp_webhook"),
        "statement_descriptor": "ENDONAUTAS",
        "expires": False,
    }

    try:
        resp = requests.post(
            f"{MP_BASE_URL}/checkout/preferences",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        init_point = data.get("init_point")  # URL de checkout
        pref_id = data.get("id")
        logger.info(f"[MP] Preferencia creada: {pref_id} para {user.email} — pack {pack.slug}")
        return init_point, pref_id
    except requests.RequestException as e:
        logger.error(f"[MP] Error creando preferencia: {e}")
        logger.error(f"[MP] Response: {getattr(e.response, 'text', 'no response')}")
        return None, None


def get_payment_info(payment_id):
    """Obtiene información de un pago desde la API de MP."""
    if not settings.MP_ACCESS_TOKEN or not payment_id:
        return None
    try:
        resp = requests.get(
            f"{MP_BASE_URL}/v1/payments/{payment_id}",
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"[MP] Error obteniendo pago {payment_id}: {e}")
        return None


def process_webhook(payload):
    """
    Procesa webhook de Mercado Pago.
    MP envía notificaciones por:
      - payment (cuando se crea/actualiza un pago)
      - merchant_order (órdenes de cobro)
    Retorna (ok: bool, message: str).
    """
    logger.info(f"[MP] Webhook recibido: {payload}")

    # MP puede enviar el payload como query param 'data.id' o como JSON body
    topic = payload.get("type", "")
    data_id = payload.get("data", {}).get("id", "")

    if topic == "payment" and data_id:
        return _process_payment_notification(data_id)

    logger.info(f"[MP] Webhook ignorado — topic: {topic}")
    return True, f"topic {topic} ignored"


def _process_payment_notification(payment_id):
    """Obtiene el pago de MP y acredita fractones si está aprobado."""
    from tokens.models import MpPurchase, TokenPack

    payment = get_payment_info(payment_id)
    if not payment:
        return False, f"no se pudo obtener pago {payment_id}"

    status = payment.get("status", "")
    external_ref = payment.get("external_reference", "")
    payer_email = (payment.get("payer") or {}).get("email", "")

    logger.info(
        f"[MP] Pago {payment_id}: status={status}, ref={external_ref}, "
        f"email={payer_email}"
    )

    # Extraer pack_slug y user_id de external_reference
    # Formato: "fracton_pack:{slug}:user:{id}"
    pack_slug = _parse_external_ref(external_ref)
    if not pack_slug:
        logger.warning(f"[MP] external_reference no reconocida: {external_ref}")
        return True, "external_ref not recognized"

    # Buscar usuario
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(email__iexact=payer_email.strip()).first()
    if not user:
        logger.warning(f"[MP] Usuario no encontrado: {payer_email}")
        return True, f"user {payer_email} not found"

    # Buscar pack
    try:
        pack = TokenPack.objects.get(slug=pack_slug, active=True)
    except TokenPack.DoesNotExist:
        logger.error(f"[MP] Pack no encontrado: {pack_slug}")
        return True, f"pack {pack_slug} not found"

    # Buscar o crear MpPurchase
    purchase, created = MpPurchase.objects.get_or_create(
        mp_payment_id=str(payment_id),
        defaults={
            "user":        user,
            "pack":         pack,
            "pack_slug":    pack.slug,
            "fractones":    pack.fractones,
            "amount_clp":   pack.price_clp,
            "mp_raw":       payment,
        },
    )

    # Actualizar siempre el payload crudo
    purchase.mp_raw = payment

    # Solo acreditar si el pago fue aprobado y la compra no estaba ya aprobada
    if status == "approved" and purchase.status != "approved":
        purchase.status = "approved"
        purchase.save(update_fields=["status", "mp_raw", "updated_at"])
        _credit_fractones(user, pack, purchase)
        logger.info(f"[MP] {pack.fractones} fractones acreditaron para {user.email}")
        return True, f"{pack.fractones} fractones credited to {user.email}"

    # Si ya estaba aprobado, idempotente
    if purchase.status == "approved":
        return True, f"already approved — idempotent"

    # Otros estados: pending, rejected, etc.
    purchase.status = _map_status(status)
    purchase.save(update_fields=["status", "mp_raw", "updated_at"])
    return True, f"status {status} mapped to {purchase.status}"


def _credit_fractones(user, pack, purchase):
    """Acredita los fractones al usuario y registra la transacción."""
    from tokens.service import credit_pack
    credit_pack(user, pack.fractones, offer_code=f"mp:{purchase.mp_payment_id}")


def _map_status(mp_status):
    """Mapea status de MP a nuestros estados."""
    mapping = {
        "approved":   "approved",
        "rejected":   "rejected",
        "in_process":  "pending",
        "pending":    "pending",
        "refunded":   "refunded",
        "cancelled":  "rejected",
        "charged_back": "refunded",
    }
    return mapping.get(mp_status, "pending")


def _parse_external_ref(ref):
    """Extrae el pack_slug de 'fracton_pack:{slug}:user:{id}'."""
    if not ref:
        return None
    parts = str(ref).split(":")
    if len(parts) >= 2 and parts[0] == "fracton_pack":
        return parts[1]
    return None


def _base_url(request=None):
    """Obtiene la URL base del sitio."""
    if request:
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        return f"{scheme}://{host}"
    # Fallback: desde settings o dominio de Railway
    railway_domain = getattr(settings, "RAILWAY_PUBLIC_DOMAIN", "")
    if railway_domain:
        return f"https://{railway_domain}"
    return "https://app.endonautas.cl"
