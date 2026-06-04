from django.urls import path
from tokens import views

app_name = "tokens"

urlpatterns = [
    path("",                    views.tienda,           name="tienda"),
    path("fractones/",          views.balance,          name="balance"),
    path("comprar/",            views.crear_compra,     name="crear_compra"),
    path("mp-webhook/",         views.mp_webhook,       name="mp_webhook"),
    path("exito/",              views.mp_success,       name="mp_success"),
    path("fallo/",              views.mp_failure,       name="mp_failure"),
    path("pendiente/",          views.mp_pending,       name="mp_pending"),
]
