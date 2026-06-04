from django.urls import path
from tokens import views

app_name = "tokens"

urlpatterns = [
    path("",                    views.tienda,           name="tienda"),
    path("fractones/",          views.balance,          name="balance"),

    # Mercado Pago
    path("comprar/mp/",         views.crear_compra_mp,  name="crear_compra_mp"),
    path("mp-webhook/",         views.mp_webhook,       name="mp_webhook"),
    path("exito/",              views.mp_success,       name="mp_success"),
    path("fallo/",              views.mp_failure,       name="mp_failure"),
    path("pendiente/",          views.mp_pending,       name="mp_pending"),

    # PayPal
    path("comprar/pp/",         views.crear_compra_pp,  name="crear_compra_pp"),
    path("pp-return/",          views.pp_return,        name="pp_return"),
    path("pp-cancel/",          views.pp_cancel,        name="pp_cancel"),
    path("pp-webhook/",         views.pp_webhook,       name="pp_webhook"),
]
