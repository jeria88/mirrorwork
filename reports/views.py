import json
import os
import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from psychometrics.models import TestResult
from mirror.models import ConflictSession
from reports.models import SoulReport


@login_required
def dashboard(request):
    results = TestResult.objects.filter(user=request.user).select_related("test")
    mirror_sessions = ConflictSession.objects.filter(
        user=request.user
    ).exclude(status="archived").count()

    by_dimension = {}
    for r in results:
        dim = r.test.get_dimension_display()
        by_dimension.setdefault(dim, []).append(r)

    dimension_summary = [
        {"nombre": dim, "total": len(rs), "ultimo": rs[0].completed_at}
        for dim, rs in sorted(by_dimension.items(), key=lambda x: -len(x[1]))
    ]

    # Check Bitácora de Sombras status
    soul_report = SoulReport.objects.filter(user=request.user).order_by('-created_at').first()
    
    # Requirement thresholds
    required_tests = 5
    required_sessions = 3
    
    completed_tests_count = results.count()
    has_enough_info = completed_tests_count >= required_tests and mirror_sessions >= required_sessions
    
    # Calculate progress percentages for UI
    tests_pct = min(100, int((completed_tests_count / required_tests) * 100)) if required_tests > 0 else 0
    sessions_pct = min(100, int((mirror_sessions / required_sessions) * 100)) if required_sessions > 0 else 0

    return render(request, "reports/dashboard.html", {
        "total_tests": completed_tests_count,
        "mirror_sessions": mirror_sessions,
        "dimension_summary": dimension_summary,
        "recent_results": results[:5],
        "soul_report": soul_report,
        "has_enough_info": has_enough_info,
        "required_tests": required_tests,
        "required_sessions": required_sessions,
        "tests_pct": tests_pct,
        "sessions_pct": sessions_pct,
    })


@login_required
@require_POST
def generar_bitacora(request):
    results = TestResult.objects.filter(user=request.user)
    mirror_sessions = ConflictSession.objects.filter(user=request.user).exclude(status="archived")
    
    required_tests = 5
    required_sessions = 3
    
    if results.count() < required_tests or mirror_sessions.count() < required_sessions:
        return JsonResponse({"error": "Información insuficiente para compilar la bitácora."}, status=400)
    
    # Create or update report to generating
    report, created = SoulReport.objects.get_or_create(
        user=request.user,
        defaults={'status': SoulReport.STATUS_GENERATING}
    )
    report.status = SoulReport.STATUS_GENERATING
    report.save()
    
    success = _build_bitacora_content(report, results, mirror_sessions)
    if success:
        report.status = SoulReport.STATUS_COMPLETED
        report.save()
        return JsonResponse({"ok": True, "redirect_url": reverse("reports:bitacora_view")})
    else:
        report.status = SoulReport.STATUS_FAILED
        report.save()
        return JsonResponse({"error": "Error al compilar la Bitácora con la IA."}, status=500)


@login_required
def bitacora_view(request):
    report = SoulReport.objects.filter(user=request.user, status=SoulReport.STATUS_COMPLETED).order_by('-created_at').first()
    if not report:
        return redirect('reports:dashboard')
    
    return render(request, "reports/bitacora.html", {
        "report": report,
        "data": report.report_data,
    })


