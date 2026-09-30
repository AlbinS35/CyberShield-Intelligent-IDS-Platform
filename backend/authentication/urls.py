"""
Authentication URL Configuration
JWT login, refresh, logout, and user profile endpoints.
"""

from django.urls import path
from .views import (
    CyberShieldTokenObtainPairView,
    UserProfileView,
    UserRegistrationView,
    TenantListView,
    GoogleLoginView,
    CookieTokenRefreshView,
    CookieTokenBlacklistView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # POST  /api/auth/password-reset/
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),

    # POST  /api/auth/password-reset/confirm/
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    # POST  /api/auth/login/         → obtain access + refresh JWT pair
    path("login/", CyberShieldTokenObtainPairView.as_view(), name="token_obtain_pair"),

    # POST  /api/auth/refresh/       → refresh access token using refresh token
    path("refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),

    # POST  /api/auth/logout/        → blacklist refresh token
    path("logout/", CookieTokenBlacklistView.as_view(), name="token_blacklist"),

    # GET   /api/auth/me/            → current user profile
    path("me/", UserProfileView.as_view(), name="user_profile"),

    # POST  /api/auth/register/      → register new user (admin only)
    path("register/", UserRegistrationView.as_view(), name="user_register"),

    # GET   /api/auth/tenants/       → list available tenants (for login selector)
    path("tenants/", TenantListView.as_view(), name="tenant_list"),

    # POST  /api/auth/google/        → Google access token sign-in/up
    path("google/", GoogleLoginView.as_view(), name="google_login"),
]
