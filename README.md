# CyberShield: Intelligent Intrusion Detection, Prevention, and Digital Forensics Platform

## 📌 Project Overview
CyberShield is a unified, enterprise-grade security ecosystem designed to bridge the structural gaps between real-time threat detection, automated incident containment, and legally resilient digital forensics[cite: 1]. Traditional security frameworks often alert administrators without taking protective action or decouple post-incident forensic analysis from live infrastructure[cite: 1]. CyberShield unifies these pipelines into a centralized web architecture utilizing a dual-phase implementation strategy[cite: 1].

This project is developed as part of the **Research Project/Software Project Part 1 (24MCAR295)** for the Master of Computer Applications (MCA) curriculum at **Amal Jyothi College of Engineering (Autonomous), Kanjirappally**[cite: 2].

---

## 🛡️ Real-Time Prevention & Containment Methods
Unlike passive alerting tools, CyberShield actively mitigates damage via an **Intelligent Threat Prevention Engine**[cite: 1]:
* **Automated IP Blocking:** Dynamically interacts with system firewalls to instantly drop incoming packets from flagged malicious sources[cite: 1].
* **Device Isolation:** Rapidly disconnects and isolates compromised network assets to halt lateral movement across internal servers[cite: 1].
* **Configurable Playbooks:** Automatically fires severity-based execution playbooks the exact millisecond the AI flags a high-confidence threat[cite: 1].
* **Audit Trail Logging:** Automatically logs every automated response action taken for immediate forensic accountability[cite: 1].

---

## 👥 Target Users & Role-Based Dashboards
The platform provides custom multi-tenant workspaces separated via Role-Based Access Control (RBAC)[cite: 1]:
* **Security Analyst Workspace:** Live network packet tracking, threshold alert handling, and case referral pipelines[cite: 1].
* **Digital Forensic Investigator Workspace:** Chronological attack timeline reconstruction, secure evidence uploads, and SHA-256 cryptographic verification tracking[cite: 1].
* **System Administrator Workspace:** Hardware/software asset registration, system health metrics, and baseline alert rule configurations[cite: 1].
* **Organization Management Workspace:** Multi-department security metrics, audit trails, compliance logging overview, and automated high-level reporting[cite: 1].

---

## ⚙️ Technical Framework & Production Stack
* **Frontend UI:** React.js (Vite architecture)[cite: 1]
* **Styling Framework:** Tailwind CSS
* **Backend API Engine:** Python (Django & Django REST Framework)[cite: 1]
* **Database Infrastructure:** PostgreSQL (Optimized for JSONB log storage and high-throughput scaling)[cite: 1]
* **Data Integrity & Security:** SHA-256 Cryptographic Hashing engines for immutable log sealing[cite: 1]
* **AI/ML Core:** Scikit-learn (Random Forest classification models trained on NSL-KDD and CICIDS2017 baseline datasets)[cite: 1]
* **Development Utilities:** Git/GitHub, Postman API Frameworks[cite: 1]

---

## 📅 Implementation Roadmap (Scrum Architecture)

### 🔹 Phase 1: Platform Core & Web Infrastructure[cite: 1]
* Database normalization, PostgreSQL schema mappings, and migration setup[cite: 1, 2].
* Multi-tenant authentication infrastructure using Django's native RBAC framework[cite: 1].
* Basic log ingestion pipelines and manually triggered incident response tracking[cite: 1].
* SHA-256 cryptographic hashing library integrations for secure case archival[cite: 1].

### 🔹 Phase 2: Intelligence Layer & Automated Containment[cite: 1]
* Supervised machine learning model preparation (Random Forest) for anomalous network packet classification (>90% target precision accuracy)[cite: 1].
* Automated containment engine playbooks (device-level isolation & real-time IP blacklisting)[cite: 1].
* Predictive risk scoring pipelines evaluating historic node vulnerabilities[cite: 1].
* Dynamic cross-log chronological incident timeline layout generator[cite: 1].

---

## 👨‍🏫 Project Guidance & Collaboration
* **Developer:** Albin Suresh (Roll No: 8)
* **Project Guide / Scrum Master:** Jinson Devis (`jinsondevis@amaljyothi.ac.in`)[cite: 2]
* **Institution:** Department of Computer Applications, Amal Jyothi College of Engineering, Kanjirappally, Kottayam, Kerala[cite: 2].
