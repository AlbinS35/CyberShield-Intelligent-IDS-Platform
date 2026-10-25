# CyberShield: Intelligent Intrusion Detection, Prevention, and Digital Forensics Platform

<div align="center">

![CyberShield Banner](documentation/screenshots/banner.png)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**A unified, enterprise-grade security ecosystem for real-time threat detection, automated incident containment, and legally resilient digital forensics.**

[Architecture](#architecture) · [Quick Start](#quick-start) · [Features](#features) · [API Docs](#api-documentation) · [ML Pipeline](#ml-pipeline)

</div>

---

## 📌 Project Overview

CyberShield is a lightweight, explainable intrusion detection and tamper-evident digital forensics platform for small organizations. Traditional security frameworks often alert administrators without taking protective action or decouple post-incident forensic analysis from live infrastructure. CyberShield unifies these pipelines into a centralized web architecture utilizing a dual-phase implementation strategy.

This project is developed as part of the **Research Project/Software Project Part 1 (24MCAR295)** for the Master of Computer Applications (MCA) curriculum at **Amal Jyothi College of Engineering (Autonomous), Kanjirappally**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   REACT FRONTEND (Vite)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Analyst  │ │Forensics │ │  Admin   │ │  Org Mgmt  │  │
│  │Dashboard │ │  Panel   │ │  Panel   │ │  Dashboard │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬─────┘  │
│       └────────────┴────────────┴───────────────┘        │
│                      Axios + WebSocket                    │
└──────────────────────────────┬──────────────────────────┘
                               │ HTTPS / WSS
┌──────────────────────────────▼──────────────────────────┐
│              DJANGO REST FRAMEWORK BACKEND               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Auth/RBAC   │  │  Threat API  │  │  Forensics API│  │
│  │  (JWT+Roles) │  │  (Incidents) │  │  (Cases+SHA)  │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Wazuh Sync  │  │  ML Engine   │  │ Playbook Exec │  │
│  │  (Celery)    │  │  (RF Model)  │  │  (iptables)   │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└──────┬───────────────────────┬───────────────────────────┘
       │                       │
┌──────▼──────┐        ┌───────▼──────┐       ┌───────────┐
│ PostgreSQL  │        │    Redis     │       │  Wazuh    │
│ (JSONB logs)│        │(Channels+MQ) │       │  Manager  │
└─────────────┘        └──────────────┘       └───────────┘
```

---

## 🛡️ Features

### Real-Time Detection
- Live network event ingestion and normalization via Wazuh API bridge
- JSONB-optimized PostgreSQL log storage with SHA-256 tamper seals on every record
- WebSocket-powered live alert dashboard (Django Channels + Redis)

### AI/ML Classification
- Random Forest classifier trained on NSL-KDD dataset (41 features, >90% target precision)
- Auto-classification pipeline triggered on every new NetworkEvent via Django signals
- Confidence scoring and multiclass attack type identification

### Automated Prevention
- Severity-based playbook execution engine (IP blocking, device isolation)
- Full execution audit trail with stdout/stderr capture
- Configurable playbook rules per tenant and severity level

### Digital Forensics
- SHA-256 cryptographic evidence integrity verification
- Chronological attack timeline reconstruction across correlated log events
- Chain-of-custody tracking per forensic case

### Multi-Tenant RBAC
| Role | Access |
|------|--------|
| Security Analyst | Live alerts, incident management, threat dashboard |
| Forensic Investigator | Case management, evidence vault, timeline |
| System Administrator | Asset registry, system health, alert rule config |
| Org Manager | Security metrics, compliance reports, audit trail |

---

## ⚠️ Known Limitations & Threat Model

While CyberShield demonstrates a complete detection-to-response pipeline, the following limitations apply in its current iteration:
1. **Machine Learning Model Mismatch:** The current Random Forest model is trained on the NSL-KDD dataset (which uses legacy features like `serror_rate`). These features do not directly map 1:1 with real-time `eve.json` flow features emitted by Suricata. Thus, production deployments would require re-training on a flow-based dataset (e.g., CIC-IDS-2017) to achieve high accuracy on live traffic.
2. **Forensic Integrity Scope:** Evidence and log hashes are stored alongside the data in PostgreSQL. While this provides *tamper-evidence* against accidental modification, a malicious actor with direct database write access could recalculate and replace the hashes. Full legal admissibility would require anchoring these hashes to an immutable external ledger or hash chain.
3. **Automated Response Safety:** Playbook scripts (e.g., executing `iptables`) use a rigid allowlist and parameterized execution. However, any automated execution of root-level commands on sensors carries inherent risks. Playbooks should ideally be replaced with purpose-built, unprivileged agents (e.g. CrowdSec bouncers or eBPF hooks) in production environments.
4. **Load Capacity:** Ingestion is handled via Celery and Redis. While adequate for lab traffic or small network choke points, multi-gigabit traffic (generating tens of thousands of alerts per second) would require a Kafka-backed ingestion pipeline.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 20+, PostgreSQL 15+, Redis 7+

### Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS
pip install -r requirements.txt
cp ../.env.example .env         # Configure your environment
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### ML Model Training
```bash
cd ml_pipeline
pip install -r requirements.txt
python train.py --dataset data/NSL-KDD-Train.csv
```

---

## 📁 Project Structure

```
CyberShield-Intelligent-IDS-Platform/
├── backend/                    ← Django REST API
│   ├── cybershield_core/       ← Django project settings
│   ├── authentication/         ← Custom User, Tenant, RBAC
│   ├── ingestion/              ← Network events, Wazuh bridge
│   ├── detection/              ← ML inference, alert management
│   ├── forensics/              ← Cases, evidence, timeline
│   └── manage.py
├── frontend/                   ← React + Vite + Tailwind
│   └── src/
│       ├── pages/              ← Role-based dashboard pages
│       ├── components/         ← Reusable UI components
│       ├── context/            ← Auth, Theme, Socket contexts
│       └── utils/              ← Helpers, crypto, formatters
├── ml_pipeline/                ← Standalone ML training scripts
├── documentation/              ← System study, screenshots, core concepts
├── docker-compose.yml
└── .env.example
```

---

## 📡 API Documentation

Auto-generated OpenAPI specification available at:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **Schema JSON**: `http://localhost:8000/api/schema/`

---

## 🤖 ML Pipeline

The Random Forest classifier is trained on the NSL-KDD dataset:

```bash
# Train the model
python ml_pipeline/train.py

# Evaluate model performance
python ml_pipeline/evaluate.py

# Output: backend/detection/core_ml/model_bin/rf_model.pkl
```

**Target Performance Metrics:**
- Accuracy: >95% on NSL-KDD test split
- Precision: >90% (DoS, Probe, R2L, U2R class separation)
- Inference latency: <50ms per prediction

---

## 👥 Team

| Role | Name | Contact |
|------|------|---------|
| Developer | Albin Suresh (Roll No: 8) | — |
| Project Guide / Scrum Master | Jinson Devis | jinsondevis@amaljyothi.ac.in |
| Institution | Dept. of Computer Applications, Amal Jyothi College of Engineering | Kanjirappally, Kerala |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
