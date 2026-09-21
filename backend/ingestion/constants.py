"""
Ingestion Constants
Centralized definitions for NSL-KDD feature columns, attack type mappings,
protocol codes, and severity thresholds used across the ingestion pipeline.
"""

# ── NSL-KDD 41 Feature Names ──────────────────────────────────────────────────
# The exact feature order expected by the trained Random Forest model.
# Any deviation in column ordering will silently produce wrong predictions.
NSL_KDD_FEATURES = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
]

# ── Attack Category → Alert Severity Mapping ──────────────────────────────────
# Maps the ML model's prediction label to a human-readable severity level
# for Alert creation and playbook gating decisions.
ATTACK_SEVERITY_MAP = {
    "NORMAL": "INFO",
    "DOS":    "CRITICAL",   # Denial of Service — direct availability impact
    "PROBE":  "MEDIUM",     # Reconnaissance — pre-attack scanning
    "R2L":    "HIGH",       # Remote-to-Local — unauthorized access attempt
    "U2R":    "CRITICAL",   # User-to-Root — privilege escalation
    "UNKNOWN": "HIGH",      # Unknown classification — assume worst case
}

# ── Attack Category Descriptions ─────────────────────────────────────────────
# Human-readable descriptions used in alert titles and documentation.
ATTACK_DESCRIPTIONS = {
    "NORMAL": "Normal network traffic — no anomaly detected.",
    "DOS": (
        "Denial of Service (DoS) attack detected. Attacker floods the target "
        "with excessive requests (e.g., SYN flood, Ping of Death, Smurf) to "
        "exhaust resources and deny service to legitimate users."
    ),
    "PROBE": (
        "Probe / Reconnaissance attack detected. Attacker is scanning the network "
        "to discover open ports, running services, or OS fingerprints. Common "
        "types: Port Scan, Nmap, IPSweep, Satan."
    ),
    "R2L": (
        "Remote-to-Local (R2L) attack detected. An external attacker exploits a "
        "vulnerability to gain unauthorized local access to a machine. Examples: "
        "FTP Write, IMAP exploit, Guess Password."
    ),
    "U2R": (
        "User-to-Root (U2R) attack detected. An authenticated local user attempts "
        "to gain superuser (root) privileges by exploiting a local vulnerability. "
        "Examples: Buffer overflow, Rootkit, Perl attack."
    ),
    "UNKNOWN": "Unclassified network activity — manual analyst review required.",
}

# ── Well-Known Port → Service Mapping ────────────────────────────────────────
# Used to enrich NetworkEvent records with readable service names.
PORT_SERVICE_MAP = {
    20: "ftp-data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "domain",
    67: "bootps",
    68: "bootpc",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    445: "microsoft-ds",
    993: "imaps",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    6379: "redis",
    8080: "http-alt",
    8443: "https-alt",
    27017: "mongodb",
}

# ── ML Confidence Thresholds ──────────────────────────────────────────────────
# These govern when automatic actions are triggered vs. held for human review.
CONFIDENCE_GATE_AUTO_BLOCK = 0.85      # Minimum confidence to auto-run blocking playbook
CONFIDENCE_GATE_ALERT_ONLY = 0.60     # Below this, create alert with LOW severity only
CONFIDENCE_GATE_DISCARD = 0.40        # Below this, inference is discarded (too uncertain)

# Severities eligible for automatic playbook execution
AUTO_PLAYBOOK_ELIGIBLE_SEVERITIES = frozenset(["HIGH", "CRITICAL"])
