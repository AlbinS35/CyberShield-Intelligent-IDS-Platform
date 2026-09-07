"""
CyberShield - Live Traffic & Threat Simulator
=============================================
Continuously generates realistic Suricata NIDS network traffic events
(DoS SYN floods, Port Scans, SSH Brute Force, Web Browsing, etc.),
feeds them through the cryptographic SHA-256 evidence hashing and ML inference pipeline,
creates security alerts, and broadcasts them live over WebSockets to connected dashboards.

Usage:
    python manage.py simulate_traffic
    python manage.py simulate_traffic --interval 1.5 --attack-ratio 0.7
    python manage.py simulate_traffic --count 20
"""

import time
import random
import sys
from datetime import datetime, timezone
from django.core.management.base import BaseCommand
from django.utils import timezone as dj_timezone
from authentication.models import Tenant
from ingestion.models import NetworkEvent
from ingestion.tasks import _normalize_suricata_event
from detection.tasks import classify_network_event, rehash_event_batch


ATTACK_PROFILES = [
    {
        "name": "DoS SYN Flood (Neptune)",
        "attack_type": "DoS",
        "proto": "TCP",
        "dest_port": 80,
        "signature": "ET DOS Possible SYN Flood Inbound",
        "category": "Denial of Service",
        "severity": 1,
        "src_bytes": 0,
        "dst_bytes": 0,
        "data": {
            "duration": 0, "src_bytes": 0, "dst_bytes": 0, "count": 280,
            "srv_count": 280, "serror_rate": 1.0, "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0, "logged_in": 0, "dst_host_count": 255,
            "dst_host_srv_count": 255,
        }
    },
    {
        "name": "Port Scan (Nmap Probe)",
        "attack_type": "Probe",
        "proto": "TCP",
        "dest_port": 445,
        "signature": "ET SCAN Suspicious Inbound to MSSQL/SMB",
        "category": "Attempted Information Leak",
        "severity": 2,
        "src_bytes": 0,
        "dst_bytes": 0,
        "data": {
            "duration": 0, "src_bytes": 0, "dst_bytes": 0, "count": 120,
            "srv_count": 1, "serror_rate": 0.9, "same_srv_rate": 0.05,
            "diff_srv_rate": 0.95, "logged_in": 0, "dst_host_count": 255,
            "dst_host_srv_count": 5,
        }
    },
    {
        "name": "SSH Brute Force Attack",
        "attack_type": "R2L",
        "proto": "TCP",
        "dest_port": 22,
        "signature": "ET SCAN Potential SSH Brute Force Inbound",
        "category": "Attempted Administrator Access",
        "severity": 1,
        "src_bytes": 140,
        "dst_bytes": 220,
        "data": {
            "duration": 2, "src_bytes": 140, "dst_bytes": 220, "count": 45,
            "srv_count": 45, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0, "logged_in": 0, "dst_host_count": 100,
            "dst_host_srv_count": 100,
        }
    },
    {
        "name": "DNS Data Exfiltration",
        "attack_type": "Probe",
        "proto": "UDP",
        "dest_port": 53,
        "signature": "ET POLICY Suspicious Large DNS Query (Possible Exfil)",
        "category": "Data Exfiltration",
        "severity": 2,
        "src_bytes": 1840,
        "dst_bytes": 120,
        "data": {
            "duration": 1, "src_bytes": 1840, "dst_bytes": 120, "count": 60,
            "srv_count": 60, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0, "logged_in": 0, "dst_host_count": 50,
            "dst_host_srv_count": 50,
        }
    },
]

NORMAL_PROFILES = [
    {
        "name": "Normal HTTPS Web Session",
        "attack_type": "NORMAL",
        "proto": "TCP",
        "dest_port": 443,
        "signature": "Normal TLS Session",
        "category": "Normal Traffic",
        "severity": 3,
        "src_bytes": 520,
        "dst_bytes": 12400,
        "data": {
            "duration": 5, "src_bytes": 520, "dst_bytes": 12400, "count": 8,
            "srv_count": 8, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0, "logged_in": 1, "dst_host_count": 12,
            "dst_host_srv_count": 12,
        }
    },
    {
        "name": "Normal API Request (HTTP GET)",
        "attack_type": "NORMAL",
        "proto": "TCP",
        "dest_port": 80,
        "signature": "Normal HTTP Session",
        "category": "Normal Traffic",
        "severity": 3,
        "src_bytes": 215,
        "dst_bytes": 45076,
        "data": {
            "duration": 0, "src_bytes": 215, "dst_bytes": 45076, "count": 9,
            "srv_count": 9, "serror_rate": 0.0, "same_srv_rate": 1.0,
            "diff_srv_rate": 0.0, "logged_in": 1, "dst_host_count": 9,
            "dst_host_srv_count": 9,
        }
    },
]

