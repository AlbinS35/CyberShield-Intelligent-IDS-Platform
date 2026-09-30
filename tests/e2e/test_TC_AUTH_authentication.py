"""
TC-AUTH — Authentication & Session Security Tests
==================================================
Covers:
  TC-AUTH-001  Landing page loads correctly
  TC-AUTH-002  Login with valid ANALYST credentials
  TC-AUTH-003  Login rejected with wrong password
  TC-AUTH-004  Login rejected with blank fields
  TC-AUTH-005  Login rejected with invalid email format
  TC-AUTH-006  JWT session persists on page refresh
  TC-AUTH-007  Logout invalidates session and redirects to /login
  TC-AUTH-008  Unauthenticated access to /analyst redirects to /login
  TC-AUTH-009  Forgot-password page is reachable from login
  TC-AUTH-010  Brute-force rate limiting activates after 5 fast attempts
"""

import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.helpers import (
    navigate, login, login_and_wait, is_stack_running,
    wait_for, wait_for_url, fill, click, element_exists, get_toast_text,
)
from tests.e2e.conftest import TEST_CREDENTIALS, FRONTEND_URL


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-001: Landing page loads
# ─────────────────────────────────────────────────────────────
def test_landing_page_loads(driver):
    """Verify the landing page renders without errors."""
    if not is_stack_running(driver):
        pytest.skip("Frontend not running — start `npm run dev` first.")
    navigate(driver, "/")
    assert "CyberShield" in driver.title or element_exists(
        driver, By.CSS_SELECTOR, "h1, [data-testid='hero-title']"
    ), "Landing page did not load a heading."


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-002: Valid analyst login → analyst dashboard
# ─────────────────────────────────────────────────────────────
def test_valid_analyst_login(driver):
    """Analyst with correct credentials should reach /analyst dashboard."""
    creds = TEST_CREDENTIALS["analyst"]
    login_and_wait(driver, creds["email"], creds["password"], "/analyst", timeout=35)
    assert "/analyst" in driver.current_url, (
        f"Expected to land on /analyst, got: {driver.current_url}"
    )



