"""
CyberShield Core Serializers
============================
ModelSerializers for all 7 normalized tbl_ models plus a custom JWT
serializer that embeds role and org context from tbl_login.
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Organization,
    CoreUser,
    Login,
    NetworkAsset,
    ForensicCase,
    NetworkEvent,
    ContainmentAction,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Organization
# ─────────────────────────────────────────────────────────────────────────────

class OrganizationSerializer(serializers.ModelSerializer):
    user_count  = serializers.SerializerMethodField()
    asset_count = serializers.SerializerMethodField()

    class Meta:
        model  = Organization
        fields = [
            "org_id", "org_name", "domain_name",
            "status", "created_at",
            "user_count", "asset_count",
        ]
        read_only_fields = ["org_id", "created_at"]

    def get_user_count(self, obj):
        return obj.users.count()

    def get_asset_count(self, obj):
        return obj.assets.count()


# ─────────────────────────────────────────────────────────────────────────────
# 2. CoreUser
# ─────────────────────────────────────────────────────────────────────────────

class CoreUserSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source="org.org_name", read_only=True)

    class Meta:
        model  = CoreUser
        fields = [
            "user_id", "full_name", "phone_no",
            "org", "org_name", "created_at",
        ]
        read_only_fields = ["user_id", "created_at"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. Login
# ─────────────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.ModelSerializer):
    """Read serializer — password_hash is excluded from all output."""
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    org_name  = serializers.CharField(source="user.org.org_name", read_only=True)

    class Meta:
        model  = Login
        fields = [
            "login_id", "user", "user_name", "org_name",
            "email", "role", "status",
        ]
        read_only_fields = ["login_id"]
        extra_kwargs = {
            "password_hash": {"write_only": True},
        }


class LoginCreateSerializer(serializers.ModelSerializer):
    """Write serializer — accepts raw password and hashes it."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = Login
        fields = ["user", "email", "password", "role", "status"]

    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        login = Login(**validated_data)
        login.set_password(raw_password)
        login.save()
        return login

from authentication.models import User as AuthUser
class AuthUserLoginSerializer(serializers.ModelSerializer):
    login_id = serializers.UUIDField(source='id', read_only=True)
    user = serializers.UUIDField(source='id', read_only=True)
    user_name = serializers.SerializerMethodField()
    org_name = serializers.CharField(source='tenant.name', read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = AuthUser
        fields = ['login_id', 'user', 'user_name', 'org_name', 'email', 'role', 'status']
    
    def get_user_name(self, obj):
        return obj.get_full_name()
        
    def get_status(self, obj):
        return "ACTIVE" if obj.is_active else "INACTIVE"

class AuthUserCoreUserSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='id', read_only=True)
    full_name = serializers.SerializerMethodField()
    org_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = AuthUser
        fields = ['user_id', 'full_name', 'org_name']

    def get_full_name(self, obj):
        return obj.get_full_name()


# ─────────────────────────────────────────────────────────────────────────────
# 4. JWT Token — Login via tbl_login credentials
# ─────────────────────────────────────────────────────────────────────────────

class CoreLoginTokenSerializer(serializers.Serializer):
    """
    Custom JWT serializer authenticating against tbl_login.
    Returns access + refresh tokens enriched with role, user_id, and org context.
    Does NOT use Django's AUTH_USER_MODEL for auth — uses tbl_login directly.
    """
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email    = attrs["email"]
        password = attrs["password"]

        try:
            login_record = Login.objects.select_related("user__org").get(
                email=email,
                status=Login.Status.ACTIVE,
            )
        except Login.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "No active account found with this email address."}
            )

        if not login_record.check_password(password):
            raise serializers.ValidationError(
                {"password": "Invalid password."}
            )

        # Build JWT manually — we issue tokens for the CoreUser (not Django User)
        # We store login_id and user_id as claims inside the token payload.
        user     = login_record.user
        refresh  = RefreshToken()
        refresh["login_id"]   = login_record.login_id
        refresh["user_id"]    = str(user.user_id)
        refresh["email"]      = login_record.email
        refresh["role"]       = login_record.role
        refresh["full_name"]  = user.full_name
        refresh["org_id"]     = user.org.org_id
        refresh["org_name"]   = user.org.org_name

        return {
            "access":    str(refresh.access_token),
            "refresh":   str(refresh),
            "user_id":   str(user.user_id),
            "email":     login_record.email,
            "role":      login_record.role,
            "full_name": user.full_name,
            "org": {
                "org_id":   user.org.org_id,
                "org_name": user.org.org_name,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. NetworkAsset
# ─────────────────────────────────────────────────────────────────────────────

class NetworkAssetSerializer(serializers.ModelSerializer):
    org_name    = serializers.CharField(source="org.org_name", read_only=True)
    event_count = serializers.SerializerMethodField()

    class Meta:
        model  = NetworkAsset
        fields = [
            "asset_id", "org", "org_name",
            "asset_name", "ip_address", "os_type",
            "wazuh_agent_id", "status", "event_count",
        ]
        read_only_fields = ["asset_id"]

    def get_event_count(self, obj):
        return obj.events.count()


# ─────────────────────────────────────────────────────────────────────────────
# 6. ForensicCase
# ─────────────────────────────────────────────────────────────────────────────

class ForensicCaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = ForensicCase
        fields = [
            "case_id", "case_title", "description",
            "status", "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["case_id", "created_at"]

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None


# ─────────────────────────────────────────────────────────────────────────────
# 7. NetworkEvent (Telemetry)
# ─────────────────────────────────────────────────────────────────────────────

class NetworkEventSerializer(serializers.ModelSerializer):
    """
    Full telemetry event serializer.
    sha256_hash is computed server-side in NetworkEvent.save(); never client-supplied.
    """
    asset_name         = serializers.CharField(source="asset.asset_name", read_only=True)
    integrity_verified = serializers.SerializerMethodField()

    class Meta:
        model  = NetworkEvent
        fields = [
            "event_id", "asset", "asset_name",
            "timestamp", "source_ip", "destination_ip",
            "raw_telemetry", "threat_classification", "confidence_score",
            "sha256_hash", "integrity_verified",
        ]
        read_only_fields = ["event_id", "timestamp", "sha256_hash"]

    def get_integrity_verified(self, obj):
        return obj.verify_integrity()


class NetworkEventIngestSerializer(serializers.ModelSerializer):
    """
    Ingest-only serializer (POST /api/telemetry/).
    sha256_hash is excluded — auto-sealed in model.save().
    """

    class Meta:
        model  = NetworkEvent
        fields = [
            "asset", "source_ip", "destination_ip",
            "raw_telemetry", "threat_classification", "confidence_score",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 8. ContainmentAction
# ─────────────────────────────────────────────────────────────────────────────

class ContainmentActionSerializer(serializers.ModelSerializer):
    event_source_ip = serializers.CharField(
        source="event.source_ip", read_only=True
    )
    event_threat = serializers.CharField(
        source="event.threat_classification", read_only=True
    )

    class Meta:
        model  = ContainmentAction
        fields = [
            "action_id", "event", "event_source_ip", "event_threat",
            "action_type", "target_ip",
            "executed_at", "execution_status",
        ]
        read_only_fields = ["action_id", "executed_at"]
