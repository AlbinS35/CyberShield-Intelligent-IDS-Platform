"""
Detection Models
Alert lifecycle management, Incident grouping, Playbook execution,
IP Blocklist, and ML inference logging.
"""

import uuid
from django.db import models
from django.utils import timezone
from authentication.models import Tenant, User


class Alert(models.Model):
    """
    A security alert generated from a NetworkEvent after ML classification.
    Represents a single actionable threat notification.
    """

    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"
        INFO = "INFO", "Informational"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False Positive"
        ESCALATED = "ESCALATED", "Escalated"

    class AttackType(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        DOS = "DOS", "Denial of Service"
        PROBE = "PROBE", "Probe / Reconnaissance"
        R2L = "R2L", "Remote to Local"
        U2R = "U2R", "User to Root"
        UNKNOWN = "UNKNOWN", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="alerts")

    # Link to the triggering network event
    network_event = models.OneToOneField(
        "ingestion.NetworkEvent",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="alert",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    attack_type = models.CharField(max_length=10, choices=AttackType.choices, default=AttackType.UNKNOWN)

    # Source metadata
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    destination_ip = models.GenericIPAddressField(null=True, blank=True)
    affected_asset = models.CharField(max_length=255, blank=True)

    # ML confidence
    ml_confidence = models.FloatField(null=True, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_alerts"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cs_alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status", "severity"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title} — {self.status}"


class Incident(models.Model):
    """
    A group of related Alerts representing a sustained attack campaign.
    Analysts escalate individual alerts into an Incident for coordinated response.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        INVESTIGATING = "INVESTIGATING", "Investigating"
        CONTAINED = "CONTAINED", "Contained"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="incidents")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    severity = models.CharField(max_length=10, choices=Alert.Severity.choices, default=Alert.Severity.HIGH)
    alerts = models.ManyToManyField(Alert, related_name="incidents", blank=True)
    lead_analyst = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="led_incidents"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cs_incidents"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.status}] {self.title}"


class Playbook(models.Model):
    """
    Automated response playbook definition.
    Contains shell command sequences triggered by severity/attack type.
    """

    class TriggerMode(models.TextChoices):
        AUTO = "AUTO", "Automatic (on ML flag)"
        MANUAL = "MANUAL", "Manual (analyst-triggered)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="playbooks")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_mode = models.CharField(max_length=10, choices=TriggerMode.choices, default=TriggerMode.MANUAL)
    trigger_severity = models.CharField(max_length=10, choices=Alert.Severity.choices, null=True, blank=True)
    commands = models.JSONField(
        help_text='List of shell command strings. E.g. ["iptables -A INPUT -s {ip} -j DROP"]'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cs_playbooks"

    def __str__(self):
        return self.name


class PlaybookExecution(models.Model):
    """Records every execution of a Playbook for forensic audit."""

    class ExecStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        DRY_RUN = "DRY_RUN", "Dry Run"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playbook = models.ForeignKey(Playbook, on_delete=models.CASCADE, related_name="executions")
    alert = models.ForeignKey(Alert, on_delete=models.SET_NULL, null=True, blank=True)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=ExecStatus.choices, default=ExecStatus.PENDING)
    target_ip = models.GenericIPAddressField(null=True, blank=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    is_dry_run = models.BooleanField(default=False)
    executed_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cs_playbook_executions"
        ordering = ["-executed_at"]

    def __str__(self):
        return f"[{self.status}] {self.playbook.name} @ {self.executed_at}"


class IPBlocklist(models.Model):
    """Tracks IPs blocked via automated playbook or manual analyst action."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ip_blocklist")
    ip_address = models.GenericIPAddressField(db_index=True)
    reason = models.CharField(max_length=500, blank=True)
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    playbook_execution = models.ForeignKey(PlaybookExecution, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    blocked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Auto-unblock after this datetime")

    class Meta:
        db_table = "cs_ip_blocklist"
        unique_together = [["tenant", "ip_address"]]

    def __str__(self):
        return f"{self.ip_address} ({'ACTIVE' if self.is_active else 'UNBLOCKED'})"


class MLInferenceLog(models.Model):
    """Records every ML inference call for model monitoring and audit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    network_event = models.ForeignKey(
        "ingestion.NetworkEvent", on_delete=models.SET_NULL, null=True, blank=True
    )
    input_features = models.JSONField(help_text="Feature vector sent to the model")
    prediction = models.CharField(max_length=100)
    confidence = models.FloatField()
    model_version = models.CharField(max_length=50, default="v1.0")
    inference_time_ms = models.FloatField(null=True, blank=True)
    inferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cs_ml_inference_logs"
        ordering = ["-inferred_at"]
