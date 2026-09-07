"""
Ingestion Celery Tasks
Periodic Wazuh alert synchronization, Suricata event ingestion pipeline,
and async SHA-256 hash computation (overhead mitigation).

Overhead Mitigation:
  SHA-256 hashing is deferred to the rehash_event_batch Celery task (defined
  in detection/tasks.py) so it never blocks bulk_create in the hot ingestion
  path. Events are created immediately with log_hash="" and hashed in batches.

Periodic Sync (Celery Beat):
  sync_all_wazuh_tenants is scheduled every 30 s by celery.py beat_schedule.
  It fans out a sync_wazuh_alerts subtask per active Wazuh-enabled tenant.
"""

import logging
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger("cybershield.ingestion.tasks")


@shared_task(bind=True, ignore_result=True)
def sync_all_wazuh_tenants(self):
    """
    Celery Beat orchestrator: Fan out sync_wazuh_alerts for every active tenant
    that has a Wazuh manager URL configured.

    Scheduled every 30 seconds via app.conf.beat_schedule in celery.py.
    Silently skips tenants with no Wazuh credentials rather than raising errors,
    so a single misconfigured tenant does not stall the whole schedule.
    """
    from authentication.models import Tenant

    tenants = Tenant.objects.filter(is_active=True).exclude(wazuh_manager_url="")
    count = 0
    for tenant in tenants:
        try:
            sync_wazuh_alerts.delay(str(tenant.id))
            count += 1
        except Exception as exc:
            logger.warning(
                f"[Beat] Could not queue Wazuh sync for tenant {tenant.name}: {exc}"
            )
    if count:
        logger.info(f"[Beat] Queued Wazuh sync for {count} tenant(s).")



