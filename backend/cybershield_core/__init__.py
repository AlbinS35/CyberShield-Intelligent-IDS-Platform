"""
CyberShield Django Backend — __init__.py
Ensures Celery app is loaded when Django starts (required for @shared_task).
"""

from .celery import app as celery_app
import pymysql

pymysql.install_as_MySQLdb()

__all__ = ("celery_app",)
