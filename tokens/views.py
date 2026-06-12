import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from tokens.models import MpPurchase, PayPalPurchase, TokenBalance, TokenPack, TokenTransaction

logger = logging.getLogger(__name__)


@login_required
def balance(request):
    balance_obj, _ = TokenBalance.objects.get_or_create(
        user=request.user, defaults={"permanent": 0, "monthly": 0}
    )
    transactions = TokenTransaction.objects.filter(user=request.user)[:30]
    mp_purchases = MpPurchase.objects.filter(user=request.user)[:5]
    pp_purchases = PayPalPurchase.objects.filter(user=request.user)[:5]
    return render(request, "tokens/balance.html", {
        "balance": balance_obj,
        "transactions": transactions,
        "mp_purchases": mp_purchases,
        "pp_purchases": pp_purchases,
    })


@login_required
def tienda(request):
    """Tienda de packs de fractones."""
    packs = TokenPack.objects.filter(active=True)
    balance_obj, _ = TokenBalance.objects.get_or_create(
        user=request.user, defaults={"permanent": 0, "monthly": 0}
    )
    return render(request, "tokens/tienda.html", {
        "packs": packs,
        "balance": balance_obj,
    })


# ── Mercado Pago ──────────────────────────────────────────────────────────────

@login_required
@require_POST
def crear_compra_mp(request):
    """Crea preferencia de checkout en Mercado Pago."""
    pack_slug = request.POST.get("pack_slug", "")
    pack = get_object_or_404(TokenPack, slug=pack_slug, active=True)

    from tokens.mercadopago import create_checkout_preference
    init_point, pref_id = create_checkout_preference(pack, request.user, request)

    if not init_point:
        return render(request, "tokens/tienda.html", {
            "packs": TokenPack.objects.filter(active=True),
            "balance": TokenBalance.objects.get_or_create(user=request.user)[0],
            "error": "No se pudo crear el enlace de pago. Intenta de nuevo.",
        })

    MpPurchase.objects.create(
        user=request.user,
        pack=pack,
        mp_preference_id=pref_id or "",
        pack_slug=pack.slug,
        fractones=pack.fractones,
        amount_clp=pack.price_clp,
        status="pending",
    )

    return redirect(init_point)


@csrf_exempt
@require_POST
def mp_webhook(request):
    """Webhook de Mercado Pago."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Bad JSON", status=400)

    from tokens.mercadopago import process_webhook
    ok, msg = process_webhook(payload)
    logger.info(f"[MP] webhook: {msg}")
    return JsonResponse({"ok": ok, "msg": msg}, status=200 if ok else 422)


def mp_success(request):
    return render(request, "tokens/success.html", {"status": "success"})

def mp_failure(request):
    return render(request, "tokens/success.html", {"status": "failure"})

def mp_pending(request):
    return render(request, "tokens/success.html", {"status": "pending"})


# ── PayPal ────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def crear_compra_pp(request):
    """Crea orden de PayPal."""
    pack_slug = request.POST.get("pack_slug", "")
    pack = get_object_or_404(TokenPack, slug=pack_slug, active=True)

    from tokens.paypal import create_order
    approval_url, order_id = create_order(pack, request.user, request)

    if not approval_url:
        return render(request, "tokens/tienda.html", {
            "packs": TokenPack.objects.filter(active=True),
            "balance": TokenBalance.objects.get_or_create(user=request.user)[0],
            "error": "No se pudo crear el enlace de PayPal. Intenta de nuevo.",
        })

    PayPalPurchase.objects.create(
        user=request.user,
        pack=pack,
        pp_order_id=order_id or "",
        pack_slug=pack.slug,
        fractones=pack.fractones,
        amount_usd=pack.price_usd,
        status="pending",
    )

    return redirect(approval_url)


def pp_return(request):
    """Usuario vuelve de PayPal después de aprobar."""
    order_id = request.GET.get("token", "")
    if not order_id:
        return render(request, "tokens/success.html", {"status": "failure"})

    from tokens.paypal import capture_order
    ok, data = capture_order(order_id)

    if ok:
        # Actualizar la compra
        purchase = PayPalPurchase.objects.filter(pp_order_id=order_id).first()
        if purchase and purchase.status != "approved":
            purchase.status = "approved"
            purchase.pp_raw = data
            purchase.save(update_fields=["status", "pp_raw", "updated_at"])
            from tokens.paypal import _credit_fractones
            _credit_fractones(purchase.user, purchase.pack, purchase)
        return render(request, "tokens/success.html", {"status": "success"})
    else:
        logger.error(f"[PP] Error capturando {order_id}: {data}")
        return render(request, "tokens/success.html", {"status": "failure"})


def pp_cancel(request):
    """Usuario canceló el pago en PayPal."""
    order_id = request.GET.get("token", "")
    if order_id:
        purchase = PayPalPurchase.objects.filter(pp_order_id=order_id).first()
        if purchase:
            purchase.status = "rejected"
            purchase.save(update_fields=["status", "updated_at"])
    return render(request, "tokens/success.html", {"status": "failure"})


@csrf_exempt
@require_POST
def pp_webhook(request):
    """Webhook de PayPal."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Bad JSON", status=400)

    # Verificar signature (simplificado — en producción verificar con cert)
    from tokens.paypal import process_webhook
    ok, msg = process_webhook(payload, request.headers)
    logger.info(f"[PP] webhook: {msg}")
    return JsonResponse({"ok": ok, "msg": msg}, status=200 if ok else 422)


@login_required
def planes(request):
    """Muestra la página de planes de suscripción de Hotmart."""
    try:
        profile = request.user.profile
    except Exception:
        profile = None
    return render(request, "tokens/planes.html", {
        "profile": profile,
        "hotmart_urls": settings.HOTMART_CHECKOUT_URLS,
    })
