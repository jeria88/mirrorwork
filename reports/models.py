from django.db import models
from django.conf import settings

class SoulReport(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_GENERATING = 'generating'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente de pago'),
        (STATUS_GENERATING, 'Generando'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_FAILED, 'Error'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='soul_reports')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_paid = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='soul_reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Store aggregated insights and structured content
    report_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Bitácora de Sombras - {self.user.email} ({self.get_status_display()})"
