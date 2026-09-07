"""
ML Model Evaluation Script
Loads a saved model and produces a full evaluation report on a test dataset.

Usage:
    # NSL-KDD evaluation
    python evaluate.py
    python evaluate.py --model ../backend/detection/core_ml/model_bin/rf_model.pkl

    # CIC-IDS2017 evaluation
    python evaluate.py --dataset-type cic-ids2017 \\
                       --model ../backend/detection/core_ml/model_bin/cic_rf_model.pkl \\
                       --dataset data/CIC-IDS2017-combined.csv
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Evaluate saved CyberShield ML model")
    parser.add_argument(
        "--dataset-type",
        type=str,
        choices=["nsl-kdd", "cic-ids2017"],
        default="nsl-kdd",
        help="Dataset schema to use for evaluation (default: nsl-kdd)",
    )
    parser.add_argument(
        "--model", type=str,
        default=None,   # auto-selected based on dataset-type
        help="Path to saved model .pkl file",
    )
    parser.add_argument(
        "--scaler", type=str,
        default=None,
        help="Path to saved scaler .pkl file",
    )
    parser.add_argument(
        "--dataset", type=str,
        default=None,   # auto-selected based on dataset-type
        help="Path to test CSV dataset",
    )
    args = parser.parse_args()

    MODEL_BIN = Path("../backend/detection/core_ml/model_bin")

    # Auto-select paths based on dataset type
    if args.dataset_type == "nsl-kdd":
        model_path  = Path(args.model  or MODEL_BIN / "rf_model.pkl")
        scaler_path = Path(args.scaler or MODEL_BIN / "scaler.pkl")
        data_path   = Path(args.dataset or "data/NSL-KDD-Test.csv")
    else:
        model_path  = Path(args.model  or MODEL_BIN / "cic_rf_model.pkl")
        scaler_path = Path(args.scaler or MODEL_BIN / "cic_scaler.pkl")
        data_path   = Path(args.dataset or "data/CIC-IDS2017-combined.csv")

    if not model_path.exists():
        print(f"❌ Model not found: {model_path}")
        if args.dataset_type == "nsl-kdd":
            print("   Run: python train.py")
        else:
            print("   Run: python train.py --dataset-type cic-ids2017 --dataset data/CIC-IDS2017-combined.csv")
        sys.exit(1)

    if not data_path.exists():
        print(f"❌ Dataset not found: {data_path}")
        print("   Run: python download_datasets.py")
        sys.exit(1)

    import joblib
    import numpy as np
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    from train_core import CLASS_NAMES

    print("=" * 60)
    print(f"  CyberShield — Model Evaluation Report [{args.dataset_type.upper()}]")
    print("=" * 60)

    clf    = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None
    print(f"\n  Model:       {type(clf).__name__} ({clf.n_estimators} trees)")
    print(f"  Dataset:     {data_path}")
    print(f"  Schema:      {args.dataset_type}")

    # Load using the correct schema
    if args.dataset_type == "nsl-kdd":
        from train_core import load_and_preprocess
        X_test, y_test, _ = load_and_preprocess(str(data_path))
    else:
        from train_core import load_cic_ids2017
        X_test, y_test, feat_cols = load_cic_ids2017(str(data_path))

    if scaler:
        X_test = scaler.transform(X_test)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n  Overall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"\n{classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0)}")

    print("\n  Per-Class Avg Confidence:")
    for i, name in enumerate(CLASS_NAMES):
        mask = y_test == i
        if mask.any():
            avg_conf = y_prob[mask, i].mean()
            print(f"    {name:<10} avg_confidence = {avg_conf:.3f}")

    print("\n✅ Evaluation complete.")


if __name__ == "__main__":
    main()
