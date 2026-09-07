"""
Ingestion Models
Network event logs with JSONB storage, SHA-256 tamper sealing,
Wazuh alert normalization, and automated IP reputation tracking.
"""

import uuid
from django.db import models
from django.utils import timezone
from authentication.models import Tenant


class NetworkEvent(models.Model):
    """
    Represents a single raw network event log entry.

    - raw_data: JSONB column for flexible Wazuh/syslog payload storage
    - log_hash: SHA-256 fingerprint of raw_data for tamper evidence
    - source: origin of the event (WAZUH / MANUAL / API_FEED)
    """

    class Source(models.TextChoices):
        WAZUH = "WAZUH", "Wazuh Agent"
        MANUAL = "MANUAL", "Manual Entry"
        API_FEED = "API_FEED", "External API Feed"
        SIMULATOR = "SIMULATOR", "Test Simulator"
        SURICATA = "SURICATA", "Suricata NIDS"

    class Protocol(models.TextChoices):
        TCP = "TCP", "TCP"
        UDP = "UDP", "UDP"
        ICMP = "ICMP", "ICMP"
        HTTP = "HTTP", "HTTP"
        HTTPS = "HTTPS", "HTTPS"
        DNS = "DNS", "DNS"
        UNKNOWN = "UNKNOWN", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="network_events")

    # Network metadata
    source_ip = models.GenericIPAddressField(db_index=True, null=True, blank=True)
    destination_ip = models.GenericIPAddressField(db_index=True, null=True, blank=True)
    source_port = models.PositiveIntegerField(null=True, blank=True)
    destination_port = models.PositiveIntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=10, choices=Protocol.choices, default=Protocol.UNKNOWN)
    bytes_sent = models.BigIntegerField(null=True, blank=True)
    bytes_received = models.BigIntegerField(null=True, blank=True)
    duration_ms = models.FloatField(null=True, blank=True, help_text="Connection duration in milliseconds")

    # Payload
    raw_data = models.JSONField(help_text="JSONB: full Wazuh/syslog alert payload")
    log_hash = models.CharField(max_length=64, editable=False, help_text="SHA-256 hash of raw_data for tamper detection")

    # Source tracking
    event_source = models.CharField(max_length=20, choices=Source.choices, default=Source.WAZUH)
    wazuh_alert_id = models.CharField(max_length=100, blank=True, db_index=True)
    agent_hostname = models.CharField(max_length=255, blank=True)

    # Classification (set by ML engine post-ingestion)
    ml_classification = models.CharField(max_length=100, blank=True, help_text="ML model output: Normal/DoS/Probe/R2L/U2R")
    ml_confidence = models.FloatField(null=True, blank=True, help_text="Classification confidence 0-1")
    is_threat = models.BooleanField(null=True, blank=True)

    # Timestamps
    event_timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cs_network_events"
        ordering = ["-event_timestamp"]
        indexes = [
            models.Index(fields=["tenant", "event_timestamp"]),
            models.Index(fields=["source_ip", "is_threat"]),
            models.Index(fields=["tenant", "is_threat", "event_timestamp"]),
        ]

    def __str__(self):
        return f"[{self.event_source}] {self.source_ip} → {self.destination_ip} @ {self.event_timestamp}"


class WazuhSyncLog(models.Model):
    """Tracks Wazuh API synchronization history per tenant."""

    class SyncStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        PARTIAL = "PARTIAL", "Partial"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="wazuh_sync_logs")
    status = models.CharField(max_length=10, choices=SyncStatus.choices)
    alerts_fetched = models.IntegerField(default=0)
    alerts_ingested = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    sync_started_at = models.DateTimeField(auto_now_add=True)
    sync_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cs_wazuh_sync_logs"
        ordering = ["-sync_started_at"]

    def __str__(self):
        return f"[{self.tenant}] {self.status} — {self.alerts_ingested} ingested"
