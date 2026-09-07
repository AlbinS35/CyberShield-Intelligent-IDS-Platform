# ML Pipeline — CyberShield Intrusion Detection

Standalone machine learning training environment for the CyberShield Random Forest classifier.

## Setup

```bash
cd ml_pipeline
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Dataset

Download NSL-KDD from: https://www.unb.ca/cic/datasets/nsl.html

Place files in `data/`:
```
ml_pipeline/data/
├── NSL-KDD-Train.csv   ← KDDTrain+.txt
└── NSL-KDD-Test.csv    ← KDDTest+.txt
```

## Training

```bash
# Basic training (200 trees, depth 20)
python train.py

# Custom parameters
python train.py --estimators 300 --depth 25

# With separate test dataset
python train.py --dataset data/NSL-KDD-Train.csv --test-dataset data/NSL-KDD-Test.csv

# Skip plots
python train.py --no-plots
```

**Output** (in `../backend/detection/core_ml/model_bin/`):
- `rf_model.pkl` — Trained Random Forest model
- `scaler.pkl` — Fitted StandardScaler
- `feature_importance.png` — Top 20 features chart
- `confusion_matrix.png` — Confusion matrix heatmap
- `training_results.json` — Metrics summary

## Evaluation

```bash
python evaluate.py
python evaluate.py --dataset data/NSL-KDD-Test.csv
```

## Target Performance

| Metric   | Target  |
|----------|---------|
| Accuracy | > 95%   |
| Precision| > 90%   |
| Recall   | > 90%   |
| F1 Score | > 90%   |

## Attack Classes

| Class | Label | Description |
|-------|-------|-------------|
| 0 | Normal | Legitimate traffic |
| 1 | DoS | Denial of Service (neptune, smurf, etc.) |
| 2 | Probe | Reconnaissance (nmap, ipsweep, etc.) |
| 3 | R2L | Remote to Local (ftp_write, guess_passwd, etc.) |
| 4 | U2R | User to Root (buffer_overflow, rootkit, etc.) |
