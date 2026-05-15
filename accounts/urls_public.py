from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bienvenido/', views.bienvenido, name='bienvenido'),
    path('onboarding/mapa/', views.onboarding_mapa, name='onboarding_mapa'),
    path('onboarding/tests/', views.onboarding_tests, name='onboarding_tests'),
    path('onboarding/viaje/', views.onboarding_viaje, name='onboarding_viaje'),
    path('onboarding/viaje/guardar/', views.onboarding_viaje_guardar, name='onboarding_viaje_guardar'),
    path('onboarding/viaje/nacimiento/', views.onboarding_viaje_nacimiento, name='onboarding_viaje_nacimiento'),
    path('mapa/', views.mapa_interior, name='mapa_interior'),
    path('perfil/', views.perfil, name='perfil'),
    path('debug/perfil/', views.perfil_debug, name='perfil_debug'),
]
