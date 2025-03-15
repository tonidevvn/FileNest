"""Authentication views for web interface."""

from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from core.auth import AuthService


def user_login(request):
    """Handle user login."""
    if request.method == "POST":
        try:
            user = AuthService.validate_login(
                username=request.POST.get("username"),
                password=request.POST.get("password"),
            )
            login(request, user)
            return redirect("web:home")
        except ValueError as e:
            return render(request, "login.html", {"error": str(e)})

    return render(request, "login.html")


def user_signup(request):
    """Handle user registration."""
    if request.method == "POST":
        try:
            # Validate passwords match
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            AuthService.validate_passwords(password1, password2)

            # Create user
            user, _ = AuthService.create_user(
                username=request.POST.get("username"),
                email=request.POST.get("email"),
                password=password1,
            )
            login(request, user)
            return redirect("web:home")
        except ValueError as e:
            return render(request, "signup.html", {"error": str(e)})

    return render(request, "signup.html")


def user_logout(request):
    """Log out the current user."""
    logout(request)
    return redirect("web:login")
