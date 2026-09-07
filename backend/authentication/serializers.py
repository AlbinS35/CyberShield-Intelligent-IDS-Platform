"""
Authentication Serializers
JWT login, user profile, and tenant serializers.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth import get_user_model
from .models import User, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "industry", "is_active"]


class UserProfileSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "tenant", "date_joined", "is_active",
        ]
        read_only_fields = ["id", "date_joined", "role", "tenant"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class CyberShieldTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that embeds user role and tenant info
    directly into the access token claims for frontend routing.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Embed role and tenant into JWT payload
        token["role"] = user.role
        token["tenant_id"] = str(user.tenant_id) if user.tenant_id else None
        token["tenant_name"] = user.tenant.name if user.tenant else None
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Include user profile in login response
        data["user"] = UserProfileSerializer(self.user).data
        return data


class CyberShieldTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom JWT refresh serializer that gracefully handles cases where
    the user referenced by the refresh token no longer exists in the database
    (e.g., deleted user or database reset), returning InvalidToken instead of a 500 error.
    """

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except get_user_model().DoesNotExist:
            raise InvalidToken("User matching token payload does not exist or has been deleted.")


class UserRegistrationSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_no  = serializers.CharField(write_only=True, required=False, allow_blank=True)
    org_id    = serializers.CharField(write_only=True, required=False, allow_blank=True)
    org_name  = serializers.CharField(write_only=True, required=False, allow_blank=True)
    industry  = serializers.CharField(write_only=True, required=False, allow_blank=True)
    clearance_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_no", "password", "role", "org_id", "org_name", "industry", "clearance_code"]

    def validate(self, attrs):
        role = attrs.get("role", "ANALYST")
        clearance_code = attrs.get("clearance_code", "")
        org_name = attrs.get("org_name", "").strip()

        if not role:
            attrs["role"] = "ANALYST"
            role = "ANALYST"

        from decouple import config
        admin_clearance = config("CYBERSHIELD_ADMIN_CLEARANCE", default="SECURE_CYBER_SHIELD_2026")

        # Check privileged roles
        if role in ["SYS_ADMIN", "SUPER_ADMIN"]:
            if clearance_code != admin_clearance:
                raise serializers.ValidationError({"clearance_code": "Invalid security clearance code for privileged role."})
        elif role == "ORG_MANAGER":
            # If registering a brand new organization with org_name, no clearance code is required
            # If attempting to join an existing organization as ORG_MANAGER, clearance code is required
            if not org_name and clearance_code != admin_clearance:
                raise serializers.ValidationError({"clearance_code": "Invalid security clearance code for privileged role."})

        if org_name:
            from .models import Tenant
            if Tenant.objects.filter(name__iexact=org_name).exists():
                raise serializers.ValidationError({"org_name": f"An organization named '{org_name}' already exists."})

        return attrs

    def create(self, validated_data):
        from django.utils.text import slugify
        from .models import Tenant
        import uuid

        # Split full_name into first/last
        full_name = validated_data.pop("full_name", "")
        parts = full_name.strip().split(" ", 1)
        validated_data["first_name"] = parts[0]
        validated_data["last_name"]  = parts[1] if len(parts) > 1 else ""

        # Extract extra fields
        phone_no = validated_data.pop("phone_no", None)
        clearance_code = validated_data.pop("clearance_code", None)
        org_name = validated_data.pop("org_name", "").strip()
        industry = validated_data.pop("industry", "").strip()
        org_id = validated_data.pop("org_id", None)
        password = validated_data.pop("password")

        user = User(**validated_data)

        # 1. Registering a brand new organization
        if org_name:
            base_slug = slugify(org_name)[:80] or f"org-{uuid.uuid4().hex[:8]}"
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            tenant = Tenant.objects.create(
                name=org_name,
                slug=slug,
                industry=industry,
                contact_email=user.email,
            )
            user.tenant = tenant
        # 2. Joining an existing org via org_id
        elif org_id:
            try:
                tenant = Tenant.objects.get(pk=uuid.UUID(str(org_id)))
                user.tenant = tenant
            except Exception:
                pass
        # 3. Fallback to first existing tenant if available
        elif not user.tenant:
            first_tenant = Tenant.objects.first()
            if first_tenant:
                user.tenant = first_tenant

        if phone_no and hasattr(user, "phone_no"):
            user.phone_no = phone_no

        user.set_password(password)
        user.save()
        return user
