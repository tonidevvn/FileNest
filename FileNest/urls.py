"""
URL configuration for FileNest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from upload.views import *
from api.views import *
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from api.views import *

urlpatterns = ([
    path('', image_upload, name='upload'),
    path('storage', load_storage, name='storage'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('admin/', admin.site.urls),
    path('delete/<str:file_key>/', delete_file, name='delete_file'),
    path('api/signup', signup),
    path('api/login', login),
    path('api/test_token', test_token),
    path('api/upload/', api_upload_file, name='api_upload_file'),
    path('api/delete/<str:file_key>/', api_delete_file, name='api_delete_file'),
    path('api/storage/', api_list_files, name='api_list_files'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
