from django.urls import path, re_path
from . import views_studio

app_name = 'studio'

urlpatterns = [
    path('', views_studio.studio_proxy, {'path': ''}, name='proxy'),
    re_path(r'^(?P<path>.*)$', views_studio.studio_proxy, name='proxy'),
]
