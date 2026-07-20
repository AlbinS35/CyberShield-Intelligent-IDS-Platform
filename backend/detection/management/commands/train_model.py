"""
Django Management Command: train_model
Trains the Random Forest intrusion detection classifier.

Usage:
    python manage.py train_model
    python manage.py train_model --dataset data/NSL-KDD-Train.csv
    python manage.py train_model --estimators 300 --depth 25
"""

import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from detection.core_ml.train_rf import train_model


class Command(BaseCommand):
    help = "Train the Random Forest intrusion detection model on NSL-KDD dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            type=str,
            default="ml_pipeline/data/NSL-KDD-Train.csv",
            help="Path to NSL-KDD training CSV file.",
        )
        parser.add_argument("--estimators", type=int, default=200, help="Number of RF trees (default: 200).")
        parser.add_argument("--depth", type=int, default=20, help="Max tree depth (default: 20).")

    def handle(self, *args, **options):
        dataset_path = options["dataset"]
        if not Path(dataset_path).exists():
            raise CommandError(
                f"Dataset not found at '{dataset_path}'.\n"
                f"Download NSL-KDD from: https://www.unb.ca/cic/datasets/nsl.html\n"
                f"Place KDDTrain+.csv at: {dataset_path}"
            )

        self.stdout.write(self.style.WARNING(f"Starting model training on: {dataset_path}"))

        result = train_model(
            dataset_path=dataset_path,
            n_estimators=options["estimators"],
            max_depth=options["depth"],
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Training Complete!\n"
            f"   Accuracy:       {result['accuracy']:.4f} ({result['accuracy']*100:.2f}%)\n"
            f"   Training time:  {result['training_time_s']}s\n"
            f"   Train samples:  {result['n_samples_train']}\n"
            f"   Test samples:   {result['n_samples_test']}\n"
            f"   Model saved:    {result['model_path']}\n"
        ))

        # Print per-class metrics
        self.stdout.write("\n📊 Classification Report:")
        for class_name, metrics in result["classification_report"].items():
            if isinstance(metrics, dict):
                self.stdout.write(
                    f"   {class_name:<10} precision={metrics['precision']:.3f}  "
                    f"recall={metrics['recall']:.3f}  f1={metrics['f1-score']:.3f}"
                )
