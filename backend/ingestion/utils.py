"""
Ingestion Utilities
SHA-256 cryptographic hashing pipelines for tamper-evident log sealing.
Wazuh API client for alert fetching and normalization.
"""

import hashlib
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger("cybershield.ingestion")


# ─── SHA-256 Hashing ─────────────────────────────────────────────────────────

def generate_log_hash(data: dict) -> str:
    """
    Generate a SHA-256 cryptographic hash of a log payload.

    The raw_data dict is serialized to a canonical JSON string
    (sorted keys, no extra whitespace) before hashing to ensure
    deterministic hash output regardless of key ordering.

    Args:
        data: The log payload dictionary to hash.

    Returns:
        64-character lowercase hex string of the SHA-256 digest.
    """
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_log_hash(data: dict, stored_hash: str) -> bool:
    """
    Verify the integrity of a stored log by recomputing its hash.

    Args:
        data: The raw_data payload from the database.
        stored_hash: The log_hash value stored at ingestion time.

    Returns:
        True if hash matches (data untampered), False otherwise.
    """
    computed = generate_log_hash(data)
    return computed == stored_hash


def generate_file_hash(file_obj) -> str:
    """
    Compute SHA-256 hash of an uploaded file for forensic evidence integrity.

    Args:
        file_obj: Django InMemoryUploadedFile or UploadedFile object.

    Returns:
        64-character SHA-256 hex digest.
    """
    sha256 = hashlib.sha256()
    for chunk in file_obj.chunks(chunk_size=65536):
        sha256.update(chunk)
    file_obj.seek(0)  # Reset file pointer after reading
    return sha256.hexdigest()


# ─── Wazuh API Client ─────────────────────────────────────────────────────────

class WazuhAPIClient:
    """
    REST API client for fetching alerts and agent data from a Wazuh Manager.

    Wazuh API v4 uses JWT authentication.
    Reference: https://documentation.wazuh.com/current/user-manual/api/
    """

    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self._token: Optional[str] = None

    def authenticate(self) -> bool:
        """Obtain JWT token from Wazuh Manager API."""
        try:
            resp = requests.post(
                f"{self.base_url}/security/user/authenticate",
                auth=(self.username, self.password),
                verify=self.verify_ssl,
                timeout=10,
            )
            resp.raise_for_status()
            self._token = resp.json()["data"]["token"]
            logger.info("Wazuh API authentication successful.")
            return True
        except Exception as exc:
            logger.error(f"Wazuh authentication failed: {exc}")
            return False

    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def get_alerts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch recent security alerts from the Wazuh Manager.

        Returns:
            List of raw Wazuh alert dictionaries.
        """
        if not self._token:
            self.authenticate()
        try:
            resp = requests.get(
                f"{self.base_url}/security/events",
                headers=self._headers,
                params={"limit": limit, "offset": offset, "sort": "-timestamp"},
                verify=self.verify_ssl,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("affected_items", [])
        except Exception as exc:
            logger.error(f"Failed to fetch Wazuh alerts: {exc}")
            return []

    def get_agents(self) -> List[Dict[str, Any]]:
        """Fetch all registered Wazuh agents."""
        if not self._token:
            self.authenticate()
        try:
            resp = requests.get(
                f"{self.base_url}/agents",
                headers=self._headers,
                params={"limit": 500},
                verify=self.verify_ssl,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("affected_items", [])
        except Exception as exc:
            logger.error(f"Failed to fetch Wazuh agents: {exc}")
            return []


# ─── Wazuh Alert Normalizer ───────────────────────────────────────────────────

def normalize_wazuh_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw Wazuh alert JSON into the CyberShield NetworkEvent schema.

    Wazuh alert structure varies by rule type. This normalizer extracts
    common fields and falls back gracefully for non-standard formats.

    Args:
        alert: Raw Wazuh alert dictionary from the API.

    Returns:
        Normalized dictionary ready to create a NetworkEvent record.
    """
    data = alert.get("data", {})
    agent = alert.get("agent", {})
    network = data.get("srcip") or data.get("win", {}).get("system", {}).get("computer", "")

    return {
        "source_ip": data.get("srcip") or data.get("src_ip"),
        "destination_ip": data.get("dstip") or data.get("dst_ip"),
        "source_port": _safe_int(data.get("srcport") or data.get("src_port")),
        "destination_port": _safe_int(data.get("dstport") or data.get("dst_port")),
        "protocol": (data.get("proto") or "UNKNOWN").upper(),
        "agent_hostname": agent.get("name", ""),
        "wazuh_alert_id": alert.get("id", ""),
        "event_timestamp": _parse_timestamp(alert.get("timestamp")),
        "raw_data": alert,
    }


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(ts_str: Optional[str]) -> datetime:
    if not ts_str:
        return datetime.now(tz=timezone.utc)
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(tz=timezone.utc)
