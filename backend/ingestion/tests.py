"""
Test Suite 2 — Ingestion Module
Tests: NetworkEvent creation, SHA-256 tamper-seal, hash verification endpoint,
       WazuhSyncLog, and ingestion constants/feature list integrity.

Week 11-12 Scrum Register Requirement:
  "Software testing with Automation Tools & Testing Report"
"""

import hashlib
import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from authentication.models import Tenant, User
from ingestion.models import NetworkEvent, WazuhSyncLog
from ingestion.utils import generate_log_hash, verify_log_hash
from ingestion.constants import (
    NSL_KDD_FEATURES,
    ATTACK_SEVERITY_MAP,
    CONFIDENCE_GATE_AUTO_BLOCK,
    CONFIDENCE_GATE_ALERT_ONLY,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_tenant():
    return Tenant.objects.create(name="Ingestion Org", slug="ingestion-org")

def make_user(tenant, role=User.Role.ANALYST):
    return User.objects.create_user(
        email="ing_analyst@test.org",
        password="TestPass123!",
        first_name="Ingest",
        last_name="User",
        role=role,
        tenant=tenant,
    )

SAMPLE_RAW_DATA = {
    "duration": 0,
    "protocol_type": "tcp",
    "service": "http",
    "flag": "SF",
    "src_bytes": 232,
    "dst_bytes": 8153,
    "land": 0,
    "wrong_fragment": 0,
    "urgent": 0,
}


# ─── Test Classes ─────────────────────────────────────────────────────────────

class NetworkEventModelTest(TestCase):
    """Unit tests for the NetworkEvent model fields and SHA-256 hash sealing."""

    def setUp(self):
        self.tenant = make_tenant()
        raw = SAMPLE_RAW_DATA
        log_hash = generate_log_hash(raw)
        self.event = NetworkEvent.objects.create(
            tenant=self.tenant,
            source_ip="192.168.1.10",
            destination_ip="10.0.0.5",
            source_port=4321,
            destination_port=80,
            protocol=NetworkEvent.Protocol.TCP,
            bytes_sent=232,
            bytes_received=8153,
            raw_data=raw,
            log_hash=log_hash,
            event_source=NetworkEvent.Source.MANUAL,
        )

    def test_event_created_successfully(self):
        """NetworkEvent should be saved with all required fields."""
        self.assertEqual(self.event.source_ip, "192.168.1.10")
        self.assertEqual(self.event.destination_ip, "10.0.0.5")
        self.assertEqual(self.event.protocol, "TCP")
        self.assertEqual(self.event.tenant, self.tenant)

    def test_event_has_sha256_hash(self):
        """log_hash must be a 64-character SHA-256 hex string."""
        self.assertEqual(len(self.event.log_hash), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in self.event.log_hash))

    def test_event_uuid_primary_key(self):
        """Event primary key should be a UUID."""
        self.assertEqual(len(str(self.event.pk)), 36)

    def test_event_str_representation(self):
        """Event __str__ should include source and destination IPs."""
        s = str(self.event)
        self.assertIn("192.168.1.10", s)
        self.assertIn("10.0.0.5", s)

    def test_event_classification_defaults_to_empty(self):
        """ml_classification should be blank by default (before ML runs)."""
        self.assertEqual(self.event.ml_classification, "")
        self.assertIsNone(self.event.is_threat)


class HashIntegrityTest(TestCase):
    """Unit tests for the SHA-256 tamper-detection hash utility."""

    def test_generate_log_hash_returns_64_char_string(self):
        """generate_log_hash must return a 64-character hex digest."""
        raw_data = {"key": "value", "count": 42}
        result = generate_log_hash(raw_data)
        self.assertEqual(len(result), 64)

    def test_hash_is_deterministic(self):
        """Same raw_data must always produce the same hash."""
        raw_data = {"protocol": "tcp", "src_bytes": 500}
        h1 = generate_log_hash(raw_data)
        h2 = generate_log_hash(raw_data)
        self.assertEqual(h1, h2)

    def test_different_data_produces_different_hash(self):
        """Different raw_data payloads must produce different hashes."""
        h1 = generate_log_hash({"src_bytes": 100})
        h2 = generate_log_hash({"src_bytes": 200})
        self.assertNotEqual(h1, h2)

    def test_verify_log_hash_passes_on_correct_data(self):
        """verify_log_hash should return True for unmodified data."""
        raw_data = SAMPLE_RAW_DATA
        stored_hash = generate_log_hash(raw_data)
        self.assertTrue(verify_log_hash(raw_data, stored_hash))

    def test_verify_log_hash_fails_on_tampered_data(self):
        """verify_log_hash should return False when data has been modified."""
        raw_data = {"src_bytes": 500}
        stored_hash = generate_log_hash(raw_data)
        tampered_data = {"src_bytes": 9999}  # modified!
        self.assertFalse(verify_log_hash(tampered_data, stored_hash))


