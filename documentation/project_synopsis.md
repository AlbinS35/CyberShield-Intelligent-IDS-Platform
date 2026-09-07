# Project Synopsis & Proposal
## CyberShield: Intelligent Intrusion Detection, Prevention, and Digital Forensics Platform

**Course Code:** 24MCAR295 — Research Project/Software Project Part 1  
**Institution:** Department of Computer Applications, Amal Jyothi College of Engineering (Autonomous), Kanjirappally  
**Developer:** Albin Suresh (Roll No: 8)  
**Project Guide / Scrum Master:** Jinson Devis  

---

## 1. Project Abstract
Traditional network security infrastructures suffer from a critical decoupling between real-time threat detection, incident containment, and post-incident digital forensics. Standard Security Information and Event Management (SIEM) systems alert administrators but rarely take automated containment actions, leaving a window of vulnerability for lateral movement. Furthermore, when forensic analysis is conducted, proving the integrity and chronological timeline of log files in a legally resilient manner is difficult due to the lack of immutable audit trails.

**CyberShield** is a unified, multi-tenant enterprise security platform designed to address these gaps. It integrates real-time telemetry ingestion from Wazuh agents, anomaly classification using a Random Forest machine learning model, automated prevention playbooks (such as IP blacklisting and host isolation), and a digital forensics vault where evidence files and log data are cryptographically sealed using SHA-256 hashing. The system provides role-based workspaces optimized for local banking and private audit infrastructures, ensuring strict compliance and chain-of-custody tracking.

---

## 2. Problem Statement
Modern enterprise networks, particularly in sensitive sectors like local banking, face sophisticated, multi-stage cyber threats. Current security approaches present three major challenges:
1. **Passive Alerting vs. Active Mitigation:** High-severity alerts often sit in a queue waiting for manual intervention, allowing threat actors to compromise internal networks.
2. **Untampered Log & Evidence Verification:** During forensic investigations, there is no native system to guarantee that ingested log records or uploaded evidence files have not been modified post-incident.
3. **Siloed Dashboards:** Security analysts, forensic investigators, system administrators, and organizational compliance managers operate on separate, disconnected platforms, delaying response and reporting pipelines.

---

## 3. Project Objectives
* **Unified Telemetry Ingestion:** Develop a secure bridge to sync and normalize real-time logs from Wazuh Managers via REST API endpoints.
* **Intelligent Threat Classification:** Train and deploy a Random Forest classifier using the NSL-KDD dataset to categorize network event traffic (Normal, DoS, Probe, R2L, U2R) with >90% precision.
* **Automated Containment Engine:** Build an automated playbook execution system capable of running system firewall commands to block malicious IPs or isolate compromised nodes immediately upon high-confidence threat detection.
* **Legally Resilient Forensics:** Implement a secure evidence vault that automatically computes SHA-256 hashes of uploads, maintains a strict chain-of-custody ledger, and reconstructs chronological attack timelines.
* **Role-Based Access Control (RBAC):** Provide distinct, multi-tenant workspaces for Security Analysts, Forensic Investigators, System Administrators, and Organization Managers.

---

## 4. System Architecture & Modules

