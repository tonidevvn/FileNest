"""URL configuration for FileNest project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

urlpatterns = [
    # Main app URLs
    path("", include("web.urls", namespace="web")),
    # Admin and API URLs
    path("admin/", admin.site.urls),
    # API endpoints...
    path("api/", include("api.urls", namespace="api")),
    # Monitoring URLs
    path("monitoring/", include("monitoring.urls", namespace="monitoring")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
