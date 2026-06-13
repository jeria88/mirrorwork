from django.urls import path
from reports import views

app_name = "reports"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("generar/", views.generar_bitacora, name="generar_bitacora"),
    path("bitacora/", views.bitacora_view, name="bitacora_view"),
]
