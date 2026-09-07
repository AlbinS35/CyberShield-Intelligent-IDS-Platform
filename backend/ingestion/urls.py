"""
Ingestion URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NetworkEventViewSet, WazuhSyncLogViewSet,
    WazuhSyncTriggerView, SuricataIngestView,
    IngestionStatusView,
)

router = DefaultRouter()
router.register("network-events", NetworkEventViewSet, basename="network-events")
router.register("sync-logs", WazuhSyncLogViewSet, basename="wazuh-sync-logs")

urlpatterns = [
    path("", include(router.urls)),
    # POST /api/ingestion/wazuh/sync/ → manually trigger Wazuh sync
    path("wazuh/sync/", WazuhSyncTriggerView.as_view(), name="wazuh-sync-trigger"),
    # POST /api/ingestion/suricata/ → Suricata watcher event ingestion
    path("suricata/", SuricataIngestView.as_view(), name="suricata-ingest"),
    # GET  /api/ingestion/status/   → live ingestion pipeline health report
    path("status/", IngestionStatusView.as_view(), name="ingestion-status"),
]