def _build_bitacora_content(report, test_results, mirror_sessions):
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        report.report_data = _generate_mock_bitacora(report.user)
        return True

    # Compile the user profile data
    tests_summary = []
    for r in test_results:
        tests_summary.append(
            f"Test: {r.test.name} (Dimensión: {r.test.get_dimension_display()})\n"
            f"Evaluación: {json.dumps(r.evaluation)}\n"
            f"Análisis IA: {r.ai_insight}\n"
        )
    
    sessions_summary = []
    for s in mirror_sessions:
        msgs = [f"{m.get('role')}: {m.get('content')}" for m in s.messages if m.get('role') in ('user', 'assistant')]
        sessions_summary.append(f"Sesión de Conflicto #{s.pk}:\n" + "\n".join(msgs[:6]))

    system_prompt = (
        "Eres la consciencia profunda del Espejo de Endonautas. Tu tarea es compilar una 'Bitácora de Sombras' "
        "personalizada e integrada para el usuario basándote en sus respuestas de tests psicométricos y sesiones de introspección del Espejo.\n\n"
        "Debes analizar los datos clínicos y adaptados proporcionados, identificar patrones de autosabotaje, "
        "heridas fundamentales (rechazo, abandono, traición, injusticia, humillación), la polaridad entre su Máscara (lo que muestra) "
        "y su Sombra (lo que reprime), y sus fortalezas latentes (su Luz).\n\n"
        "Debes retornar UN OBJETO JSON estructurado con el siguiente formato exacto:\n"
        "{\n"
        "  \"introduccion\": \"Un prólogo poético y junguiano de ~200 palabras hablándole directamente al alma del usuario, validando su viaje interior.\",\n"
        "  \"arquetipo_mascara\": {\n"
        "    \"titulo\": \"Nombre del arquetipo de la máscara (ej: El Buscador Incansable, El Protector Rígido)\",\n"
        "    \"descripcion\": \"Descripción detallada de cómo funciona su máscara social, por qué la construyó y cómo le sirve para protegerse.\"\n"
        "  },\n"
        "  \"sombra_integrar\": {\n"
        "    \"titulo\": \"El núcleo de la sombra reprimida\",\n"
        "    \"descripcion\": \"Análisis compasivo pero penetrante de los miedos reprimidos, impulsos negados, heridas infantiles activas y patrones de autosabotaje inconsciente.\",\n"
        "    \"disparadores\": [\"Lista de 3 situaciones cotidianas que detonan su sombra\"]\n"
        "  },\n"
        "  \"fuerza_luz\": {\n"
        "    \"titulo\": \"La luz de la integración\",\n"
        "    \"descripcion\": \"Tus talentos naturales y virtudes que surgen cuando integras tu sombra. El potencial de tu ser unificado.\"\n"
        "  },\n"
        "  \"hoja_ruta\": [\n"
        "    {\n"
        "      \"fase\": \"Fase 1: Reconocimiento\",\n"
        "      \"ejercicio\": \"Un ejercicio práctico específico para observar y documentar el arquetipo en su día a día.\"\n"
        "    },\n"
        "    {\n"
        "      \"fase\": \"Fase 2: Integración\",\n"
        "      \"ejercicio\": \"Una práctica meditativa o de diario (shadow work) para dialogar con la herida.\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    user_message = (
        f"Datos del Usuario:\n"
        f"Email: {report.user.email}\n\n"
        f"--- RESULTADOS DE CUESTIONARIOS ---\n"
        f"{chr(10).join(tests_summary)}\n\n"
        f"--- SESIONES DEL ESPEJO DE CONFLICTOS ---\n"
        f"{chr(10).join(sessions_summary)}"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }

    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=55,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        report.report_data = json.loads(raw)
        return True
    except Exception as e:
        print(f"Error calling DeepSeek for SoulReport: {e}")
        report.report_data = _generate_mock_bitacora(report.user)
        return True


def _generate_mock_bitacora(user):
    return {
        "introduccion": (
            "Bienvenido al registro de tu viaje interior. Esta Bitácora de Sombras es un reflejo sagrado "
            "de las aguas de tu inconsciente. Al explorar las profundidades de tus respuestas y tus diálogos con el Espejo, "
            "comenzamos a trazar el mapa de tus territorios inexplorados. Tu disposición a mirar lo que se esconde en la oscuridad "
            "es el primer gran paso hacia la unificación de tu ser."
        ),
        "arquetipo_mascara": {
            "titulo": "El Protector Rígido",
            "descripcion": (
                "Has construido una máscara de alta competencia, autosuficiencia y control. "
                "Esta armadura te protege contra la vulnerabilidad de ser rechazado o no ser visto. "
                "Prefieres resolver todo tú solo, mostrando al mundo una imagen de invulnerabilidad."
            )
        },
        "sombra_integrar": {
            "titulo": "El miedo al abandono y la descalificación",
            "descripcion": (
                "Debajo de la máscara de control yace el miedo a no ser suficiente, a ser excluido "
                "o a ser visto como incapaz. La sombra reprime tus necesidades de contención, descanso y juego, "
                "etiquetándolas inconscientemente como debilidades."
            ),
            "disparadores": [
                "Cuando alguien no responde tus mensajes o correos con la rapidez que esperas.",
                "Cuando cometes un pequeño error en público o en el trabajo.",
                "Cuando te ves obligado a pedir ayuda o delegar una tarea importante."
            ]
        },
        "fuerza_luz": {
            "titulo": "El Líder Compasivo e Integrador",
            "descripcion": (
                "Al abrazar tu sombra y aceptar tu vulnerabilidad, tu máscara de control madura hacia una "
                "capacidad de liderazgo compasivo. Eres capaz de guiar a otros desde la empatía real, no desde la exigencia."
            )
        },
        "hoja_ruta": [
            {
                "fase": "Fase 1: Reconocimiento",
                "ejercicio": "Lleva un registro de cada vez que sientas la tentación de decir 'yo puedo con todo solo'. Respira profundamente y anótalo."
            },
            {
                "fase": "Fase 2: Integración",
                "ejercicio": "Escribe una carta de agradecimiento a tu Máscara por haberte protegido en la infancia, pero aclárale que hoy, como adulto, es seguro bajar la guardia."
            }
        ]
    }
