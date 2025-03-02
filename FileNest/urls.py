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
from api.views import *

urlpatterns = ([
    path('', image_upload, name='upload'),
    path('storage', load_storage, name='storage'),
    path('storage/chunks/<uuid:file_key>/', view_chunks, name='view_chunks'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('delete/<str:file_key>/', delete_file, name='delete_file'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
