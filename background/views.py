import json
import os
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import BackgroundTemplate, TemplateRating

PEXELS_KEY = os.getenv('PEXELS_API_KEY', '')
DEEPSEEK_KEY = getattr(settings, 'DEEPSEEK_API_KEY', '')
DEEPSEEK_URL = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat')

SECTIONS = ['general', 'espejo', 'tests', 'onboarding', 'birth']

AGENT_SYSTEM_PROMPT = """Eres un agente experto en HTML/CSS/JS creativo.
Tu tarea es generar el código HTML de un fondo visual para una sección específica de una app web de autoconocimiento llamada MirrorWork.

Reglas obligatorias:
1. El HTML debe ser COMPLETAMENTE AUTOCONTENIDO — todo el CSS y JS va inline, en etiquetas <style> y <script>.
2. El fondo ocupa el 100% del viewport: body { margin:0; overflow:hidden; width:100vw; height:100vh; background:#000; }
3. Puedes usar canvas, SVG, animaciones CSS, Three.js via CDN (https://cdn.jsdelivr.net/npm/three@0.160/build/three.min.js), o efectos con partículas.
4. Si el usuario proporcionó URLs de imágenes/videos, úsalas como recursos centrales del diseño.
5. Si el usuario no proporcionó imágenes, diseña el fondo solo con código (generativo/procesal).
6. Cada sección tiene un tono:
   - general: neutro, contemplativo
   - espejo: introspectivo, profundo, sombra/luz
   - tests: activo, exploración
   - onboarding: acogedor, inicio del viaje
   - birth: natal, cósmico, tiempo
7. Las transiciones entre secciones deben ser suaves — diseña cada HTML para que pueda fundirse (opacity transition).
8. No incluyas texto ni UI. Solo el fondo visual.
9. Responde con JSON puro, sin markdown, sin explicaciones:
{
  "general":    "<html completo>",
  "espejo":     "<html completo>",
  "tests":      "<html completo>",
  "onboarding": "<html completo>",
  "birth":      "<html completo>",
  "transitions": {
    "general_to_espejo": "fade",
    "espejo_to_tests":   "dissolve"
  }
}"""


def _pexels_search(query: str, per_page: int = 6) -> list:
    if not PEXELS_KEY:
        return []
    try:
        r = requests.get(
            'https://api.pexels.com/v1/search',
            headers={'Authorization': PEXELS_KEY},
            params={'query': query, 'per_page': per_page, 'orientation': 'landscape'},
            timeout=8,
        )
        if r.ok:
            return [p['src']['large'] for p in r.json().get('photos', [])]
    except Exception:
        pass
    return []


def _call_deepseek(user_description: str, media_urls: list) -> dict:
    media_block = ''
    if media_urls:
        media_block = '\n\nIMÁGENES/VIDEOS proporcionados por el usuario:\n' + '\n'.join(f'- {u}' for u in media_urls)

    user_msg = (
        f'Descripción del mundo interior del usuario:\n"{user_description}"{media_block}\n\n'
        'Genera los 5 HTMLs de fondo (general, espejo, tests, onboarding, birth) inspirados en esta descripción.'
    )

    payload = {
        'model': DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': AGENT_SYSTEM_PROMPT},
            {'role': 'user',   'content': user_msg},
        ],
        'temperature': 0.85,
        'max_tokens': 8000,
    }
    resp = requests.post(
        f'{DEEPSEEK_URL}/chat/completions',
        headers={
            'Authorization': f'Bearer {DEEPSEEK_KEY}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    raw = resp.json()['choices'][0]['message']['content'].strip()
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[1].rsplit('```', 1)[0]
    return json.loads(raw)


@login_required
def mapa_tab(request):
    profile = request.user.profile
    user_templates = BackgroundTemplate.objects.filter(user=request.user).order_by('-created_at')
    public_templates = BackgroundTemplate.objects.filter(is_public=True).order_by('-use_count', '-created_at')[:24]
    return render(request, 'background/mapa_tab.html', {
        'user_templates': user_templates,
        'public_templates': public_templates,
        'active_template': profile.active_template,
    })


@login_required
@require_POST
def generate(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    description = data.get('description', '').strip()
    if not description:
        return JsonResponse({'ok': False, 'error': 'Descripción vacía'}, status=400)

    user_urls = [u.strip() for u in data.get('media_urls', []) if u.strip()]
    use_pexels = data.get('use_pexels', False)

    if use_pexels and not user_urls:
        user_urls = _pexels_search(description[:80], per_page=4)

    try:
        scenes_data = _call_deepseek(description, user_urls)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    scenes = {k: scenes_data.get(k, '') for k in SECTIONS}
    transitions = scenes_data.get('transitions', {})

    template = BackgroundTemplate.objects.create(
        user=request.user,
        name=description[:60],
        description=description,
        prompt_used=description,
        scenes=scenes,
        transitions=transitions,
        media_urls=user_urls,
    )

    return JsonResponse({'ok': True, 'template_id': template.pk, 'name': template.name})


@login_required
def preview(request, template_id):
    tpl = get_object_or_404(BackgroundTemplate, pk=template_id)
    if not tpl.is_public and tpl.user != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    section = request.GET.get('section', 'general')
    html = tpl.scenes.get(section, '<html><body style="background:#000"></body></html>')
    from django.http import HttpResponse
    return HttpResponse(html, content_type='text/html')


@login_required
@require_POST
def activate(request, template_id):
    tpl = get_object_or_404(BackgroundTemplate, pk=template_id)
    if not tpl.is_public and tpl.user != request.user:
        return JsonResponse({'ok': False}, status=403)
    profile = request.user.profile
    if profile.active_template_id != tpl.pk:
        tpl.use_count += 1
        tpl.save(update_fields=['use_count'])
    profile.active_template = tpl
    profile.save(update_fields=['active_template'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def deactivate(request):
    profile = request.user.profile
    profile.active_template = None
    profile.save(update_fields=['active_template'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def rate(request, template_id):
    tpl = get_object_or_404(BackgroundTemplate, pk=template_id, is_public=True)
    try:
        data = json.loads(request.body)
        score = int(data.get('score', 0))
    except Exception:
        return JsonResponse({'ok': False}, status=400)
    if not 1 <= score <= 5:
        return JsonResponse({'ok': False, 'error': 'score 1-5'}, status=400)
    TemplateRating.objects.update_or_create(
        template=tpl, user=request.user,
        defaults={'score': score},
    )
    return JsonResponse({'ok': True, 'avg': tpl.avg_rating})


@login_required
@require_POST
def publish(request, template_id):
    tpl = get_object_or_404(BackgroundTemplate, pk=template_id, user=request.user)
    tpl.is_public = True
    tpl.save(update_fields=['is_public'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def delete_template(request, template_id):
    tpl = get_object_or_404(BackgroundTemplate, pk=template_id, user=request.user)
    if request.user.profile.active_template_id == tpl.pk:
        request.user.profile.active_template = None
        request.user.profile.save(update_fields=['active_template'])
    tpl.delete()
    return JsonResponse({'ok': True})


@login_required
def pexels_search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    urls = _pexels_search(query, per_page=9)
    return JsonResponse({'results': urls})
