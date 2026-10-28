#!/usr/bin/env python
"""
CyberShield — PostgreSQL Database Bootstrap
============================================
Creates the cybershield_user + cybershield_db, enables required
PostgreSQL extensions, and runs Django migrations.

Usage:
    python bootstrap_db.py --pg-password YOUR_POSTGRES_SUPERUSER_PASSWORD
    python bootstrap_db.py --pg-password YOUR_PG_PASSWORD --migrate
    python bootstrap_db.py --pg-password YOUR_PG_PASSWORD --migrate --seed

Arguments:
    --pg-password   PostgreSQL superuser (postgres) password  [REQUIRED]
    --migrate       Run Django makemigrations + migrate after DB setup
    --seed          Create demo Organization + CoreUser + Login seed data
    --reset         DROP and recreate (DESTRUCTIVE!)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# ─── Load .env ────────────────────────────────────────────────────────────────
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    from decouple import Config, RepositoryEnv
    _cfg = Config(RepositoryEnv(str(env_file)))
else:
    from decouple import config as _cfg

DB_NAME     = _cfg("DB_NAME",     default="cybershield_db")
DB_USER     = _cfg("DB_USER",     default="cybershield_user")
DB_PASSWORD = _cfg("DB_PASSWORD", default="cybershield_pass")
DB_HOST     = _cfg("DB_HOST",     default="localhost")
DB_PORT     = _cfg("DB_PORT",     default="5432", cast=int)


def get_conn(pg_password: str, dbname: str = "postgres"):
    """Connect to PostgreSQL as the postgres superuser."""
    import psycopg2
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=dbname,
        user="postgres",
        password=pg_password,
        connect_timeout=10,
    )


def exec_sql(conn, sql: str, ignore_errors: bool = True) -> bool:
    """Execute SQL on an existing connection."""
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        try:
            cur.execute(sql)
            return True
        except Exception as e:
            err = str(e).strip()
            if ignore_errors and "already exists" in err:
                print(f"    [INFO] Skipped (already exists): {err[:80]}")
                return True
            print(f"    [ERR] SQL error: {err}")
            return not ignore_errors


def setup_database(pg_password: str, reset: bool = False) -> bool:
    print("=" * 62)
    print("  CyberShield — PostgreSQL Bootstrap")
    print("=" * 62)

    try:
        conn = get_conn(pg_password)
        print(f"\n[OK] Connected to PostgreSQL as superuser.\n")
    except Exception as e:
        print(f"\n[ERROR] Could not connect as postgres superuser: {e}")
        print("   Ensure PostgreSQL is running and --pg-password is correct.")
        return False

    if reset:
        print(f"[WARN] RESET: Dropping DB '{DB_NAME}' and user '{DB_USER}'...")
        exec_sql(conn, f"DROP DATABASE IF EXISTS {DB_NAME};")
        exec_sql(conn, f"DROP USER IF EXISTS {DB_USER};")
        print("   Dropped.\n")

    # 1. Create user
    print(f"[1/4] Creating user '{DB_USER}'...")
    exec_sql(conn, f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}';")
    exec_sql(conn, f"ALTER USER {DB_USER} CREATEDB;")
    print(f"      [OK] User ready.\n")

    # 2. Create database
    print(f"[2/4] Creating database '{DB_NAME}'...")
    exec_sql(conn, f"CREATE DATABASE {DB_NAME} OWNER {DB_USER} ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8' TEMPLATE template0;",
             ignore_errors=False) or \
    exec_sql(conn, f"CREATE DATABASE {DB_NAME} OWNER {DB_USER} ENCODING 'UTF8';")
    print(f"      [OK] Database ready.\n")

    # 3. Grant privileges
    print(f"[3/4] Granting privileges...")
    exec_sql(conn, f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")
    conn.close()

    # Connect to the new DB to enable extensions
    try:
        db_conn = get_conn(pg_password, dbname=DB_NAME)
        exec_sql(db_conn, "GRANT ALL ON SCHEMA public TO " + DB_USER + ";")
        exec_sql(db_conn, 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        exec_sql(db_conn, "CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        exec_sql(db_conn, "CREATE EXTENSION IF NOT EXISTS btree_gin;")
        db_conn.close()
        print(f"      [OK] Privileges and extensions configured.\n")
    except Exception as e:
        print(f"      [WARN] Extension setup warning: {e}")

    print(f"[4/4] Database bootstrap complete.")
    print(f"\n{'='*62}")
    print(f"  PostgreSQL ready:")
    print(f"    Host:     {DB_HOST}:{DB_PORT}")
    print(f"    Database: {DB_NAME}")
    print(f"    User:     {DB_USER}")
    print(f"    Password: {DB_PASSWORD}")
    print(f"{'='*62}\n")
    return True


def run_migrations() -> None:
    print("\n[Migrations] Running makemigrations + migrate...")
    backend_dir = Path(__file__).parent

    result1 = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", "--verbosity=1"],
        cwd=backend_dir,
    )
    result2 = subprocess.run(
        [sys.executable, "manage.py", "migrate", "--verbosity=1"],
        cwd=backend_dir,
    )

    if result2.returncode == 0:
        print("\n[OK] All migrations applied successfully.")
    else:
        print("\n[ERROR] Migration failed -- check the output above.")


def create_seed_data() -> None:
    """Seed an Organization, CoreUser, and Login in tbl_ tables for testing."""
    print("\n[Seed] Creating demo data in tbl_ schema...")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")
    import django
    django.setup()

    from authentication.models import Tenant, User

    tenant, created = Tenant.objects.get_or_create(
        name="CyberShield Demo Bank",
        defaults={"slug": "cybershield-demo", "industry": "Banking", "is_active": True},
    )
    print(f"  Tenant: {tenant.name} ({'created' if created else 'exists'})")

    # Login credential for each role
    demo_accounts = [
        ("analyst@cybershield.demo",      User.Role.ANALYST,      "CyberShield@2024", "Demo", "Analyst"),
        ("investigator@cybershield.demo", User.Role.INVESTIGATOR, "CyberShield@2024", "Demo", "Investigator"),
        ("admin@cybershield.demo",        User.Role.SYS_ADMIN,    "CyberShield@2024", "Demo", "Admin"),
        ("manager@cybershield.demo",      User.Role.ORG_MANAGER,  "CyberShield@2024", "Demo", "Manager"),
    ]

    for email, role, password, first_name, last_name in demo_accounts:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "last_name": last_name, "tenant": tenant, "role": role},
        )
        if created:
            user.set_password(password)
            user.save()
        # Also update password if user exists to ensure it matches the demo password
        elif not user.check_password(password):
            user.set_password(password)
            user.save()
            print(f"  User: {email} [{role}] (password updated)")
            
        print(f"  User: {email} [{role}] ({'created' if created else 'exists'})")

    # Seed initial compliance reports for the demo tenant
    try:
        from detection.models import ComplianceReport
        if not ComplianceReport.objects.filter(tenant=tenant).exists():
            manager_user = User.objects.filter(tenant=tenant, role=User.Role.ORG_MANAGER).first()
            sample_metrics = {
                "total_events": 806,
                "threat_events": 45,
                "verified_hashes": 806,
                "active_playbooks": 3,
            }
            reports_to_create = [
                {
                    "title": "Q3 2026 ISO/IEC 27001:2022 Continuous Security Audit",
                    "report_type": "ISO_27001",
                    "status": "APPROVED",
                    "auditor_notes": "All cryptographic checksums verified. Ingress perimeter monitoring fully active.",
                    "findings": [
                        {"code": "ISO/IEC 27001:2022 A.8.20", "name": "Network Security Controls & Logging", "status": "COMPLIANT", "details": "Continuous monitoring of network traffic is active. Recorded 806 events."},
                        {"code": "ISO/IEC 27001:2022 A.8.16", "name": "Monitoring Activities & Anomaly Detection", "status": "COMPLIANT", "details": "Real-time AI/ML threat detection pipeline actively classifying network ingress vectors."},
                        {"code": "ISO/IEC 27001:2022 A.8.24", "name": "Use of Cryptography", "status": "COMPLIANT", "details": "SHA-256 immutable checksum chains verified on 806 network logs."},
                    ]
                },
                {
                    "title": "PCI-DSS v4.0 Network Telemetry & Cryptographic Audit",
                    "report_type": "PCI_DSS",
                    "status": "REVIEWED",
                    "auditor_notes": "Requirement 10 audit trails established with immutable SHA-256 ledger seals.",
                    "findings": [
                        {"code": "PCI-DSS v4.0 Req 10.2.1", "name": "Audit Trails for System & Cardholder Events", "status": "COMPLIANT", "details": "Logs secured using cryptographic SHA-256 hashes. Verified 806 audit seals."},
                        {"code": "PCI-DSS v4.0 Req 11.4.1", "name": "Intrusion Detection & Threat Mitigation", "status": "COMPLIANT", "details": "Automated response playbooks configured (3 active) for real-time containment."},
                    ]
                },
                {
                    "title": "RBI Banking Cybersecurity Compliance & Incident Assessment",
                    "report_type": "RBI_BANKING",
                    "status": "APPROVED",
                    "auditor_notes": "Continuous SOC monitoring in compliance with Reserve Bank of India Cyber Security Framework CC-5.1.",
                    "findings": [
                        {"code": "RBI Banking Security CC-5.1", "name": "Incident Containment & Action Logs", "status": "COMPLIANT", "details": "Telemetry surveillance active across all tenant subnets. 45 threat classifications tracked."},
                        {"code": "RBI Banking Security CC-6.3", "name": "Boundary Defense & Automated Playbooks", "status": "COMPLIANT", "details": "3 automated incident mitigation playbooks ready for rapid isolation."},
                    ]
                }
            ]
            for rep in reports_to_create:
                ComplianceReport.objects.create(
                    tenant=tenant,
                    title=rep["title"],
                    report_type=rep["report_type"],
                    status=rep["status"],
                    generated_by=manager_user,
                    metrics=sample_metrics,
                    findings=rep["findings"],
                    auditor_notes=rep["auditor_notes"],
                )
            print("  Compliance reports created.")
    except Exception as e:
        print(f"  [WARN] Failed to seed compliance reports: {e}")

    print("\n[OK] Seed data created.")
    print("   Login at POST /api/auth/login/ with any of the above emails")
    print("   and password: CyberShield@2024")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CyberShield PostgreSQL bootstrap utility"
    )
    parser.add_argument("--pg-password", required=True,
                        help="PostgreSQL superuser (postgres) password")
    parser.add_argument("--migrate", action="store_true",
                        help="Run Django migrations after DB setup")
    parser.add_argument("--seed", action="store_true",
                        help="Create demo tbl_ schema seed data")
    parser.add_argument("--reset", action="store_true",
                        help="DROP and recreate database (DESTRUCTIVE!)")
    args = parser.parse_args()

    ok = setup_database(args.pg_password, reset=args.reset)

    if ok and args.migrate:
        run_migrations()

    if ok and args.seed:
        create_seed_data()
