"""
CyberShield — Network Traffic & Threat Simulator
Simulates realistic incoming network traffic, runs the ML model on each packet,
and saves the events + alerts + incidents into PostgreSQL for all tenants.
"""

import os
import random
import hashlib
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")
django.setup()

from django.utils import timezone
from authentication.models import Tenant, User
from ingestion.models import NetworkEvent
from detection.models import Alert, Incident, MLInferenceLog
from detection.core_ml.inference import classifier

# Ensure classifier is loaded
classifier.load()

tenants = list(Tenant.objects.all())
if not tenants:
    print("[ERROR] No tenants found in DB.")
    exit(1)

TRAFFIC_SAMPLES = [
    # Normal Browsing
    {
        "source_ip": "192.168.1.105",
        "destination_ip": "10.0.0.1",
        "source_port": 54231,
        "destination_port": 443,
        "protocol": NetworkEvent.Protocol.HTTPS,
        "bytes_sent": 420,
        "bytes_received": 15840,
        "duration_ms": 12.4,
        "title": "Normal HTTPS Web Request",
        "features": {
            "duration": 0, "protocol_type": 6, "service": 10, "flag": 10,
            "src_bytes": 420, "dst_bytes": 15840, "land": 0, "logged_in": 1,
            "count": 5, "srv_count": 5, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "dst_host_count": 5, "dst_host_srv_count": 5
        }
    },
    {
        "source_ip": "192.168.1.110",
        "destination_ip": "10.0.0.1",
        "source_port": 52100,
        "destination_port": 80,
        "protocol": NetworkEvent.Protocol.HTTP,
        "bytes_sent": 310,
        "bytes_received": 8940,
        "duration_ms": 8.1,
        "title": "Normal HTTP Asset Request",
        "features": {
            "duration": 0, "protocol_type": 6, "service": 10, "flag": 10,
            "src_bytes": 310, "dst_bytes": 8940, "land": 0, "logged_in": 1,
            "count": 8, "srv_count": 8, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "dst_host_count": 8, "dst_host_srv_count": 8
        }
    },
    # DoS Attack (SYN Flood)
    {
        "source_ip": "45.154.255.89",
        "destination_ip": "10.0.0.1",
        "source_port": 49152,
        "destination_port": 80,
        "protocol": NetworkEvent.Protocol.TCP,
        "bytes_sent": 0,
        "bytes_received": 0,
        "duration_ms": 0.1,
        "title": "High-Volume TCP SYN Flood Attack",
        "features": {
            "duration": 0, "protocol_type": 6, "service": 5, "flag": 4,
            "src_bytes": 0, "dst_bytes": 0, "land": 0, "logged_in": 0,
            "count": 511, "srv_count": 511, "serror_rate": 1.0, "srv_serror_rate": 1.0,
            "same_srv_rate": 1.0, "dst_host_count": 255, "dst_host_srv_count": 255,
            "dst_host_serror_rate": 1.0, "dst_host_srv_serror_rate": 1.0
        }
    },
    # DoS Attack #2 (Smurf ICMP Flood)
    {
        "source_ip": "185.220.101.5",
        "destination_ip": "10.0.0.1",
        "source_port": 0,
        "destination_port": 0,
        "protocol": NetworkEvent.Protocol.ICMP,
        "bytes_sent": 1032,
        "bytes_received": 0,
        "duration_ms": 0.2,
        "title": "ICMP Echo Broadcast Flood (Smurf)",
        "features": {
            "duration": 0, "protocol_type": 1, "service": 2, "flag": 10,
            "src_bytes": 1032, "dst_bytes": 0, "land": 0, "logged_in": 0,
            "count": 480, "srv_count": 480, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "dst_host_count": 255, "dst_host_srv_count": 255
        }
    },
    # Port Scan Probe
    {
        "source_ip": "194.26.29.112",
        "destination_ip": "10.0.0.1",
        "source_port": 58912,
        "destination_port": 22,
        "protocol": NetworkEvent.Protocol.TCP,
        "bytes_sent": 0,
        "bytes_received": 0,
        "duration_ms": 0.5,
        "title": "Rapid Port Scanning / Reconnaissance",
        "features": {
            "duration": 0, "protocol_type": 6, "service": 10, "flag": 2,
            "src_bytes": 0, "dst_bytes": 0, "land": 0, "logged_in": 0,
            "count": 229, "srv_count": 3, "serror_rate": 0.0, "rerror_rate": 1.0,
            "same_srv_rate": 0.06, "diff_srv_rate": 0.07, "dst_host_count": 255,
            "dst_host_srv_count": 3, "dst_host_diff_srv_rate": 0.07,
            "dst_host_rerror_rate": 1.0
        }
    },
    # DNS Query
    {
        "source_ip": "192.168.1.108",
        "destination_ip": "10.0.0.53",
        "source_port": 53535,
        "destination_port": 53,
        "protocol": NetworkEvent.Protocol.DNS,
        "bytes_sent": 74,
        "bytes_received": 142,
        "duration_ms": 3.2,
        "title": "Internal DNS Lookup",
        "features": {
            "duration": 0, "protocol_type": 17, "service": 4, "flag": 10,
            "src_bytes": 74, "dst_bytes": 142, "land": 0, "logged_in": 0,
            "count": 2, "srv_count": 2, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "dst_host_count": 2, "dst_host_srv_count": 2
        }
    },
    # R2L Password Guessing
    {
        "source_ip": "103.251.167.20",
        "destination_ip": "10.0.0.1",
        "source_port": 41290,
        "destination_port": 22,
        "protocol": NetworkEvent.Protocol.TCP,
        "bytes_sent": 1420,
        "bytes_received": 1820,
        "duration_ms": 45.0,
        "title": "SSH Brute-Force Password Attack",
        "features": {
            "duration": 5, "protocol_type": 6, "service": 8, "flag": 10,
            "src_bytes": 1420, "dst_bytes": 1820, "land": 0, "num_failed_logins": 7,
            "logged_in": 0, "count": 12, "srv_count": 12, "serror_rate": 0.0,
            "same_srv_rate": 1.0, "dst_host_count": 50, "dst_host_srv_count": 12
        }
    }
]

