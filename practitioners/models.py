from django.db import models
from django.conf import settings
import uuid


class TemporaryProfile(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_profiles'
    )
    alias = models.CharField(max_length=80)
    notes = models.TextField(blank=True)
    access_code = models.UUIDField(default=uuid.uuid4, unique=True)
    claimed_by = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='claimed_profile'
    )
    assigned_tests = models.ManyToManyField(
        'psychometrics.Test', blank=True, related_name='assigned_profiles'
    )
    clinical_summary = models.TextField(blank=True)
    clinical_summary_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.alias} (de {self.created_by.email})'

    @property
    def tests_completed_count(self):
        from psychometrics.models import TestResult
        if self.claimed_by:
            from django.db.models import Q
            return TestResult.objects.filter(
                Q(temp_profile=self) | Q(user=self.claimed_by)
            ).values('test').distinct().count()
        return self.test_results.values('test').distinct().count()

    @property
    def tests_assigned_count(self):
        return self.assigned_tests.count()
