from django.apps import AppConfig


class DetectionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "detection"
    verbose_name = "Threat Detection & Response"

    def ready(self):
        """Pre-load the ML model when Django starts to avoid cold-start latency."""
        try:
            from detection.core_ml.inference import classifier
            if not classifier.is_loaded:
                classifier.load()
        except Exception:
            pass  # Model binary not present yet — will load on first inference
