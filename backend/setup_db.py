#!/usr/bin/env python
"""
CyberShield Database Setup Script
Initializes PostgreSQL database with required extensions and seed data.

Usage:
    python setup_db.py
    python setup_db.py --seed         # also create demo tenant + users
    python setup_db.py --reset        # DROP and recreate (DESTRUCTIVE!)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Load .env (prioritize backend/.env for local settings, fallback to root .env)
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"

if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

DB_NAME     = os.getenv("DB_NAME",     "cybershield_db")
DB_USER     = os.getenv("DB_USER",     "cybershield_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cybershield_pass")
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")


def run_psql(sql: str, db: str = "postgres") -> bool:
    """Run a SQL statement via psql CLI."""
    cmd = [
        "psql",
        f"--host={DB_HOST}",
        f"--port={DB_PORT}",
        f"--username=postgres",
        f"--dbname={db}",
        "--no-password",
        "--command", sql,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and "already exists" not in result.stderr:
        print(f"  SQL Error: {result.stderr.strip()}")
        return False
    return True


def setup_database(reset: bool = False) -> None:
    print("=" * 60)
    print("  CyberShield — PostgreSQL Setup")
    print("=" * 60)

    import shutil
    if not shutil.which("psql"):
        if reset:
            print("\n❌ Error: 'psql' command not found, but --reset was specified.")
            print("   Cannot recreate the database without 'psql'.")
            sys.exit(1)
        else:
            print("\n⚠️  Warning: 'psql' command not found. Skipping database/user creation.")
            print("   Assuming database and user are already configured (e.g., via Docker).")
            return

    if reset:
        print(f"\n⚠️  RESET MODE: Dropping database '{DB_NAME}'...")
        run_psql(f"DROP DATABASE IF EXISTS {DB_NAME};")
        run_psql(f"DROP USER IF EXISTS {DB_USER};")
        print("  Database and user dropped.")

    # Create user
    print(f"\n[1/4] Creating user '{DB_USER}'...")
    run_psql(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';")
    run_psql(f"ALTER USER {DB_USER} CREATEDB;")

    # Create database
    print(f"[2/4] Creating database '{DB_NAME}'...")
    run_psql(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER} ENCODING 'UTF8';")

    # Enable PostgreSQL extensions
    print(f"[3/4] Enabling PostgreSQL extensions...")
    run_psql("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",   db=DB_NAME)
    run_psql("CREATE EXTENSION IF NOT EXISTS pg_trgm;",         db=DB_NAME)  # for fast text search
    run_psql("CREATE EXTENSION IF NOT EXISTS btree_gin;",       db=DB_NAME)  # for JSONB GIN indexes
    run_psql(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")
    run_psql(f"GRANT ALL ON SCHEMA public TO {DB_USER};", db=DB_NAME)

    print("[4/4] Database setup complete.")
    print(f"\n✅ PostgreSQL database ready:")
    print(f"   Host:     {DB_HOST}:{DB_PORT}")
    print(f"   Database: {DB_NAME}")
    print(f"   User:     {DB_USER}")
    print(f"\nNext steps:")
    print(f"   cd backend")
    print(f"   python manage.py migrate")
    print(f"   python manage.py createsuperuser")


def run_migrations() -> None:
    print("\n[Migrations] Running Django migrations...")
    result = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--verbosity=1"],
        cwd=Path(__file__).parent,
    )
    if result.returncode == 0:
        print("✅ Migrations applied successfully.")
    else:
        print("❌ Migration failed. Check Django settings.")


def create_seed_data() -> None:
    """Create a demo tenant and sample users for development testing."""
    print("\n[Seed] Creating demo tenant and users...")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")

    import django
    django.setup()

    from authentication.models import Tenant, User

    # Create demo tenant
    tenant, created = Tenant.objects.get_or_create(
        slug="amal-jyothi-bank",
        defaults={
            "name":          "Amal Jyothi Bank (Demo)",
            "industry":      "Banking",
            "contact_email": "security@ajbank.demo",
        },
    )
    print(f"  Tenant: {tenant.name} ({'created' if created else 'exists'})")

    # Create demo users for each role
    demo_users = [
        {"email": "analyst@cybershield.demo",     "first_name": "Priya",   "last_name": "Menon",    "role": "ANALYST",      "password": "CyberShield@2024"},
        {"email": "investigator@cybershield.demo","first_name": "Rahul",   "last_name": "Sharma",   "role": "INVESTIGATOR", "password": "CyberShield@2024"},
        {"email": "admin@cybershield.demo",        "first_name": "Suresh",  "last_name": "Kumar",    "role": "SYS_ADMIN",    "password": "CyberShield@2024"},
        {"email": "manager@cybershield.demo",      "first_name": "Anitha",  "last_name": "Varghese", "role": "ORG_MANAGER",  "password": "CyberShield@2024"},
        {"email": "superadmin@cybershield.demo",   "first_name": "Albin",   "last_name": "Suresh",   "role": "SUPER_ADMIN",  "password": "CyberShield@2024"},
    ]
    for u in demo_users:
        password = u.pop("password")
        user, created = User.objects.get_or_create(email=u["email"], defaults={**u, "tenant": tenant})
        if created:
            user.set_password(password)
            user.save()
        print(f"  User: {user.email} [{user.role}] ({'created' if created else 'exists'})")

    # Hook forensics seeding
    try:
        investigator = User.objects.get(email="investigator@cybershield.demo")
        create_forensics_seed_data(tenant, investigator)
    except Exception as e:
        print(f"  [WARN] Failed to seed forensics: {e}")

    print("\n✅ Seed data created.")
    print("   Login credentials (all use password: CyberShield@2024):")
    for u in demo_users:
        print(f"   {u['role']:<15} → {u['email']}")


def create_forensics_seed_data(tenant, investigator) -> None:
    """Seed digital forensics data including cases, evidence logs, timelines, and custody chain."""
    print("\n[Seed] Creating digital forensics demo data...")
    from django.utils import timezone
    from datetime import timedelta
    from forensics.models import ForensicCase, Evidence, CaseTimeline, ChainOfCustody
    
    # helper for mock files
    def create_mock_evidence_file(case_id, filename, content):
        from django.conf import settings
        from pathlib import Path
        import hashlib
        
        media_dir = Path(settings.MEDIA_ROOT)
        case_dir = media_dir / "forensics" / str(case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = case_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        # compute sha256
        hasher = hashlib.sha256()
        hasher.update(content.encode("utf-8"))
        sha256 = hasher.hexdigest()
        
        relative_path = f"forensics/{case_id}/{filename}"
        return relative_path, len(content), sha256

    # 1. Case 1: Exfiltration of PII via SSH Tunnel
    c1, created = ForensicCase.objects.get_or_create(
        title="Exfiltration of PII via SSH Tunnel",
        tenant=tenant,
        defaults={
            "description": "Unauthorized transfer of customer database backup to an external IP via a reverse SSH tunnel. The incident was detected on the primary database server.",
            "status": ForensicCase.Status.ACTIVE,
            "classification": ForensicCase.Classification.CONFIDENTIAL,
            "lead_investigator": investigator,
            "attack_vector": "SSH Tunneling & Data Exfiltration",
            "affected_systems": ["db-primary-01.local", "ssh-gateway-external"],
            "legal_hold": True,
        }
    )
    if created:
        print(f"  Forensic Case 1 created: {c1.case_number}")
        # Seeding Evidence for Case 1
        # Evidence 1: ssh_auth.log
        rel_path, size, sha = create_mock_evidence_file(
            c1.id, "ssh_auth.log",
            "Aug 17 04:12:01 ssh-gw sshd[14221]: Failed password for invalid user admin from 198.51.100.42\n"
            "Aug 17 04:12:05 ssh-gw sshd[14221]: Failed password for invalid user admin from 198.51.100.42\n"
            "Aug 17 05:01:23 ssh-gw sshd[14512]: Accepted password for admin from 198.51.100.42 port 49212 ssh2"
        )
        e1 = Evidence.objects.create(
            case=c1,
            evidence_type=Evidence.EvidenceType.LOG_FILE,
            title="SSH Auth Log dump",
            description="Excerpts from /var/log/auth.log highlighting brute force attempts and successful session initiation.",
            file=rel_path,
            file_name="ssh_auth.log",
            file_size_bytes=size,
            mime_type="text/plain",
            sha256_hash=sha,
            uploaded_by=investigator,
        )
        ChainOfCustody.objects.create(
            evidence=e1,
            action=ChainOfCustody.Action.COLLECTED,
            performed_by=investigator,
            notes="Extracted from gateway server.",
        )
        
        # Evidence 2: exfil_capture.pcap
        rel_path, size, sha = create_mock_evidence_file(
            c1.id, "exfil_capture.pcap",
            "[MOCK PCAP DATA: BINARY PACKETS SHOWN AS HEX STREAMS IN ACTUAL CASE]"
        )
        e2 = Evidence.objects.create(
            case=c1,
            evidence_type=Evidence.EvidenceType.PCAP,
            title="Reverse Tunnel Traffic Capture",
            description="Network packet capture of the connection on port 22 showing high throughput transfer consistent with database backup exfiltration.",
            file=rel_path,
            file_name="exfil_capture.pcap",
            file_size_bytes=size,
            mime_type="application/vnd.tcpdump.pcap",
            sha256_hash=sha,
            uploaded_by=investigator,
        )
        ChainOfCustody.objects.create(
            evidence=e2,
            action=ChainOfCustody.Action.COLLECTED,
            performed_by=investigator,
            notes="Captured by Suricata sensor on interface docker0.",
        )

        # Seeding Timeline for Case 1
        CaseTimeline.objects.create(
            case=c1,
            category=CaseTimeline.EventCategory.INITIAL_ACCESS,
            title="Brute Force Success on SSH Gateway",
            description="An external IP successfully authenticated as 'admin' on the SSH gateway after 400+ failed attempts.",
            source_ip="198.51.100.42",
            target_ip="10.0.1.5",
            source_system="Wazuh",
            event_time=timezone.now() - timedelta(hours=2),
            recorded_by=investigator,
            evidence=e1,
        )
        CaseTimeline.objects.create(
            case=c1,
            category=CaseTimeline.EventCategory.LATERAL_MOVEMENT,
            title="Lateral Movement from Gateway to DB-Primary",
            description="SSH session established from gateway to database server using compromised credentials.",
            source_ip="10.0.1.5",
            target_ip="10.0.2.10",
            source_system="SSH Daemon",
            event_time=timezone.now() - timedelta(minutes=90),
            recorded_by=investigator,
        )
        CaseTimeline.objects.create(
            case=c1,
            category=CaseTimeline.EventCategory.DATA_EXFILTRATION,
            title="Database Backup Archive Created",
            description="A compressed tar archive of the customer schema was generated in /tmp/dump.tar.gz.",
            source_ip="10.0.2.10",
            target_ip="10.0.2.10",
            source_system="Auditd",
            event_time=timezone.now() - timedelta(minutes=60),
            recorded_by=investigator,
            evidence=e2,
        )
        CaseTimeline.objects.create(
            case=c1,
            category=CaseTimeline.EventCategory.RESPONSE,
            title="Gateway Blocked by Automated Playbook",
            description="Automated containment playbook triggered: blocked external IP on the gateway firewall.",
            source_ip="10.0.1.1",
            target_ip="198.51.100.42",
            source_system="CyberShield IPS",
            event_time=timezone.now() - timedelta(minutes=55),
            recorded_by=investigator,
        )

    # 2. Case 2: Ransomware Attack on Server-04
    c2, created = ForensicCase.objects.get_or_create(
        title="Ransomware Attack on Server-04",
        tenant=tenant,
        defaults={
            "description": "Detection of lockbit-style ransomware executing on Server-04, attempting to encrypt network shares and local files.",
            "status": ForensicCase.Status.OPEN,
            "classification": ForensicCase.Classification.RESTRICTED,
            "lead_investigator": investigator,
            "attack_vector": "Ransomware Execution",
            "affected_systems": ["app-server-04.local", "share-billing-01"],
            "legal_hold": False,
        }
    )
    if created:
        print(f"  Forensic Case 2 created: {c2.case_number}")
        # Seeding Evidence for Case 2
        rel_path, size, sha = create_mock_evidence_file(
            c2.id, "lockbit_sample.exe",
            "[MOCK MALWARE BINARY HASH SEALED FOR LAB INVESTIGATION]"
        )
        e3 = Evidence.objects.create(
            case=c2,
            evidence_type=Evidence.EvidenceType.DISK_IMAGE,
            title="Server-04 Malware Sample",
            description="Cryptographic capture of the ransomware executable discovered in the user's temp directory.",
            file=rel_path,
            file_name="lockbit_sample.exe",
            file_size_bytes=size,
            mime_type="application/octet-stream",
            sha256_hash=sha,
            uploaded_by=investigator,
        )
        ChainOfCustody.objects.create(
            evidence=e3,
            action=ChainOfCustody.Action.COLLECTED,
            performed_by=investigator,
            notes="Retrieved from App-Server-04 disk image dump.",
        )

        # Seeding Timeline for Case 2
        CaseTimeline.objects.create(
            case=c2,
            category=CaseTimeline.EventCategory.INITIAL_ACCESS,
            title="Malicious Attachment Downloaded",
            description="User downloaded a malicious invoice attachment via webmail on App-Server-04.",
            source_ip="10.0.4.12",
            target_ip="198.51.100.89",
            source_system="Squid Proxy",
            event_time=timezone.now() - timedelta(hours=4),
            recorded_by=investigator,
        )
        CaseTimeline.objects.create(
            case=c2,
            category=CaseTimeline.EventCategory.PRIVILEGE_ESCALATION,
            title="UAC Bypass via DLL Hijacking",
            description="Process billing_invoice.exe successfully bypassed UAC control to gain administrative privileges.",
            source_ip="10.0.4.12",
            target_ip="10.0.4.12",
            source_system="Sysmon",
            event_time=timezone.now() - timedelta(hours=2),
            recorded_by=investigator,
            evidence=e3,
        )
        CaseTimeline.objects.create(
            case=c2,
            category=CaseTimeline.EventCategory.IMPACT,
            title="Local File Encryption Started",
            description="System detected massive file renaming activity with extension '.lockbit' on local directories.",
            source_ip="10.0.4.12",
            target_ip="10.0.4.12",
            source_system="CyberShield Agent",
            event_time=timezone.now() - timedelta(hours=1),
            recorded_by=investigator,
        )

    # 3. Case 3: Unauthorized API Access from Suspicious IP
    c3, created = ForensicCase.objects.get_or_create(
        title="Unauthorized API Access from Suspicious IP",
        tenant=tenant,
        defaults={
            "description": "Repeated API calls made to customer endpoints using leaked administrator API keys from an unapproved geographic location.",
            "status": ForensicCase.Status.CLOSED,
            "classification": ForensicCase.Classification.INTERNAL,
            "lead_investigator": investigator,
            "attack_vector": "API Key Compromise",
            "affected_systems": ["api-gateway-prod"],
            "legal_hold": False,
        }
    )
    if created:
        print(f"  Forensic Case 3 created: {c3.case_number}")
        # Seeding Timeline for Case 3
        CaseTimeline.objects.create(
            case=c3,
            category=CaseTimeline.EventCategory.DETECTION,
            title="API Authentication Anomalous Geo-Location",
            description="API requests made using API-KEY-992 from an IP address block registered to a country without business relations.",
            source_ip="203.0.113.15",
            target_ip="10.0.3.5",
            source_system="NGINX Access Log",
            event_time=timezone.now() - timedelta(days=1),
            recorded_by=investigator,
        )
        CaseTimeline.objects.create(
            case=c3,
            category=CaseTimeline.EventCategory.RESPONSE,
            title="API Key Revoked",
            description="Security analyst revoked API-KEY-992 to prevent further access.",
            source_ip="10.0.3.1",
            target_ip="10.0.3.5",
            source_system="Auth Server",
            event_time=timezone.now() - timedelta(hours=23),
            recorded_by=investigator,
        )

    print("  [OK] Forensics seed data created successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberShield PostgreSQL setup utility")
    parser.add_argument("--seed",    action="store_true", help="Create demo tenant and users")
    parser.add_argument("--migrate", action="store_true", help="Run Django migrations after setup")
    parser.add_argument("--reset",   action="store_true", help="DROP and recreate database (DESTRUCTIVE)")
    args = parser.parse_args()

    setup_database(reset=args.reset)

    if args.migrate:
        run_migrations()

    if args.seed:
        create_seed_data()
