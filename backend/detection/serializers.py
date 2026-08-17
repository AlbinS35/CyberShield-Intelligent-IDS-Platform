"""
Detection Serializers
Alert, Incident, Playbook, IPBlocklist, SHAP Explanation serializers.
"""

from rest_framework import serializers
from .models import Alert, Incident, Playbook, PlaybookExecution, IPBlocklist, MLInferenceLog, ComplianceReport
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
            "dataset_source", "inference_time_ms", "inferred_at",
        ]
        read_only_fields = fields


class SHAPFeatureSerializer(serializers.Serializer):
    """Single SHAP feature contribution entry."""
    feature   = serializers.CharField()
    value     = serializers.FloatField()
    shap_value = serializers.FloatField()
    direction = serializers.ChoiceField(choices=["increases_risk", "decreases_risk"])


class SHAPExplanationSerializer(serializers.Serializer):
    """
    Response schema for GET /api/detection/alerts/{id}/explain/
    Returns the SHAP-ranked feature contributions for an Alert's ML inference.
    """
    alert_id       = serializers.UUIDField()
    prediction     = serializers.CharField()
    confidence     = serializers.FloatField()
    dataset_source = serializers.CharField()
    model_version  = serializers.CharField()
    playbook_gated = serializers.BooleanField()
    explanation    = SHAPFeatureSerializer(many=True)
    explanation_note = serializers.CharField()


class ComplianceReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ComplianceReport
        fields = [
            "id", "title", "report_type", "status", "generated_by",
            "generated_by_name", "created_at", "metrics", "findings", "auditor_notes"
        ]
        read_only_fields = ["id", "created_at"]

    def get_generated_by_name(self, obj):
        return obj.generated_by.get_full_name() if obj.generated_by else "System"

