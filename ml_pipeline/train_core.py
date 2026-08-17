"""
ML Training Core Logic
Complete training pipeline: data loading, preprocessing, model training,
evaluation, visualization, and model export.
"""

import time
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)

logger = logging.getLogger(__name__)

# ─── NSL-KDD Schema ───────────────────────────────────────────────────────────

NSL_KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins",
    "logged_in", "num_compromised", "root_shell", "su_attempted", "num_root",
    "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
    "label", "difficulty_level",
]

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]
FEATURE_COLS     = [c for c in NSL_KDD_COLUMNS if c not in ("label", "difficulty_level")]
CLASS_NAMES      = ["Normal", "DoS", "Probe", "R2L", "U2R"]

ATTACK_CATEGORY_MAP = {
    "normal": 0,
    # DoS
    "neptune": 1, "back": 1, "land": 1, "pod": 1, "smurf": 1, "teardrop": 1,
    "apache2": 1, "udpstorm": 1, "processtable": 1, "worm": 1,
    # Probe
    "satan": 2, "ipsweep": 2, "nmap": 2, "portsweep": 2, "mscan": 2, "saint": 2,
    # R2L
    "guess_passwd": 3, "ftp_write": 3, "imap": 3, "phf": 3, "multihop": 3,
    "warezmaster": 3, "warezclient": 3, "spy": 3, "xlock": 3, "xsnoop": 3,
    "snmpguess": 3, "snmpgetattack": 3, "httptunnel": 3, "sendmail": 3, "named": 3,
    # U2R
    "buffer_overflow": 4, "loadmodule": 4, "perl": 4, "rootkit": 4,
    "sqlattack": 4, "xterm": 4, "ps": 4,
}

# ─── CIC-IDS2017 Schema ────────────────────────────────────────────────────────
# Source: University of New Brunswick CIC-IDS2017 dataset (80 features).
# Reference: https://www.unb.ca/cic/datasets/ids-2017.html

CIC_LABEL_COLUMN = " Label"   # note leading space in original CSV headers

# CIC-IDS2017 label → 5-class CyberShield attack category
CIC_ATTACK_MAP = {
    "BENIGN":                        0,  # Normal
    # DoS / DDoS
    "DoS slowloris":                 1,
    "DoS Slowhttptest":              1,
    "DoS Hulk":                      1,
    "DoS GoldenEye":                 1,
    "DDoS":                          1,
    "Heartbleed":                    1,
    # Probe / Reconnaissance
    "PortScan":                      2,
    "Bot":                           2,   # Bot scanning behaviour → Probe
    # R2L — Remote exploits / brute force
    "FTP-Patator":                   3,
    "SSH-Patator":                   3,
    "Web Attack – Brute Force":      3,
    "Web Attack – XSS":              3,
    "Web Attack – Sql Injection":    3,
    # U2R — Privilege escalation / infiltration
    "Infiltration":                  4,
}

# 20 CIC-IDS2017 features that map cleanly to live Suricata/Wazuh telemetry
CIC_FEATURE_COLS = [
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Mean", "Bwd Packet Length Mean",
    "Flow Bytes/s", "Flow Packets/s",
    "Flow IAT Mean", "Fwd IAT Mean", "Bwd IAT Mean",
    "Fwd PSH Flags", "FIN Flag Count", "SYN Flag Count",
    "RST Flag Count", "PSH Flag Count", "ACK Flag Count",
    "URG Flag Count", "Down/Up Ratio",
]


