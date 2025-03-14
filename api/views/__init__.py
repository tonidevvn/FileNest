"""Views package initialization."""
from .auth import hello, login, signup, test_token
from .files import (
    detail_file,
    download_file,
    list_files,
    upload_file,
    delete_file,
)

__all__ = [
    # Auth views
    'hello',
    'login',
    'signup',
    'test_token',
    # File views
    'detail_file',
    'download_file',
    'list_files',
    'upload_file',
    'delete_file',
]
