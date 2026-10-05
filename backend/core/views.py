"""
CyberShield Core Views
======================
REST API endpoints for the normalized tbl_ schema.

Endpoint Map:
    POST   /api/core/auth/login/          → JWT token from tbl_login credentials
    GET    /api/core/organizations/        → Organization list
    GET    /api/core/users/                → CoreUser list (RBAC-scoped)

    GET    /api/telemetry/                 → Network event log
    POST   /api/telemetry/                 → Ingest new telemetry + SHA-256 seal
    GET    /api/telemetry/<id>/            → Event detail + integrity status
    GET    /api/telemetry/<id>/verify/     → Re-verify SHA-256 seal

    GET    /api/forensics/cases/           → Forensic case vault (all cases)
    POST   /api/forensics/cases/           → Open new forensic case
    GET    /api/forensics/cases/<id>/      → Case detail
    PUT    /api/forensics/cases/<id>/      → Update case status/title

    GET    /api/assets/                    → Infrastructure asset register
    POST   /api/assets/                    → Register new asset
    GET    /api/assets/<id>/               → Asset detail
    PUT    /api/assets/<id>/               → Update asset status/metadata

    GET    /api/containment/               → Containment action log
    POST   /api/containment/               → Log new containment action
    GET    /api/containment/<id>/          → Action detail
"""

