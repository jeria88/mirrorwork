import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from .evaluator import evaluate_test
from .models import Question, Test, TestResult


def _generate_ai_insight(test_name, instrument_type, evaluation):
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return ""
    tipo_label = {
        "clinical": "instrumento clínico validado",
        "adapted":  "adaptación orientativa",
        "custom":   "herramienta de reflexión endonauta",
    }.get(instrument_type, "herramienta")
    ev_texto = json.dumps(evaluation, ensure_ascii=False, indent=2)
    prompt = (
        f'Eres el Espejo Endonauta. El usuario acaba de completar "{test_name}" '
        f'({tipo_label}).\n\nResultados:\n{ev_texto}\n\n'
        "Escribe una lectura endonauta de 3-4 párrafos: sin diagnosticar, "
        "devolviendo la conciencia al interior del usuario, terminando con una "
        "pregunta de exploración. Tono cálido, curioso, empoderador. En español."
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
                "temperature": 0.75,
                "max_tokens": 600,
            },
            timeout=25,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("_generate_ai_insight failed: %s", e)
        return ""


def _run_insight_thread(result_pk, test_name, instrument_type, evaluation):
    insight = _generate_ai_insight(test_name, instrument_type, evaluation)
    if insight:
        TestResult.objects.filter(pk=result_pk).update(ai_insight=insight)
    else:
        TestResult.objects.filter(pk=result_pk).update(ai_insight="—")


@login_required
def test_list(request):
    tests = Test.objects.filter(active=True)
    
    # Define portals mapping
    portal_1_slugs = [
        'big-five-inventario-de-personalidad',
        'tipologia-de-jung',
        'riasec-perfil-vocacional-de-holland',
        'rueda-de-la-vida-integracion'
    ]
    portal_2_slugs = [
        'autosabotaje',
        'heridas-de-la-infancia-lise-bourbeau',
        'eneagrama-tipologia-de-caracter',
        'phq-9-cuestionario-de-salud-del-paciente',
        'gad-7-ansiedad-generalizada',
        'dirty-dozen-triada-oscura',
        'ibi-creencias-irracionales'
    ]
    portal_3_slugs = [
        'maia-consciencia-interoceptiva',
        'psqi-calidad-del-sueno-de-pittsburgh',
        'ders-dificultades-en-regulacion-emocional',
        'pss-10-estres-percibido',
        'tas-20-alexitimia-escala-toronto',
        'perfil-neurosensorial'
    ]
    
    # Calculate user progress
    completed_ids = set(
        TestResult.objects.filter(user=request.user).values_list("test_id", flat=True)
    )
    completed_slugs = set(
        TestResult.objects.filter(user=request.user).values_list("test__slug", flat=True)
    )
    
    # Retrieve assigned test ids
    assigned_test_ids = set()
    try:
        if hasattr(request.user, 'claimed_profile'):
            assigned_test_ids = set(request.user.claimed_profile.assigned_tests.values_list('id', flat=True))
    except Exception:
        pass
    
    # Count completions in each portal
    p1_completed_count = sum(1 for slug in portal_1_slugs if slug in completed_slugs)
    p2_completed_count = sum(1 for slug in portal_2_slugs if slug in completed_slugs)
    p3_completed_count = sum(1 for slug in portal_3_slugs if slug in completed_slugs)
    
    # Subscribed check
    has_active_plan = getattr(request.user, 'profile', None) and request.user.profile.plan in ('navegante', 'practicante', 'empresa')
    
    # Unlock logic
    p1_unlocked = True
    p2_unlocked = has_active_plan or p1_completed_count >= 3
    p3_unlocked = has_active_plan or (p2_unlocked and p2_completed_count >= 3)
    p4_unlocked = has_active_plan or (p3_unlocked and p3_completed_count >= 3)
    
    # Organize tests into portals
    portals = [
        {
            "id": 1,
            "name": "Portal I: La Máscara (Personalidad Externa)",
            "desc": "Explora tu personalidad consciente, tu tipología y tu rol social.",
            "unlocked": p1_unlocked,
            "required_prev": 0,
            "prev_completed": 0,
            "tests": [],
        },
        {
            "id": 2,
            "name": "Portal II: El Descenso (La Sombra)",
            "desc": "Conoce tus patrones de autosabotaje, tus heridas de infancia y tus respuestas ante el estrés.",
            "unlocked": p2_unlocked,
            "required_prev": 3,
            "prev_completed": p1_completed_count,
            "tests": [],
        },
        {
            "id": 3,
            "name": "Portal III: El Templo Interno (Regulación)",
            "desc": "Profundiza en tu conciencia corporal, la calidad de tu sueño y tu regulación emocional.",
            "unlocked": p3_unlocked,
            "required_prev": 3,
            "prev_completed": p2_completed_count,
            "tests": [],
        },
        {
            "id": 4,
            "name": "Portal IV: La Integración (Luz y Trascendencia)",
            "desc": "El potencial de tu ser unificado: fortalezas, chakras, sueños y trascendencia.",
            "unlocked": p4_unlocked,
            "required_prev": 3,
            "prev_completed": p3_completed_count,
            "tests": [],
        }
    ]
    
    for test in tests:
        if test.slug in portal_1_slugs:
            portals[0]["tests"].append(test)
        elif test.slug in portal_2_slugs:
            portals[1]["tests"].append(test)
        elif test.slug in portal_3_slugs:
            portals[2]["tests"].append(test)
        else:
            portals[3]["tests"].append(test)
 
    # Sort tests in each portal by their 'order' field
    for p in portals:
        p["tests"].sort(key=lambda t: t.order)
            
    return render(request, "psychometrics/test_list.html", {
        "portals": portals,
        "completed_ids": completed_ids,
        "assigned_test_ids": assigned_test_ids,
        "has_active_plan": has_active_plan,
    })
 
 
