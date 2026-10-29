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
        tenant = getattr(self.request.user, "tenant", None)
        qs = ForensicCase.objects.select_related("lead_investigator", "related_incident")
        if tenant:
            return qs.filter(tenant=tenant)
        return qs.all()

    def perform_create(self, serializer):
        tenant = getattr(self.request.user, "tenant", None)
        if not tenant:
            from authentication.models import Tenant
            tenant = Tenant.objects.first()
        case = serializer.save(tenant=tenant, lead_investigator=self.request.user)
        self._auto_populate_timeline(case)

    def _auto_populate_timeline(self, case):
        """
        Auto-populates chronological timeline events for a case if none exist.
        Derives initial detection with SHA-256 seal, alert escalation,
        active containment actions, and case vault opening from related incident.
        """
        if CaseTimeline.objects.filter(case=case).exists():
            return

        from django.utils import timezone
        from datetime import timedelta
        from detection.models import IPBlocklist

        created_events = []
        user = getattr(self.request, "user", None) or case.lead_investigator

        if case.related_incident:
            inc = case.related_incident
            alerts = inc.alerts.all().order_by("created_at")

            if alerts.exists():
                for alert in alerts:
                    # 1. Threat Detection & Canonical SHA-256 Ingestion Seal
                    attack_type = alert.attack_type or "THREAT"
                    cat = CaseTimeline.EventCategory.DETECTION
                    if attack_type in ["R2L", "PROBE"]:
                        cat = CaseTimeline.EventCategory.INITIAL_ACCESS
                    elif attack_type == "U2R":
                        cat = CaseTimeline.EventCategory.PRIVILEGE_ESCALATION
                    elif attack_type == "DOS":
                        cat = CaseTimeline.EventCategory.IMPACT

                    net_ev = alert.network_event
                    hash_preview = f" (SHA-256 seal: {net_ev.log_hash[:16]}...)" if (net_ev and net_ev.log_hash) else ""

                    t1 = (net_ev.event_timestamp if (net_ev and net_ev.event_timestamp) else alert.created_at) or timezone.now()
                    created_events.append(CaseTimeline(
                        case=case,
                        category=cat,
                        title=f"Threat Ingested & Cryptographically Sealed: {alert.title}",
                        description=(
                            f"Suspicious {attack_type} telemetry detected with {alert.severity} severity. "
                            f"Canonical JSON payload immutable and SHA-256 hash-sealed at ingestion{hash_preview}."
                        ),
                        source_ip=alert.source_ip or (net_ev.source_ip if net_ev else None),
                        target_ip=net_ev.destination_ip if net_ev else None,
                        source_system=net_ev.event_source if (net_ev and net_ev.event_source) else "CyberShield IDS",
                        network_event=net_ev,
                        event_time=t1 - timedelta(minutes=2),
                        recorded_by=user,
                    ))

                    # 2. SOC Analyst Alert Escalation
                    created_events.append(CaseTimeline(
                        case=case,
                        category=CaseTimeline.EventCategory.DETECTION,
                        title=f"Alert Escalated: {alert.title}",
                        description=f"SOC Analyst verified telemetry signature and escalated alert into Incident '{inc.title}'.",
                        source_ip=alert.source_ip,
                        target_ip=net_ev.destination_ip if net_ev else None,
                        source_system="SOC Command Center",
                        network_event=net_ev,
                        event_time=alert.created_at or (t1 - timedelta(minutes=1)),
                        recorded_by=user,
                    ))

                    # Check for active blocks on this IP
                    if alert.source_ip:
                        block = IPBlocklist.objects.filter(tenant=case.tenant, ip_address=alert.source_ip).first()
                        if block:
                            created_events.append(CaseTimeline(
                                case=case,
                                category=CaseTimeline.EventCategory.RESPONSE,
                                title=f"Automated Firewall Containment: Blocked {alert.source_ip}",
                                description=f"Containment playbook triggered: inbound/outbound packets to {alert.source_ip} dropped.",
                                source_ip=alert.source_ip,
                                target_ip=net_ev.destination_ip if net_ev else None,
                                source_system="CyberShield IPS",
                                event_time=block.blocked_at if block.blocked_at else (alert.created_at + timedelta(seconds=12)),
                                recorded_by=user,
                            ))

            # 3. Incident Referral / Case Vault Opened
            first_ip = None
            if alerts.exists():
                first_ip = alerts.first().source_ip
            elif case.affected_systems and len(case.affected_systems) > 0:
                first_ip = str(case.affected_systems[0])

            created_events.append(CaseTimeline(
                case=case,
                category=CaseTimeline.EventCategory.RESPONSE,
                title=f"Case Vault Opened: {case.title}",
                description=(
                    f"Incident referred to Digital Forensics Vault. Case #{case.case_number} "
                    f"assigned for forensic chain-of-custody tracking under legal hold."
                ),
                source_ip=first_ip,
                source_system="Forensic Vault",
                event_time=case.created_at or timezone.now(),
                recorded_by=user,
            ))
        else:
            # Case opened without linked incident
            first_ip = str(case.affected_systems[0]) if (case.affected_systems and len(case.affected_systems) > 0) else None
            created_events.append(CaseTimeline(
                case=case,
                category=CaseTimeline.EventCategory.DETECTION,
                title=f"Forensic Investigation Initiated: {case.title}",
                description=case.description or f"Forensic investigation initiated under case #{case.case_number}.",
                source_ip=first_ip,
                source_system="Forensic Vault",
                event_time=case.created_at or timezone.now(),
                recorded_by=user,
            ))

        if created_events:
            CaseTimeline.objects.bulk_create(created_events)

    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request, pk=None):
        """GET /api/forensics/cases/{id}/timeline/ → chronological attack timeline."""
        case = self.get_object()
        events = CaseTimeline.objects.filter(case=case).order_by("event_time")
        if not events.exists():
            self._auto_populate_timeline(case)
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
        from django.utils import timezone
        event_time = self.request.data.get("event_time") or timezone.now()
        serializer.save(recorded_by=self.request.user, event_time=event_time)
