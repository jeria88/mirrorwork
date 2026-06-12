from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.images import urls as wagtailimages_urls

from centro.views_studio import studio_proxy

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('images/', include(wagtailimages_urls)),

    path('accounts/', include('accounts.urls')),
    path('tokens/', include('tokens.urls')),
    path('psicometria/', include('psychometrics.urls')),
    path('espejo/', include('mirror.urls')),
    path('practicantes/', include('practitioners.urls')),
    path('reportes/', include('reports.urls')),
    path('nacimiento/', include('birth.urls')),
    path('regulacion/', include('sensorial.urls')),
    path('comunidad/', include('community.urls')),

    # Editorial & Marketing
    path('centro/', include('centro.urls', namespace='centro')),
    path('centro/studio/', include('centro.urls_studio', namespace='studio')),
    
    # Root proxies for Content Studio assets and API (no duplicate namespaces)
    re_path(r'^api/(?P<path>.*)$', studio_proxy),
    re_path(r'^preview/(?P<path>.*)$', studio_proxy),
    re_path(r'^repo/(?P<path>.*)$', studio_proxy),
    re_path(r'^fondos-pexels/(?P<path>.*)$', studio_proxy),
    re_path(r'^brand-assets/(?P<path>.*)$', studio_proxy),

    path('crm/', include('crm.urls')),
    path('cgm/', include('blog.urls_cgm', namespace='cgm')),
    path('blog/api/', include('blog.urls')),
    path('search/', include('search.urls')),
    path('', include('home.urls')),

    # Público (landing sin prefijo)
    path('', include('accounts.urls_public')),

    # Wagtail pages — debe ir último (captura slug suelto)
    path('', include(wagtail_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
