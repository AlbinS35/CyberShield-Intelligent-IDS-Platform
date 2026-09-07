"""
Ingestion Serializers
"""

from rest_framework import serializers
from .models import NetworkEvent, WazuhSyncLog


class NetworkEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkEvent
        fields = [
            "id", "source_ip", "destination_ip", "source_port", "destination_port",
            "protocol", "bytes_sent", "bytes_received", "duration_ms",
            "event_source", "wazuh_alert_id", "agent_hostname",
            "ml_classification", "ml_confidence", "is_threat",
            "log_hash", "event_timestamp", "ingested_at",
        ]
        read_only_fields = ["id", "log_hash", "ingested_at"]


class WazuhSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WazuhSyncLog
        fields = "__all__"
        read_only_fields = ["id"]