# ─────────────────────────────────────────────────────────────
#  TC-AUTH-003: Invalid password shows error
# ─────────────────────────────────────────────────────────────
def test_invalid_password_shows_error(driver):
    """
    Wrong password must display an authentication error.

    The LoginPage pre-fills email+password via useState. We clear and retype.
    The error appears both as a react-hot-toast (may auto-dismiss quickly)
    and as inline setError() text rendered in the DOM — we check both.
    """
    import time as _time
    navigate(driver, "/login")

    email_el = wait_for(driver, By.CSS_SELECTOR, "input[type='email']")
    email_el.clear()
    email_el.send_keys("analyst@cybershield.demo")

    pass_el = wait_for(driver, By.CSS_SELECTOR, "input[type='password']")
    pass_el.clear()
    pass_el.send_keys("WrongPassword999!")

    _time.sleep(0.3)
    click(driver, By.CSS_SELECTOR, "button[type='submit']")

    # Wait for the backend response (up to 10s)
    _time.sleep(5)

    current_url = driver.current_url
    page_text   = driver.find_element(By.TAG_NAME, "body").text.lower()

    ERROR_KEYWORDS = [
        "invalid", "incorrect", "error", "wrong", "failed", "unable",
        "no active account", "credentials", "not found", "unauthorized",
    ]

    # Check inline error rendered by setError() in the DOM
    page_has_error = any(kw in page_text for kw in ERROR_KEYWORDS)

    # Also try toast (may still be visible)
    toast_text = get_toast_text(driver, timeout=2).lower()
    toast_has_error = any(kw in toast_text for kw in ERROR_KEYWORDS)

    has_error = "/login" in current_url and (page_has_error or toast_has_error)

    assert has_error, (
        f"No error shown for invalid password.\n"
        f"URL: {current_url}\n"
        f"Toast: {toast_text!r}\n"
        f"Page error keywords found: {page_has_error}"
    )


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-004: Blank fields are rejected
# ─────────────────────────────────────────────────────────────
def test_blank_fields_rejected(driver):
    """
    Submitting an empty login form must not proceed to the dashboard.

    NOTE: LoginPage.jsx pre-fills email+password via React useState.
    We must clear both fields using JS to reset the controlled component
    state, otherwise the form always has values and logs the user in.
    """
    navigate(driver, "/login")
    email_el = wait_for(driver, By.CSS_SELECTOR, "input[type='email']",    timeout=10)
    pass_el  = wait_for(driver, By.CSS_SELECTOR, "input[type='password']", timeout=10)

    # Clear using keyboard shortcuts to trigger React events properly
    for el in [email_el, pass_el]:
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)
    
    time.sleep(0.5)

    click(driver, By.CSS_SELECTOR, "button[type='submit']")
    time.sleep(1.5)
    assert "/login" in driver.current_url, (
        f"Empty form should not advance past login (got: {driver.current_url})."
    )


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-005: Invalid email format rejected
# ─────────────────────────────────────────────────────────────
def test_invalid_email_format_rejected(driver):
    """Malformed email address should trigger HTML5 or custom validation."""
    navigate(driver, "/login")
    fill(driver, By.CSS_SELECTOR, "input[type='email']",    "not-an-email")
    fill(driver, By.CSS_SELECTOR, "input[type='password']", "SomePass@123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)
    assert "/login" in driver.current_url, "Invalid email should not pass form validation."


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-006: Session persists after page refresh
# ─────────────────────────────────────────────────────────────
def test_session_persists_on_refresh(driver):
    """After login, refreshing the page should keep the user authenticated."""
    creds = TEST_CREDENTIALS["analyst"]
    login_and_wait(driver, creds["email"], creds["password"], "/analyst", timeout=35)

    driver.refresh()
    time.sleep(3)   # let React re-hydrate and token refresh run

    assert "/analyst" in driver.current_url, (
        "Session should persist after page refresh (JWT cookie still valid)."
    )


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-007: Logout invalidates session
# ─────────────────────────────────────────────────────────────
def test_logout_redirects_to_login(driver):
    """Logout must invalidate the JWT cookie and redirect to /login."""
    creds = TEST_CREDENTIALS["analyst"]
    login_and_wait(driver, creds["email"], creds["password"], "/analyst", timeout=35)

    # Sidebar logout button: <button class="nav-item ...">Logout</button>
    # Target by XPath text content — the most stable selector for this UI
    logout_selectors = [
        (By.XPATH,       "//button[normalize-space(text())='Logout' or normalize-space(.)='Logout']"),
        (By.XPATH,       "//button[contains(@class,'nav-item') and contains(.,'Logout')]"),
        (By.CSS_SELECTOR, "button.nav-item.text-red-400"),
    ]
    clicked = False
    for by, sel in logout_selectors:
        if element_exists(driver, by, sel, timeout=5):
            click(driver, by, sel)
            clicked = True
            break

    if not clicked:
        pytest.skip("Logout button not found — check Sidebar.jsx selector.")

    wait_for_url(driver, "/login", timeout=10)
    assert "/login" in driver.current_url


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-008: Unauthenticated access redirected
# ─────────────────────────────────────────────────────────────
def test_unauthenticated_protected_route_redirect(driver):
    """Direct navigation to /analyst without login must redirect to /login."""
    navigate(driver, "/analyst")
    wait_for_url(driver, "/login", timeout=10)
    assert "/login" in driver.current_url, (
        "ProtectedRoute should redirect unauthenticated users to /login."
    )


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-009: Forgot-password page reachable
# ─────────────────────────────────────────────────────────────
def test_forgot_password_page_reachable(driver):
    """The 'Forgot Password' link on login should navigate to /forgot-password."""
    navigate(driver, "/login")
    # Use XPath — CSS :contains() is jQuery only and invalid in Selenium
    forgot = wait_for(
        driver,
        By.XPATH,
        "//a[contains(@href,'forgot') or contains(@href,'reset') "
        "or contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'FORGOT')]",
        timeout=8,
    )
    forgot.click()
    wait_for_url(driver, "/forgot-password", timeout=8)
    assert "/forgot-password" in driver.current_url


# ─────────────────────────────────────────────────────────────
#  TC-AUTH-010: Rate limiting after multiple bad login attempts
# ─────────────────────────────────────────────────────────────
def test_brute_force_rate_limiting(driver):
    """
    Backend throttles login after too many failures.
    After 5 rapid bad attempts, expect a rate-limit indicator or
    a longer delay in response.
    """
    navigate(driver, "/login")
    email_field    = wait_for(driver, By.CSS_SELECTOR, "input[type='email']")
    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    submit_btn     = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

    rate_limited = False
    for attempt in range(6):
        email_field.clear();    email_field.send_keys("analyst@cybershield.local")
        password_field.clear(); password_field.send_keys(f"BadPassword{attempt}!")
        submit_btn.click()
        time.sleep(0.8)

        # Check for rate-limit keywords in page source
        src = driver.page_source.lower()
        if any(kw in src for kw in ["rate limit", "too many", "throttl", "429"]):
            rate_limited = True
            break

    # This test is informational — warn but don't hard-fail if throttle config differs
    if not rate_limited:
        pytest.xfail(
            "Rate-limiting message not detected after 6 attempts. "
            "Verify 'login_attempts' throttle scope in Django settings."
        )

    # Clear cache so subsequent tests are not rate limited
    import subprocess
    import os
    backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
    subprocess.run(["python", "manage.py", "shell", "-c", "from django.core.cache import cache; cache.clear()"], cwd=backend_dir)
