#!/usr/bin/env python3
"""
CyberShield Dataset Download Helper
=====================================
Downloads and prepares benchmark datasets for CyberShield ML training.

Supported Datasets:
    nsl-kdd     NSL-KDD (1999/2009) — baseline benchmark, 41 features
    cic-ids2017 CIC-IDS2017 (2017)  — modern dataset, 80 features

Usage:
    python download_datasets.py --dataset nsl-kdd
    python download_datasets.py --dataset cic-ids2017
    python download_datasets.py --dataset both
"""

import argparse
import os
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def download_nsl_kdd():
    """Download NSL-KDD dataset from UNB server."""
    print_header("NSL-KDD Dataset")

    train_path = DATA_DIR / "NSL-KDD-Train.csv"
    test_path  = DATA_DIR / "NSL-KDD-Test.csv"

    if train_path.exists() and test_path.exists():
        print(f"✅ NSL-KDD already present:")
        print(f"   {train_path}")
        print(f"   {test_path}")
        return

    print("""
NSL-KDD is derived from the KDD Cup 1999 intrusion detection dataset.
It is the standard academic benchmark for IDS research.

📥 Download Steps:
   1. Visit: https://www.unb.ca/cic/datasets/nsl.html
   2. Download: KDDTrain+.txt and KDDTest+.txt
   3. Rename KDDTrain+.txt → NSL-KDD-Train.csv
   4. Rename KDDTest+.txt  → NSL-KDD-Test.csv
   5. Place both files in: ml_pipeline/data/

Attempting automatic download via requests...""")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # NSL-KDD is available from the UNB CIC server
    urls = {
        str(train_path): "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B.txt",
        str(test_path):  "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest%2B.txt",
    }

    try:
        import requests
        for dest, url in urls.items():
            dest_path = Path(dest)
            if dest_path.exists():
                print(f"   ✅ Already exists: {dest_path.name}")
                continue
            print(f"   Downloading {dest_path.name} from GitHub mirror...")
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"   ✅ Saved: {dest_path}")
        print("\n✅ NSL-KDD download complete!")

    except ImportError:
        print("\n❌ 'requests' not installed. Manual download required.")
        _print_manual_instructions("NSL-KDD")
    except Exception as exc:
        print(f"\n❌ Auto-download failed: {exc}")
        print("   Please download manually from: https://www.unb.ca/cic/datasets/nsl.html")


def download_cic_ids2017():
    """Instructions for CIC-IDS2017 dataset (requires manual download due to size)."""
    print_header("CIC-IDS2017 Dataset")

    combined_path = DATA_DIR / "CIC-IDS2017-combined.csv"
    if combined_path.exists():
        print(f"✅ CIC-IDS2017 combined file already present: {combined_path}")
        return

    print("""
CIC-IDS2017 is a modern network intrusion dataset (2017) created by the
Canadian Institute for Cybersecurity at University of New Brunswick.

It contains 80 features extracted from real network traffic, including:
  - DDoS, DoS Hulk, DoS GoldenEye, DoS slowloris, DoS Slowhttptest
  - Heartbleed (CVE-2014-0160)
  - Web Attacks: Brute Force, XSS, SQL Injection
  - SSH and FTP Patator (brute force)
  - Port Scan, Botnet, Infiltration

⚠️  Dataset Size: ~1.2 GB (7 daily CSV files)
⚠️  Direct download requires registration on the UNB CIC portal.

📥 Download Steps:
   1. Visit: https://www.unb.ca/cic/datasets/ids-2017.html
   2. Click "Download" and register (free academic account)
   3. Download all 7 CSV files (Monday through Friday)
      The files are inside "MachineLearningCSV.zip"
   4. Extract all CSVs to: ml_pipeline/data/cic-ids2017/

📦 After download, combine the CSVs into one file:""")

    print("""
   # On Linux/macOS:
   cd ml_pipeline/data/cic-ids2017/
   head -1 Monday-WorkingHours.pcap_ISCX.csv > ../CIC-IDS2017-combined.csv
   tail -n +2 -q *.csv >> ../CIC-IDS2017-combined.csv

   # On Windows PowerShell:
   $files = Get-ChildItem .\\data\\cic-ids2017\\*.csv
   $header = Get-Content $files[0] -TotalCount 1
   $header | Out-File .\\data\\CIC-IDS2017-combined.csv -Encoding utf8
   foreach ($f in $files) {
       Get-Content $f | Select-Object -Skip 1 | Add-Content .\\data\\CIC-IDS2017-combined.csv -Encoding utf8
   }
""")

    print("""📌 Alternative — Kaggle Mirror (no registration, smaller):
   Dataset: https://www.kaggle.com/datasets/cicdataset/cicids2017
   Install kaggle CLI: pip install kaggle
   Download: kaggle datasets download -d cicdataset/cicids2017
   Extract and combine as above.

   ─────────────────────────────────────────────────────────
   After preparing CIC-IDS2017-combined.csv, train with:
       python train.py --dataset-type cic-ids2017 \\
                       --dataset data/CIC-IDS2017-combined.csv
   ─────────────────────────────────────────────────────────""")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n  Data directory ready: {DATA_DIR.resolve()}")


def _print_manual_instructions(dataset: str):
    print(f"\n  Please download {dataset} manually and place in: {DATA_DIR.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="CyberShield Dataset Download Helper",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=["nsl-kdd", "cic-ids2017", "both"],
        default="both",
        help="Dataset to download (default: both)",
    )
    args = parser.parse_args()

    if args.dataset in ("nsl-kdd", "both"):
        download_nsl_kdd()

    if args.dataset in ("cic-ids2017", "both"):
        download_cic_ids2017()

    print("\n✅ Done. Run 'python train.py --help' to see training options.")


if __name__ == "__main__":
    main()
