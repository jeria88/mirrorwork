from django.contrib import admin
from .models import BirthProfile, BirthReport


@admin.register(BirthProfile)
class BirthProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'birth_place', 'birth_time')
    search_fields = ('user__email', 'birth_place')


@admin.register(BirthReport)
class BirthReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_type', 'status', 'created_at')
    list_filter = ('report_type', 'status')
    search_fields = ('user__email',)
