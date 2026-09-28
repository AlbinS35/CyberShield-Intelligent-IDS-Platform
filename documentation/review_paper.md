# Review Paper: Intelligent Network Intrusion Detection using Random Forest and Real-Time Containment Playbooks

**Authors:** Albin Suresh, Jinson Devis (Guide)  
**Institution:** Amal Jyothi College of Engineering (Autonomous), Kanjirappally  

## Abstract
Traditional Intrusion Detection Systems (IDS) often generate alerts without taking automated action, leading to a critical window of vulnerability. In this paper, we present CyberShield, an intelligent IDS platform that integrates real-time telemetry from Wazuh and Suricata with a machine learning classification engine. Using a Random Forest classifier trained on the NSL-KDD and CIC-IDS2017 datasets, the system achieves over 97% detection accuracy. To address the gap between detection and response, the system utilizes confidence-gated automated playbooks to execute firewall block rules in real time, only when prediction confidence exceeds 85%. Furthermore, a cryptographic chain-of-custody vault secures digital forensics evidence.

## 1. Introduction
Modern enterprise networks face sophisticated cyber threats such as Distributed Denial of Service (DDoS), Remote-to-Local (R2L) exploits, and privilege escalation (U2R). Security Information and Event Management (SIEM) solutions aggregate logs but often rely heavily on static signature matching, which fails against zero-day attacks. 

This paper introduces a hybrid architecture combining signature-based event ingestion with machine-learning anomaly detection. By routing telemetry through a high-performance message broker (Redis) and Celery workers, CyberShield achieves an average inference latency of under 50ms, enabling real-time mitigation.

## 2. Methodology
### 2.1 Dataset and Feature Engineering
The models were trained using two benchmark datasets:
- **NSL-KDD:** A refined version of the KDD'99 dataset, offering 41 features.
- **CIC-IDS2017:** A modern dataset containing benign and diverse attack flows (e.g., DoS, Web Attacks, Brute Force).

Raw network logs are ingested and normalized into a unified `NetworkEvent` schema. We extract key features such as `duration`, `src_bytes`, `dst_bytes`, and TCP flag counts, mapping them to the expected model inputs.

### 2.2 Model Architecture
A Random Forest Classifier was chosen due to its robustness against overfitting and interpretable tree structure. The model was trained with:
- `n_estimators=200`
- `max_depth=20`
- Balanced class weights to handle minority attack classes (U2R, R2L).

### 2.3 Confidence-Gated Playbooks
Automated response introduces the risk of false positives disrupting legitimate business operations. CyberShield implements a dual-gate validation system:
1. The model must classify the event with a severity of HIGH or CRITICAL.
2. The model's prediction confidence must equal or exceed a threshold (e.g., 0.85).

Events failing these gates are logged and flagged for manual analyst review, maintaining system integrity while minimizing downtime.

## 3. Results and Evaluation
The Random Forest model achieved the following performance metrics on the test splits:
- **Accuracy:** 97.3%
- **Precision (DoS):** 98.1%
- **Average Inference Latency:** 12ms (well within the <50ms real-time budget)

Additionally, the asynchronous SHA-256 hashing architecture allowed the system to ingest thousands of events per second without bottlenecking the database bulk insertion pathway.

## 4. Conclusion
CyberShield demonstrates that integrating machine learning anomaly detection with automated, confidence-gated playbooks significantly reduces incident response times. Future work will focus on integrating deep learning architectures (e.g., LSTMs) for sequence-based attack detection and expanding the forensic module's capability to parse raw PCAP files.
