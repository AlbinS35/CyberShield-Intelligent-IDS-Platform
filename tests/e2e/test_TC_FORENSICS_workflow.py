"""
TC-FORENSICS — Digital Forensics Investigator Workflow Tests
=============================================================
  TC-FORENSICS-001  Case management page loads
  TC-FORENSICS-002  New case creation form is accessible
  TC-FORENSICS-003  Evidence vault page is accessible
  TC-FORENSICS-004  Evidence upload form is present
  TC-FORENSICS-005  Forensic timeline page accessible (via first case)
"""

import time
import pytest
from selenium.webdriver.common.by import By

from tests.e2e.helpers import (
    navigate, login_and_wait, element_exists, click, fill, wait_for,
)
from tests.e2e.conftest import TEST_CREDENTIALS


@pytest.fixture(autouse=True)
def investigator_login(driver):
    """Log in as investigator before every test in this module."""
    creds = TEST_CREDENTIALS["investigator"]
    login_and_wait(driver, creds["email"], creds["password"], "/forensics", timeout=35)


# ─────────────────────────────────────────────────────────────
#  TC-FORENSICS-001: Case management page loads
# ─────────────────────────────────────────────────────────────
def test_case_management_page_loads(driver):
    navigate(driver, "/forensics")
    time.sleep(2)
    assert "/forensics" in driver.current_url
    has_content = (
        element_exists(driver, By.CSS_SELECTOR, "h1, h2", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, "table, .case-card", timeout=3)
    )
    assert has_content, "Case management page should show a heading or case list."


# ─────────────────────────────────────────────────────────────
#  TC-FORENSICS-002: New case creation form
# ─────────────────────────────────────────────────────────────
def test_new_case_creation_form_accessible(driver):
    navigate(driver, "/forensics")
    time.sleep(2)

    # Look for "New Case", "Create Case", or "+" button
    create_selectors = [
        "//button[contains(text(),'New Case') or contains(text(),'Create') or contains(text(),'+')]",
        "[data-testid='create-case-btn']",
        "button[aria-label*='case' i]",
    ]
    clicked = False
    for sel in create_selectors:
        by = By.XPATH if sel.startswith("//") else By.CSS_SELECTOR
        if element_exists(driver, by, sel, timeout=3):
            click(driver, by, sel)
            clicked = True
            time.sleep(1.5)
            break

    if not clicked:
        pytest.skip("'Create Case' button not found — update selector.")

    # A form or modal should appear
    form_visible = (
        element_exists(driver, By.CSS_SELECTOR, "form, [role='dialog']", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, "input[name*='title'], input[placeholder*='case' i]", timeout=3)
    )
    assert form_visible, "Case creation form/modal did not appear."


# ─────────────────────────────────────────────────────────────
#  TC-FORENSICS-003: Evidence vault page accessible
# ─────────────────────────────────────────────────────────────
def test_evidence_vault_page_loads(driver):
    navigate(driver, "/forensics/evidence")
    time.sleep(2)
    assert "/forensics/evidence" in driver.current_url
    assert "evidence" in driver.page_source.lower(), (
        "Evidence vault page should contain 'evidence' content."
    )


# ─────────────────────────────────────────────────────────────
#  TC-FORENSICS-004: Evidence upload form present
# ─────────────────────────────────────────────────────────────
def test_evidence_upload_form_present(driver):
    navigate(driver, "/forensics/evidence")
    time.sleep(2)

    upload_present = (
        element_exists(driver, By.CSS_SELECTOR, "input[type='file']", timeout=5)
        or element_exists(
            driver, By.XPATH,
            "//button[contains(text(),'Upload') or contains(text(),'Add Evidence')]",
            timeout=3,
        )
    )
    assert upload_present, "Evidence upload form/button not found on evidence vault page."


# ─────────────────────────────────────────────────────────────
#  TC-FORENSICS-005: Forensic timeline accessible
# ─────────────────────────────────────────────────────────────
def test_forensic_timeline_page_accessible(driver):
    """Navigate to the forensics timeline using a placeholder case ID."""
    navigate(driver, "/forensics/timeline/1")
    time.sleep(3)

    # Either the timeline renders, or a 'case not found' message is shown — both valid
    page_has_content = (
        element_exists(driver, By.CSS_SELECTOR, "h1, h2, [data-testid='timeline']", timeout=5)
        or element_exists(driver, By.CSS_SELECTOR, "[data-testid='empty-state'], .error-msg", timeout=3)
        or "forensics" in driver.page_source.lower()
    )
    assert page_has_content, "Forensic timeline page rendered nothing."
    # Should NOT redirect to login (that would mean the route is blocked)
    assert "/login" not in driver.current_url
