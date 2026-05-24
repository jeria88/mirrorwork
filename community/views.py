import json
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import Comment, Follow, Reaction, SharedInsight

User = get_user_model()


def _get_facilitador(user):
    try:
        return user.claimed_profile.created_by
    except Exception:
        return None


# ── Feed ──────────────────────────────────────────────────────────────────────

@login_required
def feed(request):
    following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    facilitador = _get_facilitador(request.user)

    author_ids = set(following_ids)
    if facilitador:
        author_ids.add(facilitador.pk)

    insights = (
        SharedInsight.objects
        .filter(user_id__in=author_ids, visibility=SharedInsight.VISIBILITY_PUBLIC)
        .select_related('user', 'test_result__test', 'espejo_session')
        .prefetch_related('reactions', 'comments')
        [:40]
    )

    return render(request, 'community/feed.html', {
        'insights': insights,
        'facilitador': facilitador,
        'tab': 'feed',
        'reactions_choices': Reaction._meta.get_field('type').choices,
    })


@login_required
def explorar(request):
    insights = (
        SharedInsight.objects
        .filter(
            visibility=SharedInsight.VISIBILITY_PUBLIC,
            user__profile__profile_public=True,
        )
        .exclude(user=request.user)
        .select_related('user', 'test_result__test', 'espejo_session')
        .prefetch_related('reactions', 'comments')
        [:40]
    )

    return render(request, 'community/feed.html', {
        'insights': insights,
        'tab': 'explorar',
        'reactions_choices': Reaction._meta.get_field('type').choices,
    })


# ── Mensajes directos ─────────────────────────────────────────────────────────

@login_required
def mensajes(request):
    recibidos = (
        SharedInsight.objects
        .filter(recipient=request.user, visibility=SharedInsight.VISIBILITY_DIRECT)
        .select_related('user', 'test_result__test', 'espejo_session')
        [:40]
    )
    enviados = (
        SharedInsight.objects
        .filter(user=request.user, visibility=SharedInsight.VISIBILITY_DIRECT)
        .select_related('recipient', 'test_result__test', 'espejo_session')
        [:40]
    )
    return render(request, 'community/mensajes.html', {
        'recibidos': recibidos,
        'enviados': enviados,
    })


# ── Perfil ────────────────────────────────────────────────────────────────────

@login_required
def perfil_propio(request):
    insights = (
        SharedInsight.objects
        .filter(user=request.user, visibility=SharedInsight.VISIBILITY_PUBLIC)
        .select_related('test_result__test', 'espejo_session')
        .prefetch_related('reactions', 'comments')
    )
    followers_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()

    return render(request, 'community/perfil.html', {
        'perfil_user': request.user,
        'insights': insights,
        'followers_count': followers_count,
        'following_count': following_count,
        'es_propio': True,
    })


@login_required
def perfil(request, username):
    perfil_user = get_object_or_404(User, username=username)

    if perfil_user == request.user:
        return perfil_propio(request)

    is_following = Follow.objects.filter(follower=request.user, following=perfil_user).exists()
    is_public = getattr(getattr(perfil_user, 'profile', None), 'profile_public', False)

    if not is_public and not is_following:
        return render(request, 'community/perfil_privado.html', {'perfil_user': perfil_user})

    insights = (
        SharedInsight.objects
        .filter(user=perfil_user, visibility=SharedInsight.VISIBILITY_PUBLIC)
        .select_related('test_result__test', 'espejo_session')
        .prefetch_related('reactions', 'comments')
    )
    followers_count = Follow.objects.filter(following=perfil_user).count()
    following_count = Follow.objects.filter(follower=perfil_user).count()

    return render(request, 'community/perfil.html', {
        'perfil_user': perfil_user,
        'insights': insights,
        'followers_count': followers_count,
        'following_count': following_count,
        'es_propio': False,
        'is_following': is_following,
    })


# ── AJAX: compartir ───────────────────────────────────────────────────────────

