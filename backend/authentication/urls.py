"""
Authentication URL Configuration
JWT login, refresh, logout, and user profile endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import (
    CyberShieldTokenObtainPairView,
    UserProfileView,
    UserRegistrationView,
    TenantListView,
)

urlpatterns = [
    # POST  /api/auth/login/         → obtain access + refresh JWT pair
    path("login/", CyberShieldTokenObtainPairView.as_view(), name="token_obtain_pair"),

    # POST  /api/auth/refresh/       → refresh access token using refresh token
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # POST  /api/auth/logout/        → blacklist refresh token
    path("logout/", TokenBlacklistView.as_view(), name="token_blacklist"),

    # GET   /api/auth/me/            → current user profile
    path("me/", UserProfileView.as_view(), name="user_profile"),

    # POST  /api/auth/register/      → register new user (admin only)
    path("register/", UserRegistrationView.as_view(), name="user_register"),

    # GET   /api/auth/tenants/       → list available tenants (for login selector)
    path("tenants/", TenantListView.as_view(), name="tenant_list"),
]
