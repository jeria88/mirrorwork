from django.urls import path
from reports import views

app_name = "reports"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("generar/", views.generar_bitacora, name="generar_bitacora"),
    path("comprar/", views.mock_checkout, name="mock_checkout"),
    path("webhook/", views.webhook_receiver, name="webhook_receiver"),
    path("bitacora/", views.bitacora_view, name="bitacora_view"),
]
