"""
CyberShield Core Models — Normalized PostgreSQL Schema
=======================================================
Implements the 7 canonical IDS platform tables using explicit tbl_ prefixes.
All tables are PostgreSQL-optimized with JSONB, UUID PKs where specified,
DecimalField for confidence scores, and SHA-256 tamper sealing on events.

Table Map:
    tbl_organization      → Organization
    tbl_user              → CoreUser
    tbl_login             → Login
    tbl_network_asset     → NetworkAsset
    tbl_forensic_case     → ForensicCase
    tbl_network_event     → NetworkEvent
    tbl_containment_action → ContainmentAction
"""

import uuid
import hashlib
import json
from django.db import models


# ─────────────────────────────────────────────────────────────────────────────
# 1.  tbl_organization
# ─────────────────────────────────────────────────────────────────────────────

class Organization(models.Model):
    """
    Multi-tenant organization root entity.
    Every user, asset, event, and case is scoped to an Organization.
    """

    class Status(models.TextChoices):
        ACTIVE   = "ACTIVE",   "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"

    org_id      = models.BigAutoField(primary_key=True)
    org_name    = models.CharField(max_length=255, unique=True, null=False)
    domain_name = models.CharField(max_length=255, null=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    status      = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "tbl_organization"
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["org_name"]

    def __str__(self):
        return f"{self.org_name} ({self.status})"


# ─────────────────────────────────────────────────────────────────────────────
# 2.  tbl_user
# ─────────────────────────────────────────────────────────────────────────────

class CoreUser(models.Model):
    """
    Platform user — scoped to an Organization.
    Stores identity metadata only; authentication credentials live in tbl_login.
    UUID primary key for global uniqueness across tenants.
    """

    user_id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255, null=False)
    phone_no  = models.CharField(max_length=15, null=False)
    org       = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        db_column="org_id",
        related_name="users",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_user"
        verbose_name = "Core User"
        verbose_name_plural = "Core Users"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} — {self.org.org_name}"


# ─────────────────────────────────────────────────────────────────────────────
# 3.  tbl_login
# ─────────────────────────────────────────────────────────────────────────────

