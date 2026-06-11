from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('contacto/', views.contacto_view, name='contacto'),
    path('subscribe/', views.brevo_subscribe, name='subscribe'),
]
