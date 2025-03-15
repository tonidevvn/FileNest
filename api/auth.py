"""API-specific authentication logic."""
from rest_framework.authentication import TokenAuthentication

class CustomTokenAuthentication(TokenAuthentication):
    """Custom token authentication for API."""
    keyword = 'Token'  # Use 'Token' as the keyword (default)