class NetworkEventAPITest(TestCase):
    """
    Integration tests for the Network Event read-only API.
    GET /api/ingestion/network-events/
    GET /api/ingestion/network-events/{id}/verify-hash/
    """

    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant()
        self.user = make_user(self.tenant)
        self.client.force_authenticate(user=self.user)

        raw = SAMPLE_RAW_DATA
        self.event = NetworkEvent.objects.create(
            tenant=self.tenant,
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol=NetworkEvent.Protocol.TCP,
            raw_data=raw,
            log_hash=generate_log_hash(raw),
            event_source=NetworkEvent.Source.MANUAL,
        )

    def test_list_network_events_returns_200(self):
        """Authenticated analyst should be able to list network events."""
        response = self.client.get("/api/ingestion/network-events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_is_tenant_scoped(self):
        """Events from a different tenant should NOT appear in the list."""
        other_tenant = Tenant.objects.create(name="Other Corp", slug="other-corp")
        NetworkEvent.objects.create(
            tenant=other_tenant,
            source_ip="1.2.3.4",
            destination_ip="5.6.7.8",
            protocol=NetworkEvent.Protocol.UDP,
            raw_data={"x": 1},
            log_hash=generate_log_hash({"x": 1}),
            event_source=NetworkEvent.Source.MANUAL,
        )
        response = self.client.get("/api/ingestion/network-events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only events for our tenant should be returned
        for item in response.data.get("results", response.data):
            self.assertNotEqual(item.get("source_ip"), "1.2.3.4")

    def test_hash_verification_endpoint_returns_valid(self):
        """verify-hash endpoint should confirm integrity of unmodified event."""
        url = f"/api/ingestion/network-events/{self.event.id}/verify-hash/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["integrity_valid"])

    def test_unauthenticated_cannot_list_events(self):
        """Unauthenticated request should return 401."""
        unauth = APIClient()
        response = unauth.get("/api/ingestion/network-events/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NSLKDDConstantsTest(TestCase):
    """
    Unit tests to verify the integrity of the NSL-KDD constants module.
    These tests ensure the feature list and config are always correct.
    """

    def test_nsl_kdd_features_has_41_entries(self):
        """NSL_KDD_FEATURES must contain exactly 41 feature names."""
        self.assertEqual(len(NSL_KDD_FEATURES), 41)

    def test_nsl_kdd_features_are_unique(self):
        """Each feature name in NSL_KDD_FEATURES must be unique."""
        self.assertEqual(len(NSL_KDD_FEATURES), len(set(NSL_KDD_FEATURES)))

    def test_attack_severity_map_covers_all_classes(self):
        """ATTACK_SEVERITY_MAP must cover all known attack classes."""
        expected_classes = {"NORMAL", "DOS", "PROBE", "R2L", "U2R", "UNKNOWN"}
        self.assertEqual(set(ATTACK_SEVERITY_MAP.keys()), expected_classes)

    def test_confidence_gate_values_in_valid_range(self):
        """Confidence gate thresholds must be floats between 0 and 1."""
        self.assertGreater(CONFIDENCE_GATE_AUTO_BLOCK, 0.0)
        self.assertLessEqual(CONFIDENCE_GATE_AUTO_BLOCK, 1.0)
        self.assertGreater(CONFIDENCE_GATE_ALERT_ONLY, 0.0)
        self.assertLessEqual(CONFIDENCE_GATE_ALERT_ONLY, 1.0)

    def test_auto_block_gate_higher_than_alert_only_gate(self):
        """Auto-block threshold must be stricter than alert-only threshold."""
        self.assertGreater(CONFIDENCE_GATE_AUTO_BLOCK, CONFIDENCE_GATE_ALERT_ONLY)

    def test_duration_is_first_feature(self):
        """'duration' must be the first feature in NSL-KDD (column 1)."""
        self.assertEqual(NSL_KDD_FEATURES[0], "duration")

    def test_dst_host_srv_rerror_rate_is_last_feature(self):
        """'dst_host_srv_rerror_rate' must be the 41st (last) feature."""
        self.assertEqual(NSL_KDD_FEATURES[-1], "dst_host_srv_rerror_rate")
