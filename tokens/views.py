import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from tokens.models import MpPurchase, TokenBalance, TokenPack, TokenTransaction

logger = logging.getLogger(__name__)


@login_required
def balance(request):
    balance_obj, _ = TokenBalance.objects.get_or_create(
        user=request.user, defaults={"permanent": 0, "monthly": 0}
    )
    transactions = TokenTransaction.objects.filter(user=request.user)[:30]
    purchases = MpPurchase.objects.filter(user=request.user)[:10]
    return render(request, "tokens/balance.html", {
        "balance": balance_obj,
        "transactions": transactions,
        "purchases": purchases,
    })


@login_required
def tienda(request):
    """Tienda de packs de fractones — reemplaza a planes.html."""
    packs = TokenPack.objects.filter(active=True)
    balance_obj, _ = TokenBalance.objects.get_or_create(
        user=request.user, defaults={"permanent": 0, "monthly": 0}
    )
    return render(request, "tokens/tienda.html", {
        "packs": packs,
        "balance": balance_obj,
    })


@login_required
@require_POST
def crear_compra(request):
    """Crea una preferencia de checkout en MP y redirige al usuario."""
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

    # Registrar compra pendiente
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
    """Webhook que MP llama cuando hay un evento de pago."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Bad JSON", status=400)

    from tokens.mercadopago import process_webhook
    ok, msg = process_webhook(payload)
    logger.info(f"[MP] webhook: {msg}")
    return JsonResponse({"ok": ok, "msg": msg}, status=200 if ok else 422)


def mp_success(request):
    """Usuario vuelve después de pagar exitosamente."""
    return render(request, "tokens/success.html", {"status": "success"})


def mp_failure(request):
    """Usuario vuelve después de un pago fallido."""
    return render(request, "tokens/success.html", {"status": "failure"})


def mp_pending(request):
    """Usuario vuelve con pago pendiente."""
    return render(request, "tokens/success.html", {"status": "pending"})
