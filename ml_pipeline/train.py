"""
CyberShield ML Training Pipeline — Entry Point
Trains Random Forest classifier on NSL-KDD and/or CIC-IDS2017 dataset.
Produces separate model binaries for each dataset (preferred) or a combined model.

Usage:
    # NSL-KDD only (baseline)
    python train.py

    # CIC-IDS2017 only (modern dataset)
    python train.py --dataset-type cic-ids2017 --dataset data/CIC-IDS2017-combined.csv

    # Train BOTH (produces rf_model.pkl + cic_rf_model.pkl)
    python train.py --dataset-type both --dataset data/NSL-KDD-Train.csv --cic-dataset data/CIC-IDS2017-combined.csv

Dataset Downloads:
    NSL-KDD:     https://www.unb.ca/cic/datasets/nsl.html
    CIC-IDS2017: https://www.unb.ca/cic/datasets/ids-2017.html
                 (Download Monday-Friday CSVs and concatenate, or use download_datasets.py)
"""

import argparse
import sys
import json
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from train_core import train_and_evaluate, train_cic_ids2017


def main():
    parser = argparse.ArgumentParser(
        description="CyberShield Random Forest Training Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset-type",
        type=str,
        choices=["nsl-kdd", "cic-ids2017", "both"],
        default="nsl-kdd",
        help="Dataset type to train on (default: nsl-kdd)",
    )
    parser.add_argument(
        "--dataset", type=str,
        default="data/NSL-KDD-Train.csv",
        help="Path to NSL-KDD training CSV",
    )
    parser.add_argument(
        "--test-dataset", type=str,
        default="data/NSL-KDD-Test.csv",
        help="Path to NSL-KDD test CSV",
    )
    parser.add_argument(
        "--cic-dataset", type=str,
        default="data/CIC-IDS2017-combined.csv",
        help="Path to CIC-IDS2017 CSV (required for --dataset-type cic-ids2017 or both)",
    )
    parser.add_argument("--estimators", type=int, default=200, help="Number of trees (default: 200)")
    parser.add_argument("--depth",      type=int, default=20,  help="Max tree depth (default: 20)")
    parser.add_argument(
        "--output", type=str,
        default="../backend/detection/core_ml/model_bin",
        help="Output directory for model binaries",
    )
    parser.add_argument("--no-plots", action="store_true", help="Skip generating evaluation plots")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  CyberShield — ML Training Pipeline")
    print("=" * 65)
    print(f"  Dataset Type: {args.dataset_type}")
    print(f"  Estimators:   {args.estimators}")
    print(f"  Max Depth:    {args.depth}")
    print(f"  Output Dir:   {output_dir.resolve()}")
    print("=" * 65)

    all_results = {}

    # ── Train NSL-KDD model ───────────────────────────────────────────────────
    if args.dataset_type in ("nsl-kdd", "both"):
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            print(f"\n❌ NSL-KDD dataset not found: {dataset_path}")
            print(f"   Download from: https://www.unb.ca/cic/datasets/nsl.html")
            if args.dataset_type == "nsl-kdd":
                sys.exit(1)
            else:
                print("   Skipping NSL-KDD training (--dataset-type both continues with CIC).")
        else:
            print(f"\n🔵 Training NSL-KDD model → rf_model.pkl")
            results = train_and_evaluate(
                train_path=str(dataset_path),
                test_path=args.test_dataset if Path(args.test_dataset).exists() else None,
                n_estimators=args.estimators,
                max_depth=args.depth,
                output_dir=str(output_dir),
                generate_plots=not args.no_plots,
            )
            all_results["nsl_kdd"] = {k: v for k, v in results.items() if k != "confusion_matrix"}
            print(f"   ✅ NSL-KDD model saved → {output_dir}/rf_model.pkl")

    # ── Train CIC-IDS2017 model ───────────────────────────────────────────────
    if args.dataset_type in ("cic-ids2017", "both"):
        cic_path = Path(args.cic_dataset)
        if not cic_path.exists():
            print(f"\n❌ CIC-IDS2017 dataset not found: {cic_path}")
            print(f"   Run: python download_datasets.py --dataset cic-ids2017")
            if args.dataset_type == "cic-ids2017":
                sys.exit(1)
            else:
                print("   Skipping CIC-IDS2017 training.")
        else:
            print(f"\n🟢 Training CIC-IDS2017 model → cic_rf_model.pkl")
            results = train_cic_ids2017(
                csv_path=str(cic_path),
                n_estimators=args.estimators,
                max_depth=args.depth,
                output_dir=str(output_dir),
                generate_plots=not args.no_plots,
            )
            all_results["cic_ids2017"] = {k: v for k, v in results.items() if k != "confusion_matrix"}
            print(f"   ✅ CIC-IDS2017 model saved → {output_dir}/cic_rf_model.pkl")

    # ── Save combined results summary ─────────────────────────────────────────
    if all_results:
        summary_path = output_dir / "training_results.json"
        with open(summary_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n📄 Full results saved to: {summary_path}")

    print("\n✅ Training pipeline complete!")
    print("\n📌 Model priority at inference:")
    print("   1. CIC-IDS2017 model (cic_rf_model.pkl) — preferred if present")
    print("   2. NSL-KDD model    (rf_model.pkl)       — fallback baseline")


if __name__ == "__main__":
    main()
