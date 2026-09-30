"""
Test Suite 3 — Detection Module
Tests: Alert model CRUD, severity/status choices, ML helper functions,
       feature vector validation, alert API endpoints, and RBAC enforcement.

Week 11-12 Scrum Register Requirement:
  "Software testing with Automation Tools & Testing Report"
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from authentication.models import Tenant, User
from ingestion.models import NetworkEvent
from ingestion.utils import generate_log_hash
from detection.models import Alert, Incident, IPBlocklist
from detection.helpers import (
    resolve_severity,
    should_auto_block,
    build_alert_title,
    get_attack_description,
)
from detection.ml_validators import validate_feature_vector, FeatureValidationError


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_tenant():
    return Tenant.objects.create(name="Detection Org", slug="detection-org")

def make_user(tenant, role=User.Role.ANALYST, email="det_analyst@test.org"):
    return User.objects.create_user(
        email=email, password="TestPass123!",
        first_name="Det", last_name="User",
        role=role, tenant=tenant,
    )

def make_network_event(tenant):
    raw = {"protocol": "tcp", "src_bytes": 500, "duration": 0}
    return NetworkEvent.objects.create(
        tenant=tenant,
        source_ip="192.168.1.50",
        destination_ip="10.0.0.1",
        protocol=NetworkEvent.Protocol.TCP,
        raw_data=raw,
        log_hash=generate_log_hash(raw),
        event_source=NetworkEvent.Source.MANUAL,
        ml_classification="DOS",
        ml_confidence=0.92,
        is_threat=True,
    )

def make_alert(tenant, user, network_event=None, severity=Alert.Severity.HIGH, attack_type=Alert.AttackType.DOS):
    return Alert.objects.create(
        tenant=tenant,
        title="DoS Attack Detected — 192.168.1.50 → 10.0.0.1",
        description="High-volume SYN flood detected.",
        severity=severity,
        attack_type=attack_type,
        source_ip="192.168.1.50",
        destination_ip="10.0.0.1",
        ml_confidence=0.92,
        network_event=network_event,
    )


# ─── Model Tests ─────────────────────────────────────────────────────────────

class AlertModelTest(TestCase):
    """Unit tests for the Alert model fields, choices, and defaults."""

    def setUp(self):
        self.tenant = make_tenant()
        self.user = make_user(self.tenant)
        self.event = make_network_event(self.tenant)
        self.alert = make_alert(self.tenant, self.user, self.event)

    def test_alert_created_with_correct_fields(self):
        """Alert should be created and persist all fields correctly."""
        self.assertEqual(self.alert.title, "DoS Attack Detected — 192.168.1.50 → 10.0.0.1")
        self.assertEqual(self.alert.severity, "HIGH")
        self.assertEqual(self.alert.attack_type, "DOS")
        self.assertEqual(self.alert.status, Alert.Status.NEW)  # default

    def test_alert_uuid_primary_key(self):
        """Alert PK must be a UUID."""
        self.assertEqual(len(str(self.alert.pk)), 36)

    def test_alert_links_to_network_event(self):
        """Alert should be linked to its triggering NetworkEvent."""
        self.assertEqual(self.alert.network_event, self.event)

    def test_alert_default_status_is_new(self):
        """Newly created alert should have status=NEW."""
        self.assertEqual(self.alert.status, "NEW")

    def test_alert_playbook_gated_default_false(self):
        """playbook_gated should default to False."""
        self.assertFalse(self.alert.playbook_gated)

    def test_alert_str_includes_severity_and_title(self):
        """__str__ should include severity and title."""
        s = str(self.alert)
        self.assertIn("HIGH", s)
        self.assertIn("DoS Attack", s)

    def test_alert_tenant_scoping(self):
        """Alert should be associated with the correct tenant."""
        self.assertEqual(self.alert.tenant.name, "Detection Org")

    def test_alert_severity_choices_are_valid(self):
        """All defined severity choices should be in the valid set."""
        valid = {c[0] for c in Alert.Severity.choices}
        self.assertIn("CRITICAL", valid)
        self.assertIn("HIGH", valid)
        self.assertIn("MEDIUM", valid)
        self.assertIn("LOW", valid)
        self.assertIn("INFO", valid)

    def test_alert_attack_type_choices_are_valid(self):
        """All attack type choices should be correctly defined."""
        valid = {c[0] for c in Alert.AttackType.choices}
        self.assertIn("DOS", valid)
        self.assertIn("PROBE", valid)
        self.assertIn("R2L", valid)
        self.assertIn("U2R", valid)
        self.assertIn("NORMAL", valid)
        self.assertIn("UNKNOWN", valid)


class IncidentModelTest(TestCase):
    """Unit tests for the Incident model and alert grouping."""

    def setUp(self):
        self.tenant = make_tenant()
        self.user = make_user(self.tenant)
        self.alert = make_alert(self.tenant, self.user)
        self.incident = Incident.objects.create(
            tenant=self.tenant,
            title="Sustained DoS Campaign",
            severity=Alert.Severity.CRITICAL,
            lead_analyst=self.user,
        )

    def test_incident_created_with_open_status(self):
        """New incident should default to OPEN status."""
        self.assertEqual(self.incident.status, "OPEN")

    def test_incident_can_add_alert(self):
        """Incident should accept linked alerts via ManyToManyField."""
        self.incident.alerts.add(self.alert)
        self.assertIn(self.alert, self.incident.alerts.all())

    def test_incident_str_contains_title(self):
        """Incident __str__ should contain the title."""
        self.assertIn("Sustained DoS Campaign", str(self.incident))


# ─── Helper Function Tests ────────────────────────────────────────────────────

class SeverityHelperTest(TestCase):
    """Unit tests for resolve_severity() and should_auto_block() helpers."""

    def test_normal_traffic_resolves_to_info(self):
        """NORMAL classification should always resolve to INFO severity."""
        self.assertEqual(resolve_severity("NORMAL", 0.99), "INFO")

    def test_dos_high_confidence_resolves_to_critical(self):
        """DoS with high confidence should resolve to CRITICAL."""
        self.assertEqual(resolve_severity("DOS", 0.95), "CRITICAL")

    def test_probe_resolves_to_medium(self):
        """PROBE classification should resolve to MEDIUM severity."""
        self.assertEqual(resolve_severity("PROBE", 0.90), "MEDIUM")

    def test_r2l_resolves_to_high(self):
        """R2L classification should resolve to HIGH severity."""
        self.assertEqual(resolve_severity("R2L", 0.88), "HIGH")

    def test_u2r_resolves_to_critical(self):
        """U2R privilege escalation should resolve to CRITICAL."""
        self.assertEqual(resolve_severity("U2R", 0.91), "CRITICAL")

    def test_low_confidence_downgrades_severity_to_low(self):
        """Any attack type with confidence < 0.60 should be downgraded to LOW."""
        self.assertEqual(resolve_severity("DOS", 0.55), "LOW")
        self.assertEqual(resolve_severity("U2R", 0.40), "LOW")

    def test_auto_block_triggers_for_high_confidence_critical(self):
        """should_auto_block must return True for DoS with confidence >= 0.85."""
        self.assertTrue(should_auto_block("DOS", 0.92))
        self.assertTrue(should_auto_block("U2R", 0.87))

    def test_auto_block_rejected_for_low_confidence(self):
        """should_auto_block must return False when confidence is below 0.85."""
        self.assertFalse(should_auto_block("DOS", 0.80))
        self.assertFalse(should_auto_block("U2R", 0.70))

    def test_auto_block_rejected_for_probe_medium(self):
        """PROBE resolves to MEDIUM — should NOT trigger auto-block."""
        self.assertFalse(should_auto_block("PROBE", 0.95))

    def test_auto_block_rejected_for_normal_traffic(self):
        """NORMAL traffic should never trigger auto-block."""
        self.assertFalse(should_auto_block("NORMAL", 0.99))


class AlertTitleBuilderTest(TestCase):
    """Unit tests for the build_alert_title() helper."""

    def test_dos_title_format(self):
        """DoS alert title should contain 'Denial of Service' text."""
        title = build_alert_title("DOS", "192.168.1.10", "10.0.0.1")
        self.assertIn("Denial of Service", title)
        self.assertIn("192.168.1.10", title)
        self.assertIn("10.0.0.1", title)

    def test_probe_title_format(self):
        """Probe alert title should mention 'Reconnaissance'."""
        title = build_alert_title("PROBE", "10.0.0.5", "172.16.0.1")
        self.assertIn("Reconnaissance", title)

    def test_none_ips_handled_gracefully(self):
        """None IPs should be replaced with 'Unknown' in the title."""
        title = build_alert_title("R2L", None, None)
        self.assertIn("Unknown", title)

    def test_attack_description_not_empty(self):
        """get_attack_description should return a non-empty string for all types."""
        for attack_type in ["NORMAL", "DOS", "PROBE", "R2L", "U2R", "UNKNOWN"]:
            desc = get_attack_description(attack_type)
            self.assertIsInstance(desc, str)
            self.assertGreater(len(desc), 10)


# ─── ML Validator Tests ───────────────────────────────────────────────────────

class MLFeatureValidatorTest(TestCase):
    """Unit tests for the ML pre-inference feature vector validator."""

    def _full_feature_vector(self, overrides=None):
        """Build a minimal valid 41-feature dict for testing."""
        from ingestion.constants import NSL_KDD_FEATURES
        vec = {f: 0.0 for f in NSL_KDD_FEATURES}
        if overrides:
            vec.update(overrides)
        return vec

    def test_valid_vector_passes_validation(self):
        """A correctly formed 41-feature dict should pass without error."""
        vec = self._full_feature_vector()
        result = validate_feature_vector(vec)
        self.assertEqual(len(result), 41)

    def test_missing_feature_defaults_to_zero(self):
        """A feature that is absent should be filled with 0, not raise an error."""
        from ingestion.constants import NSL_KDD_FEATURES
        vec = {f: 1.0 for f in NSL_KDD_FEATURES[:-1]}  # missing last feature
        result = validate_feature_vector(vec)
        self.assertEqual(result[NSL_KDD_FEATURES[-1]], 0.0)

    def test_rate_feature_clamped_to_one(self):
        """Rate features exceeding 1.0 must be clamped down to 1.0."""
        vec = self._full_feature_vector({"serror_rate": 5.0})
        result = validate_feature_vector(vec)
        self.assertEqual(result["serror_rate"], 1.0)

    def test_rate_feature_clamped_to_zero(self):
        """Rate features below 0.0 must be clamped up to 0.0."""
        vec = self._full_feature_vector({"rerror_rate": -0.5})
        result = validate_feature_vector(vec)
        self.assertEqual(result["rerror_rate"], 0.0)

    def test_non_negative_feature_clipped(self):
        """Non-negative features with negative values must be clipped to 0."""
        vec = self._full_feature_vector({"src_bytes": -100})
        result = validate_feature_vector(vec)
        self.assertEqual(result["src_bytes"], 0.0)

    def test_non_numeric_feature_raises_error(self):
        """A non-numeric feature value should raise FeatureValidationError."""
        vec = self._full_feature_vector({"duration": "invalid_string"})
        with self.assertRaises(FeatureValidationError):
            validate_feature_vector(vec)

    def test_output_length_always_41(self):
        """Validated output must always have exactly 41 keys."""
        vec = self._full_feature_vector()
        result = validate_feature_vector(vec)
        self.assertEqual(len(result), 41)


# ─── Detection API Tests ──────────────────────────────────────────────────────

class AlertAPITest(TestCase):
    """
    Integration tests for the Alert API endpoints.
    GET  /api/detection/alerts/
    GET  /api/detection/alerts/{id}/
    POST /api/detection/alerts/{id}/escalate/
    """

    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant()
        self.user = make_user(self.tenant)
        self.client.force_authenticate(user=self.user)
        self.alert = make_alert(self.tenant, self.user)

    def test_list_alerts_returns_200(self):
        """Authenticated analyst should get 200 from alert list endpoint."""
        response = self.client.get("/api/detection/alerts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_alert_list_is_tenant_scoped(self):
        """Alerts from another tenant must not appear in the response."""
        other_tenant = Tenant.objects.create(name="Other Corp", slug="other-corp")
        other_user = User.objects.create_user(
            email="other@other.org", password="pass", tenant=other_tenant,
            first_name="O", last_name="T",
        )
        Alert.objects.create(
            tenant=other_tenant,
            title="Other Tenant Alert",
            severity=Alert.Severity.LOW,
            attack_type=Alert.AttackType.PROBE,
            source_ip="1.2.3.4",
            destination_ip="5.6.7.8",
        )
        response = self.client.get("/api/detection/alerts/")
        titles = [
            item["title"]
            for item in response.data.get("results", response.data)
        ]
        self.assertNotIn("Other Tenant Alert", titles)

    def test_alert_detail_returns_correct_data(self):
        """GET /alerts/{id}/ should return the correct alert."""
        response = self.client.get(f"/api/detection/alerts/{self.alert.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.alert.id))
        self.assertEqual(response.data["attack_type"], "DOS")

    def test_unauthenticated_cannot_list_alerts(self):
        """Unauthenticated user should receive 401 on alert list."""
        unauth = APIClient()
        response = unauth.get("/api/detection/alerts/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_escalate_alert_creates_incident(self):
        """POST /alerts/{id}/escalate/ should create a linked Incident."""
        response = self.client.post(
            f"/api/detection/alerts/{self.alert.id}/escalate/",
            {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)  # Incident ID returned
        # Alert status should now be ESCALATED
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.ESCALATED)

    def test_filter_alerts_by_severity(self):
        """?severity=HIGH filter should return only HIGH severity alerts."""
        Alert.objects.create(
            tenant=self.tenant, title="Low Alert",
            severity=Alert.Severity.LOW,
            attack_type=Alert.AttackType.PROBE,
        )
        response = self.client.get("/api/detection/alerts/?severity=HIGH")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        for item in results:
            self.assertEqual(item["severity"], "HIGH")
