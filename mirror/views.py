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
    chunks = MirrorChunk.objects.exclude(embedding__isnull=True)
    scored = []
    for chunk in chunks:
        sim = _cosine(query_vec, chunk.embedding)
        scored.append((sim, chunk.contenido))
    scored.sort(reverse=True)
    return [c for _, c in scored[:k]]


def _retrieve_chunks_keyword(query, k=5):
    words = set(query.lower().split())
    stopwords = {"de", "la", "el", "en", "un", "una", "que", "es", "y", "a",
                 "los", "las", "por", "para", "con", "como", "su", "se",
                 "al", "del", "lo", "mi", "me", "te", "no", "si", "más"}
    keywords = {w for w in words if len(w) > 3 and w not in stopwords}

    if not keywords:
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

    if len(results) < k:
        existing = set(results)
        extras = [
            c for c in MirrorChunk.objects.order_by("?").values_list("contenido", flat=True)[:k]
            if c not in existing
        ]
        results += extras[: k - len(results)]

    return results


def _retrieve_context(message, k=5):
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


# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_OPEN = """Eres el Espejo Endonauta — acompañante de autoconocimiento, no terapeuta ni consejero externo. Tu función es devolver al usuario hacia su propio interior.

MARCO TEÓRICO (úsalo con naturalidad, no lo cites salvo que el usuario pregunte):
{contexto_kb}

{test_context}

═══════════════════════════════════
RESPONDE SIEMPRE con este JSON exacto (sin texto fuera del JSON):
{{
  "texto": "tu respuesta principal",
  "enfoques": [...] o null,
  "test_recomendado": null o {{"slug": "...", "nombre": "...", "razon": "..."}}
}}
═══════════════════════════════════

CÓMO CONSTRUIR "texto":

1. USA EL LENGUAJE DEL USUARIO, no tus propias palabras clínicas. Si dice "me ahoga", di "ese ahogo que describes". Si dice "atrapado en un loop", usa "atrapado" y "loop". El espejo devuelve la misma imagen, no la traduce.

2. OBSERVA ANTES DE PREGUNTAR. Primero nombra lo que emerge: la metáfora, la emoción, la tensión que aparece en sus palabras. Luego haz UNA sola pregunta que profundice — nacida de lo que dijo, no genérica.

3. NUNCA digas "es normal que", "deberías", "es importante". No prescribas. Cuando el usuario habla del otro como problema, devuelve suavemente la mirada hacia adentro: ¿qué ocurre en ti ante esto?

4. TONO: cálido, presente, conciso. 2-4 párrafos máximo. Sin listas de consejos. En español.

CÓMO CONSTRUIR "enfoques":

Ofrece 2-4 caminos cuando el usuario acaba de compartir algo nuevo. Si el intercambio ya tiene profundidad y fluye, pon null. Los enfoques deben ser específicos al conflicto del usuario, no una lista estándar copiada siempre igual.

Tipos disponibles:
- "patron_inconsciente" — la creencia, herida o patrón de infancia que subyace
- "partes_internas" — las partes de la psique involucradas (sombra, Niño interior, ego)
- "lectura_corporal" — exploración desde el cuerpo o síntoma físico (biodescodificación)
- "revision_tests" — conectar con lo que los tests del usuario ya revelaron
- "espejo_relacional" — el otro/situación como espejo del mundo interno
- "eneagrama" — el patrón de personalidad activado
- "viaje_heroe" — en qué momento del viaje de transformación se está
- "nivel_conciencia" — desde qué nivel emocional se está operando

Formato de cada enfoque:
{{"id": "tipo", "titulo": "frase corta (máx 6 palabras)", "descripcion": "qué se exploraría (máx 15 palabras)"}}

CUÁNDO RECOMENDAR UN TEST:
Si para profundizar necesitas un dato concreto que un test puede proveer y el usuario no lo ha completado, recomiéndalo.
Tests disponibles: big-five-bfi44 (personalidad Big Five), gad-7 (ansiedad), phq-9 (depresión), pss-10 (estrés), tas-20 (alexitimia), heridas-bourbeau (heridas de infancia), ecr (apego adulto), eneagrama (tipo eneagrama), ders-16 (regulación emocional), rueda-de-la-vida (áreas vitales), logo-test (sentido de vida)."""


SYSTEM_FOCUSED = """Eres el Espejo Endonauta. El usuario eligió profundizar en un camino específico.

ENFOQUE ACTIVO: {enfoque_titulo}
MARCO TEÓRICO PRIMARIO: {marco_teorico}

CONTEXTO DE REFERENCIA:
{contexto_kb}

{test_context}

