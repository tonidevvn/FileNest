"""Authentication related views."""
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from api.serializers import UserSerializer
from .base import DEFAULT_AUTHENTICATION_CLASSES, DEFAULT_PERMISSION_CLASSES

@api_view(["POST"])
def signup(request):
    """Register a new user and return their token."""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=request.data["username"])
        user.set_password(request.data["password"])
        user.save()
        token = Token.objects.create(user=user)
        return Response({"token": token.key, "user": serializer.data})
    return Response(serializer.errors, status=status.HTTP_200_OK)

@api_view(["POST"])
def login(request):
    """Log in a user and return their token."""
    user = get_object_or_404(User, username=request.data["username"])
    if not user.check_password(request.data["password"]):
        return Response("missing user", status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    return Response({"token": token.key, "user": serializer.data})

@api_view(["GET"])
@authentication_classes(DEFAULT_AUTHENTICATION_CLASSES)
@permission_classes(DEFAULT_PERMISSION_CLASSES)
def test_token(request):
    """Verify if a token is valid."""
    serializer = UserSerializer(request.user)
    return Response(
        {"message": "Token is valid", "user": serializer.data},
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
def hello(request):
    """Test endpoint to verify API is working."""
    name = request.GET.get("name", "guest")
    data = {
        "name": name,
        "message": f"Hello {name}, your first API endpoint has been created successfully!",
    }
    return Response(data, status=status.HTTP_200_OK)
