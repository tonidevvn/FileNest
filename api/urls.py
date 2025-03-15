"""URLs configuration for the API."""
from django.urls import path
from . import views

app_name = "api"
urlpatterns = [
    # Authentication endpoints
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    
    # File operations endpoints
    path("upload/", views.upload_file, name="upload_file"),
    path("download/<str:file_id>/", views.download_file, name="download_file"),
    path("detail/<str:file_id>/", views.detail_file, name="detail_file"),
    path("delete/<str:file_id>/", views.delete_file, name="delete_file"),
    path("list/", views.list_files, name="list_files"),
]
