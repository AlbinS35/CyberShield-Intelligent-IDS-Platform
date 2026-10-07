"""
Ingestion Views
Network event CRUD, Wazuh sync status, manual sync trigger,
and live ingestion health / diagnostics endpoint.
"""

from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import NetworkEvent, WazuhSyncLog
from .serializers import NetworkEventSerializer, WazuhSyncLogSerializer
from authentication.permissions import IsAnalystOrAbove, IsSysAdmin


class NetworkEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/ingestion/network-events/       -> list all events (tenant-scoped)
    GET  /api/ingestion/network-events/{id}/  -> event detail + hash verification
    """
    serializer_class = NetworkEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_threat", "ml_classification", "event_source", "protocol"]
    search_fields = ["source_ip", "destination_ip", "agent_hostname"]
    ordering_fields = ["event_timestamp", "ingested_at", "ml_confidence"]
    ordering = ["-event_timestamp"]

    def get_queryset(self):
        return NetworkEvent.objects.filter(tenant=self.request.user.tenant)

    @action(detail=True, methods=["get"], url_path="verify-hash")
    def verify_hash(self, request, pk=None):
        """GET /api/ingestion/network-events/{id}/verify-hash/ -> verify SHA-256 integrity."""
        from .utils import verify_log_hash
        event = self.get_object()
        is_valid = verify_log_hash(event.raw_data, event.log_hash)
        return Response({
            "event_id": str(event.id),
            "stored_hash": event.log_hash,
            "integrity_valid": is_valid,
            "verified_at": event.ingested_at.isoformat(),
        })


class WazuhSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/ingestion/sync-logs/ -> Wazuh sync history."""
    serializer_class = WazuhSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsSysAdmin]

    def get_queryset(self):
        return WazuhSyncLog.objects.filter(tenant=self.request.user.tenant)


