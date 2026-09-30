"""
CyberShield IDS — Pytest Markdown + PDF Report Plugin
======================================================
Automatically generates:
  • tests/reports/test_report_<timestamp>.md   — Markdown report
  • tests/reports/test_report_<timestamp>.pdf  — PDF report

Loaded automatically by pytest because it lives in tests/e2e/conftest_report.py
and is imported in conftest.py, OR registered as a plugin in pytest.ini.
"""

import os
import time
import datetime
import pytest

# ──────────────────────────────────────────────
# Storage for test results collected during run
# ──────────────────────────────────────────────
_results = []
_session_start = None

def pytest_sessionstart(session):
    global _session_start
    _session_start = time.time()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when == "call" or (rep.when == "setup" and rep.skipped):
        _results.append({
            "name":     item.nodeid,
            "outcome":  rep.outcome,
            "duration": rep.duration,
            "reason":   _extract_reason(rep),
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
        })

def pytest_sessionfinish(session, exitstatus):
    os.makedirs("tests/reports", exist_ok=True)
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path  = f"tests/reports/test_report_{ts}.md"
    pdf_path = f"tests/reports/test_report_{ts}.pdf"

    md_content = _build_markdown(exitstatus)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n   Markdown report -> {md_path}")

    try:
        _build_pdf(md_content, pdf_path)
        print(f"   PDF report      -> {pdf_path}")
    except Exception as e:
        print(f"   PDF generation failed: {e}")
        print(f"   Run: pip install reportlab")

def _build_markdown(exitstatus: int) -> str:
    now      = datetime.datetime.now()
    elapsed  = time.time() - (_session_start or time.time())
    total    = len(_results)
    passed   = sum(1 for r in _results if r["outcome"] == "passed")
    failed   = sum(1 for r in _results if r["outcome"] == "failed")
    skipped  = sum(1 for r in _results if r["outcome"] == "skipped")
    xfailed  = sum(1 for r in _results if r["outcome"] == "xfailed")
    pass_pct = round(passed / total * 100, 1) if total else 0.0

    status_icon = "PASS" if failed == 0 else "FAIL"
    status_text = "ALL TESTS PASSED" if failed == 0 else f"{failed} TEST(S) FAILED"

    lines = [
        "# CyberShield Automated Testing Report",
        "",
        f"**Date:** {now.strftime('%B %d, %Y')}  ",
        "**Framework:** Pytest + Selenium WebDriver  ",
        "**Scope:** Core Web Application Functional Testing  ",
        "",
        "## Overview",
        "This report details the automated Selenium UI testing performed on the CyberShield platform. The testing suite focuses on simulating end-to-end user workflows for Analysts, Investigators, and Admins to ensure the critical paths of the application function as expected.",
        "",
        "## Test Suites Executed",
    ]

    modules = {}
    for r in _results:
        mod = r['name'].split("::")[0].replace("tests/e2e/", "").replace("tests\\e2e\\", "")
        if mod not in modules:
            modules[mod] = []
        modules[mod].append(r)

    idx = 1
    for mod_name, tests in modules.items():
        lines += [f"### Suite: {mod_name.replace('_', ' ').title()} (`{mod_name}`)", ""]
        lines += ["This suite executes functional and integration tests for the module.", ""]
        
        for r in tests:
            test_name = r['name'].split("::")[-1]
            status_icon = "✅ PASSED" if r["outcome"] == "passed" else ("❌ FAILED" if r["outcome"] == "failed" else "⏭️ SKIPPED")
            
            lines += [f"**{idx}. {test_name.replace('_', ' ').title()}** (`{test_name}`)", ""]
            lines += [f"- **Action:** Executes the automated steps for {test_name}."]
            lines += [f"- **Expected Result:** The workflow completes successfully without errors."]
            if r["outcome"] == "skipped":
                lines += [f"- **Status:** {status_icon} - *{r.get('reason', 'No reason provided')}*"]
            else:
                lines += [f"- **Status:** {status_icon}"]
            lines += [""]
            idx += 1

    lines += [
        "---",
        "## Execution Summary",
        f"- **Total Tests Run:** {total}",
        f"- **Tests Passed:** {passed}",
        f"- **Tests Failed:** {failed}",
        f"- **Execution Time:** ~{elapsed:.1f} seconds (Headless Mode)",
    ]

    return "\n".join(lines)


