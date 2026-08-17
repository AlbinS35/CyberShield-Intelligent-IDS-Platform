"""
Authentication Views
JWT login, user profile, registration (admin only), tenant listing.
"""

import requests
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Tenant
from .serializers import (
    CyberShieldTokenObtainPairSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    TenantSerializer,
)
from .permissions import IsSuperAdmin


from rest_framework.throttling import ScopedRateThrottle


class CyberShieldTokenObtainPairView(TokenObtainPairView):
    """Custom login view returning JWT pair + embedded user profile."""
    serializer_class = CyberShieldTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login_attempts"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # Log the login IP for the user and set cookies
        if response.status_code == 200:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")
            
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Strict",
                max_age=3600,
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite="Strict",
                max_age=7*24*3600,
            )

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
    """POST /api/auth/register/ — Public self-registration for new analysts."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

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


class GoogleLoginView(APIView):
    """
    POST /api/auth/google/
    Authenticate user using a Google OAuth2 access token.
    Validates token via Google userinfo endpoint.
    Creates account and tenant dynamically if they do not exist.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        access_token = request.data.get("credential")
        if not access_token:
            return Response(
                {"detail": "credential (Google access token) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate with Google
        try:
            resp = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if resp.status_code != 200:
                return Response(
                    {"detail": f"Failed to verify Google access token. Google returned: {resp.text}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_info = resp.json()
        except Exception as e:
            return Response(
                {"detail": f"Error validating token with Google: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        email = user_info.get("email")
        if not email:
            return Response(
                {"detail": "Email not returned by Google OAuth query."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        first_name = user_info.get("given_name", "Google")
        last_name = user_info.get("family_name", "User")

        # Find or create User
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Resolve or create a tenant dynamically based on email domain
            email_domain = email.split("@")[-1]
            if email_domain not in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com", "aol.com"):
                tenant_name = email_domain.split(".")[0].capitalize()
                tenant_slug = email_domain.split(".")[0]
                tenant, _ = Tenant.objects.get_or_create(
                    slug=tenant_slug,
                    defaults={"name": f"{tenant_name} Org", "industry": "Technology"}
                )
            else:
                tenant = Tenant.objects.first()
                if not tenant:
                    tenant = Tenant.objects.create(name="Default Org", slug="default")

            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=User.Role.ANALYST,
                tenant=tenant,
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["tenant_id"] = str(user.tenant_id) if user.tenant_id else None
        refresh["tenant_name"] = user.tenant.name if user.tenant else None
        refresh["full_name"] = user.get_full_name()

        response = Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite="Strict",
            max_age=3600,
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Strict",
            max_age=7*24*3600,
        )
        return response


from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads the refresh token from a cookie
    and writes the rotated tokens back into browser cookies.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token and "refresh" not in request.data:
            request.data["refresh"] = refresh_token

        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get("access")
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Strict",
                max_age=3600,
            )
            new_refresh = response.data.get("refresh")
            if new_refresh:
                response.set_cookie(
                    key="refresh_token",
                    value=new_refresh,
                    httponly=True,
                    secure=False,
                    samesite="Strict",
                    max_age=7*24*3600,
                )
        return response


class CookieTokenBlacklistView(TokenBlacklistView):
    """
    Custom token blacklist view that logs out the user
    by blacklisting the refresh token and deleting the JWT cookies.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token and "refresh" not in request.data:
            request.data["refresh"] = refresh_token

        response = super().post(request, *args, **kwargs)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