class SuricataIngestView(generics.GenericAPIView):
    """
    POST /api/ingestion/suricata/
    Accepts a batch of Suricata EVE JSON events from the suricata-watcher container.

    Request body:
        {
            "tenant_id": "<uuid>",
            "events": [{...eve_json_event...}, ...]
        }

    Each event is queued as an async Celery task for processing,
    so this endpoint returns quickly even for large batches.
    Authentication: Bearer JWT (service account configured via SURICATA_API_TOKEN).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .tasks import ingest_suricata_event

        events    = request.data.get("events", [])
        tenant_id = request.data.get("tenant_id", str(request.user.tenant_id))

        if not events:
            return Response({"error": "'events' list is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(events, list):
            return Response({"error": "'events' must be a list."}, status=status.HTTP_400_BAD_REQUEST)

        queued = 0
        errors = []
        for event in events[:500]:  # cap at 500 per call
            try:
                ingest_suricata_event.delay(tenant_id, event)
                queued += 1
            except Exception as e:
                import traceback
                errors.append(traceback.format_exc())

        if errors:
            return Response(
                {"detail": "Internal Server Error", "traceback": errors[0]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"queued": queued, "message": f"{queued} Suricata events queued for ingestion."},
            status=status.HTTP_202_ACCEPTED,
        )


class WazuhSyncTriggerView(generics.GenericAPIView):
    """POST /api/ingestion/wazuh/sync/ -> manually trigger Wazuh alert ingestion."""
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def post(self, request):
        from .tasks import sync_wazuh_alerts
        tenant = getattr(request.user, "tenant", None)
        if not tenant:
            return Response(
                {"error": "No tenant associated with this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant_id = str(tenant.id)
        task = sync_wazuh_alerts.delay(tenant_id)
        return Response(
            {"message": "Wazuh sync task queued.", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED,
        )


class IngestionStatusView(APIView):
    """
    GET /api/ingestion/status/

    Diagnostic health endpoint for live ingestion pipeline monitoring.
    Returns a structured JSON status report covering:
      - suricata_live_active:    Whether any SURICATA events arrived in the last 5 minutes
      - last_suricata_event_at:  Timestamp of the most recent Suricata-sourced NetworkEvent
      - wazuh_sync_active:       Last Wazuh sync status and whether credentials are configured
      - celery_queue_healthy:    Whether Celery workers are reachable and processing tasks
      - total_events_24h:        Total events ingested across all sources in the last 24 hours
      - suricata_events_24h:     Suricata-only event count in the last 24 hours

    Permission: AllowAny — intended as an ops/monitoring probe endpoint.
    Sensitive data (tenant UUIDs, credentials) is never exposed.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        now = timezone.now()
        window_5min  = now - timedelta(minutes=5)
        window_24h   = now - timedelta(hours=24)

        report = {}

        # ── Suricata liveness ─────────────────────────────────────────────────
        suricata_qs = NetworkEvent.objects.filter(
            event_source=NetworkEvent.Source.SURICATA,
        )
        last_suricata = suricata_qs.order_by("-ingested_at").first()
        suricata_live = suricata_qs.filter(ingested_at__gte=window_5min).exists()
        suricata_24h  = suricata_qs.filter(ingested_at__gte=window_24h).count()

        report["suricata_live_active"]    = suricata_live
        report["last_suricata_event_at"]  = (
            last_suricata.ingested_at.isoformat() if last_suricata else None
        )
        report["suricata_events_24h"]     = suricata_24h
        report["suricata_status_message"] = (
            "Live — SURICATA events ingested in last 5 minutes."
            if suricata_live else
            (f"Last event at {last_suricata.ingested_at.isoformat()}" if last_suricata
             else "No SURICATA events ingested yet. Run setup_live_nids.sh to activate.")
        )

        # ── Wazuh sync health ─────────────────────────────────────────────────
        last_wazuh_sync = WazuhSyncLog.objects.order_by("-sync_started_at").first()
        wazuh_sync_active = (
            last_wazuh_sync is not None
            and last_wazuh_sync.status == WazuhSyncLog.SyncStatus.SUCCESS
            and last_wazuh_sync.sync_started_at >= window_24h
        )

        report["wazuh_sync_active"] = wazuh_sync_active
        if last_wazuh_sync:
            report["last_wazuh_sync"] = {
                "status":           last_wazuh_sync.status,
                "alerts_ingested":  last_wazuh_sync.alerts_ingested,
                "alerts_fetched":   last_wazuh_sync.alerts_fetched,
                "started_at":       last_wazuh_sync.sync_started_at.isoformat(),
                "completed_at":     (
                    last_wazuh_sync.sync_completed_at.isoformat()
                    if last_wazuh_sync.sync_completed_at else None
                ),
                "error":            last_wazuh_sync.error_message or None,
            }
        else:
            report["last_wazuh_sync"] = None
            report["wazuh_sync_message"] = (
                "No Wazuh sync recorded. Configure WAZUH_MANAGER_URL in .env."
            )

        # ── Celery queue health ───────────────────────────────────────────────
        celery_healthy = False
        celery_detail  = "unknown"
        try:
            from cybershield_core.celery import app as celery_app
            inspector = celery_app.control.inspect(timeout=2.0)
            active = inspector.active()
            if active is not None:
                worker_count = len(active)
                celery_healthy = worker_count > 0
                celery_detail  = f"{worker_count} worker(s) active"
            else:
                celery_detail = "No workers responded — Celery may be stopped"
        except Exception as exc:
            celery_detail = f"Celery inspect failed: {str(exc)[:100]}"

        report["celery_queue_healthy"] = celery_healthy
        report["celery_detail"]        = celery_detail

        # ── Total ingestion summary ───────────────────────────────────────────
        report["total_events_24h"] = NetworkEvent.objects.filter(
            ingested_at__gte=window_24h
        ).count()

        # ── Overall health status ─────────────────────────────────────────────
        report["overall_status"] = (
            "HEALTHY"   if (suricata_live and celery_healthy) else
            "DEGRADED"  if (suricata_24h > 0 or wazuh_sync_active) else
            "INACTIVE"
        )
        report["checked_at"] = now.isoformat()

        return Response(report, status=status.HTTP_200_OK)
