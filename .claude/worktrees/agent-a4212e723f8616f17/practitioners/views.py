from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import TemporaryProfile


def _is_practicante(user):
    try:
        return user.profile.is_practicante
    except Exception:
        return False


@login_required
def perfil_lista(request):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    profiles = TemporaryProfile.objects.filter(
        created_by=request.user, active=True
    ).order_by("-created_at")
    return render(request, "practitioners/lista.html", {"profiles": profiles})


@login_required
@require_POST
def perfil_crear(request):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    alias = request.POST.get("alias", "").strip()
    notes = request.POST.get("notes", "").strip()
    allocation = int(request.POST.get("token_allocation", 150))
    if alias:
        TemporaryProfile.objects.create(
            created_by=request.user,
            alias=alias,
            notes=notes,
            token_allocation=allocation,
        )
    return redirect("practitioners:lista")


@login_required
def perfil_detalle(request, pk):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    profile = get_object_or_404(TemporaryProfile, pk=pk, created_by=request.user)
    results = profile.test_results.select_related("test").order_by("-completed_at")
    share_url = request.build_absolute_uri(f"/practicantes/acceso/{profile.access_code}/")
    return render(request, "practitioners/detalle.html", {
        "profile": profile,
        "results": results,
        "share_url": share_url,
    })


@login_required
@require_POST
def perfil_archivar(request, pk):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    profile = get_object_or_404(TemporaryProfile, pk=pk, created_by=request.user)
    profile.active = False
    profile.save(update_fields=["active"])
    return redirect("practitioners:lista")
