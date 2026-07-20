#!/usr/bin/env python
"""
CyberShield ML Training Pipeline — Entry Point
Trains Random Forest classifier on NSL-KDD dataset and saves model binary.

Usage:
    python train.py
    python train.py --dataset data/NSL-KDD-Train.csv
    python train.py --estimators 300 --depth 25 --output ../backend/detection/core_ml/model_bin/

NSL-KDD Dataset Download:
    https://www.unb.ca/cic/datasets/nsl.html
    → Download KDDTrain+.txt and KDDTest+.txt
    → Place in ml_pipeline/data/
"""

import argparse
import sys
import json
import time
from pathlib import Path

# Add backend to path for shared code reuse
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from train_core import train_and_evaluate


def main():
    parser = argparse.ArgumentParser(
        description="CyberShield Random Forest Training Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset", type=str,
        default="data/NSL-KDD-Train.csv",
        help="Path to NSL-KDD training CSV (default: data/NSL-KDD-Train.csv)",
    )
    parser.add_argument(
        "--test-dataset", type=str,
        default="data/NSL-KDD-Test.csv",
        help="Path to NSL-KDD test CSV (default: data/NSL-KDD-Test.csv)",
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

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"\n❌ Dataset not found: {dataset_path}")
        print(f"\n📥 Download NSL-KDD from: https://www.unb.ca/cic/datasets/nsl.html")
        print(f"   Place KDDTrain+.csv at: {dataset_path.absolute()}")
        print(f"   Place KDDTest+.csv  at: data/NSL-KDD-Test.csv")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  CyberShield — Random Forest Training Pipeline")
    print("=" * 65)
    print(f"  Dataset:    {dataset_path}")
    print(f"  Estimators: {args.estimators}")
    print(f"  Max Depth:  {args.depth}")
    print(f"  Output Dir: {output_dir.resolve()}")
    print("=" * 65)

    results = train_and_evaluate(
        train_path=str(dataset_path),
        test_path=args.test_dataset if Path(args.test_dataset).exists() else None,
        n_estimators=args.estimators,
        max_depth=args.depth,
        output_dir=str(output_dir),
        generate_plots=not args.no_plots,
    )

    # Save results summary
    summary_path = output_dir / "training_results.json"
    with open(summary_path, "w") as f:
        # Convert non-serializable types
        serializable = {k: v for k, v in results.items()
                        if k not in ("confusion_matrix",)}
        json.dump(serializable, f, indent=2)

    print(f"\n📄 Full results saved to: {summary_path}")
    print("\n✅ Training pipeline complete!")


if __name__ == "__main__":
    main()
