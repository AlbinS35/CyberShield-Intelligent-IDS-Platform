"""
CyberShield — Root URL Configuration
Maps all API endpoints, WebSocket routes, and documentation endpoints.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # ─── Django Admin ────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ─── Authentication & User Management ───────────────────────────────────
    path("api/auth/", include("authentication.urls")),

    # ─── Threat Ingestion & Alert Management ────────────────────────────────
    path("api/ingestion/", include("ingestion.urls")),

    # ─── AI/ML Detection & Incident Management ──────────────────────────────
    path("api/detection/", include("detection.urls")),

    # ─── Digital Forensics ──────────────────────────────────────────────────
    path("api/forensics/", include("forensics.urls")),

    # ─── OpenAPI Documentation ───────────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
