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

    class Meta:
        model = CaseTimeline
        fields = [
            "id", "case", "category", "category_display", "title", "description",
            "source_ip", "target_ip", "source_system",
            "network_event", "evidence", "event_time",
            "recorded_by", "recorded_at",
        ]
        read_only_fields = ["id", "recorded_at"]


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
