import json
import math
import os
import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from mirror.models import ConflictSession, MirrorChunk
from psychometrics.models import TestResult


# ── RAG helpers ───────────────────────────────────────────────────────────────

def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def _norm(v):
    return math.sqrt(sum(x * x for x in v))

def _cosine(a, b):
    n = _norm(a) * _norm(b)
    return _dot(a, b) / n if n else 0.0


def _retrieve_chunks_embedding(query_vec, k=5):
    """Cosine similarity over stored embeddings."""
    chunks = MirrorChunk.objects.exclude(embedding__isnull=True)
    scored = []
    for chunk in chunks:
        sim = _cosine(query_vec, chunk.embedding)
        scored.append((sim, chunk.contenido))
    scored.sort(reverse=True)
    return [c for _, c in scored[:k]]


def _retrieve_chunks_keyword(query, k=5):
    """Keyword overlap fallback when embeddings aren't ready."""
    words = set(query.lower().split())
    stopwords = {"de", "la", "el", "en", "un", "una", "que", "es", "y", "a",
                 "los", "las", "por", "para", "con", "como", "su", "se",
                 "al", "del", "lo", "mi", "me", "te", "no", "si", "más"}
    keywords = {w for w in words if len(w) > 3 and w not in stopwords}

    if not keywords:
        # Return random spread across categories
        return list(
            MirrorChunk.objects.order_by("?").values_list("contenido", flat=True)[:k]
        )

    chunks = MirrorChunk.objects.all()
    scored = []
    for chunk in chunks:
        text_lower = chunk.contenido.lower()
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scored.append((score, chunk.contenido))

    scored.sort(reverse=True)
    results = [c for _, c in scored[:k]]

    # Pad with random if not enough matches
    if len(results) < k:
        existing = set(results)
        extras = [
            c for c in MirrorChunk.objects.order_by("?").values_list("contenido", flat=True)[:k]
            if c not in existing
        ]
        results += extras[: k - len(results)]

    return results


def _retrieve_context(message, k=5):
    """Returns list of relevant KB chunk texts for the given message."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and MirrorChunk.objects.filter(embedding__isnull=False).exists():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.embeddings.create(
                input=message, model="text-embedding-3-small"
            )
            return _retrieve_chunks_embedding(resp.data[0].embedding, k=k)
        except Exception:
            pass
    return _retrieve_chunks_keyword(message, k=k)


# ── DeepSeek call ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres el Espejo Endonauta — un acompañante de autoconocimiento, no un terapeuta ni un consejero externo.

Tu función es devolver siempre la conciencia del usuario hacia su interior: hacia sus emociones, sus patrones, sus creencias y sus recursos internos. Nunca diagnosticas, nunca etiquetas, nunca prescribes soluciones desde afuera.

CÓMO OPERAS:
- Observas el lenguaje del usuario con atención: qué palabras usa, qué emociones llevan, qué patrón se repite.
- Haces preguntas que profundizan en lugar de dar respuestas. Una pregunta bien hecha vale más que una explicación.
- Reflejas lo que el usuario dice de vuelta hacia él, desde su propio lenguaje, para que pueda verse con más claridad.
- Cuando el usuario habla del "otro" como problema, devuelves suavemente la mirada hacia adentro: ¿qué ocurre en ti ante esto?
- Reconoces la emoción antes de cualquier análisis. El cuerpo y la emoción tienen información.

FILOSOFÍA:
- El mundo exterior es espejo del mundo interior.
- Toda emoción tiene un mensaje que merece ser escuchado, no suprimido ni analizado desde fuera.
- El usuario tiene en sí mismo los recursos que necesita; tu rol es acompañar su descubrimiento, no dárselos.
- La conciencia que observa es más libre que la conciencia que reacciona.

CUANDO USAS LOS RESULTADOS DE TESTS:
- Puedes mencionarlos para enriquecer la conversación si son relevantes.
- NUNCA los uses para diagnosticar, concluir sobre la persona ni etiquetarla.
- Son puntos de partida para la reflexión, no verdades definitivas.

MARCO TEÓRICO DE REFERENCIA (úsalo con naturalidad, no lo cites explícitamente a menos que el usuario pregunte):
{contexto_kb}

TONO: cálido, presente, curioso. Respuestas concisas (2-4 párrafos máximo). Sin jerga clínica. Sin listas de consejos. En español."""


