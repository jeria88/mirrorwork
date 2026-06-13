from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User, UserProfile
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
    if alias:
        TemporaryProfile.objects.create(
            created_by=request.user,
            alias=alias,
            notes=notes,
        )
    return redirect("practitioners:lista")


@login_required
def perfil_detalle(request, pk):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    profile = get_object_or_404(TemporaryProfile, pk=pk, created_by=request.user)
    
    from django.db.models import Q
    from psychometrics.models import Test, TestResult
    
    if profile.claimed_by:
        results = TestResult.objects.filter(
            Q(temp_profile=profile) | Q(user=profile.claimed_by)
        ).select_related("test").order_by("-completed_at")
    else:
        results = profile.test_results.select_related("test").order_by("-completed_at")
        
    all_tests = Test.objects.filter(active=True).order_by("dimension", "order")
    assigned_test_ids = set(profile.assigned_tests.values_list("id", flat=True))
    
    share_url = request.build_absolute_uri(f"/practicantes/acceso/{profile.access_code}/")
    return render(request, "practitioners/detalle.html", {
        "profile": profile,
        "results": results,
        "all_tests": all_tests,
        "assigned_test_ids": assigned_test_ids,
        "share_url": share_url,
    })


def _generate_clinical_summary(profile):
    from psychometrics.models import TestResult
    import json
    import requests
    import os
    from django.db.models import Q
    
    if profile.claimed_by:
        results = TestResult.objects.filter(
            Q(temp_profile=profile) | Q(user=profile.claimed_by)
        ).select_related("test").order_by("test", "-completed_at")
    else:
        results = profile.test_results.select_related("test").order_by("test", "-completed_at")
        
    latest_results = {}
    for r in results:
        if r.test_id not in latest_results:
            latest_results[r.test_id] = r
            
    if not latest_results:
        return "El paciente aún no ha completado ningún test. No se puede generar una ficha clínica."
        
    summary_data = []
    for test_id, r in latest_results.items():
        summary_data.append({
            "test": r.test.name,
            "dimension": r.test.get_dimension_display(),
            "fecha": r.completed_at.strftime("%d/%m/%Y"),
            "evaluacion": r.evaluation,
            "ai_insight": r.ai_insight or "Sin insight aún"
        })
        
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return "Error: DEEPSEEK_API_KEY no configurado en las variables de entorno."
        
    texto_resultados = json.dumps(summary_data, ensure_ascii=False, indent=2)
    prompt = (
        "Eres un supervisor de psicología y coaching integrativo de alta gama. "
        "Analiza los resultados del cliente y elabora una Ficha Clínica y de Acompañamiento "
        "para preparar la sesión del terapeuta.\n\n"
        f"Paciente (Alias): {profile.alias}\n"
        f"Resultados de los Cuestionarios:\n{texto_resultados}\n\n"
        "Por favor, estructura tu respuesta con los siguientes puntos, usando formato Markdown limpio:\n"
        "1. **Perfil General e Integración** (Luces, sombras principales y nivel general de integración/conciencia)\n"
        "2. **Puntos Críticos y Alertas** (Heridas infantiles prominentes, desregulación emocional, niveles altos de estrés/ansiedad, o cualquier creencia limitante severa detectada)\n"
        "3. **Estrategia de Acompañamiento** (Recomendación del enfoque terapéutico y 3 preguntas socráticas de exploración profunda para la próxima sesión)\n\n"
        "Mantén un tono profesional, analítico y constructivo. Escribe en español."
    )
    
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1200,
            },
            timeout=35,
        )
        resp.raise_for_status()
        summary = resp.json()["choices"][0]["message"]["content"]
        return summary
    except Exception as e:
        return f"Error al generar el resumen clínico por IA: {str(e)}"


@login_required
@require_POST
def perfil_asignar_tests(request, pk):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    profile = get_object_or_404(TemporaryProfile, pk=pk, created_by=request.user)
    
    test_ids = request.POST.getlist("assigned_tests")
    profile.assigned_tests.set(test_ids)
    
    from django.contrib import messages
    messages.success(request, "Asignación de cuestionarios actualizada con éxito.")
    return redirect("practitioners:detalle", pk=pk)


@login_required
@require_POST
def perfil_generar_resumen_clinico(request, pk):
    if not _is_practicante(request.user):
        return HttpResponseForbidden("Esta función requiere el plan Practicante o Empresa.")
    profile = get_object_or_404(TemporaryProfile, pk=pk, created_by=request.user)
    
    from django.utils import timezone
    summary = _generate_clinical_summary(profile)
    profile.clinical_summary = summary
    profile.clinical_summary_updated_at = timezone.now()
    profile.save(update_fields=["clinical_summary", "clinical_summary_updated_at"])
    
    from django.contrib import messages
    messages.success(request, "Ficha clínica con IA generada con éxito.")
    return redirect("practitioners:detalle", pk=pk)


def perfil_acceso(request, access_code):
    """Vista pública: el cliente abre el link del facilitador."""
    temp = get_object_or_404(TemporaryProfile, access_code=access_code, active=True)

    # Si ya tiene cuenta vinculada, redirigir al dashboard
    if temp.claimed_by:
        if request.user == temp.claimed_by:
            return redirect('dashboard')
        # otra persona autenticada viendo el link — mostrar info básica
        return render(request, "practitioners/acceso.html", {
            "temp": temp, "facilitador": temp.created_by,
            "already_claimed": True,
        })

    # Usuario ya autenticado sin vinculación → vincular directamente
    if request.user.is_authenticated:
        temp.claimed_by = request.user
        temp.save(update_fields=["claimed_by"])
        return redirect('dashboard')

    error = None
    if request.method == "POST":
        nombre   = request.POST.get("nombre", "").strip()
        email    = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not nombre or not email or len(password) < 6:
            error = "Completa todos los campos. La contraseña debe tener al menos 6 caracteres."
        elif User.objects.filter(email=email).exists():
            error = "Ya existe una cuenta con ese email. Inicia sesión para vincular tu perfil."
        else:
            username = email.split("@")[0]
            base = username
            n = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{n}"
                n += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
            )
            UserProfile.objects.create(user=user, plan="free")
            temp.claimed_by = user
            temp.save(update_fields=["claimed_by"])
            login(request, user)
            return redirect('dashboard')

    return render(request, "practitioners/acceso.html", {
        "temp": temp,
        "facilitador": temp.created_by,
        "already_claimed": False,
        "error": error,
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
