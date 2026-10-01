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
from .permissions import IsSuperAdmin, IsSysAdmin


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

            # Log the IP using the user id already returned in the response —
            # avoids a redundant second authentication call that caused a 500.
            user_data = response.data.get("user", {})
            user_id = user_data.get("id") if isinstance(user_data, dict) else None
            if user_id:
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                ip = x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
                User.objects.filter(pk=user_id).update(last_login_ip=ip)
        return response



class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET /api/auth/me/ — Retrieve or update current user profile."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/auth/register/ — Public self-registration for new users and organizations.

    Rate-limited to 10 registrations per IP per hour (ScopedRateThrottle: 'registration')
    to prevent automated tenant flooding and bulk account-generation attacks.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "registration"

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
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .serializers import CyberShieldTokenRefreshSerializer

class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads the refresh token from a cookie
    and writes the rotated tokens back into browser cookies.
    Cleans up stale cookies and returns HTTP 401 if user no longer exists or token is invalid.
    """
    serializer_class = CyberShieldTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token and "refresh" not in request.data:
            if hasattr(request.data, "_mutable") and not request.data._mutable:
                request.data._mutable = True
                request.data["refresh"] = refresh_token
                request.data._mutable = False
            elif isinstance(request.data, dict):
                request.data["refresh"] = refresh_token
            else:
                try:
                    request.data["refresh"] = refresh_token
                except Exception:
                    pass

        try:
            response = super().post(request, *args, **kwargs)
        except (InvalidToken, TokenError, get_user_model().DoesNotExist):
            response = Response(
                {"detail": "Token is invalid or user no longer exists.", "code": "token_not_valid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response

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
        else:
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

        return response


class CookieTokenBlacklistView(TokenBlacklistView):
    """
    Custom token blacklist view that logs out the user
    by blacklisting the refresh token and deleting the JWT cookies.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token and "refresh" not in request.data:
            if hasattr(request.data, "_mutable") and not request.data._mutable:
                request.data._mutable = True
                request.data["refresh"] = refresh_token
                request.data._mutable = False
            elif isinstance(request.data, dict):
                request.data["refresh"] = refresh_token
            else:
                try:
                    request.data["refresh"] = refresh_token
                except Exception:
                    pass

        try:
            response = super().post(request, *args, **kwargs)
        except Exception:
            response = Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response



from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer

class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/
    Accepts an email, generates a token, and sends a password reset link.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "If the email is registered, a reset link has been sent."}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = f"http://localhost:5173/reset-password/{uid}/{token}"
        
        send_mail(
            subject="CyberShield Password Reset Request",
            message=f"Hello {user.first_name},\n\nYou requested a password reset. Please click the link below to set a new password:\n\n{reset_url}\n\nIf you did not request this, please ignore this email.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@cybershield.demo"),
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"detail": "If the email is registered, a reset link has been sent."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset/confirm/
    Accepts uid, token, and new_password to reset the user's password.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)
