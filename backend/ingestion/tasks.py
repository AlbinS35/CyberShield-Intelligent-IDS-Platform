"""
Ingestion Celery Tasks
Periodic Wazuh alert synchronization, Suricata event ingestion pipeline,
and async SHA-256 hash computation (overhead mitigation).

Overhead Mitigation:
  SHA-256 hashing is deferred to the rehash_event_batch Celery task (defined
  in detection/tasks.py) so it never blocks bulk_create in the hot ingestion
  path. Events are created immediately with log_hash="" and hashed in batches.
"""

import logging
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger("cybershield.ingestion.tasks")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def sync_wazuh_alerts(self, tenant_id: str):
    """
    Celery task: Fetch alerts from Wazuh API and ingest into CyberShield.

    Pipeline:
    1. Load tenant Wazuh credentials
    2. Authenticate with Wazuh Manager API
    3. Fetch new alerts (not already ingested)
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

        if not tenant.wazuh_manager_url:
            logger.warning(f"Tenant {tenant.name} has no Wazuh manager URL configured.")
            sync_log.status = "FAILED"
            sync_log.error_message = "No Wazuh manager URL configured for this tenant."
            sync_log.save()
            return

        client = WazuhAPIClient(
            base_url=tenant.wazuh_manager_url,
            username=tenant.wazuh_api_user,
            password=tenant.wazuh_api_password,
        )

        if not client.authenticate():
            raise Exception("Wazuh API authentication failed.")

        raw_alerts = client.get_alerts(limit=200)
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
