"""
Detection Serializers
Alert, Incident, Playbook, and IPBlocklist serializers.
"""

from rest_framework import serializers
from .models import Alert, Incident, Playbook, PlaybookExecution, IPBlocklist, MLInferenceLog
from authentication.serializers import UserProfileSerializer


class AlertSerializer(serializers.ModelSerializer):
    assigned_to_display = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id", "title", "description", "severity", "status", "attack_type",
            "source_ip", "destination_ip", "affected_asset",
            "ml_confidence", "assigned_to", "assigned_to_display",
            "created_at", "updated_at", "resolved_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_assigned_to_display(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None


class AlertStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["status", "assigned_to", "resolved_at"]


class IncidentSerializer(serializers.ModelSerializer):
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            "id", "title", "description", "status", "severity",
            "alert_count", "lead_analyst", "created_at", "updated_at", "closed_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_alert_count(self, obj):
        return obj.alerts.count()


class PlaybookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playbook
        fields = [
            "id", "name", "description", "trigger_mode", "trigger_severity",
            "commands", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PlaybookExecutionSerializer(serializers.ModelSerializer):
    playbook_name = serializers.CharField(source="playbook.name", read_only=True)

    class Meta:
        model = PlaybookExecution
        fields = [
            "id", "playbook", "playbook_name", "alert", "status",
            "target_ip", "stdout", "stderr", "exit_code",
            "is_dry_run", "executed_at", "completed_at",
        ]
        read_only_fields = ["id", "executed_at"]


class IPBlocklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPBlocklist
        fields = [
            "id", "ip_address", "reason", "is_active",
            "blocked_at", "expires_at",
        ]
        read_only_fields = ["id", "blocked_at"]


class MLInferenceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLInferenceLog
        fields = [
            "id", "prediction", "confidence", "model_version",
            "inference_time_ms", "inferred_at",
        ]
        read_only_fields = fields
