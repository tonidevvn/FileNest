from django.urls import path
from .views import FileUploadView, FileDownloadView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name="file-upload"),
    path('download/<str:file_hash>/', FileDownloadView.as_view(), name="file-download"),
]
