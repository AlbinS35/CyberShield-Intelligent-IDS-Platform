"""
Forensics URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForensicCaseViewSet, EvidenceViewSet, CaseTimelineViewSet

router = DefaultRouter()
router.register("cases", ForensicCaseViewSet, basename="cases")
router.register("evidence", EvidenceViewSet, basename="evidence")
router.register("timeline", CaseTimelineViewSet, basename="timeline")

urlpatterns = [
    path("", include(router.urls)),
]
