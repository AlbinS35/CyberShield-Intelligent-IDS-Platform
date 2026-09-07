#!/usr/bin/env python3
"""
CyberShield - Root Shortcut for Live Traffic Simulator
Run from project root:
    python scripts/simulate_traffic.py [--interval 2.0] [--count 0] [--attack-ratio 0.6]
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")

import django
django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    args = sys.argv[1:]
    call_command("simulate_traffic", *args)
