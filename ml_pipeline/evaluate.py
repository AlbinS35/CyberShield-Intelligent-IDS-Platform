"""
ML Model Evaluation Script
Loads a saved model and produces a full evaluation report on a test dataset.

Usage:
    python evaluate.py
    python evaluate.py --model ../backend/detection/core_ml/model_bin/rf_model.pkl
    python evaluate.py --dataset data/NSL-KDD-Test.csv
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Evaluate saved CyberShield ML model")
    parser.add_argument(
        "--model", type=str,
        default="../backend/detection/core_ml/model_bin/rf_model.pkl",
        help="Path to saved model .pkl file",
    )
    parser.add_argument(
        "--scaler", type=str,
        default="../backend/detection/core_ml/model_bin/scaler.pkl",
        help="Path to saved scaler .pkl file",
    )
    parser.add_argument(
        "--dataset", type=str,
        default="data/NSL-KDD-Test.csv",
        help="Path to test CSV dataset",
    )
    args = parser.parse_args()

    model_path  = Path(args.model)
    scaler_path = Path(args.scaler)
    data_path   = Path(args.dataset)

    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        print("   Run: python train.py first")
        sys.exit(1)

    if not data_path.exists():
        print(f"❌ Dataset not found: {data_path}")
        sys.exit(1)

    import joblib
    import numpy as np
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from train_core import load_and_preprocess, CLASS_NAMES

    print("=" * 60)
    print("  CyberShield — Model Evaluation Report")
    print("=" * 60)

    # Load model + scaler
    clf    = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None
    print(f"\n  Model:   {type(clf).__name__} ({clf.n_estimators} trees)")
    print(f"  Dataset: {data_path}")

    # Load test data
    X_test, y_test, _ = load_and_preprocess(str(data_path))
    if scaler:
        X_test = scaler.transform(X_test)

    # Predict
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n  Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"\n{classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0)}")

    # Per-class confidence stats
    print("\n  Per-Class Avg Confidence:")
    for i, name in enumerate(CLASS_NAMES):
        mask = y_test == i
        if mask.any():
            avg_conf = y_prob[mask, i].mean()
            print(f"    {name:<10} avg_confidence = {avg_conf:.3f}")

    print("\n✅ Evaluation complete.")


if __name__ == "__main__":
    main()
