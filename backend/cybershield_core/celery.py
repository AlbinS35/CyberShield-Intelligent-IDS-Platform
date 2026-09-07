"""
Celery Application Configuration for CyberShield

Periodic Tasks (Celery Beat):
  - sync_all_wazuh_tenants: Every 30 s, fetches Wazuh alerts for every
    active tenant that has a Wazuh manager URL configured. This ensures
    continuous telemetry ingestion without requiring manual UI sync clicks.

Beat scheduler: django_celery_beat.schedulers:DatabaseScheduler
(configured in settings.CELERY_BEAT_SCHEDULER)
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield_core.settings")

app = Celery("cybershield")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# ── Periodic Task: Wazuh telemetry sync every 30 seconds ─────────────────────
# This schedule is registered in the Celery Beat database via the
# django_celery_beat DatabaseScheduler (see settings.CELERY_BEAT_SCHEDULER).
# The sync_all_wazuh_tenants task queries all active tenants with a configured
# Wazuh URL and fires a sync_wazuh_alerts subtask for each one.
app.conf.beat_schedule = {
    "sync-all-wazuh-tenants-every-30s": {
        "task": "ingestion.tasks.sync_all_wazuh_tenants",
        "schedule": 30.0,   # seconds
        "options": {"expires": 25},  # discard if not started within 25 s (prevents queue pile-up)
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