SOURCE_IPS_SUSPICIOUS = [
    "185.220.101.5", "45.155.205.12", "194.26.29.114", "91.240.118.232",
    "193.142.146.35", "103.145.13.50", "218.92.0.218", "80.82.77.139"
]

SOURCE_IPS_INTERNAL = [
    "10.0.0.15", "10.0.0.42", "10.0.1.105", "192.168.1.55", "172.16.0.20"
]

DEST_IPS = [
    "10.0.0.1", "10.0.0.2", "10.0.0.5", "192.168.1.10", "172.16.0.1"
]


class Command(BaseCommand):
    help = "Simulate live network traffic and stream real-time attacks & alerts to dashboards"

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=2.0, help="Seconds between simulated events (default: 2.0)")
        parser.add_argument("--count", type=int, default=0, help="Total events to generate (0 = infinite, default: 0)")
        parser.add_argument("--attack-ratio", type=float, default=0.6, help="Ratio of attacks vs normal (0.0 to 1.0, default: 0.6)")
        parser.add_argument("--tenant-id", type=str, default="", help="Tenant UUID (defaults to first active tenant)")

    def handle(self, *args, **options):
        interval = options["interval"]
        total_count = options["count"]
        attack_ratio = options["attack_ratio"]
        tenant_id = options["tenant_id"]

        # 1. Resolve Tenant
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id, is_active=True).first()
        else:
            tenant = Tenant.objects.filter(is_active=True).first()

        if not tenant:
            self.stderr.write(self.style.ERROR("[!] No active Tenant found in database. Run migrations or create a tenant first."))
            return

        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(self.style.SUCCESS("  CYBERSHIELD - LIVE THREAT & TRAFFIC SIMULATOR"))
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(f"  Target Tenant : {tenant.name} ({tenant.id})")
        self.stdout.write(f"  Event Interval: {interval}s")
        self.stdout.write(f"  Attack Ratio  : {attack_ratio * 100:.0f}% attacks, {(1 - attack_ratio) * 100:.0f}% normal")
        self.stdout.write(f"  Mode          : {'Infinite (Ctrl+C to stop)' if total_count == 0 else f'{total_count} events'}")
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write("  Streaming live events into pipeline & WebSockets...\n")

        generated = 0
        threat_count = 0

        try:
            while total_count == 0 or generated < total_count:
                is_attack = random.random() < attack_ratio
                profile = random.choice(ATTACK_PROFILES) if is_attack else random.choice(NORMAL_PROFILES)

                src_ip = random.choice(SOURCE_IPS_SUSPICIOUS) if is_attack else random.choice(SOURCE_IPS_INTERNAL)
                dest_ip = random.choice(DEST_IPS)
                src_port = random.randint(1024, 65535)
                dest_port = profile["dest_port"]
                proto = profile["proto"]

                # Build Suricata EVE JSON event
                eve_event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": "alert" if is_attack else "flow",
                    "src_ip": src_ip,
                    "src_port": src_port,
                    "dest_ip": dest_ip,
                    "dest_port": dest_port,
                    "proto": proto,
                    "alert": {
                        "signature": profile["signature"],
                        "category": profile["category"],
                        "severity": profile["severity"],
                    },
                    "flow": {
                        "bytes_toserver": profile["src_bytes"],
                        "bytes_toclient": profile["dst_bytes"],
                        "pkts_toserver": random.randint(5, 50),
                        "pkts_toclient": random.randint(5, 50),
                        "duration": profile["data"].get("duration", 0),
                    },
                    "data": profile["data"],
                    "host": "sensor-alpha-01",
                }

                # Ingest into CyberShield NetworkEvent
                normalized = _normalize_suricata_event(eve_event)
                event = NetworkEvent.objects.create(
                    tenant=tenant,
                    raw_data=eve_event,
                    log_hash="",
                    event_source=NetworkEvent.Source.SURICATA,
                    **normalized,
                )

                # Process synchronous or async
                rehash_event_batch.delay([str(event.id)])
                classify_network_event.delay(str(event.id))

                generated += 1
                now_str = datetime.now().strftime("%H:%M:%S")

                if is_attack:
                    threat_count += 1
                    msg = f"[{now_str}] [ATTACK] -> {profile['name']} from {src_ip} -> {dest_ip}:{dest_port}"
                    self.stdout.write(self.style.WARNING(msg))
                else:
                    msg = f"[{now_str}] [NORMAL] -> {profile['name']} from {src_ip} -> {dest_ip}:{dest_port}"
                    self.stdout.write(self.style.NOTICE(msg))

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS(f"\n[Simulator stopped] Generated {generated} events ({threat_count} threats)."))
