"""
Detection Views
Alert management, incident tracking, playbook execution, and ML stats.
"""

from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Alert, Incident, Playbook, PlaybookExecution, IPBlocklist
from .serializers import (
    AlertSerializer, AlertStatusUpdateSerializer, IncidentSerializer,
    PlaybookSerializer, PlaybookExecutionSerializer, IPBlocklistSerializer,
)
from authentication.permissions import IsAnalystOrAbove, IsSysAdmin, IsAnalyst


class AlertViewSet(viewsets.ModelViewSet):
    """
    GET    /api/detection/alerts/           → list alerts (tenant-scoped)
    GET    /api/detection/alerts/{id}/      → alert detail
    PATCH  /api/detection/alerts/{id}/      → update status / assign
    POST   /api/detection/alerts/{id}/escalate/ → escalate to incident
    POST   /api/detection/alerts/{id}/trigger-playbook/ → run playbook
    """
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["severity", "status", "attack_type", "assigned_to"]
    search_fields = ["title", "source_ip", "destination_ip", "affected_asset"]
    ordering_fields = ["created_at", "severity", "ml_confidence"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Alert.objects.filter(tenant=self.request.user.tenant).select_related(
            "assigned_to", "network_event"
        )

    def get_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return AlertStatusUpdateSerializer
        return AlertSerializer

    @action(detail=True, methods=["post"], url_path="escalate")
    def escalate(self, request, pk=None):
        """Create or join an Incident from this alert."""
        alert = self.get_object()
        incident_id = request.data.get("incident_id")
        if incident_id:
            incident = Incident.objects.get(id=incident_id, tenant=request.user.tenant)
        else:
            incident = Incident.objects.create(
                tenant=request.user.tenant,
                title=f"Incident: {alert.title}",
                severity=alert.severity,
                lead_analyst=request.user,
            )
        incident.alerts.add(alert)
        alert.status = Alert.Status.ESCALATED
        alert.save()
        return Response(IncidentSerializer(incident).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="trigger-playbook")
    def trigger_playbook(self, request, pk=None):
        """Manually trigger a playbook against this alert's source IP."""
        alert = self.get_object()
        playbook_id = request.data.get("playbook_id")
        dry_run = request.data.get("dry_run", False)
        if not playbook_id:
            return Response({"error": "playbook_id required."}, status=status.HTTP_400_BAD_REQUEST)
        from .tasks import execute_playbook
        task = execute_playbook.delay(playbook_id, str(alert.id), alert.source_ip, dry_run)
        return Response({"message": "Playbook queued.", "task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class IncidentViewSet(viewsets.ModelViewSet):
    """CRUD for security incidents."""
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return Incident.objects.filter(tenant=self.request.user.tenant).prefetch_related("alerts")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, lead_analyst=self.request.user)


class PlaybookViewSet(viewsets.ModelViewSet):
    """CRUD for response playbooks (SysAdmin only for write operations)."""
    serializer_class = PlaybookSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return Playbook.objects.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, created_by=self.request.user)


class PlaybookExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit trail of playbook executions."""
    serializer_class = PlaybookExecutionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return PlaybookExecution.objects.filter(
            playbook__tenant=self.request.user.tenant
        ).select_related("playbook", "alert")


class IPBlocklistViewSet(viewsets.ModelViewSet):
    """IP blocklist management."""
    serializer_class = IPBlocklistSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return IPBlocklist.objects.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, blocked_by=self.request.user)


class MLModelStatsView(generics.GenericAPIView):
    """GET /api/detection/ml/stats/ → model info and inference statistics."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .core_ml.inference import classifier
        from .models import MLInferenceLog
        import django.db.models as db_models

        if not classifier.is_loaded:
            classifier.load()

        stats = MLInferenceLog.objects.filter(
            network_event__tenant=request.user.tenant
        ).aggregate(
            total_inferences=db_models.Count("id"),
            avg_confidence=db_models.Avg("confidence"),
            avg_inference_ms=db_models.Avg("inference_time_ms"),
        )

        return Response({
            "model_info": classifier.get_model_info(),
            "tenant_stats": {
                "total_inferences": stats["total_inferences"] or 0,
                "avg_confidence": round(stats["avg_confidence"] or 0, 4),
                "avg_inference_time_ms": round(stats["avg_inference_ms"] or 0, 2),
            },
        })
