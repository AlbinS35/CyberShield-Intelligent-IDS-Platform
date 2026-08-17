"""
CyberShield Core URL Configuration
====================================
Wires all tbl_-schema REST endpoints.

Mounted in cybershield_core/urls.py under these prefixes:
    /api/core/...         → auth, org, user, login admin
    /api/telemetry/...    → network event ingestion & verification
    /api/forensics/...    → forensic case vault (merges with forensics app routes)
    /api/assets/...       → infrastructure asset register
    /api/containment/...  → automated playbook action log
"""

from django.urls import path
from .views import (
    # Auth
    CoreLoginView,
    # Org & User management
    OrganizationListView,
    OrganizationDetailView,
    CoreUserListView,
    CoreUserDetailView,
    LoginListView,
    # Telemetry
    TelemetryListCreateView,
    TelemetryDetailView,
    TelemetryVerifyView,
    # Forensics
    ForensicCaseListCreateView,
    ForensicCaseDetailView,
    # Assets
    AssetListCreateView,
    AssetDetailView,
    # Containment
    ContainmentListCreateView,
    ContainmentDetailView,
)

# ─── Core authentication & management ────────────────────────────────────────
core_urlpatterns = [
    path("auth/login/",            CoreLoginView.as_view(),           name="core-login"),
    path("organizations/",         OrganizationListView.as_view(),    name="org-list"),
    path("organizations/<int:org_id>/", OrganizationDetailView.as_view(), name="org-detail"),
    path("users/",                 CoreUserListView.as_view(),         name="core-user-list"),
    path("users/<uuid:user_id>/",  CoreUserDetailView.as_view(),       name="core-user-detail"),
    path("logins/",                LoginListView.as_view(),            name="login-list"),
]

# ─── Telemetry ingestion & verification ──────────────────────────────────────
telemetry_urlpatterns = [
    path("",                               TelemetryListCreateView.as_view(), name="telemetry-list"),
    path("<int:event_id>/",                TelemetryDetailView.as_view(),     name="telemetry-detail"),
    path("<int:event_id>/verify/",         TelemetryVerifyView.as_view(),     name="telemetry-verify"),
]

# ─── Forensic case vault ──────────────────────────────────────────────────────
forensic_case_urlpatterns = [
    path("cases/",                         ForensicCaseListCreateView.as_view(), name="core-case-list"),
    path("cases/<uuid:case_id>/",          ForensicCaseDetailView.as_view(),     name="core-case-detail"),
]

# ─── Infrastructure asset register ───────────────────────────────────────────
asset_urlpatterns = [
    path("",                               AssetListCreateView.as_view(), name="asset-list"),
    path("<int:asset_id>/",                AssetDetailView.as_view(),     name="asset-detail"),
]

# ─── Containment action log ───────────────────────────────────────────────────
containment_urlpatterns = [
    path("",                               ContainmentListCreateView.as_view(), name="containment-list"),
    path("<int:action_id>/",               ContainmentDetailView.as_view(),     name="containment-detail"),
]
