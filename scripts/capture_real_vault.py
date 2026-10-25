import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://cyber-shield-frontend-app.vercel.app"
SCREENSHOT_DIR = os.path.abspath("tests/e2e/screenshots")

def test_investigator_vault():
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
        print("[1] Navigating to login...")
        driver.get(f"{BASE_URL}/login")
        time.sleep(1)

        print("[2] Selecting 'Forensic Investigator' role card via JS click...")
        investigator_card = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(., 'Forensic Investigator') and contains(@class, 'role-card')]")
        ))
        driver.execute_script("arguments[0].click();", investigator_card)
        time.sleep(1)

        # Explicitly verify input fields
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_val = email_input.get_attribute("value")
        print(f"[*] Email field has: {email_val}")
        if "investigator" not in email_val:
            email_input.clear()
            email_input.send_keys("investigator@cybershield.demo")
            pwd_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            pwd_input.clear()
            pwd_input.send_keys("CyberShield@2024")

        print("[3] Clicking Sign In button...")
        submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        submit_btn.click()

        print("[4] Waiting for redirect to /forensics...")
        wait.until(EC.url_contains("/forensics"))
        print(f"[OK] Logged in as Investigator! URL: {driver.current_url}")
        time.sleep(3)

        print("[5] Navigating to /forensics/vault ...")
        driver.get(f"{BASE_URL}/forensics/vault")
        time.sleep(4)
        print(f"[OK] Current URL: {driver.current_url}")

        # Assert vault page loaded
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Vault') or contains(text(), 'Evidence') or contains(text(), 'SHA-256') or contains(text(), 'Hash')]")))
        
        vault_path = os.path.join(SCREENSHOT_DIR, "Figure_27_Forensic_Evidence_Vault.png")
        driver.save_screenshot(vault_path)
        print(f"[SUCCESS] Real Forensic Vault screenshot saved to: {vault_path}")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_investigator_vault()
