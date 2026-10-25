import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://cyber-shield-frontend-app.vercel.app"
SCREENSHOT_DIR = os.path.abspath("tests/e2e/screenshots")

def capture_evidence_vault():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--incognito")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 25)

    try:
        print("[1] Opening login page...")
        driver.get(f"{BASE_URL}/login")
        time.sleep(1)

        print("[2] Selecting Forensic Investigator role...")
        investigator_card = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(., 'Forensic Investigator') and contains(@class, 'role-card')]")
        ))
        driver.execute_script("arguments[0].click();", investigator_card)
        time.sleep(1)

        print("[3] Clicking Sign In...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_btn.click()

        print("[4] Waiting for redirect to /forensics...")
        wait.until(EC.url_contains("/forensics"))
        print(f"[OK] Logged in successfully: {driver.current_url}")
        time.sleep(2)

        # Click the 'Evidence' link in the sidebar!
        print("[5] Navigating to /forensics/evidence (Evidence Vault)...")
        evidence_nav = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='/forensics/evidence']")
        ))
        evidence_nav.click()
        time.sleep(3)
        print(f"[OK] Reached Vault! Current URL: {driver.current_url}")

        # Assert Evidence Vault is visible
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(), 'Evidence Vault') or contains(text(), 'Evidence Repository') or contains(text(), 'SHA-256')]")
        ))

        # Save both Figure 19 and Figure 27!
        p19 = os.path.join(SCREENSHOT_DIR, "Figure_19_TC_FOR_05_Evidence_Vault.png")
        p27 = os.path.join(SCREENSHOT_DIR, "Figure_27_Forensic_Evidence_Vault.png")
        driver.save_screenshot(p19)
        driver.save_screenshot(p27)
        print(f"[SUCCESS] Saved Evidence Vault screenshot to:\n  - {p19}\n  - {p27}")

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_evidence_vault()
