# CyberShield — Local Development Setup Guide

## Prerequisites

| Software | Version | Download |
|----------|---------|----------|
| Python   | 3.11+   | https://python.org |
| Node.js  | 20+     | https://nodejs.org |
| PostgreSQL | 15+  | https://postgresql.org/download/windows/ |
| Redis    | 7+      | https://github.com/tporadowski/redis/releases |
| Git      | latest  | https://git-scm.com |

---

## Step 1: Clone & Configure

```bash
git clone https://github.com/AlbinS35/CyberShield-Intelligent-IDS-Platform.git
cd CyberShield-Intelligent-IDS-Platform

# Copy environment template
copy .env.example .env    # Windows
cp .env.example .env      # Linux/macOS
# Edit .env with your credentials
```

---

## Step 2: PostgreSQL Setup

### Option A — Automated Script (Recommended)
```bash
cd backend
pip install python-dotenv psycopg2-binary
python setup_db.py --migrate --seed
```
This will:
1. Create PostgreSQL user `cybershield_user`
2. Create database `cybershield_db`
3. Enable `uuid-ossp`, `pg_trgm`, and `btree_gin` extensions
4. Run all Django migrations
5. Seed demo tenant + 5 users (one per role)

### Option B — Manual psql
```sql
-- Run as postgres superuser:
CREATE USER cybershield_user WITH PASSWORD 'cybershield_pass';
ALTER USER cybershield_user CREATEDB;
CREATE DATABASE cybershield_db OWNER cybershield_user ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE cybershield_db TO cybershield_user;

-- Then connect to cybershield_db and enable extensions:
\c cybershield_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
```

### .env Database Section
```
DB_NAME=cybershield_db
DB_USER=cybershield_user
DB_PASSWORD=cybershield_pass
DB_HOST=localhost
DB_PORT=5432
```

---

## Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create superuser (if not using seed)
python manage.py createsuperuser

# Start Django development server
python manage.py runserver
```

Django server: http://localhost:8000

---

## Step 4: Redis Setup (for Celery + WebSockets)

### Windows
Download Redis from: https://github.com/tporadowski/redis/releases
```bash
# Start Redis server
redis-server
```

### Linux/macOS
```bash
sudo apt install redis-server    # Ubuntu
brew install redis               # macOS
redis-server
```

Verify: `redis-cli ping` → should return `PONG`

---

## Step 5: Celery Workers (Background Tasks)

Open a new terminal:
```bash
cd backend
.venv\Scripts\activate
celery -A cybershield_core worker --loglevel=info   # Wazuh sync + ML classification
```

For periodic tasks (Wazuh auto-sync every 30s):
```bash
celery -A cybershield_core beat --loglevel=info
```

---

## Step 6: Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

---

## Step 7: ML Model Training (Optional)

```bash
# Download NSL-KDD dataset first (see ml_pipeline/data/README.md)
cd ml_pipeline
pip install -r requirements.txt
python train.py --dataset data/NSL-KDD-Train.csv

# Or via Django management command:
cd backend
python manage.py train_model
```

---

## Demo Credentials

After running `python setup_db.py --seed`:

| Role | Email | Password |
|------|-------|----------|
| Security Analyst | analyst@cybershield.demo | CyberShield@2024 |
| Forensic Investigator | investigator@cybershield.demo | CyberShield@2024 |
| System Administrator | admin@cybershield.demo | CyberShield@2024 |
| Org Manager | manager@cybershield.demo | CyberShield@2024 |
| Super Admin | superadmin@cybershield.demo | CyberShield@2024 |

---

## API Documentation

Start the server and visit:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Django Admin**: http://localhost:8000/admin/

---

## Docker (Alternative)

```bash
# Start all services at once
docker-compose up -d

# Run migrations inside container
docker-compose exec backend python manage.py migrate

# Seed data
docker-compose exec backend python setup_db.py --seed
```

---

## Troubleshooting

### PostgreSQL connection refused
- Ensure PostgreSQL service is running: `pg_ctl status`
- Check `DB_HOST` in `.env` (use `127.0.0.1` instead of `localhost` on Windows)

### Redis connection error
- Start Redis: `redis-server --daemonize yes`
- Check Redis: `redis-cli ping`

### `psycopg2` import error
- Run: `pip install psycopg2-binary`

### Migration errors
- Run: `python manage.py showmigrations` to check state
- If needed: `python manage.py migrate --run-syncdb`
