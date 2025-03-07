from django.urls import path
from .views import *

urlpatterns = [
    path('hello/', hello),
    path('signup/', signup),
    path('login/', login),
    path('test_token/', test_token),
    path('upload/', api_upload_file, name='api_upload_file'),
    path('detail/<str:file_id>/', api_detail_file, name='api_detail_file'),
    path('delete/<str:file_id>/', api_delete_file, name='api_delete_file'),
    path('storage/', api_list_files, name='api_list_files'),
]
