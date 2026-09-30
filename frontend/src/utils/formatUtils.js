/**
 * formatUtils.js
 * General-purpose formatting utilities for timestamps, IP addresses,
 * file sizes, and duration values across the CyberShield frontend.
 */

// ── Time & Date Formatters ────────────────────────────────────────────────────

/**
 * Format an ISO 8601 datetime string into a readable local date+time string.
 *
 * @param {string} isoString - ISO 8601 datetime string (e.g., "2026-09-21T08:30:00Z").
 * @param {object} options - Optional Intl.DateTimeFormat options.
 * @returns {string} Formatted local datetime string.
 */
export function formatDateTime(isoString, options = {}) {
  if (!isoString) return "—";
  const defaultOptions = {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  };
  return new Intl.DateTimeFormat("en-IN", { ...defaultOptions, ...options }).format(
    new Date(isoString)
  );
}

/**
 * Return a relative time string like "3 minutes ago" or "just now".
 *
 * @param {string} isoString - ISO 8601 datetime string.
 * @returns {string} Human-readable relative time string.
 */
export function timeAgo(isoString) {
  if (!isoString) return "—";
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/**
 * Format connection duration from milliseconds to a readable string.
 *
 * @param {number|null} durationMs - Duration in milliseconds.
 * @returns {string} e.g., "1.23s", "450ms", or "N/A".
 */
export function formatDuration(durationMs) {
  if (durationMs === null || durationMs === undefined) return "N/A";
  if (durationMs < 1000) return `${Math.round(durationMs)}ms`;
  return `${(durationMs / 1000).toFixed(2)}s`;
}

// ── Network Formatters ────────────────────────────────────────────────────────

/**
 * Truncate a long IP address for display in tight table cells.
 * IPv6 addresses are shortened; IPv4 addresses are returned as-is.
 *
 * @param {string|null} ip - IP address string.
 * @returns {string} Formatted IP string.
 */
export function formatIP(ip) {
  if (!ip) return "—";
  // Truncate long IPv6 addresses
  if (ip.length > 20) return ip.slice(0, 17) + "...";
  return ip;
}

/**
 * Format bytes transferred to a human-readable size string.
 *
 * @param {number|null} bytes - Byte count.
 * @returns {string} e.g., "1.23 MB", "456 KB", "N/A".
 */
export function formatBytes(bytes) {
  if (bytes === null || bytes === undefined) return "N/A";
  if (bytes === 0) return "0 B";
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

// ── String Formatters ─────────────────────────────────────────────────────────

/**
 * Truncate a long string and add an ellipsis.
 *
 * @param {string} str - Input string.
 * @param {number} maxLength - Maximum length before truncation.
 * @returns {string} Truncated string with "…" or original string.
 */
export function truncate(str, maxLength = 60) {
  if (!str) return "—";
  return str.length > maxLength ? str.slice(0, maxLength) + "…" : str;
}

/**
 * Convert a snake_case or UPPER_SNAKE_CASE string to Title Case.
 *
 * @param {string} str - e.g., "attack_type", "IN_PROGRESS"
 * @returns {string} e.g., "Attack Type", "In Progress"
 */
export function toTitleCase(str) {
  if (!str) return "";
  return str
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

// ── UUID Formatters ───────────────────────────────────────────────────────────

/**
 * Shorten a UUID for display (shows first 8 characters).
 *
 * @param {string} uuid - Full UUID string.
 * @returns {string} e.g., "a1b2c3d4…"
 */
export function shortUUID(uuid) {
  if (!uuid) return "—";
  return uuid.slice(0, 8) + "…";
}