for t in tenants:
    analyst = User.objects.filter(tenant=t, role=User.Role.ANALYST).first() or User.objects.filter(tenant=t).first()
    print("=" * 65)
    print(f"  Injecting Events for: {t.name} (User: {analyst.email if analyst else 'None'})")
    print("=" * 65)

    tenant_alerts = []

    for sample in TRAFFIC_SAMPLES:
        # 1. Run ML Model Prediction
        features = sample["features"]
        ml_label, ml_confidence = classifier.predict(features)
        is_threat = (ml_label != "NORMAL")

        # 2. Build JSON raw_data + SHA-256 seal
        raw_payload = {
            "source_ip": sample["source_ip"],
            "destination_ip": sample["destination_ip"],
            "source_port": sample["source_port"],
            "destination_port": sample["destination_port"],
            "protocol": sample["protocol"],
            "bytes_sent": sample["bytes_sent"],
            "bytes_received": sample["bytes_received"],
            "features": features,
        }
        raw_json_str = json.dumps(raw_payload, sort_keys=True)
        sha256_hash = hashlib.sha256(raw_json_str.encode("utf-8")).hexdigest()

        # 3. Create NetworkEvent
        event = NetworkEvent.objects.create(
            tenant=t,
            source_ip=sample["source_ip"],
            destination_ip=sample["destination_ip"],
            source_port=sample["source_port"],
            destination_port=sample["destination_port"],
            protocol=sample["protocol"],
            bytes_sent=sample["bytes_sent"],
            bytes_received=sample["bytes_received"],
            duration_ms=sample["duration_ms"],
            raw_data=raw_payload,
            log_hash=sha256_hash,
            event_source=NetworkEvent.Source.SIMULATOR,
            ml_classification=ml_label,
            ml_confidence=ml_confidence,
            is_threat=is_threat,
            event_timestamp=timezone.now(),
        )

        # 4. Log inference
        MLInferenceLog.objects.create(
            network_event=event,
            model_version="v1.0",
            prediction=ml_label,
            confidence=ml_confidence,
            inference_time_ms=sample["duration_ms"],
            input_features=features,
        )

        # 5. Create Alert if it is a detected threat
        if is_threat:
            severity = Alert.Severity.HIGH if ml_label == "DOS" else Alert.Severity.MEDIUM
            if ml_label == "DOS" and ml_confidence > 0.8:
                severity = Alert.Severity.CRITICAL

            alert = Alert.objects.create(
                tenant=t,
                network_event=event,
                title=f"AI IDS Alert: {ml_label} Attack Detected ({sample['title']})",
                description=f"Machine learning model classified incoming traffic from {sample['source_ip']} with {ml_confidence*100:.1f}% confidence.",
                severity=severity,
                status=Alert.Status.NEW,
                attack_type=ml_label,
                source_ip=sample["source_ip"],
                destination_ip=sample["destination_ip"],
                affected_asset="Core Gateway",
                ml_confidence=ml_confidence,
                assigned_to=analyst,
            )
            tenant_alerts.append(alert)

        print(f"  [+] Ingested {sample['source_ip']:<16} -> {sample['protocol']:<5} | ML: {ml_label:<7} ({ml_confidence*100:.1f}%) | Threat: {is_threat}")

    # Create an Incident from the alerts
    if tenant_alerts:
        incident = Incident.objects.create(
            tenant=t,
            title="Sustained DDoS & Port Reconnaissance Campaign",
            description="Automated incident created from multiple correlated high-severity ML detection alerts targeting the core gateway.",
            status=Incident.Status.OPEN,
            severity=Alert.Severity.CRITICAL,
            lead_analyst=analyst,
        )
        incident.alerts.set(tenant_alerts)
        print(f"  [!] Created Incident: '{incident.title}' linked to {len(tenant_alerts)} alerts.")

print("=" * 65)
print("SUCCESS: Ingested live telemetry for ALL tenants!")
print("=" * 65)