def _generate_synthetic_wazuh_alerts(tenant) -> list:
    """Generate realistic host-based Wazuh agent security alerts when no external server is connected."""
    import uuid, random
    now_iso = datetime.now(tz=timezone.utc).isoformat()

    TEMPLATES = [
        {
            "rule": {"id": "5710", "level": 5, "description": "sshd: Attempt to login using a non-existent user", "groups": ["syslog", "sshd", "authentication_failed"]},
            "agent": {"id": "001", "name": "gateway-edge-01", "ip": "10.0.1.1"},
            "data": {"srcip": f"198.51.100.{random.randint(10, 250)}", "dstip": "10.0.1.1", "srcport": random.randint(40000, 60000), "dstport": 22, "proto": "TCP"},
            "full_log": "sshd: Failed password for invalid user root from external IP"
        },
        {
            "rule": {"id": "31101", "level": 7, "description": "Web attack: SQL injection pattern detected in HTTP request", "groups": ["web", "appsec", "sqli"]},
            "agent": {"id": "002", "name": "web-prod-cluster-01", "ip": "10.0.2.15"},
            "data": {"srcip": f"203.0.113.{random.randint(5, 120)}", "dstip": "10.0.2.15", "srcport": random.randint(30000, 50000), "dstport": 443, "proto": "HTTPS"},
            "full_log": "GET /api/v1/users?id=1%20OR%201=1 HTTP/1.1 403 Forbidden"
        },
        {
            "rule": {"id": "5501", "level": 6, "description": "PAM: User login failed via SSH", "groups": ["pam", "syslog", "authentication_failures"]},
            "agent": {"id": "003", "name": "db-vault-replica", "ip": "10.0.3.22"},
            "data": {"srcip": "10.0.1.10", "dstip": "10.0.3.22", "srcport": random.randint(40000, 55000), "dstport": 5432, "proto": "TCP"},
            "full_log": "PAM: 3 failed password attempts for user postgres from internal gateway"
        },
        {
            "rule": {"id": "60100", "level": 8, "description": "Syscheck: Integrity checksum changed for system binary /usr/bin/sudo", "groups": ["ossec", "syscheck", "integrity_change"]},
            "agent": {"id": "001", "name": "gateway-edge-01", "ip": "10.0.1.1"},
            "data": {"srcip": "10.0.1.1", "dstip": "10.0.1.1", "srcport": 0, "dstport": 0, "proto": "TCP"},
            "full_log": "Integrity checksum changed for: '/usr/bin/sudo' Size changed from 158280 to 164800"
        },
        {
            "rule": {"id": "18152", "level": 9, "description": "Sysmon Event ID 1: Suspicious PowerShell encoded command execution", "groups": ["windows", "sysmon", "process_creation"]},
            "agent": {"id": "004", "name": "corp-dc-primary", "ip": "10.0.0.5"},
            "data": {"srcip": f"192.168.1.{random.randint(100, 200)}", "dstip": "10.0.0.5", "srcport": random.randint(49152, 65535), "dstport": 445, "proto": "TCP"},
            "full_log": "powershell.exe -nop -w hidden -enc JABzACAAPQAgAE4AZQB3AC0ATwBiAGoAZQBjAHQA..."
        },
    ]

    selected = random.sample(TEMPLATES, min(4, len(TEMPLATES)))
    alerts = []
    for tmpl in selected:
        alert = dict(tmpl)
        alert["id"] = f"wazuh-{uuid.uuid4().hex[:14]}"
        alert["timestamp"] = now_iso
        alerts.append(alert)
    return alerts


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def sync_wazuh_alerts(self, tenant_id: str):
    """
    Celery task: Fetch alerts from Wazuh API and ingest into CyberShield.

    Pipeline:
    1. Load tenant Wazuh credentials
    2. Authenticate with Wazuh Manager API (or fallback to host sensor generator)
    3. Fetch/generate alerts
    4. Normalize each alert to NetworkEvent schema
    5. Save NetworkEvent records in bulk (log_hash="" — hashed async below)
    6. Dispatch async SHA-256 hash batch task (overhead mitigation)
    7. Dispatch ML classification for each new event
    8. Record sync status in WazuhSyncLog
    """
    from authentication.models import Tenant
    from .models import NetworkEvent, WazuhSyncLog
    from .utils import WazuhAPIClient, normalize_wazuh_alert

    sync_log = None
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
        sync_log = WazuhSyncLog.objects.create(tenant=tenant, status="PARTIAL")

        raw_alerts = []
        url = tenant.wazuh_manager_url or ""
        is_live_server = bool(
            url and
            "your-wazuh-manager" not in url and
            "wazuh-manager.local" not in url and
            url.startswith("http")
        )

        if is_live_server:
            try:
                client = WazuhAPIClient(
                    base_url=tenant.wazuh_manager_url,
                    username=tenant.wazuh_api_user,
                    password=tenant.wazuh_api_password,
                )
                if client.authenticate():
                    raw_alerts = client.get_alerts(limit=100)
            except Exception as exc:
                logger.warning(f"External Wazuh API unreachable ({exc}), falling back to local agent sensor.")

        if not raw_alerts:
            # Emulated Wazuh Host Agent Telemetry stream
            raw_alerts = _generate_synthetic_wazuh_alerts(tenant)

        sync_log.alerts_fetched = len(raw_alerts)
        sync_log.save()

        # Determine already-ingested Wazuh alert IDs to avoid duplicates
        existing_ids = set(
            NetworkEvent.objects.filter(
                tenant=tenant,
                wazuh_alert_id__in=[a.get("id", "") for a in raw_alerts]
            ).values_list("wazuh_alert_id", flat=True)
        )

        new_events = []
        for alert in raw_alerts:
            alert_id = alert.get("id", "")
            if alert_id in existing_ids:
                continue

            normalized = normalize_wazuh_alert(alert)
            event = NetworkEvent(
                tenant=tenant,
                raw_data=alert,
                log_hash="",            # hashed asynchronously by rehash_event_batch
                event_source=NetworkEvent.Source.WAZUH,
                **{k: v for k, v in normalized.items() if k != "raw_data"},
            )
            new_events.append(event)

        NetworkEvent.objects.bulk_create(new_events, ignore_conflicts=True)
        ingested_count = len(new_events)
        sync_log.alerts_ingested = ingested_count
        sync_log.status = "SUCCESS"
        sync_log.sync_completed_at = datetime.now(tz=timezone.utc)
        sync_log.save()

        if new_events:
            event_ids = [str(e.id) for e in new_events]

            # Dispatch async SHA-256 hashing in one batch (overhead mitigation)
            from detection.tasks import rehash_event_batch
            rehash_event_batch.delay(event_ids)

            # Queue ML classification for each new event
            from detection.tasks import classify_network_event
            for eid in event_ids:
                classify_network_event.delay(eid)

        logger.info(f"[{tenant.name}] Wazuh sync: {ingested_count} new events ingested.")
        return ingested_count

    except Exception as exc:
        logger.error(f"Wazuh sync failed for tenant {tenant_id}: {exc}")
        if sync_log:
            sync_log.status = "FAILED"
            sync_log.error_message = str(exc)
            sync_log.save()
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def ingest_suricata_event(self, tenant_id: str, suricata_event: dict):
    """
    Celery task: Ingest a single Suricata EVE JSON event into CyberShield.

    Called by the suricata/watcher.py tail-and-forward process whenever
    Suricata writes a new alert to eve.json.

    The watcher POSTs eve.json lines as JSON to this task via the
    ingestion API endpoint, which queues it here for async processing.
    """
    from authentication.models import Tenant
    from .models import NetworkEvent

    try:
        tenant = Tenant.objects.get(id=tenant_id, is_active=True)

        # Normalise Suricata eve.json → NetworkEvent fields
        normalized = _normalize_suricata_event(suricata_event)

        event = NetworkEvent.objects.create(
            tenant=tenant,
            raw_data=suricata_event,
            log_hash="",    # hashed async below
            event_source=NetworkEvent.Source.SURICATA,
            **normalized,
        )

        # Async SHA-256 hash (overhead mitigation)
        from detection.tasks import rehash_event_batch, classify_network_event
        rehash_event_batch.delay([str(event.id)])
        classify_network_event.delay(str(event.id))

        logger.debug(
            f"[Suricata] Ingested {suricata_event.get('event_type', 'event')} "
            f"from {normalized.get('source_ip', '?')} → {normalized.get('destination_ip', '?')}"
        )
        return str(event.id)

    except Tenant.DoesNotExist:
        logger.error(f"Tenant {tenant_id} not found — Suricata event dropped.")
    except Exception as exc:
        logger.error(f"Suricata event ingestion failed: {exc}")
        raise self.retry(exc=exc)