@login_required
@require_POST
def compartir(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    source_type  = data.get('source_type')
    source_id    = data.get('source_id')
    reflection   = (data.get('reflection_text') or '').strip()
    visibility   = data.get('visibility', SharedInsight.VISIBILITY_PUBLIC)
    recipient_id = data.get('recipient_id')

    if source_type not in (SharedInsight.SOURCE_TEST, SharedInsight.SOURCE_ESPEJO):
        return JsonResponse({'error': 'source_type inválido'}, status=400)

    kwargs = {
        'user': request.user,
        'source_type': source_type,
        'reflection_text': reflection,
        'visibility': visibility,
    }

    if source_type == SharedInsight.SOURCE_TEST:
        from psychometrics.models import TestResult
        tr = get_object_or_404(TestResult, pk=source_id, user=request.user)
        kwargs['test_result'] = tr
    else:
        from mirror.models import ConflictSession
        cs = get_object_or_404(ConflictSession, pk=source_id, user=request.user)
        kwargs['espejo_session'] = cs

    if visibility == SharedInsight.VISIBILITY_DIRECT:
        if not recipient_id:
            return JsonResponse({'error': 'Falta destinatario'}, status=400)
        recipient = get_object_or_404(User, pk=recipient_id)
        kwargs['recipient'] = recipient

    insight = SharedInsight.objects.create(**kwargs)
    return JsonResponse({'ok': True, 'insight_id': insight.pk})


@login_required
@require_POST
def eliminar_insight(request, pk):
    insight = get_object_or_404(SharedInsight, pk=pk, user=request.user)
    insight.delete()
    return JsonResponse({'ok': True})


# ── AJAX: reaccionar ──────────────────────────────────────────────────────────

@login_required
@require_POST
def reaccionar(request, pk):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    tipo = data.get('type')
    valid_types = [r[0] for r in Reaction._meta.get_field('type').choices]
    if tipo not in valid_types:
        return JsonResponse({'error': 'Tipo inválido'}, status=400)

    insight = get_object_or_404(SharedInsight, pk=pk, visibility=SharedInsight.VISIBILITY_PUBLIC)

    existing = Reaction.objects.filter(insight=insight, user=request.user).first()
    if existing:
        if existing.type == tipo:
            existing.delete()
            action = 'removed'
        else:
            existing.type = tipo
            existing.save(update_fields=['type'])
            action = 'changed'
    else:
        Reaction.objects.create(insight=insight, user=request.user, type=tipo)
        action = 'added'

    counts = {}
    for r in Reaction.objects.filter(insight=insight):
        counts[r.type] = counts.get(r.type, 0) + 1

    return JsonResponse({'ok': True, 'action': action, 'counts': counts})


# ── AJAX: comentar ────────────────────────────────────────────────────────────

@login_required
@require_POST
def comentar(request, pk):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    text = (data.get('text') or '').strip()
    if not text:
        return JsonResponse({'error': 'Comentario vacío'}, status=400)

    insight = get_object_or_404(SharedInsight, pk=pk, visibility=SharedInsight.VISIBILITY_PUBLIC)
    comment = Comment.objects.create(insight=insight, user=request.user, text=text)

    return JsonResponse({
        'ok': True,
        'comment': {
            'id': comment.pk,
            'user': comment.user.username or comment.user.email.split('@')[0],
            'text': comment.text,
            'created_at': comment.created_at.strftime('%d %b'),
        }
    })


# ── AJAX: seguir / dejar de seguir ───────────────────────────────────────────

@login_required
@require_POST
def seguir(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'error': 'No puedes seguirte a ti mismo'}, status=400)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow.delete()
        action = 'unfollowed'
    else:
        action = 'followed'

    count = Follow.objects.filter(following=target).count()
    return JsonResponse({'ok': True, 'action': action, 'followers': count})


# ── AJAX: datos para poblar el modal de compartir ────────────────────────────

@login_required
def compartir_info(request):
    facilitador = _get_facilitador(request.user)
    fac_data = None
    if facilitador:
        fac_data = {
            'id': facilitador.pk,
            'name': (facilitador.get_full_name() or
                     facilitador.username or
                     facilitador.email.split('@')[0]),
        }

    following = (
        Follow.objects
        .filter(follower=request.user)
        .select_related('following')
        [:20]
    )
    following_list = [
        {
            'id': f.following.pk,
            'name': f.following.username or f.following.email.split('@')[0],
        }
        for f in following
    ]

    return JsonResponse({'facilitador': fac_data, 'following': following_list})
