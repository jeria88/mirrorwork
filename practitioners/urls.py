from django.urls import path
from practitioners import views

app_name = "practitioners"

urlpatterns = [
    path("",                          views.perfil_lista,    name="lista"),
    path("nuevo/",                    views.perfil_crear,    name="crear"),
    path("<int:pk>/",                 views.perfil_detalle,  name="detalle"),
    path("<int:pk>/archivar/",        views.perfil_archivar, name="archivar"),
    path("<int:pk>/asignar/",         views.perfil_asignar_tests, name="asignar"),
    path("<int:pk>/resumen-clinico/", views.perfil_generar_resumen_clinico, name="resumen_clinico"),
    path("acceso/<uuid:access_code>/", views.perfil_acceso,  name="acceso"),
]
