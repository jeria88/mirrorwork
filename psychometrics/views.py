import json
import os

import requests
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

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
    except Exception:
        return ""


@login_required
def test_list(request):
    tests = Test.objects.filter(active=True)
    by_dimension = {}
    for test in tests:
        key = (test.dimension, test.get_dimension_display())
        by_dimension.setdefault(key, []).append(test)
    completed_ids = set(
        TestResult.objects.filter(user=request.user).values_list("test_id", flat=True)
    )
    return render(request, "psychometrics/test_list.html", {
        "by_dimension": by_dimension,
        "completed_ids": completed_ids,
    })


@login_required
def test_take(request, slug):
    test = get_object_or_404(Test, slug=slug, active=True)
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

    # Try to generate AI insight (costs 5 tokens; skip if balance insufficient)
    ai_insight = ""
    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(
            user=request.user, defaults={"balance": 0}
        )
        if balance.spend(5, reason=f"AI insight — {test.name}"):
            ai_insight = _generate_ai_insight(test.name, test.instrument_type, evaluation)
    except Exception:
        pass

    result = TestResult.objects.create(
        user=request.user,
        test=test,
        raw_scores=raw_scores,
        evaluation=evaluation,
        ai_insight=ai_insight,
    )

    return redirect("psychometrics:test_result", pk=result.pk)


@login_required
def test_result(request, pk):
    result = get_object_or_404(TestResult, pk=pk, user=request.user)
    return render(request, "psychometrics/test_result.html", {"result": result})


@login_required
def my_results(request):
    results = TestResult.objects.filter(user=request.user).select_related("test")
    return render(request, "psychometrics/my_results.html", {"results": results})
