"""URL configuration for FileNest project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin and API URLs
    path("admin/", admin.site.urls),
    # Main app URLs
    path("", include("web.urls", namespace="web")),
    # Monitoring URLs
    path("monitoring/", include("monitoring.urls", namespace="monitoring")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
