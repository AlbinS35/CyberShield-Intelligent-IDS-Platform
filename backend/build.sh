#!/usr/bin/env bash
# ─── CyberShield Render Build Script ─────────────────────────────────────────
# Executed by Render before starting the web service.
# Runs migrations, collects static files, and (optionally) seeds demo data.
set -o errexit

echo "📦 Installing Python dependencies…"
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️  Running database migrations…"
python manage.py migrate --no-input

echo "📂 Collecting static files…"
python manage.py collectstatic --no-input --clear

echo "✅ Build complete — ready to start Uvicorn ASGI server."
