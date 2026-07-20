"""
Authentication Views
JWT login, user profile, registration (admin only), tenant listing.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, Tenant
from .serializers import (
    CyberShieldTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    TenantSerializer,
)
from .permissions import IsSuperAdmin


class CyberShieldTokenObtainPairView(TokenObtainPairView):
    """Custom login view returning JWT pair + embedded user profile."""
    serializer_class = CyberShieldTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Log the login IP for the user
        if response.status_code == 200:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.user
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
                User.objects.filter(pk=user.pk).update(last_login_ip=ip)
        return response


class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET /api/auth/me/ — Retrieve or update current user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserRegistrationView(generics.CreateAPIView):
    """POST /api/auth/register/ — Admin-only user creation."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class TenantListView(generics.ListAPIView):
    """GET /api/auth/tenants/ — Public tenant list for login page selector."""
    serializer_class = TenantSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Tenant.objects.filter(is_active=True).order_by("name")
