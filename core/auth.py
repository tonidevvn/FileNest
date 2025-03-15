"""Authentication service layer."""
from typing import Tuple, Optional
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

class AuthService:
    """Service for handling authentication and user management."""
    
    @staticmethod
    def create_user(username: str, email: str, password: str) -> Tuple[User, Token]:
        """Create a new user and return user object with token."""
        # Validate user data
        if User.objects.filter(username=username).exists():
            raise ValueError("Username already taken")
        if User.objects.filter(email=email).exists():
            raise ValueError("Email is already registered")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create auth token
        token = Token.objects.create(user=user)
        
        return user, token

    @staticmethod
    def validate_login(username: str, password: str) -> Optional[User]:
        """Validate user credentials."""
        user = authenticate(username=username, password=password)
        if not user:
            raise ValueError("Invalid username or password")
        return user

    @staticmethod
    def get_or_create_token(user: User) -> Token:
        """Get existing token or create new one."""
        token, _ = Token.objects.get_or_create(user=user)
        return token

    @staticmethod
    def validate_passwords(password1: str, password2: str) -> bool:
        """Validate that passwords match."""
        if password1 != password2:
            raise ValueError("Passwords do not match")
        if len(password1) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return True

    @staticmethod
    def update_password(user: User, old_password: str, new_password: str) -> None:
        """Update user password with validation."""
        if not user.check_password(old_password):
            raise ValueError("Current password is incorrect")
        
        user.set_password(new_password)
        user.save()
