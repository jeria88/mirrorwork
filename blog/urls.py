from django.urls import path
from . import views

urlpatterns = [
    path('api/submit/', views.submit_api, name='blog_submit_api'),
    path('api/carruseles/', views.carruseles_api, name='carruseles_api'),
    path('api/reels/', views.reels_api, name='reels_api'),
]
