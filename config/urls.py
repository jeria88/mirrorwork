from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tokens/', include('tokens.urls')),
    path('psicometria/', include('psychometrics.urls')),
    path('espejo/', include('mirror.urls')),
    path('practicantes/', include('practitioners.urls')),
    path('reportes/', include('reports.urls')),
    path('', include('accounts.urls_public')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
