"""Views for web interface."""
from .auth import user_login, user_signup, user_logout
from .files import file_upload, file_detail, delete_file, load_storage
from .admin import admin_dashboard

__all__ = [
    'user_login',
    'user_signup',
    'user_logout',
    'file_upload',
    'file_detail',
    'delete_file',
    'load_storage',
    'admin_dashboard',
]