```
                        ┌──────────────────────────────────┐
                        │       React.js Frontend SPA      │
                        │ (Analyst, Investigator, Admin,   │
                        │        Manager Workspaces)       │
                        └────────────────┬─────────────────┘
                                         │ HTTPS / WebSocket
                        ┌────────────────▼─────────────────┐
                        │      Django REST API Backend     │
                        ├──────────────────────────────────┤
                        │ - JWT Multi-Tenant Auth & RBAC   │
                        │ - Celery Task Queue (Wazuh Sync) │
                        │ - Scikit-Learn Inference Engine  │
                        │ - Playbook Containment Handler   │
                        └────────────────┬─────────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
        ┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
        │ PostgreSQL DB   │     │  Redis Server   │     │  Wazuh Manager  │
        │  (JSONB Logs)   │     │ (WS/Broker MQ)  │     │  (API Telemetry)│
        └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Module 1: Multi-Tenant Authentication & RBAC
Manages user authentication scoped to organizations (Tenants) via JWT. Grants access to specific views based on roles:
* **Security Analyst:** Live threat maps, alert queues, and manual incident escalation.
* **Forensic Investigator:** Case vaults, file uploads, SHA-256 verifications, and chronological timelines.
* **System Administrator:** Wazuh sync controls, asset registration, and playbook rule configs.
* **Organization Manager:** High-level security metrics, compliance reports, and audit logs.

### Module 2: Telemetry Ingestion & Normalization
Communicates with the Wazuh Manager's REST API using asynchronous Celery workers. Normalizes ingested JSON data into a standardized `NetworkEvent` schema stored in PostgreSQL, utilizing indexing on JSONB columns for sub-second query performance.

### Module 3: AI/ML Inference & Detection
Exposes network events to a pre-loaded Scikit-Learn Random Forest model. Predicts the nature of incoming connections and flags anomalous behaviors, routing predictions back to create high-priority alerts when matching malicious patterns.

### Module 4: Active Response & Prevention
Executes user-defined playbooks. When triggered manually or automatically, the Celery worker runs shell scripts (e.g., updating system iptables) to drop packets from target IPs, logging stdout, stderr, and exit codes to an immutable execution history.

### Module 5: Case Archival & Forensics
Provides a secure file vault for forensic investigators. Automatically seals files on upload with SHA-256 hashes. Integrates a chain-of-custody ledger tracking every verification or file download to ensure data integrity is verifiable.

---

## 5. Phased Implementation Roadmap

### Phase 1: Mini Project (Current Semester)
* **Goal:** Base infrastructure, database mapping, and core logic.
* **Deliverables:**
  * Multi-tenant authentication model using PostgreSQL and JWT.
  * Log ingestion and normalization schemas with SHA-256 hash sealing.
  * Standalone Python Scikit-Learn training environment for model evaluation.
  * Custom User, Tenant, and Forensic Case databases.
  * Core React frontend dashboard views.

### Phase 2: Main Project (Next Semester)
* **Goal:** Live environment deployment, automated prevention, and advanced analytics.
* **Deliverables:**
  * Active integration with a live Wazuh VM/Docker manager.
  * Real-time threat classification of live agent telemetry.
  * Live playbook execution targeting local system firewalls.
  * Live WebSocket alert streams.
  * Chronological timeline visualization components.

---

## 6. Technical Stack & Hardware Requirements

### Software Stack
* **Frontend:** React.js (Vite), Tailwind CSS, Recharts, React Query
* **Backend:** Python 3.11, Django, Django REST Framework, Django Channels
* **Database:** PostgreSQL (with JSONB, `pg_trgm`, `btree_gin` extensions)
* **Message Broker / Cache:** Redis
* **Machine Learning:** Scikit-Learn (Random Forest Classifier), Pandas, NumPy, Joblib
* **Agent Integration:** Wazuh v4.8+ REST API

### Minimum Hardware Requirements
* **Processor:** Intel Core i5 or AMD Ryzen 5 (4 Cores, 8 Threads)
* **Memory:** 16 GB RAM (required to run PostgreSQL, Redis, Django, React, and Wazuh VMs concurrently)
* **Storage:** 50 GB Solid State Drive (SSD) space

---

## 7. Expected Outcomes & Evaluation Metrics
1. **Intrusion Precision:** Random Forest classification accuracy exceeding 95% on the NSL-KDD validation split.
2. **Inference Latency:** Average threat prediction execution time under 50 milliseconds.
3. **Integrity Validation:** Zero false negatives during SHA-256 log/evidence tampering tests.
4. **WebSocket Throughput:** Real-time alert delivery from database entry to frontend dashboard in under 2 seconds.
5. **Legally Compliant Auditing:** Automatic generation of structured audit logs for all state-changing API requests.
