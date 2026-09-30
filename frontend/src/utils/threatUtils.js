/**
 * threatUtils.js
 * Frontend utility functions for threat classification display, severity
 * badge styling, and attack type explanations in the Analyst Dashboard.
 *
 * Mirrors the backend ingestion/constants.py attack mappings for consistent
 * UI rendering without requiring extra API round-trips.
 */

// ── Attack Type Configuration ─────────────────────────────────────────────────

/**
 * Full configuration for each attack category.
 * Used to drive severity badges, icons, colors, and tooltip descriptions
 * throughout the Analyst Dashboard and Alert Detail views.
 */
export const ATTACK_CONFIG = {
  NORMAL: {
    label: "Normal",
    shortDesc: "Legitimate network traffic",
    fullDesc:
      "Normal network traffic detected. Packets adhere to standard protocol " +
      "specifications with expected payloads and predictable flow patterns.",
    badgeClass: "badge-normal",
    color: "#22c55e",      // green-500
    bgColor: "#dcfce7",    // green-100
    icon: "✅",
  },
  DOS: {
    label: "DoS Attack",
    shortDesc: "Denial of Service",
    fullDesc:
      "A Denial of Service attack floods the target with requests (e.g., SYN " +
      "flood, Ping of Death) to exhaust resources and block legitimate users. " +
      "Characterized by abnormally high packet count and connection error rates.",
    badgeClass: "badge-critical",
    color: "#ef4444",      // red-500
    bgColor: "#fee2e2",    // red-100
    icon: "🔴",
  },
  PROBE: {
    label: "Probe / Scan",
    shortDesc: "Reconnaissance activity",
    fullDesc:
      "Probe attacks scan the network to discover open ports, running services, " +
      "or OS fingerprints before launching a targeted attack. Common indicators " +
      "include sequential port connection attempts and high srv_diff_host_rate.",
    badgeClass: "badge-medium",
    color: "#f59e0b",      // amber-500
    bgColor: "#fef3c7",    // amber-100
    icon: "🟡",
  },
  R2L: {
    label: "Remote-to-Local",
    shortDesc: "Unauthorized remote access attempt",
    fullDesc:
      "A Remote-to-Local attack exploits a vulnerability to gain unauthorized " +
      "local access from an external machine. Examples: FTP Write, Guess " +
      "Password, IMAP exploit. Key indicator: num_failed_logins > 0.",
    badgeClass: "badge-high",
    color: "#f97316",      // orange-500
    bgColor: "#ffedd5",    // orange-100
    icon: "🟠",
  },
  U2R: {
    label: "User-to-Root",
    shortDesc: "Privilege escalation detected",
    fullDesc:
      "A User-to-Root attack allows an authenticated local user to gain " +
      "superuser (root) privileges by exploiting a local vulnerability. " +
      "Key indicators: root_shell=1, su_attempted=1, num_root > 0.",
    badgeClass: "badge-critical",
    color: "#dc2626",      // red-600
    bgColor: "#fecaca",    // red-200
    icon: "🚨",
  },
  UNKNOWN: {
    label: "Unknown Threat",
    shortDesc: "Unclassified — analyst review needed",
    fullDesc:
      "The ML classifier could not confidently assign this traffic to a known " +
      "attack category. Manual analyst review is required. Consider correlating " +
      "with recent alerts from the same source IP.",
    badgeClass: "badge-unknown",
    color: "#6b7280",      // gray-500
    bgColor: "#f3f4f6",    // gray-100
    icon: "❓",
  },
};

// ── Severity Configuration ────────────────────────────────────────────────────

export const SEVERITY_CONFIG = {
  CRITICAL: { label: "Critical", color: "#dc2626", bgColor: "#fee2e2", order: 5 },
  HIGH:     { label: "High",     color: "#f97316", bgColor: "#ffedd5", order: 4 },
  MEDIUM:   { label: "Medium",   color: "#f59e0b", bgColor: "#fef3c7", order: 3 },
  LOW:      { label: "Low",      color: "#3b82f6", bgColor: "#dbeafe", order: 2 },
  INFO:     { label: "Info",     color: "#22c55e", bgColor: "#dcfce7", order: 1 },
};

// ── Utility Functions ─────────────────────────────────────────────────────────

/**
 * Get the full attack configuration object for a given attack type.
 * Falls back to UNKNOWN if the type is not found.
 *
 * @param {string} attackType - e.g., "DOS", "PROBE", "NORMAL"
 * @returns {object} Attack config object with label, colors, desc, icon.
 */
export function getAttackConfig(attackType) {
  return ATTACK_CONFIG[attackType] ?? ATTACK_CONFIG.UNKNOWN;
}

/**
 * Get the severity config for a given severity string.
 *
 * @param {string} severity - e.g., "CRITICAL", "HIGH"
 * @returns {object} Severity config with label, color, bgColor, order.
 */
export function getSeverityConfig(severity) {
  return SEVERITY_CONFIG[severity] ?? SEVERITY_CONFIG.INFO;
}

/**
 * Format ML confidence float to a human-readable percentage string.
 *
 * @param {number|null} confidence - Float 0.0–1.0 from ML inference.
 * @returns {string} e.g., "87.4%" or "N/A"
 */
export function formatConfidence(confidence) {
  if (confidence === null || confidence === undefined) return "N/A";
  return `${(confidence * 100).toFixed(1)}%`;
}

/**
 * Sort alerts array by severity (most critical first), then by date.
 *
 * @param {Array} alerts - Array of alert objects with severity and created_at.
 * @returns {Array} Sorted alerts array.
 */
export function sortAlertsBySeverity(alerts) {
  return [...alerts].sort((a, b) => {
    const severityDiff =
      (SEVERITY_CONFIG[b.severity]?.order ?? 0) -
      (SEVERITY_CONFIG[a.severity]?.order ?? 0);
    if (severityDiff !== 0) return severityDiff;
    // Tie-break: most recent first
    return new Date(b.created_at) - new Date(a.created_at);
  });
}

/**
 * Determine if an alert requires immediate action based on severity.
 *
 * @param {string} severity - Alert severity string.
 * @returns {boolean} True if severity is CRITICAL or HIGH.
 */
export function isHighPriorityAlert(severity) {
  return severity === "CRITICAL" || severity === "HIGH";
}