class Login(models.Model):
    """
    Authentication credentials and RBAC role for a CoreUser.
    Separated from tbl_user so credentials can be managed independently.
    The JWT endpoint authenticates against this table.
    """

    class Role(models.TextChoices):
        ANALYST      = "Analyst",      "Security Analyst"
        INVESTIGATOR = "Investigator", "Digital Forensic Investigator"
        ADMIN        = "Admin",        "System Administrator"
        MANAGEMENT   = "Management",   "Organization Management"

    class Status(models.TextChoices):
        ACTIVE   = "ACTIVE",   "Active"
        INACTIVE = "INACTIVE", "Inactive"
        LOCKED   = "LOCKED",   "Account Locked"

    login_id      = models.BigAutoField(primary_key=True)
    user          = models.OneToOneField(
        CoreUser,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="login",
    )
    email         = models.CharField(max_length=255, unique=True, null=False, db_index=True)
    password_hash = models.CharField(max_length=255, null=False)
    role          = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.ANALYST,
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "tbl_login"
        verbose_name = "Login Credential"
        verbose_name_plural = "Login Credentials"

    def __str__(self):
        return f"{self.email} [{self.role}]"

    def set_password(self, raw_password: str) -> None:
        """Hash and store password using SHA-256 (upgrade to bcrypt for production)."""
        self.password_hash = hashlib.sha256(raw_password.encode()).hexdigest()

    def check_password(self, raw_password: str) -> bool:
        """Verify supplied password against stored hash."""
        return self.password_hash == hashlib.sha256(raw_password.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# 4.  tbl_network_asset
# ─────────────────────────────────────────────────────────────────────────────

class NetworkAsset(models.Model):
    """
    Infrastructure asset register — servers, endpoints, and network devices
    monitored by the CyberShield platform.
    """

    class Status(models.TextChoices):
        ONLINE      = "ONLINE",      "Online"
        OFFLINE     = "OFFLINE",     "Offline"
        MAINTENANCE = "MAINTENANCE", "Under Maintenance"
        COMPROMISED = "COMPROMISED", "Potentially Compromised"

    asset_id       = models.BigAutoField(primary_key=True)
    org            = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        db_column="org_id",
        related_name="assets",
    )
    asset_name     = models.CharField(max_length=255, null=False)
    ip_address     = models.CharField(max_length=45, null=False)    # Supports IPv4 + IPv6
    os_type        = models.CharField(max_length=100, null=False)
    wazuh_agent_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.ONLINE,
    )

    class Meta:
        db_table = "tbl_network_asset"
        verbose_name = "Network Asset"
        verbose_name_plural = "Network Assets"
        ordering = ["asset_name"]
        indexes = [
            models.Index(fields=["org", "status"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        return f"{self.asset_name} ({self.ip_address}) — {self.status}"


# ─────────────────────────────────────────────────────────────────────────────
# 5.  tbl_forensic_case
# ─────────────────────────────────────────────────────────────────────────────

class ForensicCase(models.Model):
    """
    Digital forensics investigation case vault.
    UUID primary key for legal reference integrity.
    """

    class Status(models.TextChoices):
        OPEN           = "OPEN",           "Open"
        ACTIVE         = "ACTIVE",         "Active Investigation"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Review"
        CLOSED         = "CLOSED",         "Closed"
        ARCHIVED       = "ARCHIVED",       "Archived"

    case_id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_title  = models.CharField(max_length=255, null=False)
    description = models.TextField(null=False)
    status      = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_by  = models.ForeignKey(
        CoreUser,
        on_delete=models.SET_NULL,
        db_column="created_by",
        null=True,
        blank=True,
        related_name="forensic_cases",
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_forensic_case"
        verbose_name = "Forensic Case"
        verbose_name_plural = "Forensic Cases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.status}] {self.case_title}"


# ─────────────────────────────────────────────────────────────────────────────
# 6.  tbl_network_event
# ─────────────────────────────────────────────────────────────────────────────

def _compute_sha256(payload: dict) -> str:
    """Deterministic SHA-256 over sorted JSON serialization of the payload dict."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class NetworkEvent(models.Model):
    """
    Raw telemetry ingestion log with PostgreSQL JSONB storage.
    sha256_hash is auto-generated server-side from raw_telemetry on save,
    providing a tamper-evident seal for forensic chain-of-custody.
    """

    event_id               = models.BigAutoField(primary_key=True)
    asset                  = models.ForeignKey(
        NetworkAsset,
        on_delete=models.CASCADE,
        db_column="asset_id",
        related_name="events",
    )
    timestamp              = models.DateTimeField(auto_now_add=True, db_index=True)
    source_ip              = models.CharField(max_length=45, null=False)
    destination_ip         = models.CharField(max_length=45, null=False)
    raw_telemetry          = models.JSONField(
        null=False,
        help_text="Native PostgreSQL JSONB — full Wazuh/syslog event payload",
    )
    threat_classification  = models.CharField(max_length=100, null=False, db_index=True)
    confidence_score       = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=False,
        help_text="ML confidence score 0.00–100.00",
    )
    sha256_hash            = models.CharField(
        max_length=64,
        null=False,
        editable=False,
        help_text="SHA-256 seal of raw_telemetry; auto-computed on save",
    )

    class Meta:
        db_table = "tbl_network_event"
        verbose_name = "Network Event"
        verbose_name_plural = "Network Events"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["asset", "timestamp"]),
            models.Index(fields=["threat_classification", "confidence_score"]),
            models.Index(fields=["source_ip"]),
        ]

    def save(self, *args, **kwargs):
        """Auto-seal raw_telemetry with SHA-256 before every save."""
        self.sha256_hash = _compute_sha256(self.raw_telemetry)
        super().save(*args, **kwargs)

    def verify_integrity(self) -> bool:
        """Re-compute hash and compare against stored seal."""
        return self.sha256_hash == _compute_sha256(self.raw_telemetry)

    def __str__(self):
        return (
            f"[{self.threat_classification}] "
            f"{self.source_ip} → {self.destination_ip} "
            f"@ {self.timestamp} (conf={self.confidence_score})"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7.  tbl_containment_action
# ─────────────────────────────────────────────────────────────────────────────

class ContainmentAction(models.Model):
    """
    Automated playbook execution log.
    Records every containment action taken in response to a NetworkEvent
    for audit, compliance, and forensic review.
    """

    class ActionType(models.TextChoices):
        BLOCK_IP        = "BLOCK_IP",        "Block IP Address"
        QUARANTINE_HOST = "QUARANTINE_HOST", "Quarantine Host"
        KILL_PROCESS    = "KILL_PROCESS",    "Kill Malicious Process"
        ISOLATE_NETWORK = "ISOLATE_NETWORK", "Network Isolation"
        ALERT_ANALYST   = "ALERT_ANALYST",   "Alert Analyst"
        CUSTOM          = "CUSTOM",          "Custom Action"

    class ExecutionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED  = "FAILED",  "Failed"
        PARTIAL = "PARTIAL", "Partial Success"
        SKIPPED = "SKIPPED", "Skipped (dry-run)"

    action_id        = models.BigAutoField(primary_key=True)
    event            = models.ForeignKey(
        NetworkEvent,
        on_delete=models.CASCADE,
        db_column="event_id",
        related_name="containment_actions",
    )
    action_type      = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        null=False,
    )
    target_ip        = models.CharField(max_length=45, null=False)
    executed_at      = models.DateTimeField(auto_now_add=True)
    execution_status = models.CharField(
        max_length=50,
        choices=ExecutionStatus.choices,
        null=False,
        default=ExecutionStatus.PENDING,
    )

    class Meta:
        db_table = "tbl_containment_action"
        verbose_name = "Containment Action"
        verbose_name_plural = "Containment Actions"
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["event", "execution_status"]),
            models.Index(fields=["target_ip"]),
        ]

    def __str__(self):
        return (
            f"[{self.execution_status}] {self.action_type} → "
            f"{self.target_ip} @ {self.executed_at}"
        )
