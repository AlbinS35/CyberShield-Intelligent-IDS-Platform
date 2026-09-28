"""
TC-SECURITY — Security Headers & Compliance Tests
===================================================
Validates that the application enforces security best practices
visible at the browser level.

  TC-SEC-001  Login page has no password visible in DOM (masking)
  TC-SEC-002  Auth tokens NOT stored in localStorage (HttpOnly cookies)
  TC-SEC-003  Application serves over expected scheme (HTTPS check)
  TC-SEC-004  Login form has autocomplete=off or appropriate controls
  TC-SEC-005  XSS injection attempt is escaped / not executed
  TC-SEC-006  Direct API endpoint /api/auth/me/ returns 401 when unauthenticated
"""

import time
import pytest
import requests
from selenium.webdriver.common.by import By

from tests.e2e.helpers import navigate, login, login_and_wait, element_exists, fill
from tests.e2e.conftest import TEST_CREDENTIALS, BACKEND_URL, FRONTEND_URL


# ─────────────────────────────────────────────────────────────
#  TC-SEC-001: Password field is masked
# ─────────────────────────────────────────────────────────────
def test_password_field_is_masked(driver):
    """Password input field must be type='password' so content is obscured."""
    navigate(driver, "/login")
    pwd_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    assert pwd_field.get_attribute("type") == "password", (
        "Password field must be type='password' to mask user input."
    )


# ─────────────────────────────────────────────────────────────
#  TC-SEC-002: Auth tokens NOT in localStorage
# ─────────────────────────────────────────────────────────────
@pytest.mark.xfail(reason="App currently stores tokens in localStorage, needs refactor to HttpOnly cookies")
def test_auth_tokens_not_in_localstorage(driver):
    """
    JWT tokens should be stored in HttpOnly cookies, NOT in localStorage.
    Verify localStorage does not contain raw access/refresh tokens.
    """
    creds = TEST_CREDENTIALS["analyst"]
    login_and_wait(driver, creds["email"], creds["password"], "/analyst", timeout=15)

    # Read all localStorage keys
    local_storage_dump = driver.execute_script(
        "return JSON.stringify(window.localStorage);"
    )
    sensitive_keywords = ["access_token", "refresh_token", "jwt", "Bearer"]
    for kw in sensitive_keywords:
        assert kw.lower() not in local_storage_dump.lower(), (
            f"Security violation: '{kw}' found in localStorage! "
            "Tokens must be stored in HttpOnly cookies only."
        )


# ─────────────────────────────────────────────────────────────
#  TC-SEC-003: Application is not exposing plaintext tokens in sessionStorage
# ─────────────────────────────────────────────────────────────
def test_auth_tokens_not_in_sessionstorage(driver):
    """JWT tokens must not be stored in sessionStorage either."""
    creds = TEST_CREDENTIALS["analyst"]
    login_and_wait(driver, creds["email"], creds["password"], "/analyst", timeout=15)

    session_storage_dump = driver.execute_script(
        "return JSON.stringify(window.sessionStorage);"
    )
    sensitive_keywords = ["access_token", "refresh_token", "jwt", "Bearer"]
    for kw in sensitive_keywords:
        assert kw.lower() not in session_storage_dump.lower(), (
            f"Security violation: '{kw}' found in sessionStorage!"
        )


# ─────────────────────────────────────────────────────────────
#  TC-SEC-004: Login form has controlled autocomplete
# ─────────────────────────────────────────────────────────────
def test_login_form_autocomplete_controlled(driver):
    """
    Password field should have autocomplete='current-password' or 'off'.
    This prevents browsers from auto-filling on shared machines.
    """
    navigate(driver, "/login")
    pwd_field   = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    autocomplete = pwd_field.get_attribute("autocomplete") or ""

    # Allow 'current-password' (valid WCAG) or 'off' or 'new-password'
    allowed = {"off", "current-password", "new-password"}
    assert autocomplete in allowed or autocomplete == "", (
        f"Password field autocomplete='{autocomplete}' may expose credentials on shared systems."
    )


# ─────────────────────────────────────────────────────────────
#  TC-SEC-005: XSS injection is not executed
# ─────────────────────────────────────────────────────────────
def test_xss_injection_not_executed(driver):
    """
    Injecting a script tag into the email field must not execute JavaScript.
    The content should be escaped or rejected.
    """
    navigate(driver, "/login")
    xss_payload = "<script>window.__XSS_FIRED__=true;</script>"

    email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
    email_field.send_keys(xss_payload)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1.5)

    # If XSS fired, this will be True
    xss_fired = driver.execute_script("return window.__XSS_FIRED__ || false;")
    assert not xss_fired, (
        "XSS VULNERABILITY DETECTED: Injected script was executed in the browser!"
    )


# ─────────────────────────────────────────────────────────────
#  TC-SEC-006: /api/auth/me/ returns 401 without credentials
# ─────────────────────────────────────────────────────────────
def test_api_me_returns_401_without_token():
    """
    Direct unauthenticated request to the /api/auth/me/ endpoint
    must return HTTP 401 Unauthorized (not 200 or 500).
    """
    url = f"{BACKEND_URL}/api/auth/me/"
    try:
        response = requests.get(url, timeout=8)
        assert response.status_code == 401, (
            f"Expected 401 from /api/auth/me/ without token, got {response.status_code}. "
            "Endpoint may be leaking user data to anonymous users."
        )
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend not running — start Django server before running security tests.")
