"""Base utilities and decorators for API views."""
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated

# Common authentication classes used across views
DEFAULT_AUTHENTICATION_CLASSES = [
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
]

# Common permission classes used across views
DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]
