"""URL configuration for the API app."""
from django.urls import path

from . import views

# URL patterns organized by functionality
urlpatterns = [
    # Authentication endpoints
    path("hello/", views.hello, name="hello"),
    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("test_token/", views.test_token, name="test_token"),

    # File operation endpoints
    path("upload/", views.upload_file, name="upload_file"),
    path("detail/<str:file_id>/", views.detail_file, name="detail_file"),
    path("delete/<str:file_id>/", views.delete_file, name="delete_file"),
    path("storage/", views.list_files, name="list_files"),
    path("download/<str:file_id>/", views.download_file, name="download_file"),
]
