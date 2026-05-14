from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bienvenido/', views.bienvenido, name='bienvenido'),
    path('onboarding/mapa/', views.onboarding_mapa, name='onboarding_mapa'),
    path('onboarding/tests/', views.onboarding_tests, name='onboarding_tests'),
    path('mapa/', views.mapa_interior, name='mapa_interior'),
    path('perfil/', views.perfil, name='perfil'),
]
