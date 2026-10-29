"""
Forensics Serializers
"""

from rest_framework import serializers
from .models import ForensicCase, Evidence, CaseTimeline, ChainOfCustody


class ForensicCaseSerializer(serializers.ModelSerializer):
    evidence_count = serializers.SerializerMethodField()
    timeline_count = serializers.SerializerMethodField()
    lead_investigator_name = serializers.SerializerMethodField()

    class Meta:
        model = ForensicCase
        fields = [
            "id", "case_number", "title", "description", "status", "classification",
            "related_incident", "lead_investigator", "lead_investigator_name",
            "attack_vector", "affected_systems", "legal_hold",
            "evidence_count", "timeline_count",
            "created_at", "updated_at", "closed_at",
        ]
        read_only_fields = ["id", "case_number", "created_at", "updated_at"]
        extra_kwargs = {
            "description": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if "case_title" in data and not data.get("title"):
            data["title"] = data["case_title"]
        return super().to_internal_value(data)

    def get_evidence_count(self, obj):
        return obj.evidence.count()

    def get_timeline_count(self, obj):
        return obj.timeline_events.count()

    def get_lead_investigator_name(self, obj):
        return obj.lead_investigator.get_full_name() if obj.lead_investigator else None


class EvidenceSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = [
            "id", "case", "case_number", "evidence_type", "title", "description",
            "file", "file_name", "file_size_bytes", "mime_type",
            "sha256_hash", "uploaded_by", "uploaded_by_name", "uploaded_at",
        ]
        read_only_fields = ["id", "file_name", "file_size_bytes", "sha256_hash", "uploaded_at"]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None


class EvidenceUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["case", "evidence_type", "title", "description", "file", "mime_type"]


class CaseTimelineSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    event_type = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    actor_name = serializers.SerializerMethodField()
    ip_address = serializers.CharField(source="source_ip", read_only=True)
    hash = serializers.SerializerMethodField()
    evidence_file = serializers.SerializerMethodField()

    class Meta:
        model = CaseTimeline
        fields = [
            "id", "case", "category", "category_display", "event_type", "title", "description",
            "source_ip", "target_ip", "ip_address", "source_system",
            "network_event", "evidence", "evidence_file", "hash", "event_time", "created_at",
            "recorded_by", "actor_name", "recorded_at",
        ]
        read_only_fields = ["id", "recorded_at"]

    def get_event_type(self, obj):
        title_lower = (obj.title or "").lower()
        if "escalat" in title_lower:
            return "ALERT_ESCALATED"
        if "opened" in title_lower:
            return "CASE_OPENED"
        if "sealed" in title_lower or "hash" in title_lower:
            return "LOG_SEALED"
        if "block" in title_lower:
            return "IP_BLOCKED"
        if "playbook" in title_lower:
            return "PLAYBOOK_FIRED"
        if obj.evidence:
            return "EVIDENCE_UPLOADED"
        return obj.category or "OTHER"

    def get_created_at(self, obj):
        dt = obj.event_time or obj.recorded_at
        return dt.isoformat() if dt else None

    def get_actor_name(self, obj):
        if obj.recorded_by:
            name = obj.recorded_by.get_full_name()
            return name if name else (obj.recorded_by.username or obj.recorded_by.email)
        return obj.source_system or "CyberShield Platform"

    def get_hash(self, obj):
        if obj.evidence and obj.evidence.sha256_hash:
            return obj.evidence.sha256_hash
        if obj.network_event and obj.network_event.log_hash:
            return obj.network_event.log_hash
        return None

    def get_evidence_file(self, obj):
        if obj.evidence:
            return obj.evidence.file_name
        return None


class ChainOfCustodySerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ChainOfCustody
        fields = [
            "id", "evidence", "action", "action_display",
            "performed_by", "performed_by_name",
            "notes", "location", "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]

    def get_performed_by_name(self, obj):
        return obj.performed_by.get_full_name() if obj.performed_by else None
