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
