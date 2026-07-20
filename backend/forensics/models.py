"""
Forensics Models
Case management vault, SHA-256 sealed evidence, chronological attack
timeline reconstruction, and legally compliant chain-of-custody tracking.
"""

import uuid
from django.db import models
from django.utils import timezone
from authentication.models import Tenant, User


class ForensicCase(models.Model):
    """
    A digital forensics investigation case.
    Groups evidence, timelines, and chain-of-custody records for a single incident.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACTIVE = "ACTIVE", "Active Investigation"
        PENDING_REVIEW = "PENDING_REVIEW", "Pending Legal Review"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    class Classification(models.TextChoices):
        CONFIDENTIAL = "CONFIDENTIAL", "Confidential"
        RESTRICTED = "RESTRICTED", "Restricted"
        INTERNAL = "INTERNAL", "Internal"
        PUBLIC = "PUBLIC", "Public"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="forensic_cases")
    case_number = models.CharField(max_length=50, unique=True, editable=False)

    title = models.CharField(max_length=300)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    classification = models.CharField(max_length=15, choices=Classification.choices, default=Classification.CONFIDENTIAL)

    # Related incident (optional)
    related_incident = models.ForeignKey(
        "detection.Incident", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="forensic_cases"
    )

    # Investigator assignment
    lead_investigator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="led_cases"
    )

    # Metadata
    attack_vector = models.CharField(max_length=200, blank=True)
    affected_systems = models.JSONField(default=list, help_text="List of affected hostnames/IPs")
    legal_hold = models.BooleanField(default=False, help_text="True if under legal hold — prevents deletion")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cs_forensic_cases"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.case_number:
            # Generate case number: CS-YYYYMMDD-XXXX
            from django.utils import timezone
            import random
            date_str = timezone.now().strftime("%Y%m%d")
            suffix = str(random.randint(1000, 9999))
            self.case_number = f"CS-{date_str}-{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.case_number}] {self.title}"


def evidence_upload_path(instance, filename):
    """Dynamic upload path: media/forensics/<case_id>/<filename>"""
    return f"forensics/{instance.case.id}/{filename}"


class Evidence(models.Model):
    """
    A single piece of forensic evidence uploaded to a case.
    SHA-256 hash is computed on upload for integrity verification.
    """

    class EvidenceType(models.TextChoices):
        LOG_FILE = "LOG_FILE", "Log File"
        PCAP = "PCAP", "Network Capture (PCAP)"
        DISK_IMAGE = "DISK_IMAGE", "Disk Image"
        SCREENSHOT = "SCREENSHOT", "Screenshot"
        MEMORY_DUMP = "MEMORY_DUMP", "Memory Dump"
        REPORT = "REPORT", "Report Document"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ForensicCase, on_delete=models.CASCADE, related_name="evidence")
    evidence_type = models.CharField(max_length=20, choices=EvidenceType.choices, default=EvidenceType.OTHER)

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=evidence_upload_path)
    file_name = models.CharField(max_length=255, editable=False)
    file_size_bytes = models.BigIntegerField(editable=False)
    mime_type = models.CharField(max_length=100, blank=True)

    # SHA-256 integrity seal — computed at upload time
    sha256_hash = models.CharField(max_length=64, editable=False, help_text="SHA-256 hash computed at upload time")

    # Uploaded by
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploaded_evidence")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Source network event (optional link)
    source_network_event = models.ForeignKey(
        "ingestion.NetworkEvent", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = "cs_evidence"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"[{self.evidence_type}] {self.title} — SHA256: {self.sha256_hash[:16]}..."


class CaseTimeline(models.Model):
    """
    A chronological event entry in a forensic case timeline.
    Reconstructs the attack progression from multiple log sources.
    """

    class EventCategory(models.TextChoices):
        INITIAL_ACCESS = "INITIAL_ACCESS", "Initial Access"
        LATERAL_MOVEMENT = "LATERAL_MOVEMENT", "Lateral Movement"
        PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION", "Privilege Escalation"
        DATA_EXFILTRATION = "DATA_EXFILTRATION", "Data Exfiltration"
        PERSISTENCE = "PERSISTENCE", "Persistence Mechanism"
        COMMAND_CONTROL = "COMMAND_CONTROL", "Command & Control"
        IMPACT = "IMPACT", "Impact / Destruction"
        DETECTION = "DETECTION", "Detection Event"
        RESPONSE = "RESPONSE", "Response Action"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(ForensicCase, on_delete=models.CASCADE, related_name="timeline_events")
    category = models.CharField(max_length=25, choices=EventCategory.choices, default=EventCategory.OTHER)
    title = models.CharField(max_length=300)
    description = models.TextField()
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    target_ip = models.GenericIPAddressField(null=True, blank=True)
    source_system = models.CharField(max_length=255, blank=True, help_text="Log source (e.g. Wazuh, SIEM, Manual)")

    # Link to original log event
    network_event = models.ForeignKey(
        "ingestion.NetworkEvent", on_delete=models.SET_NULL, null=True, blank=True
    )
    evidence = models.ForeignKey(Evidence, on_delete=models.SET_NULL, null=True, blank=True)

    # The actual time this event occurred (not when it was logged)
    event_time = models.DateTimeField(db_index=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cs_case_timeline"
        ordering = ["event_time"]

    def __str__(self):
        return f"[{self.category}] {self.title} @ {self.event_time}"


class ChainOfCustody(models.Model):
    """
    Records every access, transfer, and action taken on evidence.
    Required for legal admissibility of digital evidence.
    """

    class Action(models.TextChoices):
        COLLECTED = "COLLECTED", "Evidence Collected"
        TRANSFERRED = "TRANSFERRED", "Evidence Transferred"
        ANALYZED = "ANALYZED", "Evidence Analyzed"
        COPIED = "COPIED", "Copy Made"
        HASHED = "HASHED", "Hash Verified"
        SUBMITTED = "SUBMITTED", "Submitted to Legal"
        RETURNED = "RETURNED", "Returned to Owner"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name="custody_chain")
    action = models.CharField(max_length=20, choices=Action.choices)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True, help_text="Physical or network location")
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cs_chain_of_custody"
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.action}] {self.evidence.title} by {self.performed_by} @ {self.timestamp}"
