from django.urls import re_path
from . import views_studio

app_name = 'studio'

urlpatterns = [
    re_path(r'^(?P<path>.*)$', views_studio.studio_proxy, name='proxy'),
]
