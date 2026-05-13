from django.db import models
from django.conf import settings
import uuid


class TemporaryProfile(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_profiles'
    )
    alias = models.CharField(max_length=80)
    notes = models.TextField(blank=True)
    token_allocation = models.IntegerField(default=150)
    tokens_used = models.IntegerField(default=0)
    access_code = models.UUIDField(default=uuid.uuid4, unique=True)
    claimed_by = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='claimed_profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.alias} (de {self.created_by.email})'

    @property
    def tokens_remaining(self):
        return max(0, self.token_allocation - self.tokens_used)

    def spend_tokens(self, amount):
        if self.tokens_remaining < amount:
            return False
        self.tokens_used += amount
        self.save()
        return True
