"""Views for upload application."""
from .auth import user_login, user_logout, user_signup
from .files import file_upload, file_detail, load_storage, delete_file
from .admin import admin_dashboard

__all__ = [
    'user_login',
    'user_logout',
    'user_signup',
    'file_upload',
    'file_detail',
    'load_storage',
    'delete_file',
    'admin_dashboard',
]
