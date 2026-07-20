"""
Random Forest Training Script — NSL-KDD Dataset
Django management command: python manage.py train_model

Usage:
    python manage.py train_model
    python manage.py train_model --dataset /path/to/NSL-KDD-Train.csv
    python manage.py train_model --estimators 300 --depth 25
"""

import os
import time
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score
)

logger = logging.getLogger("cybershield.ml.training")

# ─── NSL-KDD Column Definitions ──────────────────────────────────────────────

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

ATTACK_CATEGORY_MAP = {
    "normal": 0,
    # DoS attacks
    "neptune": 1, "back": 1, "land": 1, "pod": 1, "smurf": 1, "teardrop": 1,
    "apache2": 1, "udpstorm": 1, "processtable": 1, "worm": 1,
    # Probe attacks
    "satan": 2, "ipsweep": 2, "nmap": 2, "portsweep": 2, "mscan": 2, "saint": 2,
    # R2L attacks
    "guess_passwd": 3, "ftp_write": 3, "imap": 3, "phf": 3, "multihop": 3,
    "warezmaster": 3, "warezclient": 3, "spy": 3, "xlock": 3, "xsnoop": 3,
    "snmpguess": 3, "snmpgetattack": 3, "httptunnel": 3, "sendmail": 3,
    "named": 3,
    # U2R attacks
    "buffer_overflow": 4, "loadmodule": 4, "perl": 4, "rootkit": 4,
    "sqlattack": 4, "xterm": 4, "ps": 4,
}

CLASS_NAMES = ["Normal", "DoS", "Probe", "R2L", "U2R"]

MODEL_DIR = Path(__file__).resolve().parent / "model_bin"


def train_model(
    dataset_path: str,
    n_estimators: int = 200,
    max_depth: int = 20,
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict:
    """
    Train Random Forest classifier on NSL-KDD dataset.

    Args:
        dataset_path: Path to NSL-KDD .csv training file
        n_estimators: Number of trees in the forest
        max_depth: Maximum tree depth
        test_size: Fraction of data held out for testing
        random_state: Random seed for reproducibility

    Returns:
        dict with accuracy, classification_report, model_path
    """
    logger.info(f"Loading dataset from: {dataset_path}")
    start_time = time.time()

    # ── Load Data ────────────────────────────────────────────────────────────
    df = pd.read_csv(dataset_path, header=None, names=NSL_KDD_COLUMNS)
    df.drop(columns=["difficulty_level"], inplace=True, errors="ignore")

    # ── Label Encoding ───────────────────────────────────────────────────────
    df["label_numeric"] = df["label"].str.lower().map(ATTACK_CATEGORY_MAP).fillna(0).astype(int)

    # Encode categorical features
    encoders = {}
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    # ── Feature / Target Split ───────────────────────────────────────────────
    feature_cols = [c for c in NSL_KDD_COLUMNS if c not in ("label", "difficulty_level")]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label_numeric"].values

    # ── Train/Test Split ─────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # ── Scale Features ───────────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── Train Model ──────────────────────────────────────────────────────────
    logger.info(f"Training Random Forest: {n_estimators} trees, max_depth={max_depth}")
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        n_jobs=-1,
        random_state=random_state,
        class_weight="balanced",
        verbose=1,
    )
    clf.fit(X_train_scaled, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────────
    y_pred = clf.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=CLASS_NAMES, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)

    elapsed = time.time() - start_time
    logger.info(f"Training complete in {elapsed:.1f}s. Accuracy: {accuracy:.4f}")

    # ── Save Model ───────────────────────────────────────────────────────────
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "rf_model.pkl"
    scaler_path = MODEL_DIR / "scaler.pkl"
    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)
    logger.info(f"Model saved to {model_path}")

    return {
        "accuracy": accuracy,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "training_time_s": round(elapsed, 2),
        "model_path": str(model_path),
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test),
    }