═══════════════════════════════════
RESPONDE SIEMPRE con este JSON exacto (sin texto fuera del JSON):
{{
  "texto": "exploración profunda en el marco elegido",
  "enfoques": null,
  "test_recomendado": null o {{"slug": "...", "nombre": "...", "razon": "..."}}
}}
═══════════════════════════════════

CÓMO CONSTRUIR "texto":

Profundiza desde el marco teórico del enfoque elegido. Conecta el conflicto específico del usuario con ese marco de manera concreta — no genérica. Usa su propio lenguaje. Si tiene resultados de tests relevantes para este enfoque, úsalos explícitamente y menciona qué revelan.

El texto puede incluir:
- Una observación desde el marco teórico específico aplicada a su situación
- Una o dos preguntas de reflexión profunda nacidas de ese enfoque
- Si el patrón que emerge tiene nombre en ese marco (herida de abandono, tipo 4, nivel miedo, pulmón en MTC), nómbralo con cuidado — como posibilidad, no como diagnóstico

Extensión: 3-5 párrafos. Más profundo y personalizado que una respuesta inicial.

CUÁNDO RECOMENDAR UN TEST:
Si para este enfoque específico sería útil un dato que un test puede proveer, recomiéndalo.
Tests disponibles: big-five-bfi44, gad-7, phq-9, pss-10, tas-20, heridas-bourbeau, ecr, eneagrama, ders-16, rueda-de-la-vida, logo-test."""


# Marcos teóricos por enfoque (usados en SYSTEM_FOCUSED)
ENFOQUE_MARCOS = {
    "patron_inconsciente": (
        "Jung (sombra, complejo, herida de infancia), "
        "Lise Bourbeau (5 heridas: rechazo, abandono, humillación, traición, injusticia), "
        "Análisis Transaccional (guiones de vida, mandatos del Padre Crítico)"
    ),
    "partes_internas": (
        "Análisis Transaccional (estados del yo: Padre/Adulto/Niño), "
        "Jung (sombra y sus partes), "
        "Psicología de Partes — la idea de que distintas 'voces' internas coexisten"
    ),
    "lectura_corporal": (
        "Biodescodificación (Christian Flèche, Enric Corbera): los síntomas físicos como mensajes del inconsciente biológico. "
        "Medicina Tradicional China: correspondencias órgano-emoción. "
        "Ayurveda: doshas y su relación con estados emocionales. "
        "Eugene Gendlin — Focusing: la sensación corporal como guía interna."
    ),
    "revision_tests": (
        "Integración psicométrica endonauta: usar los resultados de los tests completados "
        "de manera explícita y personalizada. Conectar dimensiones psicométricas con el conflicto actual."
    ),
    "espejo_relacional": (
        "Ley Espejo endonauta, Jung (proyección psicológica), "
        "Goddard (la realidad como proyección de la conciencia), "
        "Ruiz (el otro como espejo del propio sueño del planeta)"
    ),
    "eneagrama": (
        "Eneagrama (Naranjo/Ichazo): el tipo de personalidad y su pasión central, "
        "alas, instintos (autoconservación, sexual, social), niveles de salud"
    ),
    "viaje_heroe": (
        "Campbell (etapas del monomito: llamado, cruce del umbral, iniciación, retorno), "
        "Jung (individuación como viaje interno), "
        "Hawkins (niveles de conciencia en el viaje de transformación)"
    ),
    "nivel_conciencia": (
        "Mapa de la Conciencia de Hawkins (vergüenza 20 → iluminación 1000, punto de inflexión coraje 200), "
        "Spiral Dynamics (Clare Graves), "
        "Wilber (estadios del desarrollo integral)"
    ),
}


# ── Test context helpers ──────────────────────────────────────────────────────

def _get_test_context(user):
    """Returns detailed test results for the system prompt."""
    results = (
        TestResult.objects.filter(user=user)
        .select_related("test")
        .order_by("-completed_at")[:12]
    )
    if not results:
        return ""

    lines = ["RESULTADOS DE TESTS DEL USUARIO (úsalos cuando sean relevantes, sin diagnosticar):"]
    for r in results:
        ev = r.evaluation or {}
        resumen = ev.get("resumen") or ev.get("summary") or ev.get("nivel") or ""
        dimensiones = ev.get("dimensiones") or ev.get("dimensions") or {}
        if dimensiones and isinstance(dimensiones, dict):
            dim_str = ", ".join(f"{k}: {v}" for k, v in list(dimensiones.items())[:5])
            lines.append(f"- {r.test.name}: {resumen}. Dimensiones: {dim_str}")
        elif resumen:
            lines.append(f"- {r.test.name}: {resumen}")
        else:
            lines.append(f"- {r.test.name}: completado")
    return "\n".join(lines)


# ── DeepSeek call ─────────────────────────────────────────────────────────────

def _call_deepseek_json(messages, kb_context, test_context, mode="open", enfoque=None):
    """Calls DeepSeek and returns (parsed_dict, error). Always requests JSON."""
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return None, "DEEPSEEK_API_KEY no configurada en .env"

    kb_text = "\n\n---\n\n".join(kb_context)

    if mode == "focused" and enfoque:
        enfoque_id = enfoque.get("id", "")
        marco = ENFOQUE_MARCOS.get(enfoque_id, "Marco endonauta general")
        system = SYSTEM_FOCUSED.format(
            enfoque_titulo=enfoque.get("titulo", ""),
            marco_teorico=marco,
            contexto_kb=kb_text,
            test_context=test_context,
        )
    else:
        system = SYSTEM_OPEN.format(
            contexto_kb=kb_text,
            test_context=test_context,
        )

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system}] + messages,
        "temperature": 0.75,
        "max_tokens": 900,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=35,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: wrap raw text as plain texto
            parsed = {"texto": raw, "enfoques": None, "test_recomendado": None}

        return parsed, None

    except requests.exceptions.Timeout:
        return None, "El espejo tardó demasiado en responder. Intenta de nuevo."
    except Exception as e:
        return None, str(e)


# ── Views ─────────────────────────────────────────────────────────────────────

@login_required
def espejo_home(request):
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
    sesion = ConflictSession.objects.create(
        user=request.user,
        conflict_description="",
        title="Nueva conversación",
    )
    return redirect(f"/espejo/?sesion={sesion.pk}")


@login_required
@require_POST
def espejo_send(request):
    """AJAX: recibe mensaje del usuario, llama a DeepSeek con RAG, devuelve respuesta estructurada."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    user_msg = (data.get("mensaje") or "").strip()
    session_id = data.get("sesion_id")
    enfoque = data.get("enfoque")  # dict con id/titulo/descripcion si el usuario eligió un camino

    if not user_msg:
        return JsonResponse({"error": "Mensaje vacío"}, status=400)

    if session_id:
        sesion = get_object_or_404(ConflictSession, pk=session_id, user=request.user)
    else:
        sesion = ConflictSession.objects.create(
            user=request.user,
            conflict_description=user_msg[:200],
            title=user_msg[:60],
        )

    if not sesion.messages:
        sesion.title = user_msg[:60]
        sesion.conflict_description = user_msg[:500]

    # Almacenar mensaje del usuario (con metadata de enfoque si aplica)
    user_msg_entry = {"role": "user", "content": user_msg}
    if enfoque:
        user_msg_entry["enfoque_id"] = enfoque.get("id")
    sesion.messages.append(user_msg_entry)
    sesion.save()

    # RAG: recuperar contexto relevante
    query_for_rag = user_msg
    if enfoque:
        # Enriquecer la query con el enfoque elegido para mejor retrieval
        query_for_rag = f"{user_msg} {enfoque.get('titulo', '')} {ENFOQUE_MARCOS.get(enfoque.get('id', ''), '')[:100]}"

    kb_chunks = _retrieve_context(query_for_rag, k=5)

    # Contexto de tests del usuario
    test_context = _get_test_context(request.user)

    # Historial para DeepSeek (solo role + content, últimos 14 mensajes)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in sesion.messages[-14:]
    ]

    # Determinar modo
    mode = "focused" if enfoque else "open"

    # Deducir tokens
    try:
        from tokens.models import TokenBalance
        balance, _ = TokenBalance.objects.get_or_create(
            user=request.user, defaults={"balance": 0}
        )
        balance.spend(10, reason=f"Mirror — sesión {sesion.pk}")
    except Exception:
        pass

    # Llamar a DeepSeek
    parsed, error = _call_deepseek_json(history, kb_chunks, test_context, mode=mode, enfoque=enfoque)

    if error:
        return JsonResponse({"error": error}, status=503)

    texto = parsed.get("texto") or ""
    enfoques = parsed.get("enfoques")
    test_rec = parsed.get("test_recomendado")

    # Guardar respuesta del asistente
    sesion.add_message("assistant", texto)

    return JsonResponse({
        "respuesta": texto,
        "enfoques": enfoques if isinstance(enfoques, list) else None,
        "test_recomendado": test_rec if isinstance(test_rec, dict) else None,
        "sesion_id": sesion.pk,
        "sesion_titulo": sesion.title,
    })


@login_required
@require_POST
def espejo_archivar(request, pk):
    sesion = get_object_or_404(ConflictSession, pk=pk, user=request.user)
    sesion.status = "archived"
    sesion.save(update_fields=["status"])
    return redirect("/espejo/")