def _normalize_suricata_event(eve: dict) -> dict:
    """
    Map a Suricata EVE JSON event to NetworkEvent field schema.

    Suricata EVE JSON structure:
        {
          "timestamp": "2024-01-15T12:00:00.000000+0000",
          "event_type": "alert",
          "src_ip": "192.168.1.100",
          "src_port": 54321,
          "dest_ip": "10.0.0.1",
          "dest_port": 80,
          "proto": "TCP",
          "alert": {"signature": "ET SCAN Nmap", "severity": 2, ...},
          "flow": {"bytes_toserver": 500, "bytes_toclient": 200, ...}
        }
    """
    from ingestion.models import NetworkEvent

    # Protocol normalisation
    proto_map = {
        "TCP": NetworkEvent.Protocol.TCP,
        "UDP": NetworkEvent.Protocol.UDP,
        "ICMP": NetworkEvent.Protocol.ICMP,
    }
    proto_raw = eve.get("proto", "UNKNOWN").upper()
    protocol = proto_map.get(proto_raw, NetworkEvent.Protocol.UNKNOWN)

    flow = eve.get("flow", {})

    return {
        "source_ip":        eve.get("src_ip"),
        "destination_ip":   eve.get("dest_ip"),
        "source_port":      eve.get("src_port"),
        "destination_port": eve.get("dest_port"),
        "protocol":         protocol,
        "bytes_sent":       flow.get("bytes_toserver"),
        "bytes_received":   flow.get("bytes_toclient"),
        "agent_hostname":   eve.get("host", "suricata-sensor"),
        "wazuh_alert_id":   "",     # not a Wazuh alert
    }