@login_required
def test_take(request, slug):
    test = get_object_or_404(Test, slug=slug, active=True)
    
    # Check if test is assigned to bypass lock
    is_assigned = False
    try:
        if hasattr(request.user, 'claimed_profile'):
            is_assigned = request.user.claimed_profile.assigned_tests.filter(slug=slug).exists()
    except Exception:
        pass
    
    # Check if test is locked
    completed_slugs = set(
        TestResult.objects.filter(user=request.user).values_list("test__slug", flat=True)
    )
    has_active_plan = getattr(request.user, 'profile', None) and request.user.profile.plan in ('navegante', 'practicante', 'empresa')
    
    # Define portal mapping
    portal_1_slugs = ['big-five-inventario-de-personalidad', 'tipologia-de-jung', 'riasec-perfil-vocacional-de-holland', 'rueda-de-la-vida-integracion']
    portal_2_slugs = ['autosabotaje', 'heridas-de-la-infancia-lise-bourbeau', 'eneagrama-tipologia-de-caracter', 'phq-9-cuestionario-de-salud-del-paciente', 'gad-7-ansiedad-generalizada', 'dirty-dozen-triada-oscura', 'ibi-creencias-irracionales']
    portal_3_slugs = ['maia-consciencia-interoceptiva', 'psqi-calidad-del-sueno-de-pittsburgh', 'ders-dificultades-en-regulacion-emocional', 'pss-10-estres-percibido', 'tas-20-alexitimia-escala-toronto', 'perfil-neurosensorial']
    
    p1_completed_count = sum(1 for s in portal_1_slugs if s in completed_slugs)
    p2_completed_count = sum(1 for s in portal_2_slugs if s in completed_slugs)
    
    is_locked = False
    error_msg = ""
    
    if is_assigned:
        # assigned tests bypass lock logic
        pass
    else:
        if slug in portal_2_slugs and not has_active_plan and p1_completed_count < 3:
            is_locked = True
            error_msg = "El Portal II (La Sombra) está bloqueado. Requiere completar al menos 3 tests del Portal I o tener un plan activo."
        elif slug in portal_3_slugs and not has_active_plan:
            p2_unlocked = p1_completed_count >= 3
            if not p2_unlocked or p2_completed_count < 3:
                is_locked = True
                error_msg = "El Portal III (El Templo Interno) está bloqueado. Requiere completar al menos 3 tests del Portal II o tener un plan activo."
        elif slug not in portal_1_slugs and slug not in portal_2_slugs and slug not in portal_3_slugs and not has_active_plan:
            p2_unlocked = p1_completed_count >= 3
            p3_unlocked = p2_unlocked and p2_completed_count >= 3
            p3_completed_count = sum(1 for s in portal_3_slugs if s in completed_slugs)
            if not p3_unlocked or p3_completed_count < 3:
                is_locked = True
                error_msg = "El Portal IV (La Integración) está bloqueado. Requiere completar al menos 3 tests del Portal III o tener un plan activo."
            
    if is_locked:
        from django.contrib import messages
        messages.error(request, error_msg)
        return redirect("psychometrics:test_list")
 
    questions = test.questions.all()
    return render(request, "psychometrics/test_take.html", {
        "test": test,
        "questions": questions,
    })


