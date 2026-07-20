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
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "password", "role", "tenant_id"]

    def create(self, validated_data):
        tenant_id = validated_data.pop("tenant_id", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        if tenant_id:
            user.tenant_id = tenant_id
        user.set_password(password)
        user.save()
        return user
