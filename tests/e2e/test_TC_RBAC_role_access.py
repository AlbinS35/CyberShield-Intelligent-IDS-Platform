"""
TC-RBAC — Role-Based Access Control Tests
==========================================
Verifies that each user role lands on the correct dashboard
and CANNOT access routes reserved for other roles.

  TC-RBAC-001  ANALYST lands on /analyst after login
  TC-RBAC-002  INVESTIGATOR lands on /forensics after login
  TC-RBAC-003  SYS_ADMIN lands on /admin after login
  TC-RBAC-004  ORG_MANAGER lands on /org after login
  TC-RBAC-005  ANALYST cannot access /admin (forbidden)
  TC-RBAC-006  ANALYST cannot access /forensics (forbidden)
  TC-RBAC-007  INVESTIGATOR cannot access /analyst (forbidden)
  TC-RBAC-008  SYS_ADMIN cannot access /org (forbidden)
"""

import pytest
import time
from selenium.webdriver.common.by import By

from tests.e2e.helpers import navigate, login_and_wait, element_exists
from tests.e2e.conftest import TEST_CREDENTIALS


def _login_role(driver, role_key: str):
    """Helper: login as a specific role and wait for redirect."""
    creds = TEST_CREDENTIALS[role_key]
    login_and_wait(driver, creds["email"], creds["password"],
                   creds["dashboard_path"], timeout=25)
    return creds


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-001: ANALYST dashboard access
# ─────────────────────────────────────────────────────────────
def test_analyst_lands_on_analyst_dashboard(driver):
    creds = _login_role(driver, "analyst")
    assert "/analyst" in driver.current_url, (
        f"ANALYST should land on /analyst, got: {driver.current_url}"
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-002: INVESTIGATOR dashboard access
# ─────────────────────────────────────────────────────────────
def test_investigator_lands_on_forensics_dashboard(driver):
    creds = _login_role(driver, "investigator")
    assert "/forensics" in driver.current_url, (
        f"INVESTIGATOR should land on /forensics, got: {driver.current_url}"
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-003: SYS_ADMIN dashboard access
# ─────────────────────────────────────────────────────────────
def test_sysadmin_lands_on_admin_dashboard(driver):
    creds = _login_role(driver, "admin")
    assert "/admin" in driver.current_url, (
        f"SYS_ADMIN should land on /admin, got: {driver.current_url}"
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-004: ORG_MANAGER dashboard access
# ─────────────────────────────────────────────────────────────
def test_orgmanager_lands_on_org_dashboard(driver):
    creds = _login_role(driver, "manager")
    assert "/org" in driver.current_url, (
        f"ORG_MANAGER should land on /org, got: {driver.current_url}"
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-005: ANALYST cannot access /admin
# ─────────────────────────────────────────────────────────────
def test_analyst_cannot_access_admin(driver):
    _login_role(driver, "analyst")
    navigate(driver, "/admin")
    time.sleep(2)
    # ProtectedRoute must redirect away from /admin
    assert "/admin" not in driver.current_url, (
        "ANALYST should NOT be able to access /admin routes."
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-006: ANALYST cannot access /forensics
# ─────────────────────────────────────────────────────────────
def test_analyst_cannot_access_forensics(driver):
    _login_role(driver, "analyst")
    navigate(driver, "/forensics")
    time.sleep(2)
    assert "/forensics" not in driver.current_url, (
        "ANALYST should NOT be able to access /forensics routes."
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-007: INVESTIGATOR cannot access /analyst
# ─────────────────────────────────────────────────────────────
def test_investigator_cannot_access_analyst(driver):
    _login_role(driver, "investigator")
    navigate(driver, "/analyst")
    time.sleep(2)
    assert "/analyst" not in driver.current_url, (
        "INVESTIGATOR should NOT be able to access /analyst routes."
    )


# ─────────────────────────────────────────────────────────────
#  TC-RBAC-008: SYS_ADMIN cannot access /org
# ─────────────────────────────────────────────────────────────
def test_sysadmin_cannot_access_org(driver):
    _login_role(driver, "admin")
    navigate(driver, "/org")
    time.sleep(2)
    assert "/org" not in driver.current_url, (
        "SYS_ADMIN should NOT be able to access /org routes."
    )
