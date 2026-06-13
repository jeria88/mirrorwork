import json
import re

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import BlogSubmission, GeneratedArticle, SocialPost


def _check_token(request):
    expected = getattr(settings, 'BLOG_SUBMIT_TOKEN', '')
    if not expected:
        return False
    auth = request.headers.get('Authorization', '')
    return auth == f'Bearer {expected}'


def _is_internal_or_staff(request):
    remote = request.META.get('REMOTE_ADDR')
    if remote in ('127.0.0.1', '::1', 'localhost'):
        return True
    return request.user.is_authenticated and request.user.is_staff


@csrf_exempt
@require_POST
def submit_api(request):
    """
    Recibe postulaciones desde mirrorwork.
    Authorization: Bearer <BLOG_SUBMIT_TOKEN>
    Body JSON: { title, body, author_email, author_name, source_type, source_description }
    """
    if not _check_token(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title        = data.get('title', '').strip()
    body         = data.get('body', '').strip()
    author_email = data.get('author_email', '').strip()

    if not title or not body or not author_email:
        return JsonResponse({'error': 'title, body y author_email son obligatorios'}, status=400)

    source_type = data.get('source_type', BlogSubmission.SOURCE_FREE)
    valid_types = [t for t, _ in BlogSubmission.SOURCE_CHOICES]
    if source_type not in valid_types:
        source_type = BlogSubmission.SOURCE_FREE

    sub = BlogSubmission.objects.create(
        author_email       = author_email,
        author_name        = data.get('author_name', '').strip(),
        title              = title[:200],
        body               = body,
        source_type        = source_type,
        source_description = data.get('source_description', '').strip(),
        status             = BlogSubmission.STATUS_SUBMITTED,
    )
    return JsonResponse({'ok': True, 'id': sub.pk}, status=201)


@csrf_exempt
def carruseles_api(request):
    if not _is_internal_or_staff(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'GET':
        carruseles = []
        from django.utils.text import slugify

        # 1. GeneratedArticle
        for art in GeneratedArticle.objects.all():
            slides_data_field = art.slides_data or {}
            slides_list = []
            if isinstance(slides_data_field, dict):
                slides_list = slides_data_field.get('slides', [])
            elif isinstance(slides_data_field, list):
                slides_list = slides_data_field

            if slides_list:
                slides_formatted = []
                for i, sl in enumerate(slides_list):
                    slides_formatted.append({
                        "type": "hook" if i == 0 else ("cta" if i == len(slides_list)-1 else "content"),
                        "headline": sl.get('title') or sl.get('text') or sl.get('body') or "",
                        "body": sl.get('body', "") if sl.get('title') else "",
                        "eyebrow": sl.get('tag', '')
                    })
                carruseles.append({
                    "id": f"GA_{art.pk}",
                    "title": art.title,
                    "file": slugify(art.title),
                    "phase": "Artículo",
                    "caption": art.intro or art.meta_description or "",
                    "slides": slides_formatted
                })

        # 2. SocialPost (carruseles)
        for post in SocialPost.objects.filter(formato=SocialPost.FORMATO_CARRUSEL):
            title = post.generated_article.title if post.generated_article else (post.blog_post.title if post.blog_post else f"Post RRSS {post.pk}")
            slides_text = []
            if post.carrusel_cuerpo:
                parts = re.split(r'\s*---\s*', post.carrusel_cuerpo)
                slides_text = [p.strip() for p in parts if p.strip()]

            slides_formatted = []
            hook_text = post.carrusel_gancho or (slides_text[0] if slides_text else title)
            slides_formatted.append({
                "type": "hook",
                "headline": hook_text,
                "body": "",
                "eyebrow": "Espejo",
                "ctaText": post.carrusel_cta or "→ Desliza para entender"
            })
            for i, t in enumerate(slides_text):
                if i == 0 and t == hook_text:
                    continue
                slides_formatted.append({
                    "type": "content",
                    "headline": t,
                    "body": ""
                })
            if post.carrusel_cta and len(slides_formatted) > 1:
                slides_formatted[-1]["ctaText"] = post.carrusel_cta
                slides_formatted[-1]["eyebrow"] = "Llamado a la acción"

            carruseles.append({
                "id": f"SP_{post.pk}",
                "title": title,
                "file": slugify(title),
                "phase": post.plataforma,
                "caption": post.carrusel_descripcion or "",
                "slides": slides_formatted
            })

        return JsonResponse(carruseles, safe=False)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        mappings = {}
        for item in data:
            item_id = item.get('id', '')
            title = item.get('title', '')
            caption = item.get('caption', '')
            slides = item.get('slides', [])

            if item_id.startswith('GA_'):
                pk = item_id.split('_')[1]
                art = GeneratedArticle.objects.filter(pk=pk).first()
                if art:
                    art.title = title
                    art.intro = caption
                    slides_data_list = []
                    for sl in slides:
                        slides_data_list.append({
                            "title": sl.get('headline', ''),
                            "body": sl.get('body', ''),
                            "tag": sl.get('eyebrow', '')
                        })
                    art.slides_data = {"slides": slides_data_list}
                    art.save()

            elif item_id.startswith('SP_'):
                pk = item_id.split('_')[1]
                post = SocialPost.objects.filter(pk=pk).first()
                if post:
                    post.carrusel_descripcion = caption
                    if slides:
                        post.carrusel_gancho = slides[0].get('headline', '')
                        body_slides = []
                        for sl in slides[1:]:
                            body_slides.append(sl.get('headline', ''))
                        post.carrusel_cuerpo = '\n\n---\n\n'.join(body_slides)
                        post.carrusel_cta = slides[-1].get('ctaText', '') or slides[-1].get('headline', '')
                    post.save()
            else:
                # Nuevo carrusel en editor (C10, etc.)
                post = SocialPost.objects.create(
                    formato=SocialPost.FORMATO_CARRUSEL,
                    carrusel_descripcion=caption,
                )
                if slides:
                    post.carrusel_gancho = slides[0].get('headline', '')
                    body_slides = []
                    for sl in slides[1:]:
                        body_slides.append(sl.get('headline', ''))
                    post.carrusel_cuerpo = '\n\n---\n\n'.join(body_slides)
                    post.carrusel_cta = slides[-1].get('ctaText', '') or slides[-1].get('headline', '')
                post.save()
                mappings[item_id] = f"SP_{post.pk}"

        return JsonResponse({'ok': True, 'mappings': mappings})


@csrf_exempt
def reels_api(request):
    if not _is_internal_or_staff(request):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if request.method == 'GET':
        reels = []

        # SocialPost (reels)
        for post in SocialPost.objects.filter(formato=SocialPost.FORMATO_REEL):
            title = post.generated_article.title if post.generated_article else (post.blog_post.title if post.blog_post else f"Post RRSS {post.pk}")
            gancho = post.reel_gancho or title
            cuerpo = post.reel_cuerpo or ""
            cta = post.reel_cta or "Descubre más en endonautas.cl"

            paragraphs = [p.strip() for p in re.split(r'\n+|\.\s+', cuerpo) if p.strip()]
            if not paragraphs:
                paragraphs = ["Continúa tu viaje interior."]

            scenes = []
            current_time = 0

            # Hook scene
            scenes.append({
                "from": current_time,
                "duration": 4,
                "padding": "100px 0",
                "elements": [
                    { "type": "logo", "delay": 10 },
                    { "type": "text", "text": gancho, "delay": 15, "font": "playfair", "size": 60, "weight": 700, "color": "gold" }
                ]
            })
            current_time += 4

            # Content scenes
            for para in paragraphs:
                scenes.append({
                    "from": current_time,
                    "duration": 5,
                    "padding": "80px 0",
                    "elements": [
                        { "type": "text", "text": para, "delay": 10, "font": "inter", "size": 32 }
                    ]
                })
                current_time += 5

            # CTA scene
            scenes.append({
                "from": current_time,
                "duration": 5,
                "padding": "100px 0",
                "elements": [
                    { "type": "text", "text": cta, "delay": 15, "font": "inter", "size": 30, "color": "gold", "border": True },
                    { "type": "logo", "delay": 90 }
                ]
            })
            current_time += 5

            reels.append({
                "id": f"SP_{post.pk}",
                "title": title,
                "duration": current_time,
                "scenes": scenes
            })

        return JsonResponse(reels, safe=False)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        mappings = {}
        for item in data:
            item_id = item.get('id', '')
            title = item.get('title', '')
            scenes = item.get('scenes', [])

            if item_id.startswith('SP_'):
                pk = item_id.split('_')[1]
                post = SocialPost.objects.filter(pk=pk).first()
                if post:
                    if len(scenes) >= 2:
                        hook_el = next((el for el in scenes[0].get('elements', []) if el.get('type') == 'text'), None)
                        post.reel_gancho = hook_el.get('text', '') if hook_el else title
                        
                        body_texts = []
                        for sc in scenes[1:-1]:
                            text_el = next((el for el in sc.get('elements', []) if el.get('type') == 'text'), None)
                            if text_el:
                                body_texts.append(text_el.get('text', ''))
                        post.reel_cuerpo = '\n\n'.join(body_texts)
                        
                        cta_el = next((el for el in scenes[-1].get('elements', []) if el.get('type') == 'text'), None)
                        post.reel_cta = cta_el.get('text', '') if cta_el else ''
                    post.save()
            else:
                # Nuevo reel
                post = SocialPost.objects.create(
                    formato=SocialPost.FORMATO_REEL,
                )
                if len(scenes) >= 2:
                    hook_el = next((el for el in scenes[0].get('elements', []) if el.get('type') == 'text'), None)
                    post.reel_gancho = hook_el.get('text', '') if hook_el else title
                    body_texts = []
                    for sc in scenes[1:-1]:
                        text_el = next((el for el in sc.get('elements', []) if el.get('type') == 'text'), None)
                        if text_el:
                            body_texts.append(text_el.get('text', ''))
                    post.reel_cuerpo = '\n\n'.join(body_texts)
                    cta_el = next((el for el in scenes[-1].get('elements', []) if el.get('type') == 'text'), None)
                    post.reel_cta = cta_el.get('text', '') if cta_el else ''
                post.save()
                mappings[item_id] = f"SP_{post.pk}"

        return JsonResponse({'ok': True, 'mappings': mappings})
