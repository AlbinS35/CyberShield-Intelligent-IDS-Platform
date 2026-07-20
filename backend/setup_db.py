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

# Load .env from project root
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

    print("\n✅ Seed data created.")
    print("   Login credentials (all use password: CyberShield@2024):")
    for u in demo_users:
        print(f"   {u['role']:<15} → {u['email']}")


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