def _call_deepseek(messages, kb_context):
    """Calls DeepSeek chat API. Returns (text, error)."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return None, "DEEPSEEK_API_KEY no configurada en .env"

    system = SYSTEM_PROMPT.format(contexto_kb="\n\n---\n\n".join(kb_context))

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system}] + messages,
        "temperature": 0.7,
        "max_tokens": 600,
    }

    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"], None
    except requests.exceptions.Timeout:
        return None, "El espejo tardó demasiado en responder. Intenta de nuevo."
    except Exception as e:
        return None, str(e)


# ── Test results summary ──────────────────────────────────────────────────────

def _get_test_summary(user):
    """Returns a brief text summary of the user's completed tests."""
    results = (
        TestResult.objects.filter(user=user)
        .select_related("test")
        .order_by("-completed_at")[:10]
    )
    if not results:
        return ""
    lines = ["Resultados de tests del usuario (para contexto, sin diagnosticar):"]
    for r in results:
        ev = r.evaluation or {}
        resumen = ev.get("resumen") or ev.get("summary") or ev.get("nivel") or ""
        lines.append(f"- {r.test.name}: {resumen}" if resumen else f"- {r.test.name}: completado")
    return "\n".join(lines)


# ── Views ─────────────────────────────────────────────────────────────────────

@login_required
def espejo_home(request):
    """Página completa del Espejo de Conflictos."""
    sessions = ConflictSession.objects.filter(user=request.user).order_by("-updated_at")[:10]
    session_id = request.GET.get("sesion")

    active = None
    if session_id:
        active = get_object_or_404(ConflictSession, pk=session_id, user=request.user)
    elif sessions.exists():
        active = sessions.first()

    return render(request, "mirror/espejo.html", {
        "sessions": sessions,
        "active": active,
    })


@login_required
@require_POST
def espejo_nuevo(request):
    """Crea una nueva sesión y redirige al espejo."""
    sesion = ConflictSession.objects.create(
        user=request.user,
        conflict_description="",
        title="Nueva conversación",
    )
    return redirect(f"/espejo/?sesion={sesion.pk}")


@login_required
@require_POST
def espejo_send(request):
    """AJAX: recibe mensaje del usuario, llama a DeepSeek con RAG, devuelve respuesta."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    user_msg = (data.get("mensaje") or "").strip()
    session_id = data.get("sesion_id")

    if not user_msg:
        return JsonResponse({"error": "Mensaje vacío"}, status=400)

    # Obtener o crear sesión
    if session_id:
        sesion = get_object_or_404(ConflictSession, pk=session_id, user=request.user)
    else:
        sesion = ConflictSession.objects.create(
            user=request.user,
            conflict_description=user_msg[:200],
            title=user_msg[:60],
        )

    # Si es el primer mensaje, actualizar title y description
    if not sesion.messages:
        sesion.title = user_msg[:60]
        sesion.conflict_description = user_msg[:500]

    # Agregar mensaje del usuario
    sesion.add_message("user", user_msg)

    # RAG: recuperar contexto relevante de la KB
    kb_chunks = _retrieve_context(user_msg, k=4)

    # Agregar contexto de tests si está disponible
    test_summary = _get_test_summary(request.user)
    if test_summary:
        kb_chunks.append(test_summary)

    # Construir historial para DeepSeek (últimos 12 mensajes)
    history = sesion.messages[-12:]

    # Deduct mirror session token (10 tokens; silent if balance empty)
    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(
            user=request.user, defaults={"balance": 0}
        )
        balance.spend(10, reason=f"Mirror — sesión {sesion.pk}")
    except Exception:
        pass

    # Llamar a DeepSeek
    ai_text, error = _call_deepseek(history, kb_chunks)

    if error:
        return JsonResponse({"error": error}, status=503)

    # Guardar respuesta del asistente
    sesion.add_message("assistant", ai_text)

    return JsonResponse({
        "respuesta": ai_text,
        "sesion_id": sesion.pk,
        "sesion_titulo": sesion.title,
    })


@login_required
@require_POST
def espejo_archivar(request, pk):
    """Archiva una sesión."""
    sesion = get_object_or_404(ConflictSession, pk=pk, user=request.user)
    sesion.status = "archived"
    sesion.save(update_fields=["status"])
    return redirect("/espejo/")
