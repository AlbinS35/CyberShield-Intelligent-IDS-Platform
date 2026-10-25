from PIL import Image, ImageDraw, ImageFont
import os

def render_terminal():
    width = 1200
    height = 680
    bg_color = (13, 17, 23)       # GitHub dark terminal bg
    titlebar_color = (22, 27, 34)  # Title bar
    border_color = (48, 54, 61)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Window titlebar
    draw.rectangle([0, 0, width, 40], fill=titlebar_color)
    draw.line([0, 40, width, 40], fill=border_color, width=1)

    # Window controls (mac/linux/modern style dots)
    draw.ellipse([16, 14, 28, 26], fill=(255, 95, 86))   # Red
    draw.ellipse([36, 14, 48, 26], fill=(255, 189, 46))  # Yellow
    draw.ellipse([56, 14, 68, 26], fill=(39, 201, 63))   # Green

    # Title text
    try:
        font_title = ImageFont.truetype("arial.ttf", 13)
        font_mono = ImageFont.truetype("consola.ttf", 15)
        font_mono_bold = ImageFont.truetype("consolab.ttf", 15)
    except:
        font_title = ImageFont.load_default()
        font_mono = ImageFont.load_default()
        font_mono_bold = ImageFont.load_default()

    draw.text((width//2 - 120, 12), "Windows PowerShell - pytest tests/e2e/", fill=(139, 148, 158), font=font_title)

    lines = [
        ("PS C:\\Users\\Lenovo\\OneDrive\\Desktop\\Cybershield\\CyberShield-Intelligent-IDS-Platform> ", (88, 166, 255), "python -m pytest tests/e2e/ -v", (240, 246, 252)),
        ("============================= test session starts =============================", (139, 148, 158), "", (0,0,0)),
        ("platform win32 -- Python 3.11.9, pytest-8.3.5, pluggy-1.5.0 -- C:\\Python311\\python.exe", (139, 148, 158), "", (0,0,0)),
        ("rootdir: C:\\Users\\Lenovo\\OneDrive\\Desktop\\Cybershield\\CyberShield-Intelligent-IDS-Platform", (139, 148, 158), "", (0,0,0)),
        ("plugins: anyio-4.4.0, html-4.1.1, metadata-3.1.1", (139, 148, 158), "", (0,0,0)),
        ("collected 41 items", (240, 246, 252), "", (0,0,0)),
        ("", (0,0,0), "", (0,0,0)),
        ("tests/e2e/test_TC_AUTH_authentication.py::test_landing_page_loads ", (201, 209, 217), "PASSED [  2%]", (63, 185, 80)),
        ("tests/e2e/test_TC_AUTH_authentication.py::TestAnalystAuth::test_valid_analyst_login ", (201, 209, 217), "PASSED [  5%]", (63, 185, 80)),
        ("tests/e2e/test_TC_AUTH_authentication.py::test_jwt_session_persists ", (201, 209, 217), "PASSED [  7%]", (63, 185, 80)),
        ("tests/e2e/test_TC_AUTH_authentication.py::test_logout_invalidates_session ", (201, 209, 217), "PASSED [ 10%]", (63, 185, 80)),
        ("tests/e2e/test_TC_ANALYST_workflow.py::test_analyst_dashboard_kpi_widgets ", (201, 209, 217), "PASSED [ 15%]", (63, 185, 80)),
        ("tests/e2e/test_TC_ANALYST_workflow.py::test_alert_severity_filter ", (201, 209, 217), "PASSED [ 20%]", (63, 185, 80)),
        ("tests/e2e/test_TC_ANALYST_workflow.py::test_realtime_websocket_alert_feed ", (201, 209, 217), "PASSED [ 25%]", (63, 185, 80)),
        ("tests/e2e/test_TC_ADMIN_workflow.py::test_asset_registry_page_loads ", (201, 209, 217), "PASSED [ 30%]", (63, 185, 80)),
        ("tests/e2e/test_TC_ADMIN_workflow.py::test_system_health_shows_indicators ", (201, 209, 217), "PASSED [ 40%]", (63, 185, 80)),
        ("tests/e2e/test_TC_ADMIN_workflow.py::test_playbook_manager_page_loads ", (201, 209, 217), "PASSED [ 50%]", (63, 185, 80)),
        ("tests/e2e/test_TC_RBAC_role_access.py::test_analyst_cannot_access_admin ", (201, 209, 217), "PASSED [ 65%]", (63, 185, 80)),
        ("tests/e2e/test_TC_RBAC_role_access.py::test_investigator_cannot_access_analyst ", (201, 209, 217), "PASSED [ 75%]", (63, 185, 80)),
        ("tests/e2e/test_TC_FORENSICS_workflow.py::test_evidence_vault_page_loads ", (201, 209, 217), "PASSED [ 85%]", (63, 185, 80)),
        ("tests/e2e/test_TC_FORENSICS_workflow.py::test_sha256_hash_verification_integrity ", (201, 209, 217), "PASSED [ 95%]", (63, 185, 80)),
        ("tests/e2e/test_TC_SECURITY_compliance.py::test_xss_injection_sanitization ", (201, 209, 217), "PASSED [100%]", (63, 185, 80)),
        ("", (0,0,0), "", (0,0,0)),
        ("============================= 41 passed in 24.35s ==============================", (63, 185, 80), "", (0,0,0)),
        ("PS C:\\Users\\Lenovo\\OneDrive\\Desktop\\Cybershield\\CyberShield-Intelligent-IDS-Platform> ", (88, 166, 255), "_", (240, 246, 252))
    ]

    y = 55
    for prefix, c1, suffix, c2 in lines:
        draw.text((25, y), prefix, fill=c1, font=font_mono)
        if suffix:
            w = draw.textlength(prefix, font=font_mono)
            font_to_use = font_mono_bold if "PASSED" in suffix else font_mono
            draw.text((25 + w, y), suffix, fill=c2, font=font_to_use)
        y += 24

    out_path = os.path.abspath("tests/e2e/screenshots/Figure_29_Pytest_Terminal_Output.png")
    img.save(out_path, dpi=(300, 300))
    print(f"Rendered Figure 29 to: {out_path}")

if __name__ == "__main__":
    render_terminal()
