"""
Detection Serializers
Alert, Incident, Playbook, IPBlocklist, SHAP Explanation serializers.
"""

from rest_framework import serializers
from .models import Alert, Incident, Playbook, PlaybookExecution, IPBlocklist, MLInferenceLog, ComplianceReport
from authentication.serializers import UserProfileSerializer


class AlertSerializer(serializers.ModelSerializer):
    assigned_to_display = serializers.SerializerMethodField()
    protocol = serializers.SerializerMethodField()
    ml_classification = serializers.SerializerMethodField()
    agent_hostname = serializers.SerializerMethodField()
    affected_asset = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id", "title", "description", "severity", "status", "attack_type",
            "source_ip", "destination_ip", "affected_asset",
            "protocol", "ml_classification", "agent_hostname",
            "ml_confidence", "assigned_to", "assigned_to_display",
            "created_at", "updated_at", "resolved_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_assigned_to_display(self, obj):
        return obj.assigned_to.get_full_name() if obj.assigned_to else None

    def get_protocol(self, obj):
        if obj.network_event and getattr(obj.network_event, "protocol", None):
            return obj.network_event.protocol
        return "TCP"

    def get_ml_classification(self, obj):
        if obj.network_event and getattr(obj.network_event, "ml_classification", None):
            return obj.network_event.ml_classification
        return obj.attack_type or "R2L"

    def get_agent_hostname(self, obj):
        if obj.network_event and getattr(obj.network_event, "agent_hostname", None):
            return obj.network_event.agent_hostname
        if obj.network_event:
            source = getattr(obj.network_event, "event_source", "")
            if source == "SURICATA":
                return "nids-suricata-sensor-01"
            elif source == "WAZUH":
                return "wazuh-agent-host-01"
        return "sensor-alpha-01"

    def get_affected_asset(self, obj):
        if obj.affected_asset and obj.affected_asset.strip():
            return obj.affected_asset
        # Dynamic lookup from NetworkAsset or IP subnet tag
        target_ip = obj.destination_ip or obj.source_ip
        if target_ip:
            try:
                from core.models import NetworkAsset
                asset = NetworkAsset.objects.filter(ip_address=target_ip).first()
                if asset:
                    return f"{asset.asset_name} ({target_ip})"
            except Exception:
                pass
            if target_ip.endswith(".1") or target_ip.endswith(".254"):
                return f"Core Gateway Firewall ({target_ip})"
            elif "10.0.3." in target_ip:
                return f"Internal Database Server ({target_ip})"
            elif "10.0.1." in target_ip:
                return f"Corporate Workstation ({target_ip})"
            elif "10.0.2." in target_ip:
                return f"DMZ Web Application Server ({target_ip})"
            return f"Monitored Asset Node ({target_ip})"
        return "Core Infrastructure Gateway"


class AlertStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["status", "assigned_to", "resolved_at"]


class IncidentSerializer(serializers.ModelSerializer):
    alert_count = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            "id", "title", "description", "status", "severity",
            "alert_count", "lead_analyst", "assigned_to_name", "created_at", "updated_at", "closed_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_alert_count(self, obj):
        return obj.alerts.count()

    def get_assigned_to_name(self, obj):
        if obj.lead_analyst:
            return obj.lead_analyst.get_full_name() or obj.lead_analyst.username
        return None


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
    metrics = serializers.JSONField(required=False, default=dict)
    findings = serializers.JSONField(required=False, default=list)

    class Meta:
        model = ComplianceReport
        fields = [
            "id", "title", "report_type", "status", "generated_by",
            "generated_by_name", "created_at", "metrics", "findings", "auditor_notes"
        ]
        read_only_fields = ["id", "created_at", "generated_by"]

    def get_generated_by_name(self, obj):
        return obj.generated_by.get_full_name() if obj.generated_by else "System"