def _build_pdf(md_content: str, pdf_path: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_LEFT

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="CyberShield Automated Testing Report",
    )

    styles = getSampleStyleSheet()
    
    title_sty = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=22, spaceAfter=6, fontName="Helvetica")
    h2_sty = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=16, spaceBefore=16, spaceAfter=8, fontName="Helvetica")
    h3_sty = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=14, spaceBefore=12, spaceAfter=6, fontName="Helvetica")
    normal_sty = ParagraphStyle("NormalText", parent=styles["Normal"], fontSize=11, leading=16, fontName="Helvetica")
    bold_sty = ParagraphStyle("BoldText", parent=normal_sty, fontName="Helvetica-Bold")
    code_inline = ParagraphStyle("Code", parent=normal_sty, fontName="Courier", textColor="brown")

    story = []
    
    now = datetime.datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph("CyberShield Automated Testing Report", title_sty))
    story.append(HRFlowable(width="100%", thickness=1, color="black", spaceAfter=10))
    
    meta_text = f"<b>Date:</b> {now} <b>Framework:</b> Pytest + Selenium WebDriver <b>Scope:</b> Core Web Application Functional Testing"
    story.append(Paragraph(meta_text, normal_sty))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Overview", h2_sty))
    overview_text = "This report details the automated Selenium UI testing performed on the CyberShield platform. The testing suite focuses on simulating end-to-end user workflows for Analysts, Investigators, and Admins to ensure the critical paths of the application function as expected."
    story.append(Paragraph(overview_text, normal_sty))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color="black", spaceAfter=10))

    story.append(Paragraph("Test Suites Executed", h2_sty))
    
    modules = {}
    for r in _results:
        mod = r['name'].split("::")[0].replace("tests/e2e/", "").replace("tests\\e2e\\", "")
        if mod not in modules:
            modules[mod] = []
        modules[mod].append(r)

    idx = 1
    for mod_name, tests in modules.items():
        story.append(Paragraph(f"Suite: {mod_name.replace('_', ' ').title()} (<font name='Courier' color='brown'>{mod_name}</font>)", h3_sty))
        story.append(Paragraph("This suite executes functional and integration tests for the module.", normal_sty))
        story.append(Spacer(1, 10))
        
        for r in tests:
            test_name = r['name'].split("::")[-1]
            status_icon = "✅ PASSED" if r["outcome"] == "passed" else ("❌ FAILED" if r["outcome"] == "failed" else "⏭️ SKIPPED")
            
            story.append(Paragraph(f"<b>{idx}. {test_name.replace('_', ' ').title()}</b> (<font name='Courier' color='brown'>{test_name}</font>)", normal_sty))
            
            bullet_sty = ParagraphStyle("Bullet", parent=normal_sty, leftIndent=30, spaceBefore=2, spaceAfter=2)
            
            story.append(Paragraph(f"◦ <b>Action:</b> Executes the automated steps for {test_name}.", bullet_sty))
            story.append(Paragraph(f"◦ <b>Expected Result:</b> The workflow completes successfully without errors.", bullet_sty))
            
            if r["outcome"] == "skipped":
                reason = r.get("reason", "No reason provided")
                story.append(Paragraph(f"◦ <b>Status:</b> {status_icon} - <i>{reason}</i>", bullet_sty))
            else:
                story.append(Paragraph(f"◦ <b>Status:</b> {status_icon}", bullet_sty))
                
            story.append(Spacer(1, 10))
            idx += 1

    story.append(HRFlowable(width="100%", thickness=1, color="black", spaceAfter=10))
    story.append(Paragraph("Execution Summary", h2_sty))
    
    total   = len(_results)
    passed  = sum(1 for r in _results if r["outcome"] == "passed")
    failed  = sum(1 for r in _results if r["outcome"] == "failed")
    elapsed = time.time() - (_session_start or time.time())
    
    bullet_sty2 = ParagraphStyle("Bullet2", parent=normal_sty, leftIndent=15, spaceBefore=4, spaceAfter=4)
    story.append(Paragraph(f"• <b>Total Tests Run:</b> {total}", bullet_sty2))
    story.append(Paragraph(f"• <b>Tests Passed:</b> {passed}", bullet_sty2))
    story.append(Paragraph(f"• <b>Tests Failed:</b> {failed}", bullet_sty2))
    story.append(Paragraph(f"• <b>Execution Time:</b> ~{elapsed:.1f} seconds (Headless Mode)", bullet_sty2))

    doc.build(story)

def _fmt_dur(seconds: float) -> str:
    if seconds < 1:
        return f"{int(seconds*1000)}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"

def _extract_reason(rep) -> str:
    if rep.skipped:
        if hasattr(rep.longrepr, "reprcrash"):
            return rep.longrepr.reprcrash.message.replace("Skipped: ", "")
        return str(rep.longrepr).split("\n")[-1].replace("Skipped: ", "")
    if rep.failed:
        if hasattr(rep.longrepr, "reprcrash"):
            return rep.longrepr.reprcrash.message
        return str(rep.longrepr)[:150]
    return ""
