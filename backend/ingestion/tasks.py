"""
Ingestion Celery Tasks
Periodic Wazuh alert synchronization and network event ingestion pipeline.
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
    5. Compute SHA-256 hash on raw_data
    6. Save NetworkEvent records in bulk
    7. Dispatch ML classification for each new event
    8. Record sync status in WazuhSyncLog

    Args:
        tenant_id: UUID string of the target tenant.
    """
    from authentication.models import Tenant
    from .models import NetworkEvent, WazuhSyncLog
    from .utils import WazuhAPIClient, normalize_wazuh_alert, generate_log_hash

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
            raw_data = alert
            log_hash = generate_log_hash(raw_data)

            event = NetworkEvent(
                tenant=tenant,
                raw_data=raw_data,
                log_hash=log_hash,
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

        # Queue ML classification for each new event
        for event in new_events:
            from detection.tasks import classify_network_event
            classify_network_event.delay(str(event.id))

        logger.info(f"[{tenant.name}] Wazuh sync: {ingested_count} new events ingested.")
        return ingested_count

    except Exception as exc:
        logger.error(f"Wazuh sync failed for tenant {tenant_id}: {exc}")
        if sync_log:
            sync_log.status = "FAILED"
            sync_log.error_message = str(exc)
            sync_log.save()
        raise self.retry(exc=exc)
