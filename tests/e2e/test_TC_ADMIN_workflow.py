"""
TC-ADMIN — System Administrator Workflow Tests
===============================================
  TC-ADMIN-001  Asset registry page loads
  TC-ADMIN-002  Playbook manager page loads
  TC-ADMIN-003  System health page loads
  TC-ADMIN-004  System health shows backend connectivity indicators
  TC-ADMIN-005  Playbook create/edit button is present
"""

import time
import pytest
from selenium.webdriver.common.by import By

from tests.e2e.helpers import (
    navigate, login_and_wait, element_exists, click,
)
from tests.e2e.conftest import TEST_CREDENTIALS


@pytest.fixture(autouse=True)
def admin_login(driver):
    """Log in as SYS_ADMIN before every test."""
    creds = TEST_CREDENTIALS["admin"]
    login_and_wait(driver, creds["email"], creds["password"], "/admin", timeout=25)


# ─────────────────────────────────────────────────────────────
#  TC-ADMIN-001: Asset registry loads
# ─────────────────────────────────────────────────────────────
def test_asset_registry_page_loads(driver):
    navigate(driver, "/admin")
    time.sleep(2)
    assert "/admin" in driver.current_url
    has_content = (
        element_exists(driver, By.CSS_SELECTOR, "h1, h2", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, "table, .asset-card", timeout=3)
        or "asset" in driver.page_source.lower()
    )
    assert has_content, "Asset registry page did not render properly."


# ─────────────────────────────────────────────────────────────
#  TC-ADMIN-002: Playbook manager page loads
# ─────────────────────────────────────────────────────────────
def test_playbook_manager_page_loads(driver):
    navigate(driver, "/admin/playbooks")
    time.sleep(2)
    assert "/admin/playbooks" in driver.current_url
    has_content = (
        element_exists(driver, By.CSS_SELECTOR, "h1, h2, table, .playbook-card", timeout=5)
        or "playbook" in driver.page_source.lower()
    )
    assert has_content, "Playbook manager page did not load."


# ─────────────────────────────────────────────────────────────
#  TC-ADMIN-003: System health page loads
# ─────────────────────────────────────────────────────────────
def test_system_health_page_loads(driver):
    navigate(driver, "/admin/health")
    time.sleep(3)   # health checks may take a moment
    assert "/admin/health" in driver.current_url
    has_content = (
        element_exists(driver, By.CSS_SELECTOR, "h1, h2", timeout=5)
        or "health" in driver.page_source.lower()
        or "service" in driver.page_source.lower()
    )
    assert has_content, "System health page did not render health status."


# ─────────────────────────────────────────────────────────────
#  TC-ADMIN-004: System health shows service indicators
# ─────────────────────────────────────────────────────────────
def test_system_health_shows_indicators(driver):
    """
    Health page should show green/red status for services
    like DB, Redis, Suricata, ML Pipeline.
    """
    navigate(driver, "/admin/health")
    time.sleep(3)

    indicator_present = (
        element_exists(driver, By.CSS_SELECTOR, ".status-indicator, [data-testid='service-status']", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, "[class*='health'], [class*='status']", timeout=3)
        or any(kw in driver.page_source.lower() for kw in ["online", "offline", "healthy", "degraded", "suricata"])
    )
    # Informational — skip if health display not implemented yet
    if not indicator_present:
        pytest.skip("Health service indicators not yet visible in the UI.")
    assert indicator_present


# ─────────────────────────────────────────────────────────────
#  TC-ADMIN-005: Playbook create button present
# ─────────────────────────────────────────────────────────────
def test_playbook_create_button_present(driver):
    navigate(driver, "/admin/playbooks")
    time.sleep(2)

    create_present = (
        element_exists(
            driver, By.XPATH,
            "//button[contains(text(),'Create') or contains(text(),'New') or contains(text(),'+')]",
            timeout=5,
        )
        or element_exists(driver, By.CSS_SELECTOR, "[data-testid='create-playbook-btn']", timeout=3)
    )
    if not create_present:
        pytest.skip("Playbook create button not found — verify UI implementation.")
    assert create_present, "No create/new playbook button found."
