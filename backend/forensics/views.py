"""
Forensics Views
Case management, evidence upload with SHA-256 hashing,
timeline reconstruction, and chain-of-custody tracking.
"""

from rest_framework import viewsets, generics, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ForensicCase, Evidence, CaseTimeline, ChainOfCustody
from .serializers import (
    ForensicCaseSerializer, EvidenceSerializer, EvidenceUploadSerializer,
    CaseTimelineSerializer, ChainOfCustodySerializer,
)
from authentication.permissions import IsInvestigator, IsAnalystOrAbove


class ForensicCaseViewSet(viewsets.ModelViewSet):
    """
    CRUD for forensic investigation cases.
    GET    /api/forensics/cases/
    POST   /api/forensics/cases/
    GET    /api/forensics/cases/{id}/
    PATCH  /api/forensics/cases/{id}/
    GET    /api/forensics/cases/{id}/timeline/   → chronological event list
    GET    /api/forensics/cases/{id}/evidence/   → evidence list for case
    """
    serializer_class = ForensicCaseSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return ForensicCase.objects.filter(tenant=self.request.user.tenant).select_related(
            "lead_investigator", "related_incident"
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, lead_investigator=self.request.user)

    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request, pk=None):
        """GET /api/forensics/cases/{id}/timeline/ → chronological attack timeline."""
        case = self.get_object()
        events = CaseTimeline.objects.filter(case=case).order_by("event_time")
        serializer = CaseTimelineSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="evidence")
    def evidence_list(self, request, pk=None):
        """GET /api/forensics/cases/{id}/evidence/ → all evidence for this case."""
        case = self.get_object()
        evidence = Evidence.objects.filter(case=case)
        serializer = EvidenceSerializer(evidence, many=True)
        return Response(serializer.data)


class EvidenceViewSet(viewsets.ModelViewSet):
    """
    POST  /api/forensics/evidence/              → upload evidence file
    GET   /api/forensics/evidence/{id}/verify/  → SHA-256 integrity check
    GET   /api/forensics/evidence/{id}/custody/ → chain-of-custody trail
    """
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_serializer_class(self):
        if self.action == "create":
            return EvidenceUploadSerializer
        return EvidenceSerializer

    def get_queryset(self):
        return Evidence.objects.filter(case__tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        """Compute SHA-256 hash on file upload before saving."""
        from ingestion.utils import generate_file_hash
        file_obj = self.request.FILES.get("file")
        sha256_hash = generate_file_hash(file_obj) if file_obj else ""
        evidence = serializer.save(
            uploaded_by=self.request.user,
            sha256_hash=sha256_hash,
            file_name=file_obj.name if file_obj else "",
            file_size_bytes=file_obj.size if file_obj else 0,
        )
        # Auto-record in chain of custody
        ChainOfCustody.objects.create(
            evidence=evidence,
            action=ChainOfCustody.Action.COLLECTED,
            performed_by=self.request.user,
            notes="Initial evidence upload via CyberShield platform.",
        )

    @action(detail=True, methods=["get"], url_path="verify")
    def verify_hash(self, request, pk=None):
        """GET /api/forensics/evidence/{id}/verify/ → recompute and compare SHA-256."""
        evidence = self.get_object()
        from ingestion.utils import generate_file_hash
        try:
            with evidence.file.open("rb") as f:
                computed_hash = generate_file_hash(f)
            is_valid = computed_hash == evidence.sha256_hash
            # Log hash verification in chain of custody
            ChainOfCustody.objects.create(
                evidence=evidence,
                action=ChainOfCustody.Action.HASHED,
                performed_by=request.user,
                notes=f"Hash verification: {'PASSED' if is_valid else 'FAILED'}",
            )
            return Response({
                "evidence_id": str(evidence.id),
                "file_name": evidence.file_name,
                "stored_hash": evidence.sha256_hash,
                "computed_hash": computed_hash,
                "integrity_valid": is_valid,
                "verified_by": request.user.get_full_name(),
            })
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"], url_path="custody")
    def custody_trail(self, request, pk=None):
        """GET /api/forensics/evidence/{id}/custody/ → chain-of-custody log."""
        evidence = self.get_object()
        custody = ChainOfCustody.objects.filter(evidence=evidence)
        serializer = ChainOfCustodySerializer(custody, many=True)
        return Response(serializer.data)


class CaseTimelineViewSet(viewsets.ModelViewSet):
    """Add/remove chronological events to a forensic case timeline."""
    serializer_class = CaseTimelineSerializer
    permission_classes = [permissions.IsAuthenticated, IsAnalystOrAbove]

    def get_queryset(self):
        return CaseTimeline.objects.filter(case__tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
