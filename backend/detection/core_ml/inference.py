"""
ML Inference Engine
Random Forest classifier for network intrusion detection.
Supports dual models: NSL-KDD baseline + CIC-IDS2017 modern dataset.
SHAP explanations are computed asynchronously and stored in MLInferenceLog.
"""

import os
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger("cybershield.ml")

# ── Model paths ───────────────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).resolve().parent / "model_bin"

# NSL-KDD model (primary baseline)
NSL_MODEL_PATH   = MODEL_DIR / "rf_model.pkl"
NSL_SCALER_PATH  = MODEL_DIR / "scaler.pkl"

# CIC-IDS2017 model (modern dataset — preferred if available)
CIC_MODEL_PATH   = MODEL_DIR / "cic_rf_model.pkl"
CIC_SCALER_PATH  = MODEL_DIR / "cic_scaler.pkl"

# ── NSL-KDD feature schema (41 features) ─────────────────────────────────────
NSL_FEATURE_COLUMNS = [
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

# ── CIC-IDS2017 common feature schema (shared flow features, ~20) ─────────────
# These are the features available at inference time from live Suricata/Wazuh data
CIC_FEATURE_COLUMNS = [
    "duration", "src_bytes", "dst_bytes", "src_port", "dst_port",
    "protocol", "fwd_packets", "bwd_packets", "fwd_pkt_len_mean",
    "bwd_pkt_len_mean", "flow_iat_mean", "fwd_iat_mean", "bwd_iat_mean",
    "fin_flag_count", "syn_flag_count", "rst_flag_count", "psh_flag_count",
    "ack_flag_count", "urg_flag_count", "down_up_ratio",
]

# ── Attack class labels (shared across both models) ───────────────────────────
ATTACK_CLASSES = {
    0: "NORMAL",
    1: "DOS",
    2: "PROBE",
    3: "R2L",
    4: "U2R",
}


class IntrusionClassifier:
    """
    Singleton wrapper around the trained Random Forest model(s).

    Load priority:
      1. CIC-IDS2017 model (preferred — modern dataset)
      2. NSL-KDD model (fallback — baseline benchmark)

    SHAP explanations are computed on-demand and returned as a ranked list.
    """

    _instance: Optional["IntrusionClassifier"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model        = None
            cls._instance._scaler       = None
            cls._instance._explainer    = None
            cls._instance._feature_cols = NSL_FEATURE_COLUMNS
            cls._instance._dataset_src  = "NSL-KDD"
            cls._instance._model_version = "v1.0"
        return cls._instance

    # ── Loading ───────────────────────────────────────────────────────────────

    def load(self) -> bool:
        """
        Load model and scaler. Prefers CIC-IDS2017 model if available,
        falls back to NSL-KDD. Returns True if any model was loaded.
        """
        import joblib
        # Try CIC-IDS2017 first
        if CIC_MODEL_PATH.exists():
            try:
                self._model  = joblib.load(CIC_MODEL_PATH)
                self._scaler = joblib.load(CIC_SCALER_PATH) if CIC_SCALER_PATH.exists() else None
                self._feature_cols = CIC_FEATURE_COLUMNS
                self._dataset_src  = "CIC-IDS2017"
                self._model_version = "v2.0"
                self._explainer = None  # reset — will be built on first explain() call
                logger.info(f"[ML] CIC-IDS2017 model loaded from {CIC_MODEL_PATH}")
                return True
            except Exception as exc:
                logger.warning(f"[ML] CIC model load failed ({exc}), falling back to NSL-KDD")

        # Fall back to NSL-KDD
        if NSL_MODEL_PATH.exists():
            try:
                self._model  = joblib.load(NSL_MODEL_PATH)
                self._scaler = joblib.load(NSL_SCALER_PATH) if NSL_SCALER_PATH.exists() else None
                self._feature_cols = NSL_FEATURE_COLUMNS
                self._dataset_src  = "NSL-KDD"
                self._model_version = "v1.0"
                self._explainer = None
                logger.info(f"[ML] NSL-KDD model loaded from {NSL_MODEL_PATH}")
                return True
            except Exception as exc:
                logger.error(f"[ML] NSL-KDD model load failed: {exc}")
                return False

        logger.warning(
            f"[ML] No model found in {MODEL_DIR}. "
            "Run: python ml_pipeline/train.py"
        )
        return False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def dataset_source(self) -> str:
        return self._dataset_src

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """
        Run inference on a feature dictionary.

        Returns:
            (predicted_class_label, confidence_score)
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
            class_idx  = int(np.argmax(proba))
            confidence = float(proba[class_idx])
            label      = ATTACK_CLASSES.get(class_idx, "UNKNOWN")
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.debug(
                f"[ML] {self._dataset_src}: {label} ({confidence:.3f}) in {elapsed_ms:.1f}ms"
            )
            return label, confidence
        except Exception as exc:
            logger.error(f"[ML] Inference error: {exc}")
            return "UNKNOWN", 0.0

    # ── SHAP Explainability ───────────────────────────────────────────────────

    def explain(self, features: Dict[str, Any], top_n: int = 10) -> List[Dict]:
        """
        Compute SHAP feature contributions for a single prediction.

        Returns a ranked list of top_n features:
            [{"feature": str, "value": float, "shap_value": float, "direction": "increases_risk"|"decreases_risk"}]

        This is designed to be called ASYNCHRONOUSLY from a Celery task after
        the main predict() call, so it does not block the inference latency path.
        """
        if not self.is_loaded:
            self.load()
        if not self.is_loaded:
            return []

        try:
            import shap

            # Build SHAP explainer once; cache on instance
            if self._explainer is None:
                self._explainer = shap.TreeExplainer(
                    self._model,
                    feature_perturbation="tree_path_dependent",
                )
                logger.info(f"[ML] SHAP TreeExplainer initialised for {self._dataset_src} model")

            vector = self._build_feature_vector(features)
            if self._scaler:
                vector = self._scaler.transform(vector)

            # shap_values shape: (n_classes, 1, n_features)
            shap_values = self._explainer.shap_values(vector)

            # Use the class with highest probability (same as predict)
            proba = self._model.predict_proba(vector)[0]
            class_idx = int(np.argmax(proba))

            if isinstance(shap_values, list):
                # Multi-class output: list of arrays per class
                sv = shap_values[class_idx][0]
            else:
                sv = shap_values[0]

            # Build ranked explanation
            ranked_indices = np.argsort(np.abs(sv))[::-1][:top_n]
            explanation = []
            for idx in ranked_indices:
                feat_name = self._feature_cols[idx] if idx < len(self._feature_cols) else f"feature_{idx}"
                shap_val  = float(sv[idx])
                explanation.append({
                    "feature":    feat_name,
                    "value":      float(features.get(feat_name, 0.0)),
                    "shap_value": round(shap_val, 5),
                    "direction":  "increases_risk" if shap_val > 0 else "decreases_risk",
                })
            return explanation

        except ImportError:
            logger.warning("[ML] SHAP not installed — skipping explanation. pip install shap")
            return []
        except Exception as exc:
            logger.error(f"[ML] SHAP explanation error: {exc}")
            return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Build a numpy feature vector from a dict, filling missing features with 0."""
        row = [float(features.get(col, 0.0)) for col in self._feature_cols]
        return np.array([row])

    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the loaded model."""
        if not self.is_loaded:
            return {"loaded": False}
        return {
            "loaded":         True,
            "version":        self._model_version,
            "dataset_source": self._dataset_src,
            "model_type":     type(self._model).__name__,
            "n_estimators":   getattr(self._model, "n_estimators", None),
            "feature_count":  len(self._feature_cols),
            "classes":        list(ATTACK_CLASSES.values()),
            "cic_model_available": CIC_MODEL_PATH.exists(),
            "nsl_model_available": NSL_MODEL_PATH.exists(),
        }

    # Keep backward compat alias
    FEATURE_COLUMNS = NSL_FEATURE_COLUMNS


# Global singleton
classifier = IntrusionClassifier()

# Convenience aliases (used in feature extraction)
FEATURE_COLUMNS = NSL_FEATURE_COLUMNS
ATTACK_CLASSES  = ATTACK_CLASSES
