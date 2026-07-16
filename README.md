# CyberShield: Intelligent Intrusion Detection, Prevention, and Digital Forensics Platform

## 📌 Project Overview
CyberShield is a unified, enterprise-grade security ecosystem designed to bridge the structural gaps between real-time threat detection, automated incident containment, and legally resilient digital forensics. Traditional security frameworks often alert administrators without taking protective action or decouple post-incident forensic analysis from live infrastructure. CyberShield unifies these pipelines into a centralized web architecture utilizing a dual-phase implementation strategy.

This project is developed as part of the **Research Project/Software Project Part 1 (24MCAR295)** for the Master of Computer Applications (MCA) curriculum at **Amal Jyothi College of Engineering (Autonomous), Kanjirappally**.

---

## 👥 Target Users & Role-Based Dashboards
The platform provides custom multi-tenant workspaces separated via Role-Based Access Control (RBAC):
* **Security Analyst Workspace:** Live network packet tracking, threshold alert handling, and case referral pipelines.
* **Digital Forensic Investigator Workspace:** Chronological attack timeline reconstruction, secure evidence uploads, and SHA-256 cryptographic verification tracking.
* **System Administrator Workspace:** Hardware/software asset registration, system health metrics, and baseline alert rule configurations.
* **Organization Management Workspace:** Multi-department security metrics, audit trails, compliance logging overview, and automated high-level reporting.

---

## ⚙️ Technical Framework & Architecture
* **Frontend:** React.js / HTML5, CSS3, Bootstrap
* **Backend:** Python (Django / Flask Frameworks)
* **Database Infrastructure:** MySQL / PostgreSQL Relational Database Systems
* **AI/ML Core:** Scikit-learn (Random Forest classification models trained on NSL-KDD and CICIDS2017 baseline datasets)
* **Data Integrity & Security:** SHA-256 Cryptographic Hashing engines for immutable log sealing
* **Development Tools:** Git/GitHub, Postman API Frameworks

---

## 📅 Implementation Roadmap (Scrum Architecture)

### 🔹 Phase 1: Platform Core & Web Infrastructure
* Database normalization and schema mappings.
* Multi-tenant authentication infrastructure and user role assignment.
* Basic log ingestion pipelines and manually triggered incident response tracking.
* SHA-256 cryptographic hashing library integrations for secure case archival.

### 🔹 Phase 2: Intelligence Layer & Automated Containment
* Supervised machine learning model preparation (Random Forest) for anomalous network packet classification (>90% target precision accuracy).
* Automated containment engine scripts (device level isolation & real-time IP blacklisting).
* Predictive risk scoring pipelines evaluating historic node vulnerabilities.
* Dynamic cross-log chronological incident timeline layout generator.

---

## 👨‍🏫 Project Guidance & Collaboration
* **Developer:** Albin Suresh (Roll No:8)
* **Project Guide / Scrum Master:** Jinson Devis (`jinsondevis@amaljyothi.ac.in`)
* **Institution:** Department of Computer Applications, Amal Jyothi College of Engineering, Kanjirappally, Kottayam, Kerala.