def load_and_preprocess(csv_path: str) -> tuple:
    """Load NSL-KDD CSV, encode categoricals, return (X, y, encoders, scaler)."""
    print(f"\n  Loading: {csv_path}")
    df = pd.read_csv(csv_path, header=None, names=NSL_KDD_COLUMNS)
    df.drop(columns=["difficulty_level"], inplace=True, errors="ignore")
    print(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")

    # Map attack labels to class integers
    df["label_int"] = df["label"].str.lower().map(ATTACK_CATEGORY_MAP).fillna(0).astype(int)

    # Print class distribution
    dist = df["label_int"].value_counts().sort_index()
    print("\n  Class Distribution:")
    for idx, count in dist.items():
        pct = count / len(df) * 100
        print(f"    {CLASS_NAMES[idx]:<10} {count:>7,}  ({pct:.1f}%)")

    # Label-encode categoricals
    encoders = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    X = df[FEATURE_COLS].values.astype(np.float32)
    y = df["label_int"].values

    return X, y, encoders


def train_and_evaluate(
    train_path:      str,
    test_path:       Optional[str] = None,
    n_estimators:    int   = 200,
    max_depth:       int   = 20,
    output_dir:      str   = ".",
    generate_plots:  bool  = True,
    random_state:    int   = 42,
) -> dict:
    """Full training + evaluation pipeline."""
    start = time.time()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # ── Load & Preprocess ─────────────────────────────────────────────────────
    print("\n[1/5] Loading and preprocessing training data...")
    X_train_full, y_train_full, encoders = load_and_preprocess(train_path)

    # Internal validation split if no separate test set
    if test_path and Path(test_path).exists():
        print("\n[2/5] Loading test dataset...")
        X_test, y_test, _ = load_and_preprocess(test_path)
        X_train, y_train = X_train_full, y_train_full
    else:
        print("\n[2/5] Splitting train/validation (80/20)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_train_full, y_train_full,
            test_size=0.2, stratify=y_train_full, random_state=random_state
        )
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # ── Scale ─────────────────────────────────────────────────────────────────
    print("\n[3/5] Scaling features (StandardScaler)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # ── Train ─────────────────────────────────────────────────────────────────
    print(f"\n[4/5] Training Random Forest ({n_estimators} trees, max_depth={max_depth})...")
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        n_jobs=-1,
        random_state=random_state,
        class_weight="balanced",
        verbose=0,
        min_samples_split=5,
        min_samples_leaf=2,
    )
    clf.fit(X_train_scaled, y_train)

    # ── Evaluate ──────────────────────────────────────────────────────────────
    print("\n[5/5] Evaluating model...")
    y_pred = clf.predict(X_test_scaled)
    y_prob = clf.predict_proba(X_test_scaled)

    accuracy  = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1        = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    cm        = confusion_matrix(y_test, y_pred)

    elapsed = time.time() - start
    print(f"\n{'='*55}")
    print(f"  RESULTS")
    print(f"{'='*55}")
    print(f"  Accuracy:  {accuracy:.4f}  ({accuracy*100:.2f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  Time:      {elapsed:.1f}s")
    print(f"\n{classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0)}")

    # ── Save Models ───────────────────────────────────────────────────────────
    model_path  = output_path / "rf_model.pkl"
    scaler_path = output_path / "scaler.pkl"
    joblib.dump(clf,    model_path)
    joblib.dump(scaler, scaler_path)
    print(f"  Model  → {model_path}")
    print(f"  Scaler → {scaler_path}")

    # ── Feature Importance Plot ───────────────────────────────────────────────
    if generate_plots:
        _plot_feature_importance(clf, output_path)
        _plot_confusion_matrix(cm, output_path)

    return {
        "accuracy":     round(accuracy,  4),
        "precision":    round(precision, 4),
        "recall":       round(recall,    4),
        "f1_score":     round(f1,        4),
        "training_time_s": round(elapsed, 2),
        "n_train":      len(X_train),
        "n_test":       len(X_test),
        "confusion_matrix": cm,
        "model_path":   str(model_path),
        "scaler_path":  str(scaler_path),
    }


def _plot_feature_importance(clf, output_path: Path, prefix: str = "", feature_cols: list = None) -> None:
    try:
        import matplotlib.pyplot as plt
        cols = feature_cols if feature_cols is not None else FEATURE_COLS
        importances = clf.feature_importances_
        top_n = min(20, len(cols))
        indices = np.argsort(importances)[::-1][:top_n]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_facecolor("#0B0F1A")
        fig.patch.set_facecolor("#0B0F1A")
        ax.bar(range(top_n), importances[indices], color="#00F5FF", alpha=0.8)
        ax.set_xticks(range(top_n))
        ax.set_xticklabels([cols[i] for i in indices], rotation=45, ha="right",
                           fontsize=8, color="#9CA3AF")
        ax.set_ylabel("Importance", color="#9CA3AF")
        ax.set_title(f"Top {top_n} Feature Importances — Random Forest", color="white", pad=12)
        ax.tick_params(colors="#9CA3AF")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1F2937")
        plt.tight_layout()
        path = output_path / f"{prefix}feature_importance.png"
        plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0B0F1A")
        plt.close()
        print(f"  Plot  → {path}")
    except Exception as e:
        print(f"  (Plot skipped: {e})")


def _plot_confusion_matrix(cm: np.ndarray, output_path: Path, prefix: str = "") -> None:
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_facecolor("#0B0F1A")
        fig.patch.set_facecolor("#0B0F1A")
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
            ax=ax, linewidths=0.5, linecolor="#1F2937",
        )
        ax.set_xlabel("Predicted", color="#9CA3AF")
        ax.set_ylabel("Actual",    color="#9CA3AF")
        ax.set_title("Confusion Matrix", color="white", pad=12)
        ax.tick_params(colors="#9CA3AF")
        plt.tight_layout()
        path = output_path / f"{prefix}confusion_matrix.png"
        plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="#0B0F1A")
        plt.close()
        print(f"  Plot  → {path}")
    except Exception as e:
        print(f"  (Confusion matrix plot skipped: {e})")


# ─── CIC-IDS2017 Training Pipeline ────────────────────────────────────────────

