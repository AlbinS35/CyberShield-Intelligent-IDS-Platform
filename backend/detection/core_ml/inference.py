"""
ML Inference Engine
Random Forest classifier for network intrusion detection.
Loads pre-trained model from disk and provides fast inference.
"""

import os
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("cybershield.ml")

# Path to the trained model binary
MODEL_DIR = Path(__file__).resolve().parent / "model_bin"
MODEL_PATH = MODEL_DIR / "rf_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# NSL-KDD feature column names (41 features)
FEATURE_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins",
    "logged_in", "num_compromised", "root_shell", "su_attempted", "num_root",
    "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
]

# Attack class labels
ATTACK_CLASSES = {
    0: "NORMAL",
    1: "DOS",
    2: "PROBE",
    3: "R2L",
    4: "U2R",
}


class IntrusionClassifier:
    """
    Singleton wrapper around the trained Random Forest model.
    Handles model loading, feature validation, and inference.
    """

    _instance: Optional["IntrusionClassifier"] = None
    _model = None
    _scaler = None
    _model_version = "v1.0"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self) -> bool:
        """Load model and scaler from disk. Returns True if successful."""
        try:
            import joblib
            if not MODEL_PATH.exists():
                logger.warning(f"Model not found at {MODEL_PATH}. Run: python manage.py train_model")
                return False
            self._model = joblib.load(MODEL_PATH)
            if SCALER_PATH.exists():
                self._scaler = joblib.load(SCALER_PATH)
            logger.info(f"ML model loaded from {MODEL_PATH}")
            return True
        except Exception as exc:
            logger.error(f"Failed to load ML model: {exc}")
            return False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def predict(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """
        Run inference on a feature dictionary.

        Args:
            features: Dict mapping feature names to numeric values.

        Returns:
            Tuple of (predicted_class_label, confidence_score)
        """
        if not self.is_loaded:
            self.load()
        if not self.is_loaded:
            return "UNKNOWN", 0.0

        start = time.perf_counter()
        try:
            vector = self._build_feature_vector(features)
            if self._scaler:
                vector = self._scaler.transform(vector)
            proba = self._model.predict_proba(vector)[0]
            class_idx = int(np.argmax(proba))
            confidence = float(proba[class_idx])
            label = ATTACK_CLASSES.get(class_idx, "UNKNOWN")
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.debug(f"ML inference: {label} ({confidence:.3f}) in {elapsed_ms:.1f}ms")
            return label, confidence
        except Exception as exc:
            logger.error(f"Inference error: {exc}")
            return "UNKNOWN", 0.0

    def _build_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Build a numpy feature vector from a dict, filling missing features with 0."""
        row = [float(features.get(col, 0.0)) for col in FEATURE_COLUMNS]
        return np.array([row])

    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the loaded model."""
        if not self.is_loaded:
            return {"loaded": False}
        return {
            "loaded": True,
            "version": self._model_version,
            "model_type": type(self._model).__name__,
            "n_estimators": getattr(self._model, "n_estimators", None),
            "feature_count": len(FEATURE_COLUMNS),
            "classes": list(ATTACK_CLASSES.values()),
        }


# Global singleton
classifier = IntrusionClassifier()
