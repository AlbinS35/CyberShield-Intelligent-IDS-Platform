@echo off
REM ═══════════════════════════════════════════════════════════════════
REM  CyberShield IDS — E2E Test Runner (Windows)
REM  Usage: run_e2e_tests.bat [--headless] [--module <module>]
REM ═══════════════════════════════════════════════════════════════════

echo.
echo  ██████╗██╗   ██╗██████╗ ███████╗██████╗ ███████╗██╗  ██╗██╗███████╗██╗     ██████╗
echo ██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗
echo ██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝███████╗███████║██║█████╗  ██║     ██║  ██║
echo ██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║
echo ╚██████╗   ██║   ██████╔╝███████╗██║  ██║███████║██║  ██║██║███████╗███████╗██████╔╝
echo  ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝
echo.
echo  Intelligent IDS Platform — Selenium E2E Test Suite
echo  ─────────────────────────────────────────────────────────────────
echo.

REM ─── Dependency check ───────────────────────────────────────────────
echo [1/3] Checking dependencies...
python -c "import selenium, pytest; print('  selenium:', selenium.__version__, '  pytest:', pytest.__version__)" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo  ERROR: Missing dependencies. Run: pip install selenium pytest webdriver-manager
    exit /b 1
)
echo  Dependencies OK.
echo.

REM ─── Pre-flight: check if stack is up ────────────────────────────────
echo [2/3] Checking application stack...
curl -s --max-time 3 http://localhost:8000/api/auth/tenants/ >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo  WARNING: Django backend not responding on http://localhost:8000
    echo  Start it with: python backend/manage.py runserver
    echo.
)
curl -s --max-time 3 http://localhost:5173 >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo  WARNING: Vite frontend not responding on http://localhost:5173
    echo  Start it with: cd frontend ^&^& npm run dev
    echo.
)
echo.

REM ─── Run tests ───────────────────────────────────────────────────────
echo [3/3] Running Selenium E2E tests...
echo.

SET ARGS=
IF "%1"=="--headless" SET ARGS=--headless

IF "%2"=="--module" (
    python -m pytest tests/e2e/test_%3*.py %ARGS% --tb=short -v
) ELSE (
    python -m pytest tests/e2e/ %ARGS% --tb=short -v
)

echo.
echo  ─────────────────────────────────────────────────────────────────
echo  Test run complete. Screenshots of failures saved to: tests/e2e/screenshots/
echo  ─────────────────────────────────────────────────────────────────
