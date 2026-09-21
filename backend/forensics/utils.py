"""
Forensics Utilities
Helper functions for chain-of-custody operations, evidence integrity
verification, and forensic timeline reconstruction.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone as tz
from typing import Optional

logger = logging.getLogger("cybershield.forensics.utils")


def compute_sha256(data: bytes) -> str:
    """
    Compute the SHA-256 hex digest of a byte sequence.

    Used for both file evidence hashing and raw_data JSONB tamper-sealing.

    Args:
        data: Raw bytes to hash (file content or JSON-encoded string bytes).

    Returns:
        64-character lowercase hex string of the SHA-256 digest.
    """
    return hashlib.sha256(data).hexdigest()


def verify_evidence_integrity(stored_hash: str, file_bytes: bytes) -> bool:
    """
    Verify that a piece of evidence has not been tampered with since upload.

    Re-computes the SHA-256 hash of the raw file bytes and compares it to
    the hash stored at upload time in the Evidence model.

    Args:
        stored_hash: The sha256_hash field value from the Evidence record.
        file_bytes: Raw bytes read from the stored file.

    Returns:
        True if hashes match (integrity confirmed), False if tampered.
    """
    computed = compute_sha256(file_bytes)
    is_valid = computed == stored_hash
    if not is_valid:
        logger.warning(
            "Evidence integrity check FAILED. "
            f"Stored={stored_hash!r}, Computed={computed!r}"
        )
    return is_valid


def build_timeline_entry(
    event_time: datetime,
    event_type: str,
    description: str,
    source_ip: Optional[str] = None,
    destination_ip: Optional[str] = None,
    severity: str = "INFO",
) -> dict:
    """
    Build a structured timeline entry dict for CaseTimeline creation.

    This is the canonical format consumed by the CaseTimelineSerializer
    and the frontend Forensics Timeline Panel.

    Args:
        event_time: UTC datetime of the network event.
        event_type: Category label (e.g., 'INTRUSION', 'SCAN', 'DATA_EXFIL').
        description: Human-readable description of what happened.
        source_ip: Source IP involved in the event (optional).
        destination_ip: Destination IP involved (optional).
        severity: Severity string matching Alert.Severity choices.

    Returns:
        Dictionary ready to be passed to CaseTimeline.objects.create(**entry).
    """
    return {
        "event_time": event_time.isoformat() if isinstance(event_time, datetime) else event_time,
        "event_type": event_type,
        "description": description,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "severity": severity,
    }


def reconstruct_attack_timeline(network_events) -> list[dict]:
    """
    Reconstruct a chronological attack timeline from a queryset of NetworkEvents.

    Groups events by source IP and sorts them chronologically to produce
    a readable narrative of the attack progression.

    Args:
        network_events: QuerySet of NetworkEvent objects (should be filtered
                        to threat events only: is_threat=True).

    Returns:
        List of timeline entry dicts ordered by event_timestamp ascending.
    """
    timeline = []

    for event in network_events.order_by("event_timestamp"):
        classification = event.ml_classification or "UNKNOWN"
        confidence_pct = int((event.ml_confidence or 0) * 100)

        entry = build_timeline_entry(
            event_time=event.event_timestamp,
            event_type=classification,
            description=(
                f"[{classification}] Traffic from {event.source_ip or 'Unknown'} "
                f"to {event.destination_ip or 'Unknown'} "
                f"via {event.protocol} — "
                f"ML Confidence: {confidence_pct}%"
            ),
            source_ip=str(event.source_ip) if event.source_ip else None,
            destination_ip=str(event.destination_ip) if event.destination_ip else None,
        )
        timeline.append(entry)

    return timeline


def generate_case_summary(forensic_case) -> dict:
    """
    Generate a summary report dict for a ForensicCase.

    Aggregates evidence count, timeline event count, and chain-of-custody
    steps into a single dict for dashboard display or PDF export.

    Args:
        forensic_case: A ForensicCase model instance.

    Returns:
        Summary dict with case metadata and aggregate statistics.
    """
    from forensics.models import Evidence, CaseTimeline, ChainOfCustody

    evidence_count = Evidence.objects.filter(case=forensic_case).count()
    timeline_count = CaseTimeline.objects.filter(case=forensic_case).count()
    custody_count  = ChainOfCustody.objects.filter(evidence__case=forensic_case).count()

    return {
        "case_id":          str(forensic_case.id),
        "case_title":       forensic_case.title,
        "status":           forensic_case.status,
        "lead_investigator": forensic_case.lead_investigator.get_full_name()
                             if forensic_case.lead_investigator else "Unassigned",
        "created_at":       forensic_case.created_at.isoformat(),
        "evidence_count":   evidence_count,
        "timeline_events":  timeline_count,
        "custody_steps":    custody_count,
        "generated_at":     datetime.now(tz.utc).isoformat(),
    }
