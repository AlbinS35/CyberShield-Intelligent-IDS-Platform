"""
CyberShield — Root URL Configuration
Maps all API endpoints, WebSocket routes, and documentation endpoints.
Includes normalized tbl_-schema routes from the core app.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseRedirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from core.urls import (
    core_urlpatterns,
    telemetry_urlpatterns,
    forensic_case_urlpatterns,
    asset_urlpatterns,
    containment_urlpatterns,
)

def api_root(_request):
    return HttpResponseRedirect("http://127.0.0.1:5173/")


def favicon(_request):
    return HttpResponse(status=204)


urlpatterns = [
    path("", api_root, name="api-root"),
    path("favicon.ico", favicon, name="favicon"),

    # ─── Django Admin ────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ─── Authentication & User Management ───────────────────────────────────
    path("api/auth/", include("authentication.urls")),

    # ─── Core App: tbl_-schema management console ────────────────────────────
    # POST /api/core/auth/login/       → JWT from tbl_login
    # GET  /api/core/organizations/    → Org list
    # GET  /api/core/users/            → CoreUser list
    # GET  /api/core/logins/           → Login credential list
    path("api/core/", include((core_urlpatterns, "core"), namespace="core")),

    # ─── Telemetry Ingestion ─────────────────────────────────────────────────
    # GET  /api/telemetry/             → paginated network event log
    # POST /api/telemetry/             → ingest event (SHA-256 auto-sealed)
    # GET  /api/telemetry/<id>/        → event detail
    # GET  /api/telemetry/<id>/verify/ → tamper-seal re-verification
    path("api/telemetry/", include((telemetry_urlpatterns, "telemetry"), namespace="telemetry")),

    # ─── Infrastructure Asset Register ───────────────────────────────────────
    # GET  /api/assets/                → asset register list
    # POST /api/assets/                → register new asset
    # GET  /api/assets/<id>/           → asset detail
    # PUT  /api/assets/<id>/           → update asset
    path("api/assets/", include((asset_urlpatterns, "assets"), namespace="assets")),

    # ─── Containment Action Log ───────────────────────────────────────────────
    # GET  /api/containment/           → playbook execution log
    # POST /api/containment/           → log new containment action
    path("api/containment/", include((containment_urlpatterns, "containment"), namespace="containment")),

    # ─── Forensics (core tbl_forensic_case + advanced forensics app) ─────────
    # Core normalized endpoints:
    #   GET/POST /api/forensics/cases/        → ForensicCase CRUD (tbl_forensic_case)
    #   GET/PUT  /api/forensics/cases/<id>/   → Case detail
    # path("api/forensics/", include((forensic_case_urlpatterns, "core-forensics"), namespace="core-forensics")),
    # Full forensics app (evidence, timelines, chain-of-custody):
    path("api/forensics/", include("forensics.urls")),

    # ─── Threat Ingestion & Alert Management ────────────────────────────────
    path("api/ingestion/", include("ingestion.urls")),

    # ─── AI/ML Detection & Incident Management ──────────────────────────────
    path("api/detection/", include("detection.urls")),

    # ─── OpenAPI Documentation ───────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/",  SpectacularRedocView.as_view(url_name="schema"),   name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
