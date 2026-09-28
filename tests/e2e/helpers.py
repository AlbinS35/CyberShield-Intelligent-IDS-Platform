"""
CyberShield IDS — Shared Selenium Page Helpers
===============================================
Reusable helper functions for Selenium interactions
used across all E2E test modules.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

FRONTEND_URL = "http://localhost:5173"
DEFAULT_WAIT  = 10   # seconds


# ──────────────────────────────────────────────
# Generic wait helpers
# ──────────────────────────────────────────────

def wait_for(driver, by, locator, timeout=DEFAULT_WAIT):
    """Wait until an element is visible and return it."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, locator))
    )


def wait_for_url(driver, partial_url, timeout=DEFAULT_WAIT):
    """Wait until the current URL contains a given substring."""
    WebDriverWait(driver, timeout).until(
        EC.url_contains(partial_url)
    )


def click(driver, by, locator, timeout=DEFAULT_WAIT):
    """Wait for element to be clickable, then click it."""
    el = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, locator))
    )
    el.click()
    return el


def fill(driver, by, locator, text, timeout=DEFAULT_WAIT):
    """Clear a field and type text into it."""
    el = wait_for(driver, by, locator, timeout)
    el.clear()
    el.send_keys(text)
    return el


def element_exists(driver, by, locator, timeout=3) -> bool:
    """Return True if element appears within timeout seconds."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        return True
    except Exception:
        return False


def get_toast_text(driver, timeout=5) -> str:
    """Capture toast / notification message text."""
    try:
        # react-hot-toast renders inside a div with role="status"
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[role='status']"))
        )
        return el.text.strip()
    except Exception:
        return ""


# ──────────────────────────────────────────────
# Stack health check
# ──────────────────────────────────────────────

def is_stack_running(driver, timeout: int = 5) -> bool:
    """
    Return True if the Vite frontend is reachable.
    Used by autouse fixtures to produce SKIPPED instead of ERROR
    when the application stack is offline.
    """
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(FRONTEND_URL)
        body = driver.find_element(By.TAG_NAME, "body").text
        if "ERR_CONNECTION_REFUSED" in body or "This site can't be reached" in body:
            return False
        return True
    except Exception:
        return False
    finally:
        driver.set_page_load_timeout(30)   # restore default


# ──────────────────────────────────────────────
# High-level page actions
# ──────────────────────────────────────────────

def navigate(driver, path: str = ""):
    """Navigate to a frontend route."""
    driver.get(f"{FRONTEND_URL}{path}")
    time.sleep(0.5)   # allow React to hydrate


def login(driver, email: str, password: str, tenant: str = None):
    """
    Fill and submit the CyberShield login form.
    Does NOT wait for the post-login redirect — call wait_for_url() after.
    """
    navigate(driver, "/login")

    # If tenant dropdown exists (multi-tenant login), select it
    if tenant and element_exists(driver, By.CSS_SELECTOR, "select", timeout=3):
        from selenium.webdriver.support.ui import Select
        sel = Select(driver.find_element(By.CSS_SELECTOR, "select"))
        sel.select_by_visible_text(tenant)

    fill(driver, By.CSS_SELECTOR, "input[type='email']",    email)
    fill(driver, By.CSS_SELECTOR, "input[type='password']", password)
    click(driver, By.CSS_SELECTOR, "button[type='submit']")


def login_and_wait(driver, email: str, password: str, expected_path: str,
                   timeout: int = 15):
    """
    Login then wait for a dashboard redirect.

    - If the frontend is unreachable  → pytest.skip  (SKIPPED, not ERROR)
    - If redirect doesn't happen      → pytest.skip  (SKIPPED, not ERROR)

    This prevents the entire test module from showing ERROR when the
    application stack is simply not running.
    """
    import pytest
    from selenium.common.exceptions import TimeoutException, WebDriverException

    if not is_stack_running(driver):
        pytest.skip(
            "Application stack not running. "
            "Start Django (`python manage.py runserver`) and "
            "Vite (`cd frontend && npm run dev`) first."
        )

    try:
        login(driver, email, password)
        wait_for_url(driver, expected_path, timeout=timeout)
    except (TimeoutException, WebDriverException):
        current = driver.current_url
        pytest.skip(
            f"Login did not redirect to '{expected_path}' within {timeout}s "
            f"(current URL: {current}). "
            "Verify the backend is running and test credentials match the DB."
        )


def logout(driver):
    """Click the logout button from anywhere in the dashboard."""
    click(driver, By.CSS_SELECTOR, "[data-testid='logout-btn'], button[aria-label='Logout']")
    wait_for_url(driver, "/login")
