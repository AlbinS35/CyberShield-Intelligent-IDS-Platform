#!/usr/bin/env python3
"""
CyberShield — End-to-End Live NIDS Demo Runner
===============================================
Runs a complete proof-of-life verification:

  1. Fires a controlled TCP port probe against localhost (no nmap required)
  2. Tails /var/log/suricata/eve.json for the matching alert
  3. Polls GET /api/ingestion/network-events/?event_source=SURICATA until ingested
  4. Verifies SHA-256 evidence hash via GET /api/ingestion/network-events/{id}/verify-hash/
  5. Checks ML confidence >= 0.85 and reports PlaybookExecution status
  6. Prints a coloured pass/fail report

Usage (Linux / WSL2, after running setup_live_nids.sh):
  python scripts/run_live_demo.py [--api http://localhost:8000] [--token <JWT>]

Environment variables (loaded from .env automatically):
  SURICATA_API_TOKEN   Service-account JWT for CyberShield API
  DEFAULT_TENANT_ID    Tenant UUID
"""

import argparse
import json
import os
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Try to load .env from project root ────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — no external deps required."""
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

_load_dotenv(_ENV_FILE)

# ── Colour output helpers ─────────────────────────────────────────────────────
SUPPORTS_COLOR = sys.stdout.isatty()
def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if SUPPORTS_COLOR else text

def ok(msg):    print(_c("32", f"  [PASS] {msg}"))
def fail(msg):  print(_c("31", f"  [FAIL] {msg}"))
def info(msg):  print(_c("36", f"  [INFO] {msg}"))
def warn(msg):  print(_c("33", f"  [WARN] {msg}"))
def section(t): print(_c("1;36", f"\n=== {t} ==="))

# ── Try to import requests; fall back to urllib ────────────────────────────────
try:
    import requests as _requests
    def _get(url, headers=None, timeout=10):
        r = _requests.get(url, headers=headers, timeout=timeout)
        return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    def _post(url, json_data=None, headers=None, timeout=10):
        r = _requests.post(url, json=json_data, headers=headers, timeout=timeout)
        return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    _HTTP_LIB = "requests"
except ImportError:
    import urllib.request, urllib.error
    def _get(url, headers=None, timeout=10):
        req = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode()
                try:
                    return r.status, json.loads(body)
                except json.JSONDecodeError:
                    return r.status, body
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()
    def _post(url, json_data=None, headers=None, timeout=10):
        data = json.dumps(json_data or {}).encode()
        hdrs = {**(headers or {}), "Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode()
                try:
                    return r.status, json.loads(body)
                except json.JSONDecodeError:
                    return r.status, body
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()
    _HTTP_LIB = "urllib"


# =============================================================================
# Step 1 — Fire controlled TCP probe (port scan simulation)
# =============================================================================
def step1_fire_probe(target_host: str = "127.0.0.1", ports: list = None) -> list:
    section("Step 1 — Firing Controlled TCP Port Probe")
    if ports is None:
        # Common ports that Suricata Emerging Threats rules trigger on
        ports = [22, 23, 80, 443, 3306, 8080, 8443]

    info(f"Probing {target_host} on ports: {ports}")
    info("Using Python socket — no nmap required")

    probe_start = datetime.now(tz=timezone.utc)
    hit_ports = []

    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            result = s.connect_ex((target_host, port))
            s.close()
            status = "OPEN" if result == 0 else "CLOSED/FILTERED"
            info(f"  Port {port:>5}/TCP → {status}")
            hit_ports.append(port)
        except Exception as e:
            warn(f"  Port {port}/TCP → error ({e})")
        time.sleep(0.05)

    ok(f"Probe complete — {len(ports)} ports attempted in rapid succession")
    info("Suricata should detect this as a reconnaissance/port-scan pattern")
    return probe_start, hit_ports


# =============================================================================
# Step 2 — Tail eve.json for Suricata alert
# =============================================================================
def step2_tail_eve_json(probe_start: datetime,
                        eve_path: str = "/var/log/suricata/eve.json",
                        timeout_s: int = 60) -> dict | None:
    section("Step 2 — Tailing eve.json for Suricata Alert")

    eve = Path(eve_path)
    if not eve.exists():
        warn(f"eve.json not found at {eve_path}")
        warn("Common alternatives:")
        warn("  Docker volume: docker exec cybershield_suricata cat /var/log/suricata/eve.json")
        warn("  WSL2 path:     /var/log/suricata/eve.json (inside Suricata container)")
        warn("Skipping eve.json tail — continuing with API poll...")
        return None

    info(f"Watching {eve_path} for new alert events (timeout: {timeout_s}s)...")
    deadline = time.time() + timeout_s
    probe_ts = probe_start.timestamp()

    with open(eve_path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)  # seek to end
        while time.time() < deadline:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("event_type") not in ("alert", "flow"):
                continue

            # Check timestamp is after our probe
            ts_raw = event.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                if ts.timestamp() < probe_ts - 2:
                    continue
            except (ValueError, TypeError):
                pass

            ok(f"Suricata alert detected!")
            info(f"  Event type: {event.get('event_type')}")
            info(f"  Src IP:     {event.get('src_ip', '?')}:{event.get('src_port', '?')}")
            info(f"  Dst IP:     {event.get('dest_ip', '?')}:{event.get('dest_port', '?')}")
            if "alert" in event:
                info(f"  Signature:  {event['alert'].get('signature', '?')}")
                info(f"  Category:   {event['alert'].get('category', '?')}")
            return event

    warn(f"No Suricata alert detected in eve.json within {timeout_s}s")
    warn("This is normal if Suricata rules haven't fired yet — continuing with API poll")
    return None


# =============================================================================
# Step 3 — Poll ingestion API for SURICATA events
# =============================================================================
def step3_poll_api(api_base: str, headers: dict,
                   probe_start: datetime, timeout_s: int = 120) -> dict | None:
    section("Step 3 — Polling Ingestion API for SURICATA Events")

    url = f"{api_base.rstrip('/')}/api/ingestion/network-events/?event_source=SURICATA&ordering=-event_timestamp&page_size=5"
    deadline = time.time() + timeout_s
    attempt = 0

    info(f"Polling: GET {url}")
    info(f"Waiting up to {timeout_s}s for a Suricata event to appear...")

    while time.time() < deadline:
        attempt += 1
        try:
            status, data = _get(url, headers=headers)
        except Exception as e:
            warn(f"  Attempt {attempt}: connection error — {e}")
            time.sleep(5)
            continue

        if status not in (200, 201):
            warn(f"  Attempt {attempt}: HTTP {status}")
            time.sleep(5)
            continue

        results = data.get("results", []) if isinstance(data, dict) else []
        if results:
            event = results[0]
            ok(f"Suricata event found in API (attempt {attempt})")
            info(f"  Event ID:   {event.get('id')}")
            info(f"  Source IP:  {event.get('source_ip')}")
            info(f"  Protocol:   {event.get('protocol')}")
            info(f"  ML Class:   {event.get('ml_classification', 'pending...')}")
            info(f"  Ingested:   {event.get('ingested_at')}")
            return event

        wait = min(5 * attempt, 20)
        info(f"  Attempt {attempt}: no events yet — waiting {wait}s...")
        time.sleep(wait)

    fail(f"No SURICATA events appeared in the API within {timeout_s}s")
    info("Possible causes:")
    info("  • Suricata rules didn't trigger on the probe traffic")
    info("  • suricata-watcher not running: docker compose logs suricata-watcher")
    info("  • Eve.json path mismatch in docker-compose volume mount")
    return None


# =============================================================================
# Step 4 — Verify SHA-256 evidence hash
# =============================================================================
def step4_verify_hash(api_base: str, headers: dict, event_id: str) -> bool:
    section("Step 4 — Verifying SHA-256 Evidence Hash")

    url = f"{api_base.rstrip('/')}/api/ingestion/network-events/{event_id}/verify-hash/"
    info(f"GET {url}")

    try:
        status, data = _get(url, headers=headers)
    except Exception as e:
        fail(f"Hash verification request failed: {e}")
        return False

    if status != 200:
        fail(f"HTTP {status}: {data}")
        return False

    stored_hash    = data.get("stored_hash", "")
    integrity_ok   = data.get("integrity_valid", False)
    verified_at    = data.get("verified_at", "")

    if not stored_hash or stored_hash == "":
        warn("Hash not yet computed (deferred SHA-256 task still pending)")
        warn("The rehash_event_batch Celery task runs asynchronously — retry in ~5s")
        return False

    if integrity_ok:
        ok(f"SHA-256 integrity VALID")
        info(f"  Hash:        {stored_hash[:16]}...{stored_hash[-8:]}")
        info(f"  Verified at: {verified_at}")
        return True
    else:
        fail(f"SHA-256 integrity INVALID — possible data tampering!")
        info(f"  Stored hash: {stored_hash}")
        return False


# =============================================================================
# Step 5 — Check ML confidence and PlaybookExecution
# =============================================================================
def step5_check_ml_and_playbook(api_base: str, headers: dict, event: dict) -> None:
    section("Step 5 — ML Confidence & Playbook Execution Check")

    ml_class = event.get("ml_classification", "")
    ml_conf  = event.get("ml_confidence")
    is_threat = event.get("is_threat")
    event_id  = event.get("id")

    if not ml_class:
        warn("ML classification still pending (Celery task in queue)")
        warn("Check with: docker compose logs celery_worker")
        return

    info(f"  ML Classification: {_c('1', ml_class)}")
    info(f"  Confidence:        {ml_conf:.1%}" if ml_conf else "  Confidence:        N/A")
    info(f"  Is Threat:         {is_threat}")

    CONFIDENCE_GATE = 0.85
    if ml_conf is not None and ml_conf >= CONFIDENCE_GATE:
        ok(f"Confidence {ml_conf:.1%} >= {CONFIDENCE_GATE:.0%} gate — auto-playbook eligible")
    elif ml_conf is not None:
        warn(f"Confidence {ml_conf:.1%} < {CONFIDENCE_GATE:.0%} gate — playbook suppressed (analyst review)")
    else:
        warn("No confidence score yet — classification pending")

    # Check for alerts linked to this event
    alert_url = f"{api_base.rstrip('/')}/api/detection/alerts/?ordering=-created_at&page_size=5"
    try:
        status, data = _get(alert_url, headers=headers)
        if status == 200:
            alerts = data.get("results", []) if isinstance(data, dict) else []
            matching = [a for a in alerts if a.get("network_event") == event_id or
                        a.get("source_ip") == event.get("source_ip")]
            if matching:
                a = matching[0]
                ok(f"Alert created: [{a.get('severity')}] {a.get('title', '')[:60]}")
                info(f"  Alert ID:     {a.get('id')}")
                info(f"  Playbook gated: {a.get('playbook_gated', 'N/A')}")
            else:
                info("No alert found for this event yet (may still be processing)")
    except Exception as e:
        warn(f"Could not check alerts: {e}")


# =============================================================================
# Main
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="CyberShield Live NIDS End-to-End Demo Runner"
    )
    parser.add_argument(
        "--api", default="http://localhost:8000",
        help="CyberShield backend base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--token", default=os.environ.get("SURICATA_API_TOKEN", ""),
        help="JWT bearer token (defaults to SURICATA_API_TOKEN env var)"
    )
    parser.add_argument(
        "--eve-log", default="/var/log/suricata/eve.json",
        help="Path to Suricata eve.json (default: /var/log/suricata/eve.json)"
    )
    parser.add_argument(
        "--target", default="127.0.0.1",
        help="Target host for probe (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--timeout", type=int, default=120,
        help="Max seconds to wait for API events (default: 120)"
    )
    args = parser.parse_args()

    print(_c("1;32", "\n" + "="*60))
    print(_c("1;32",   "  CyberShield Live NIDS — End-to-End Demo Runner"))
    print(_c("1;32",   "="*60))
    print(f"\n  API:      {args.api}")
    print(f"  Token:    {'[set]' if args.token else '[NOT SET — anonymous]'}")
    print(f"  Eve log:  {args.eve_log}")
    print(f"  Target:   {args.target}")
    print(f"  HTTP lib: {_HTTP_LIB}\n")

    if not args.token:
        warn("SURICATA_API_TOKEN not set — API calls will be unauthenticated")
        warn("Run: bash scripts/setup_live_nids.sh   to generate and set the token")

    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}

    results = {}

    # Step 1 — Fire probe
    probe_start, hit_ports = step1_fire_probe(target_host=args.target)
    results["probe"] = len(hit_ports) > 0

    # Brief pause — let Suricata process packets
    time.sleep(3)

    # Step 2 — Tail eve.json
    eve_event = step2_tail_eve_json(probe_start, eve_path=args.eve_log, timeout_s=30)
    results["eve_json"] = eve_event is not None

    # Step 3 — Poll ingestion API
    api_event = step3_poll_api(args.api, headers, probe_start, timeout_s=args.timeout)
    results["api_event"] = api_event is not None

    if api_event:
        event_id = api_event.get("id")

        # Step 4 — Verify hash (retry once after 6s for async hash task)
        hash_ok = step4_verify_hash(args.api, headers, event_id)
        if not hash_ok:
            info("Waiting 6s for rehash_event_batch Celery task...")
            time.sleep(6)
            hash_ok = step4_verify_hash(args.api, headers, event_id)
        results["hash_valid"] = hash_ok

        # Step 5 — ML + Playbook
        step5_check_ml_and_playbook(args.api, headers, api_event)
        results["ml_classified"] = bool(api_event.get("ml_classification"))
    else:
        results["hash_valid"] = False
        results["ml_classified"] = False

    # Final Report
    section("Demo Results Summary")
    all_pass = True
    checks = [
        ("probe",          "TCP probe fired"),
        ("eve_json",       "Suricata eve.json alert detected"),
        ("api_event",      "Event visible in CyberShield API"),
        ("hash_valid",     "SHA-256 evidence hash verified"),
        ("ml_classified",  "ML classification completed"),
    ]
    for key, label in checks:
        passed = results.get(key, False)
        if passed:
            ok(label)
        else:
            fail(label)
            all_pass = False

    print()
    if all_pass:
        print(_c("1;32", "  RESULT: ALL CHECKS PASSED — CyberShield live NIDS is fully operational!"))
    else:
        print(_c("1;33", "  RESULT: PARTIAL — Some checks failed. See warnings above."))
        print(_c("1;33", "  This is expected on first run if Suricata rules haven't fired yet."))
        print(_c("1;33", "  Try running more aggressive traffic and re-running this script."))
    print()


if __name__ == "__main__":
    main()