from rest_framework import generics, status, filters, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    Organization,
    CoreUser,
    Login,
    NetworkAsset,
    ForensicCase,
    NetworkEvent,
    ContainmentAction,
)
from .serializers import (
    OrganizationSerializer,
    CoreUserSerializer,
    LoginSerializer,
    LoginCreateSerializer,
    CoreLoginTokenSerializer,
    NetworkAssetSerializer,
    ForensicCaseSerializer,
    NetworkEventSerializer,
    NetworkEventIngestSerializer,
    ContainmentActionSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# JWT Login — tbl_login authentication
# ─────────────────────────────────────────────────────────────────────────────

class CoreLoginView(APIView):
    """
    POST /api/core/auth/login/
    Authenticate against tbl_login credentials.
    Returns JWT access + refresh tokens with embedded role and org context.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class   = CoreLoginTokenSerializer  # for Swagger schema

    @extend_schema(
        request=CoreLoginTokenSerializer,
        responses={200: CoreLoginTokenSerializer},
        summary="Login (tbl_login credentials → JWT)",
        description=(
            "Authenticate with email + password from tbl_login. "
            "Returns access/refresh JWT tokens embedding role, user_id, and org context. "
            "Use the access token as 'Bearer <token>' in subsequent requests."
        ),
    )
    def post(self, request):
        serializer = CoreLoginTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Organization
# ─────────────────────────────────────────────────────────────────────────────

class OrganizationListView(generics.ListCreateAPIView):
    """
    GET  /api/core/organizations/  → list all organizations
    POST /api/core/organizations/  → create a new organization
    """
    serializer_class   = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["org_name", "domain_name"]
    ordering_fields    = ["org_name", "created_at"]
    ordering           = ["org_name"]

    def get_queryset(self):
        if hasattr(self.request.user, "tenant") and self.request.user.tenant:
            tenant = self.request.user.tenant
            # Auto-create the core Organization if it doesn't exist so legacy endpoints work
            Organization.objects.get_or_create(
                org_name=tenant.name,
                defaults={"domain_name": f"{tenant.slug}.local"}
            )
            return Organization.objects.filter(org_name=tenant.name)
        return Organization.objects.none()


class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/core/organizations/<id>/
    PUT    /api/core/organizations/<id>/
    DELETE /api/core/organizations/<id>/
    """
    serializer_class   = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = Organization.objects.all()
    lookup_field       = "org_id"


# ─────────────────────────────────────────────────────────────────────────────
# CoreUser
# ─────────────────────────────────────────────────────────────────────────────

class CoreUserListView(generics.ListCreateAPIView):
    """
    GET  /api/core/users/  → list users
    POST /api/core/users/  → create a new CoreUser
    """
    serializer_class   = CoreUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ["org"]
    search_fields      = ["full_name", "phone_no"]
    queryset           = CoreUser.objects.select_related("org").all()


class CoreUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = CoreUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = CoreUser.objects.select_related("org").all()
    lookup_field       = "user_id"


# ─────────────────────────────────────────────────────────────────────────────
# Login credentials
# ─────────────────────────────────────────────────────────────────────────────

class LoginListView(generics.ListCreateAPIView):
    """
    GET  /api/core/logins/  → list all user records (filtered by tenant)
    POST /api/core/logins/  → create login credentials for an existing User
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ["email", "role"]

    def get_queryset(self):
        from authentication.models import User as AuthUser
        if hasattr(self.request.user, 'tenant') and self.request.user.tenant:
            return AuthUser.objects.filter(tenant=self.request.user.tenant)
        # Fallback if no tenant
        return AuthUser.objects.none()

    def get_serializer_class(self):
        from .serializers import AuthUserLoginSerializer
        # We can just reuse AuthUserLoginSerializer for both for now to fix the view
        # or keep LoginCreateSerializer if they still rely on tbl_login POST.
        # But for now, just return AuthUserLoginSerializer for GET.
        return AuthUserLoginSerializer


# ─────────────────────────────────────────────────────────────────────────────
# Telemetry — GET/POST /api/telemetry/
# ─────────────────────────────────────────────────────────────────────────────

class TelemetryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/telemetry/  → paginated network event log, filterable by threat class
    POST /api/telemetry/  → ingest new telemetry event; sha256_hash auto-sealed server-side
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["threat_classification", "asset"]
    search_fields      = ["source_ip", "destination_ip", "threat_classification"]
    ordering_fields    = ["timestamp", "confidence_score"]
    ordering           = ["-timestamp"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return NetworkEventIngestSerializer
        return NetworkEventSerializer

    def get_queryset(self):
        return NetworkEvent.objects.select_related("asset__org").all()

    def create(self, request, *args, **kwargs):
        serializer = NetworkEventIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()            # SHA-256 auto-sealed in model.save()
        out   = NetworkEventSerializer(event)
        return Response(out.data, status=status.HTTP_201_CREATED)


class TelemetryDetailView(generics.RetrieveAPIView):
    """
    GET /api/telemetry/<event_id>/  → event detail with live integrity flag
    """
    serializer_class   = NetworkEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = NetworkEvent.objects.select_related("asset").all()
    lookup_field       = "event_id"


class TelemetryVerifyView(APIView):
    """
    GET /api/telemetry/<event_id>/verify/
    Re-compute SHA-256 from stored raw_telemetry and compare with recorded seal.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Verify SHA-256 tamper seal",
        description="Re-computes the SHA-256 hash of the stored raw_telemetry and checks it against the recorded seal.",
    )
    def get(self, request, event_id):
        try:
            event = NetworkEvent.objects.get(event_id=event_id)
        except NetworkEvent.DoesNotExist:
            return Response(
                {"detail": "Network event not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        integrity_valid = event.verify_integrity()
        return Response({
            "event_id":        event.event_id,
            "stored_hash":     event.sha256_hash,
            "integrity_valid": integrity_valid,
            "threat":          event.threat_classification,
            "confidence":      str(event.confidence_score),
            "verified_at":     event.timestamp.isoformat(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# Forensic Cases — GET/POST/PUT /api/forensics/cases/
# ─────────────────────────────────────────────────────────────────────────────

class ForensicCaseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/forensics/cases/  → forensic case vault (filterable by status)
    POST /api/forensics/cases/  → open a new forensic investigation case
    """
    serializer_class   = ForensicCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["status"]
    search_fields      = ["case_title", "description"]
    ordering_fields    = ["created_at", "status"]
    ordering           = ["-created_at"]
    queryset           = ForensicCase.objects.select_related("created_by").all()


class ForensicCaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/forensics/cases/<case_id>/  → case detail
    PUT    /api/forensics/cases/<case_id>/  → update case (status, title, description)
    PATCH  /api/forensics/cases/<case_id>/  → partial update
    DELETE /api/forensics/cases/<case_id>/  → delete (caution: irreversible)
    """
    serializer_class   = ForensicCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = ForensicCase.objects.select_related("created_by").all()
    lookup_field       = "case_id"


# ─────────────────────────────────────────────────────────────────────────────
# Assets — GET/POST/PUT /api/assets/
# ─────────────────────────────────────────────────────────────────────────────

class AssetListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/assets/  → infrastructure asset register (filterable by org, status)
    POST /api/assets/  → register a new monitored asset
    """
    serializer_class   = NetworkAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["org", "status", "os_type"]
    search_fields      = ["asset_name", "ip_address", "wazuh_agent_id"]
    ordering_fields    = ["asset_name", "ip_address", "status"]
    ordering           = ["asset_name"]

    def get_queryset(self):
        if hasattr(self.request.user, "tenant") and self.request.user.tenant:
            return NetworkAsset.objects.select_related("org").filter(org__org_name=self.request.user.tenant.name)
        return NetworkAsset.objects.none()


class AssetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/assets/<asset_id>/  → asset detail
    PUT    /api/assets/<asset_id>/  → update asset metadata/status
    PATCH  /api/assets/<asset_id>/  → partial update
    """
    serializer_class   = NetworkAssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = NetworkAsset.objects.select_related("org").all()
    lookup_field       = "asset_id"


# ─────────────────────────────────────────────────────────────────────────────
# Containment — GET/POST /api/containment/
# ─────────────────────────────────────────────────────────────────────────────

class ContainmentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/containment/  → paginated containment action log
    POST /api/containment/  → log a new automated playbook containment action
    """
    serializer_class   = ContainmentActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ["execution_status", "action_type", "event"]
    search_fields      = ["target_ip", "action_type"]
    ordering_fields    = ["executed_at", "execution_status"]
    ordering           = ["-executed_at"]
    queryset           = ContainmentAction.objects.select_related("event__asset").all()


class ContainmentDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/containment/<action_id>/  → action detail
    PATCH /api/containment/<action_id>/  → update execution_status (e.g., PENDING → SUCCESS)
    """
    serializer_class   = ContainmentActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset           = ContainmentAction.objects.select_related("event").all()
    lookup_field       = "action_id"
