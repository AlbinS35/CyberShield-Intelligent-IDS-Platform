"""
Authentication Serializers
JWT login, user profile, and tenant serializers.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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


class UserRegistrationSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone_no  = serializers.CharField(write_only=True, required=False, allow_blank=True)
    org_id    = serializers.CharField(write_only=True, required=False, allow_blank=True)
    clearance_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_no", "password", "role", "org_id", "clearance_code"]

    def validate(self, attrs):
        role = attrs.get("role", "ANALYST")
        clearance_code = attrs.get("clearance_code", "")

        if not role:
            attrs["role"] = "ANALYST"
            role = "ANALYST"

        from decouple import config
        admin_clearance = config("CYBERSHIELD_ADMIN_CLEARANCE", default="SECURE_CYBER_SHIELD_2026")

        if role in ["SYS_ADMIN", "SUPER_ADMIN", "ORG_MANAGER"]:
            if clearance_code != admin_clearance:
                raise serializers.ValidationError({"clearance_code": "Invalid security clearance code for privileged role."})

        return attrs

    def create(self, validated_data):
        # Split full_name into first/last
        full_name = validated_data.pop("full_name", "")
        parts = full_name.strip().split(" ", 1)
        validated_data["first_name"] = parts[0]
        validated_data["last_name"]  = parts[1] if len(parts) > 1 else ""

        # Store phone if the model supports it
        phone_no = validated_data.pop("phone_no", None)
        clearance_code = validated_data.pop("clearance_code", None)

        # Resolve org_id → tenant FK (try UUID, fall back to first tenant)
        org_id = validated_data.pop("org_id", None)
        password = validated_data.pop("password")

        user = User(**validated_data)

        if org_id:
            from .models import Tenant
            try:
                import uuid
                tenant = Tenant.objects.get(pk=uuid.UUID(str(org_id)))
                user.tenant = tenant
            except Exception:
                pass

        if phone_no and hasattr(user, "phone_no"):
            user.phone_no = phone_no

        user.set_password(password)
        user.save()
        return user
