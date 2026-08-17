"""
Ingestion Views
Network event CRUD, Wazuh sync status, and manual sync trigger.
"""

from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import NetworkEvent, WazuhSyncLog
from .serializers import NetworkEventSerializer, WazuhSyncLogSerializer
from authentication.permissions import IsAnalystOrAbove, IsSysAdmin


class NetworkEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/ingestion/network-events/       → list all events (tenant-scoped)
    GET  /api/ingestion/network-events/{id}/  → event detail + hash verification
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
        """GET /api/ingestion/network-events/{id}/verify-hash/ → verify SHA-256 integrity."""
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
    """GET /api/ingestion/sync-logs/ → Wazuh sync history."""
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
        for event in events[:500]:  # cap at 500 per call
            ingest_suricata_event.delay(tenant_id, event)
            queued += 1

        return Response(
            {"queued": queued, "message": f"{queued} Suricata events queued for ingestion."},
            status=status.HTTP_202_ACCEPTED,
        )


class WazuhSyncTriggerView(generics.GenericAPIView):
    """POST /api/ingestion/wazuh/sync/ → manually trigger Wazuh alert ingestion."""
    permission_classes = [permissions.IsAuthenticated, IsSysAdmin]

    def post(self, request):
        from .tasks import sync_wazuh_alerts
        tenant_id = str(request.user.tenant_id)
        task = sync_wazuh_alerts.delay(tenant_id)
        return Response(
            {"message": "Wazuh sync task queued.", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED,
        )
