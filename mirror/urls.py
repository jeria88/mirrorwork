from django.urls import path
from mirror import views

app_name = "mirror"

urlpatterns = [
    path("",          views.espejo_home,    name="home"),
    path("nuevo/",    views.espejo_nuevo,   name="nuevo"),
    path("send/",     views.espejo_send,    name="send"),
    path("<int:pk>/archivar/", views.espejo_archivar, name="archivar"),
]
