"""
Ingestion Admin Registration
"""

from django.contrib import admin
from .models import NetworkEvent, WazuhSyncLog


@admin.register(NetworkEvent)
class NetworkEventAdmin(admin.ModelAdmin):
    list_display  = ["id", "tenant", "source_ip", "destination_ip", "protocol",
                     "event_source", "ml_classification", "is_threat", "event_timestamp"]
    list_filter   = ["is_threat", "ml_classification", "event_source", "protocol", "tenant"]
    search_fields = ["source_ip", "destination_ip", "agent_hostname", "wazuh_alert_id"]
    readonly_fields = ["id", "log_hash", "ingested_at"]
    ordering      = ["-event_timestamp"]
    date_hierarchy = "event_timestamp"

    fieldsets = (
        ("Network Metadata", {
            "fields": ("tenant", "source_ip", "destination_ip", "source_port", "destination_port",
                       "protocol", "bytes_sent", "bytes_received", "duration_ms")
        }),
        ("Source", {"fields": ("event_source", "wazuh_alert_id", "agent_hostname")}),
        ("ML Classification", {"fields": ("ml_classification", "ml_confidence", "is_threat")}),
        ("Integrity", {"fields": ("log_hash",)}),
        ("Raw Payload", {"fields": ("raw_data",), "classes": ("collapse",)}),
        ("Timestamps", {"fields": ("event_timestamp", "ingested_at")}),
    )


@admin.register(WazuhSyncLog)
class WazuhSyncLogAdmin(admin.ModelAdmin):
    list_display  = ["tenant", "status", "alerts_fetched", "alerts_ingested", "sync_started_at"]
    list_filter   = ["status", "tenant"]
    readonly_fields = ["id", "sync_started_at"]
    ordering = ["-sync_started_at"]