def load_cic_ids2017(csv_path: str) -> tuple:
    """
    Load CIC-IDS2017 CSV, clean labels, and return (X, y) using CIC_FEATURE_COLS.

    CIC-IDS2017 notes:
    - Headers have leading/trailing spaces — stripped automatically
    - Contains inf/-inf values from division-by-zero in feature extraction — replaced with 0
    - Label column is ' Label' (note leading space in raw file)
    - Some labels use em-dash (–) not ASCII hyphen (-) — handled in CIC_ATTACK_MAP
    """
    print(f"\n  Loading CIC-IDS2017: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)

    # Strip whitespace from column headers
    df.columns = df.columns.str.strip()

    print(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")

    # Handle the label column (may be 'Label' or ' Label' after strip)
    label_col = "Label" if "Label" in df.columns else CIC_LABEL_COLUMN.strip()
    if label_col not in df.columns:
        raise ValueError(f"Label column not found. Available: {list(df.columns[:5])}")

    # Normalise labels to CyberShield 5-class schema
    df["label_int"] = (
        df[label_col]
        .str.strip()
        .map(CIC_ATTACK_MAP)
        .fillna(0)
        .astype(int)
    )

    # Print class distribution
    dist = df["label_int"].value_counts().sort_index()
    print("\n  Class Distribution (CIC-IDS2017 → 5-class):")
    for idx, count in dist.items():
        pct = count / len(df) * 100
        print(f"    {CLASS_NAMES[idx]:<10} {count:>7,}  ({pct:.1f}%)")

    # Select available feature columns (gracefully skip missing)
    available = [c for c in CIC_FEATURE_COLS if c in df.columns]
    missing   = [c for c in CIC_FEATURE_COLS if c not in df.columns]
    if missing:
        print(f"\n  ⚠️  Missing {len(missing)} feature columns (will be zero-padded at inference):")
        print(f"     {missing[:5]}{'...' if len(missing) > 5 else ''}")

    X = df[available].copy()

    # Replace inf/-inf with 0, then fill NaN
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    X = X.values.astype(np.float32)

    y = df["label_int"].values
    return X, y, available


def train_cic_ids2017(
    csv_path:       str,
    n_estimators:   int  = 200,
    max_depth:      int  = 20,
    output_dir:     str  = ".",
    generate_plots: bool = True,
    random_state:   int  = 42,
) -> dict:
    """
    Full CIC-IDS2017 training + evaluation pipeline.
    Saves cic_rf_model.pkl and cic_scaler.pkl alongside the NSL-KDD model files.
    The inference engine prefers the CIC model if present (more modern dataset).
    """
    start = time.time()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("\n[1/5] Loading and preprocessing CIC-IDS2017 data...")
    X_full, y_full, feature_cols = load_cic_ids2017(csv_path)

    print("\n[2/5] Splitting train/validation (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_full, y_full,
        test_size=0.2, stratify=y_full, random_state=random_state,
    )
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    print("\n[3/5] Scaling features (StandardScaler)...")
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    print(f"\n[4/5] Training CIC-IDS2017 Random Forest ({n_estimators} trees, max_depth={max_depth})...")
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        n_jobs=-1,
        random_state=random_state,
        class_weight="balanced",
        min_samples_split=5,
        min_samples_leaf=2,
    )
    clf.fit(X_train_s, y_train)

    print("\n[5/5] Evaluating CIC-IDS2017 model...")
    y_pred = clf.predict(X_test_s)
    accuracy  = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    recall    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1        = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    cm        = confusion_matrix(y_test, y_pred)

    elapsed = time.time() - start
    print(f"\n{'='*55}")
    print(f"  CIC-IDS2017 RESULTS")
    print(f"{'='*55}")
    print(f"  Accuracy:  {accuracy:.4f}  ({accuracy*100:.2f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  Time:      {elapsed:.1f}s")
    print(f"\n{classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0)}")

    # ── Save CIC model files ──────────────────────────────────────────────────
    model_path  = output_path / "cic_rf_model.pkl"
    scaler_path = output_path / "cic_scaler.pkl"
    joblib.dump(clf,    model_path)
    joblib.dump(scaler, scaler_path)
    print(f"  CIC Model  → {model_path}")
    print(f"  CIC Scaler → {scaler_path}")

    # Save feature list for inference-time validation
    feature_meta_path = output_path / "cic_features.json"
    with open(feature_meta_path, "w") as f:
        import json
        json.dump({"features": feature_cols, "n_features": len(feature_cols)}, f, indent=2)

    if generate_plots:
        try:
            _plot_feature_importance(clf, output_path, prefix="cic_", feature_cols=feature_cols)
            _plot_confusion_matrix(cm, output_path, prefix="cic_")
        except Exception as e:
            print(f"  (CIC plots skipped: {e})")

    return {
        "accuracy":        round(accuracy,  4),
        "precision":       round(precision, 4),
        "recall":          round(recall,    4),
        "f1_score":        round(f1,        4),
        "training_time_s": round(elapsed,   2),
        "n_train":         len(X_train),
        "n_test":          len(X_test),
        "n_features":      len(feature_cols),
        "confusion_matrix": cm,
        "model_path":      str(model_path),
        "scaler_path":     str(scaler_path),
        "dataset":         "CIC-IDS2017",
    }
