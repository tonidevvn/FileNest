"""URL configuration for upload app."""

from django.urls import path

from . import views

app_name = "web"

urlpatterns = [
    # File operations
    path("", views.file_upload, name="home"),
    path("upload/", views.file_upload, name="upload"),
    path("storage/", views.load_storage, name="storage"),
    path("detail/<str:file_id>/", views.file_detail, name="detail"),
    path("delete/<str:file_id>/", views.delete_file, name="delete_file"),
    # Authentication
    path("login/", views.user_login, name="login"),
    path("signup/", views.user_signup, name="signup"),
    path("logout/", views.user_logout, name="logout"),
    # Admin
    path("dashboard/", views.admin_dashboard, name="dashboard"),
]
