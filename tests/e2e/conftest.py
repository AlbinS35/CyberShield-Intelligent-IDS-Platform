"""
CyberShield IDS — Selenium E2E Test Configuration
====================================================
Shared pytest fixtures for all end-to-end tests.
Sets up Chrome WebDriver with smart wait strategies.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ──────────────────────────────────────────────
# Application URLs — update if ports change
# ──────────────────────────────────────────────
FRONTEND_URL = "http://localhost:5173"
BACKEND_URL  = "http://localhost:8000"

# Default test credentials — must match bootstrap_db.py --seed output
# Seeded by: python bootstrap_db.py --pg-password <pw> --migrate --seed
TEST_CREDENTIALS = {
    "analyst": {
        "email":    "analyst@cybershield.demo",
        "password": "CyberShield@2024",
        "role":     "ANALYST",
        "dashboard_path": "/analyst",
    },
    "investigator": {
        "email":    "investigator@cybershield.demo",
        "password": "CyberShield@2024",
        "role":     "INVESTIGATOR",
        "dashboard_path": "/forensics",
    },
    "admin": {
        "email":    "admin@cybershield.demo",
        "password": "CyberShield@2024",
        "role":     "SYS_ADMIN",
        "dashboard_path": "/admin",
    },
    "manager": {
        "email":    "manager@cybershield.demo",
        "password": "CyberShield@2024",
        "role":     "ORG_MANAGER",
        "dashboard_path": "/org",
    },
}


def build_chrome_options(headless: bool = False) -> Options:
    """Return Chrome options suited for CI and local runs."""
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--incognito")              # fresh cookie jar per test — no bleed from real browser
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    # Suppress console noise
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    return opts


@pytest.fixture(scope="function")
def driver(request):
    """
    Per-test Chrome WebDriver fixture.
    Automatically quits the browser after each test.
    Set --headless flag for CI.
    """
    headless = request.config.getoption("--headless", default=False)
    service  = Service(ChromeDriverManager().install())
    options  = build_chrome_options(headless=headless)

    browser = webdriver.Chrome(service=service, options=options)
    browser.implicitly_wait(10)
    browser.set_page_load_timeout(30)

    yield browser

    # Screenshot on test failure for debugging
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        ts   = int(time.time())
        name = request.node.name.replace(" ", "_")
        import os; os.makedirs("tests/e2e/screenshots", exist_ok=True)
        browser.save_screenshot(f"tests/e2e/screenshots/FAIL_{name}_{ts}.png")

    browser.quit()


@pytest.fixture(scope="session")
def base_url():
    """Return the frontend base URL."""
    return FRONTEND_URL


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run Chrome in headless mode (no visible browser window).",
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Expose test result to the driver fixture for failure screenshots."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