@login_required
def test_submit(request, slug):
    if request.method != "POST":
        return redirect("psychometrics:test_take", slug=slug)

    test = get_object_or_404(Test, slug=slug, active=True)
    questions = test.questions.all()

    raw_scores = {}
    for q in questions:
        val = request.POST.get(f"q_{q.id}")
        if val is None:
            continue
        try:
            score = int(val)
        except ValueError:
            continue

        if q.reverse_scored:
            if q.scale in ("likert5", "likert5a"):
                score = 6 - score
            elif q.scale == "likert4":
                score = 4 - score
            elif q.scale == "likert3":
                score = 3 - score
            elif q.scale == "likert7":
                score = 8 - score
            elif q.scale == "binary":
                score = 1 - score

        dim_key = q.dimension_key or test.dimension
        raw_scores[dim_key] = raw_scores.get(dim_key, 0) + score

    evaluation = evaluate_test(test.name, raw_scores)

    result = TestResult.objects.create(
        user=request.user,
        test=test,
        raw_scores=raw_scores,
        evaluation=evaluation,
        ai_insight="",
    )

    return redirect("psychometrics:test_result", pk=result.pk)


_ONBOARDING_SLUGS = [
    'rueda-de-la-vida-integracion',
    'big-five-inventario-de-personalidad',
    'heridas-de-la-infancia-lise-bourbeau',
]

_CRISIS_THRESHOLDS = {
    'phq-9-cuestionario-de-salud-del-paciente': 20,
    'gad-7-ansiedad-generalizada': 15,
}


@login_required
def test_result(request, pk):
    result = get_object_or_404(TestResult, pk=pk, user=request.user)

    # Onboarding completion: credit mission and flag for template
    is_onboarding_complete = False
    if result.test.slug in _ONBOARDING_SLUGS:
        done = (
            TestResult.objects.filter(user=request.user, test__slug__in=_ONBOARDING_SLUGS)
            .values('test__slug').distinct().count()
        )
        if done >= len(_ONBOARDING_SLUGS):
            is_onboarding_complete = True
            from tokens.service import credit_mission
            credit_mission(request.user, 'onboarding')

    # Crisis safety check for PHQ-9 and GAD-7
    crisis_alert = None
    threshold = _CRISIS_THRESHOLDS.get(result.test.slug)
    if threshold is not None:
        dims = (result.evaluation or {}).get('dimensiones', [])
        if dims and dims[0].get('puntos', 0) >= threshold:
            crisis_alert = result.test.slug

    return render(request, "psychometrics/test_result.html", {
        "result": result,
        "is_onboarding_complete": is_onboarding_complete,
        "crisis_alert": crisis_alert,
    })


@login_required
def my_results(request):
    results = TestResult.objects.filter(user=request.user).select_related("test")
    return render(request, "psychometrics/my_results.html", {"results": results})


@login_required
def result_status(request, pk):
    result = get_object_or_404(TestResult, pk=pk, user=request.user)
    if result.ai_insight in ("", "processing"):
        return JsonResponse({"status": "processing"})
    insight = "" if result.ai_insight == "—" else result.ai_insight
    return JsonResponse({"status": "complete", "insight": insight})


@login_required
def insight_view(request, pk):
    result = get_object_or_404(TestResult, pk=pk, user=request.user)
    return render(request, "psychometrics/insight_view.html", {"result": result})


@login_required
def insight_reveal(request, pk):
    if request.method != "POST":
        return redirect("psychometrics:insight_view", pk=pk)
    result = get_object_or_404(TestResult, pk=pk, user=request.user)

    if result.ai_insight and result.ai_insight not in ("", "—"):
        return redirect("psychometrics:insight_view", pk=pk)

    from tokens.service import has_balance, spend
    if not has_balance(request.user, 'ai_insight'):
        from django.contrib import messages
        messages.error(request, "Fractones insuficientes para generar el insight.")
        return redirect("psychometrics:insight_view", pk=pk)

    spend(request.user, 'ai_insight')
    TestResult.objects.filter(pk=pk).update(ai_insight="processing")
    threading.Thread(
        target=_run_insight_thread,
        args=(result.pk, result.test.name, result.test.instrument_type, result.evaluation),
        daemon=True,
    ).start()
    return redirect("psychometrics:insight_view", pk=pk)


# ── API endpoints for SPA ─────────────────────────────────────────────────────

from community.models import SharedInsight


@login_required
@require_GET
def api_test_list(request):
    """GET /psychometrics/api/tests/ — Returns list of active tests as JSON."""
    tests = Test.objects.filter(active=True)
    completed_ids = set(
        TestResult.objects.filter(user=request.user).values_list("test_id", flat=True)
    )

    data = []
    for t in tests:
        question_count = t.questions.count()
        data.append({
            'id': t.id,
            'name': t.name,
            'slug': t.slug,
            'description': t.description,
            'category': t.dimension,
            'duration_minutes': t.estimated_minutes,
            'question_count': question_count,
            'completed': t.id in completed_ids,
        })
    return JsonResponse(data, safe=False)


