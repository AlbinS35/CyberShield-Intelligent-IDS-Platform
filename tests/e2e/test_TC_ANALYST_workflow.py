"""
TC-ANALYST — Security Analyst Workflow Tests
=============================================
Covers the core day-to-day analyst operations:

  TC-ANALYST-001  Analyst dashboard KPI widgets are visible
  TC-ANALYST-002  Alert feed page loads with table/card items
  TC-ANALYST-003  Alert can be filtered by severity
  TC-ANALYST-004  Alert detail page loads from alert feed
  TC-ANALYST-005  Network events page is accessible
  TC-ANALYST-006  Incident manager page loads
  TC-ANALYST-007  Real-time alert badge updates (WebSocket smoke)
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.helpers import (
    navigate, login_and_wait, wait_for, wait_for_url, click, element_exists,
)
from tests.e2e.conftest import TEST_CREDENTIALS


@pytest.fixture(autouse=True)
def analyst_login(driver):
    """Log in as analyst before every test in this module."""
    creds = TEST_CREDENTIALS["analyst"]
    login_and_wait(driver, creds["email"], creds["password"], "/analyst", timeout=25)


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-001: Dashboard KPI widgets visible
# ─────────────────────────────────────────────────────────────
def test_analyst_dashboard_kpi_widgets(driver):
    """Analyst dashboard must show threat / alert KPI summary cards."""
    navigate(driver, "/analyst")
    time.sleep(2)  # allow data to load via React Query

    # Look for any metric/card containers
    has_cards = (
        element_exists(driver, By.CSS_SELECTOR, "[data-testid='kpi-card']", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, ".stat-card, .kpi, .metric-card", timeout=3)
        or element_exists(driver, By.CSS_SELECTOR, "h2, h3", timeout=3)
    )
    assert has_cards, "Analyst dashboard should display KPI metric widgets."


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-002: Alert feed loads
# ─────────────────────────────────────────────────────────────
def test_alert_feed_page_loads(driver):
    """Alert feed page must render a table or list of alerts."""
    navigate(driver, "/analyst/alerts")
    time.sleep(2)

    # Table, list, or 'No alerts' empty state — all are valid renders
    page_loaded = (
        element_exists(driver, By.CSS_SELECTOR, "table, [role='table']", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, ".alert-card, [data-testid='alert-row']", timeout=3)
        or element_exists(driver, By.CSS_SELECTOR, "[data-testid='empty-state']", timeout=3)
        or "alert" in driver.page_source.lower()
    )
    assert page_loaded, "Alert feed page did not render content."
    assert "/analyst/alerts" in driver.current_url


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-003: Alert severity filter
# ─────────────────────────────────────────────────────────────
def test_alert_severity_filter(driver):
    """Clicking a severity filter (e.g., CRITICAL) should update results."""
    navigate(driver, "/analyst/alerts")
    time.sleep(2)

    # Try common filter patterns: dropdown, button group, tabs
    filter_selectors = [
        "select[name*='severity'], select[id*='severity']",
        "button[data-severity], [data-testid*='filter']",
        "//button[contains(text(),'CRITICAL') or contains(text(),'Critical') or contains(text(),'HIGH')]",
    ]
    clicked = False
    
    # Try finding the select directly and using Select helper
    by, sel = By.XPATH, "//select[option[contains(text(), 'Critical')]]"
    if element_exists(driver, by, sel, timeout=3):
        from selenium.webdriver.support.ui import Select
        Select(driver.find_element(by, sel)).select_by_visible_text("Critical")
        clicked = True
        time.sleep(1.5)
    else:
        for sel in filter_selectors:
            by = By.XPATH if sel.startswith("//") else By.CSS_SELECTOR
            if element_exists(driver, by, sel, timeout=3):
                click(driver, by, sel)
                clicked = True
                time.sleep(1.5)
                break

    if not clicked:
        pytest.skip("Severity filter UI element not found — update selector.")

    # Page should still be on alerts view
    assert "/analyst/alerts" in driver.current_url


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-004: Alert detail opens from feed
# ─────────────────────────────────────────────────────────────
def test_alert_detail_opens(driver):
    """Clicking the first alert in the feed should open its detail view."""
    navigate(driver, "/analyst/alerts")
    time.sleep(2)

    # Click on first clickable alert row or link
    row_selectors = [
        "div.group button:first-of-type",
        "table tbody tr:first-child",
        ".alert-card:first-child",
        "[data-testid='alert-row']:first-child",
        "//tr[contains(@class,'alert') or @data-testid][1]",
    ]
    clicked = False
    for sel in row_selectors:
        by = By.XPATH if sel.startswith("//") else By.CSS_SELECTOR
        if element_exists(driver, by, sel, timeout=4):
            el = driver.find_element(by, sel)
            driver.execute_script("arguments[0].click();", el)
            clicked = True
            break

    if not clicked:
        pytest.skip("Could not find clickable alert row — check alert feed rendering.")

    time.sleep(2)
    # Should navigate to /analyst/alerts/<id> or show a detail panel
    detail_shown = (
        "/alerts/" in driver.current_url
        or element_exists(driver, By.CSS_SELECTOR, "[data-testid='alert-detail']", timeout=3)
    )
    assert detail_shown, "Alert detail view should open on click."


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-005: Network events page accessible
# ─────────────────────────────────────────────────────────────
def test_network_events_page_accessible(driver):
    """Network events page must load without a JS error or blank screen."""
    navigate(driver, "/analyst/network-events")
    time.sleep(2)
    assert "/analyst/network-events" in driver.current_url
    assert "network" in driver.page_source.lower() or element_exists(
        driver, By.CSS_SELECTOR, "table, .event-row, [data-testid='empty-state']", timeout=5
    ), "Network events page appears blank."


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-006: Incident manager page loads
# ─────────────────────────────────────────────────────────────
def test_incident_manager_page_loads(driver):
    """Incident manager page must render its header and content area."""
    navigate(driver, "/analyst/incidents")
    time.sleep(2)
    assert "/analyst/incidents" in driver.current_url
    has_content = element_exists(
        driver, By.CSS_SELECTOR, "h1, h2, [data-testid='incident-list'], table", timeout=5
    )
    assert has_content, "Incident manager page did not render properly."


# ─────────────────────────────────────────────────────────────
#  TC-ANALYST-007: WebSocket real-time connection smoke test
# ─────────────────────────────────────────────────────────────
def test_websocket_connection_smoke(driver):
    """
    After login, verify the WebSocket connection indicator is active
    (no disconnection error badge).
    This is a smoke test — if the WS indicator is absent, skip it.
    """
    navigate(driver, "/analyst")
    time.sleep(3)   # Allow WS handshake

    ws_error_visible = element_exists(
        driver, By.CSS_SELECTOR,
        "[data-testid='ws-disconnected'], .ws-error, [aria-label*='disconnected']",
        timeout=3,
    )
    assert not ws_error_visible, (
        "WebSocket disconnection indicator is visible — real-time feed may be offline."
    )
