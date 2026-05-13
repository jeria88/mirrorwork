from django.urls import path
from . import views

app_name = 'birth'

urlpatterns = [
    path('', views.birth_profile, name='profile'),
    path('generar/astral/', views.astral_generate, name='astral_generate'),
    path('reporte/<int:pk>/', views.astral_detail, name='astral_detail'),
    path('reporte/<int:pk>/estado/', views.report_status, name='report_status'),
]
