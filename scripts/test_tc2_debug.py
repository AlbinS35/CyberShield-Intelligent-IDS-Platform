import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://cyber-shield-frontend-app.vercel.app"
SCREENSHOT_DIR = os.path.abspath("tests/e2e/screenshots")

def test_tc2():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--incognito")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 30)

    try:
        print("[1] Navigating to login...")
        driver.get(f"{BASE_URL}/login")
        
        print("[2] Selecting Security Analyst role...")
        tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Security Analyst')]")))
        tab.click()
        time.sleep(1)

        print("[3] Clicking Sign In...")
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        btn.click()

        print("[4] Waiting for redirect to /analyst...")
        wait.until(EC.url_contains("/analyst"))
        print(f"[OK] Logged in successfully! URL: {driver.current_url}")
        time.sleep(3)

        # Check KPI Widgets on Dashboard
        print("[5] Waiting for Dashboard KPI widgets...")
        wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Total Alerts') or contains(text(), 'CRITICAL') or contains(text(), 'Security Operations Center')]")))
        
        # Save Dashboard screenshot
        dash_shot = os.path.join(SCREENSHOT_DIR, "Figure_16_TC_SOC_02_Dashboard_KPI.png")
        driver.save_screenshot(dash_shot)
        print(f"[OK] Dashboard KPI Screenshot saved: {dash_shot}")

        # Navigate to Alert Feed
        print("[6] Navigating to /analyst/alerts...")
        driver.get(f"{BASE_URL}/analyst/alerts")
        time.sleep(3)
        alerts_shot = os.path.join(SCREENSHOT_DIR, "Figure_16_TC_SOC_02_Dashboard_Alerts.png")
        driver.save_screenshot(alerts_shot)
        print(f"[OK] Alert Feed Screenshot saved: {alerts_shot}")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_tc2()
