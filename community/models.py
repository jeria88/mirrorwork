from django.db import models
from django.conf import settings


class Follow(models.Model):
    follower  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('follower', 'following')]

    def __str__(self):
        return f'{self.follower.email} → {self.following.email}'


class SharedInsight(models.Model):
    SOURCE_TEST    = 'test_result'
    SOURCE_ESPEJO  = 'espejo_exchange'
    SOURCE_NATIVE  = 'native'
    SOURCE_CHOICES = [
        (SOURCE_TEST, 'Resultado de test'),
        (SOURCE_ESPEJO, 'Sesión del Espejo'),
        (SOURCE_NATIVE, 'Publicación libre'),
    ]

    VISIBILITY_PUBLIC  = 'public'
    VISIBILITY_DIRECT  = 'direct'
    VISIBILITY_CHOICES = [(VISIBILITY_PUBLIC, 'Público'), (VISIBILITY_DIRECT, 'Mensaje directo')]

    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_insights')
    source_type     = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    # Contenido nativo (foto + texto libre)
    text            = models.TextField(blank=True, help_text="Texto de la publicación")
    image           = models.ImageField(upload_to='community/posts/%Y/%m/', blank=True)
    # Legacy (se mantiene por compatibilidad con posts existentes)
    reflection_text = models.TextField(blank=True)
    # Fuentes vinculadas (opcionales para native)
    test_result     = models.ForeignKey('psychometrics.TestResult', null=True, blank=True, on_delete=models.SET_NULL, related_name='shares')
    espejo_session  = models.ForeignKey('mirror.ConflictSession', null=True, blank=True, on_delete=models.SET_NULL, related_name='shares')
    visibility      = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC)
    recipient       = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_insights')
    repost_of       = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='reposts')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.source_type} ({self.visibility})'

    @property
    def source_title(self):
        if self.source_type == self.SOURCE_TEST and self.test_result:
            return self.test_result.test.name
        if self.source_type == self.SOURCE_ESPEJO and self.espejo_session:
            return self.espejo_session.title or 'Sesión del Espejo'
        if self.source_type == self.SOURCE_NATIVE:
            return self.text[:60] if self.text else 'Publicación'
        return '—'

    @property
    def display_text(self):
        """Texto a mostrar en el feed (unifica text y reflection_text)."""
        return self.text or self.reflection_text or ''


REACTION_CHOICES = [
    ('resonó',  'Resonó'),
    ('lo_vivo', 'Lo vivo también'),
    ('gracias',  'Gracias'),
]


class Reaction(models.Model):
    insight    = models.ForeignKey(SharedInsight, on_delete=models.CASCADE, related_name='reactions')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reactions')
    type       = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('insight', 'user')]

    def __str__(self):
        return f'{self.user.email} → {self.type}'


class Comment(models.Model):
    insight    = models.ForeignKey(SharedInsight, on_delete=models.CASCADE, related_name='comments')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.email} — comentario en {self.insight_id}'
