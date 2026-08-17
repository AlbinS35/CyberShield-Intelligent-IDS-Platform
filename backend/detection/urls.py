"""
Detection URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AlertViewSet, IncidentViewSet, PlaybookViewSet,
    PlaybookExecutionViewSet, IPBlocklistViewSet, MLModelStatsView,
    ComplianceReportViewSet,
)

router = DefaultRouter()
router.register("alerts", AlertViewSet, basename="alerts")
router.register("incidents", IncidentViewSet, basename="incidents")
router.register("playbooks", PlaybookViewSet, basename="playbooks")
router.register("executions", PlaybookExecutionViewSet, basename="executions")
router.register("blocklist", IPBlocklistViewSet, basename="blocklist")
router.register("compliance-reports", ComplianceReportViewSet, basename="compliance-reports")

urlpatterns = [
    path("", include(router.urls)),
    # GET /api/detection/ml/stats/
    path("ml/stats/", MLModelStatsView.as_view(), name="ml-stats"),
]
