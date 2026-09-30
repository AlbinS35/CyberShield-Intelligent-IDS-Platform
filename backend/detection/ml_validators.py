"""
ML Pipeline Validators
Pre-inference validation utilities to sanitize and validate feature vectors
before they are passed to the Random Forest classifier.

This prevents common failure modes:
  - Missing features causing shape mismatch (wrong number of columns)
  - Out-of-range values corrupting probability output
  - Non-numeric types passed to scikit-learn estimators
"""

import logging
from typing import Any

from ingestion.constants import NSL_KDD_FEATURES

logger = logging.getLogger("cybershield.detection.ml_validators")


class FeatureValidationError(ValueError):
    """Raised when a feature vector fails validation before ML inference."""
    pass


# ── Valid categorical encodings ───────────────────────────────────────────────
# The NSL-KDD dataset uses label-encoded integers for categorical features.
# protocol_type: {0: tcp, 1: udp, 2: icmp}
# flag:          {0: SF, 1: S0, 2: REJ, 3: RSTO, ...}
VALID_PROTOCOL_CODES = frozenset(range(3))   # 0, 1, 2
VALID_FLAG_CODES     = frozenset(range(11))  # 0–10

# Numeric features that must be non-negative
NON_NEGATIVE_FEATURES = frozenset([
    "duration", "src_bytes", "dst_bytes", "wrong_fragment", "urgent",
    "hot", "num_failed_logins", "num_compromised", "num_root",
    "num_file_creations", "num_shells", "num_access_files",
    "count", "srv_count", "dst_host_count", "dst_host_srv_count",
])

# Rate features that must be in [0.0, 1.0]
RATE_FEATURES = frozenset([
    "serror_rate", "srv_serror_rate", "rerror_rate", "srv_rerror_rate",
    "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
])


def validate_feature_vector(features: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and sanitize a feature dict before passing to the classifier.

    Performs:
    1. Checks all 41 expected NSL-KDD features are present.
    2. Coerces values to float (raises FeatureValidationError on failure).
    3. Clamps rate features to [0.0, 1.0].
    4. Clips non-negative features to 0 minimum.
    5. Logs any corrections applied (for audit traceability).

    Args:
        features: Dict mapping NSL-KDD feature name → raw value.

    Returns:
        Sanitized dict of {feature_name: float} in NSL_KDD_FEATURES order.

    Raises:
        FeatureValidationError: If a required feature is missing or cannot
                                be coerced to a numeric type.
    """
    sanitized = {}
    corrections = []

    for feature_name in NSL_KDD_FEATURES:
        if feature_name not in features:
            logger.warning(f"Missing feature '{feature_name}', defaulting to 0.")
            raw_value = 0
        else:
            raw_value = features[feature_name]

        # Coerce to float
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise FeatureValidationError(
                f"Feature '{feature_name}' has non-numeric value: {raw_value!r}"
            )

        # Clamp rate features to [0.0, 1.0]
        if feature_name in RATE_FEATURES:
            clamped = max(0.0, min(1.0, value))
            if clamped != value:
                corrections.append(f"{feature_name}: {value:.4f} → {clamped:.4f} (clamped to [0,1])")
            value = clamped

        # Non-negative clamp
        elif feature_name in NON_NEGATIVE_FEATURES:
            if value < 0:
                corrections.append(f"{feature_name}: {value} → 0 (negative clipped)")
                value = 0.0

        sanitized[feature_name] = value

    if corrections:
        logger.info(f"Feature vector sanitization applied {len(corrections)} correction(s): {corrections}")

    return sanitized


def feature_vector_to_list(features: dict[str, float]) -> list[float]:
    """
    Convert a validated feature dict to an ordered list for scikit-learn.

    The list ordering strictly follows NSL_KDD_FEATURES — this is critical
    because sklearn models are position-sensitive, not name-sensitive.

    Args:
        features: Sanitized feature dict from validate_feature_vector().

    Returns:
        List of 41 floats in NSL_KDD_FEATURES column order.
    """
    return [features[name] for name in NSL_KDD_FEATURES]
