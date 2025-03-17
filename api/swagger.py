from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="FileNest API",
        default_version="v1",
        description=(
            "FileNest is a cloud-based file storage system that allows users to upload, "
            "manage, and retrieve files efficiently. This API provides authentication, "
            "file management, and metadata retrieval services."
        ),
        contact=openapi.Contact(email="support@filenest.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)