@login_required
@csrf_exempt
@require_POST
def api_test_start(request, slug):
    """POST /psychometrics/api/tests/<slug>/start/ — Creates a new TestResult and returns first question."""
    test = get_object_or_404(Test, slug=slug, active=True)
    questions = list(test.questions.all().order_by('order', 'id'))

    if not questions:
        return JsonResponse({'error': 'Este test no tiene preguntas.'}, status=400)

    result = TestResult.objects.create(
        user=request.user,
        test=test,
        raw_scores={},
        evaluation={},
    )

    first_q = questions[0]
    opts = _question_options(first_q)

    return JsonResponse({
        'result_id': result.pk,
        'test_name': test.name,
        'total_questions': len(questions),
        'question': {
            'id': first_q.id,
            'text': first_q.text,
            'type': first_q.scale,
            'options': opts,
        },
    })


def _question_options(question):
    """Return option labels for a question based on its scale."""
    _opts_map = {
        'likert5':  [('1', 'Nunca'), ('2', 'Pocas veces'), ('3', 'A veces'), ('4', 'Frecuentemente'), ('5', 'Siempre')],
        'likert5a': [('1', 'Muy en desacuerdo'), ('2', 'En desacuerdo'), ('3', 'Neutral'), ('4', 'De acuerdo'), ('5', 'Muy de acuerdo')],
        'likert4':  [('0', 'Nunca'), ('1', 'Rara vez'), ('2', 'A veces'), ('3', 'Frecuentemente'), ('4', 'Siempre')],
        'likert3':  [('0', 'No'), ('1', 'A veces'), ('2', 'Sí'), ('3', 'Casi siempre')],
        'likert7':  [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')],
        'binary':   [('0', 'No'), ('1', 'Sí')],
    }
    raw = _opts_map.get(question.scale, _opts_map['likert5'])
    return [{'value': v, 'label': l} for v, l in raw]


@login_required
@csrf_exempt
@require_POST
def api_test_answer(request, slug):
    """POST /psychometrics/api/tests/<slug>/answer/ — Saves an answer and returns next question or final result."""
    test = get_object_or_404(Test, slug=slug, active=True)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    result_id = data.get('result_id')
    question_id = data.get('question_id')
    answer = data.get('answer')

    if result_id is None or question_id is None or answer is None:
        return JsonResponse({'error': 'Faltan campos: result_id, question_id, answer'}, status=400)

    result = get_object_or_404(TestResult, pk=result_id, user=request.user, test=test)
    question = get_object_or_404(Question, pk=question_id, test=test)

    # Store the answer in raw_scores
    raw_scores = result.raw_scores or {}
    dim_key = question.dimension_key or test.dimension

    try:
        score = int(answer)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Respuesta debe ser numérica'}, status=400)

    # Store per-question answer keyed by question id
    raw_scores[f'q_{question_id}'] = score
    result.raw_scores = raw_scores
    result.save(update_fields=['raw_scores'])

    # Find next question
    questions = list(test.questions.all().order_by('order', 'id'))
    current_idx = None
    for i, q in enumerate(questions):
        if q.id == question.id:
            current_idx = i
            break

    if current_idx is not None and current_idx + 1 < len(questions):
        next_q = questions[current_idx + 1]
        opts = _question_options(next_q)
        return JsonResponse({
            'next_question': {
                'id': next_q.id,
                'text': next_q.text,
                'type': next_q.scale,
                'options': opts,
            }
        })
    else:
        # No more questions — compute final scores
        final_scores = {}
        for q in questions:
            val = raw_scores.get(f'q_{q.id}')
            if val is None:
                continue
            try:
                sc = int(val)
            except (ValueError, TypeError):
                continue
            if q.reverse_scored:
                if q.scale in ('likert5', 'likert5a'):
                    sc = 6 - sc
                elif q.scale == 'likert4':
                    sc = 4 - sc
                elif q.scale == 'likert3':
                    sc = 3 - sc
                elif q.scale == 'likert7':
                    sc = 8 - sc
                elif q.scale == 'binary':
                    sc = 1 - sc
            dk = q.dimension_key or test.dimension
            final_scores[dk] = final_scores.get(dk, 0) + sc

        result.raw_scores = final_scores
        result.save(update_fields=['raw_scores'])

        result_url = f'/psicometria/resultado/{result.pk}/'

        return JsonResponse({
            'completed': True,
            'result_url': result_url,
            'scores': final_scores,
        })


@login_required
@require_GET
def api_my_results(request):
    """GET /psychometrics/api/my-results/ — Returns user's test results."""
    results = TestResult.objects.filter(user=request.user).select_related('test').order_by('-completed_at')
    data = []
    for r in results:
        data.append({
            'id': r.pk,
            'test_name': r.test.name,
            'test_slug': r.test.slug,
            'completed_at': r.completed_at.isoformat() if r.completed_at else None,
            'scores': r.evaluation or {},
        })
    return JsonResponse(data, safe=False)
