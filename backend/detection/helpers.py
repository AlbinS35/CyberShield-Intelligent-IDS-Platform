"""
Detection Helpers
Utility functions for alert enrichment, severity resolution, and
attack-type-to-description mapping used across the detection pipeline.
"""

from ingestion.constants import (
    ATTACK_SEVERITY_MAP,
    ATTACK_DESCRIPTIONS,
    CONFIDENCE_GATE_AUTO_BLOCK,
    CONFIDENCE_GATE_ALERT_ONLY,
    AUTO_PLAYBOOK_ELIGIBLE_SEVERITIES,
)


def resolve_severity(attack_type: str, confidence: float) -> str:
    """
    Determine alert severity based on attack type and ML confidence.

    Rules (in order of priority):
    1. NORMAL traffic → always INFO, no alert generated.
    2. If confidence is too low (< ALERT_ONLY gate) → downgrade to LOW.
    3. Otherwise → use the canonical ATTACK_SEVERITY_MAP entry.

    Args:
        attack_type: One of NORMAL, DOS, PROBE, R2L, U2R, UNKNOWN.
        confidence: Float 0.0–1.0 from the ML classifier.

    Returns:
        Severity string: CRITICAL | HIGH | MEDIUM | LOW | INFO
    """
    if attack_type == "NORMAL":
        return "INFO"

    base_severity = ATTACK_SEVERITY_MAP.get(attack_type, "HIGH")

    # Downgrade if model is uncertain
    if confidence < CONFIDENCE_GATE_ALERT_ONLY:
        return "LOW"

    return base_severity


def should_auto_block(attack_type: str, confidence: float) -> bool:
    """
    Return True if the detection should trigger an automatic blocking playbook.

    Both conditions must be satisfied:
    - Confidence is at or above the auto-block gate (default 0.85).
    - The resolved severity is in the AUTO_PLAYBOOK_ELIGIBLE_SEVERITIES set.

    Args:
        attack_type: Predicted class from the ML classifier.
        confidence: Prediction confidence 0.0–1.0.

    Returns:
        bool: True if automatic playbook should fire, False if held for review.
    """
    if confidence < CONFIDENCE_GATE_AUTO_BLOCK:
        return False
    severity = resolve_severity(attack_type, confidence)
    return severity in AUTO_PLAYBOOK_ELIGIBLE_SEVERITIES


def build_alert_title(attack_type: str, source_ip: str | None, destination_ip: str | None) -> str:
    """
    Build a human-readable alert title from the attack classification.

    Args:
        attack_type: ML prediction label.
        source_ip: Source IP address of the triggering network event.
        destination_ip: Destination IP of the triggering event.

    Returns:
        Formatted alert title string.
    """
    label_map = {
        "DOS":    "Denial of Service (DoS) Attack",
        "PROBE":  "Reconnaissance / Port Scan Detected",
        "R2L":    "Remote-to-Local Intrusion Attempt",
        "U2R":    "Privilege Escalation (User-to-Root) Detected",
        "UNKNOWN": "Unclassified Threat Activity",
    }
    label = label_map.get(attack_type, f"{attack_type} Threat")
    src = source_ip or "Unknown"
    dst = destination_ip or "Unknown"
    return f"{label} — {src} → {dst}"


def get_attack_description(attack_type: str) -> str:
    """
    Return the full human-readable description for a given attack type.

    Args:
        attack_type: The predicted attack class string.

    Returns:
        Descriptive string explaining the attack category.
    """
    return ATTACK_DESCRIPTIONS.get(attack_type, ATTACK_DESCRIPTIONS["UNKNOWN"])
