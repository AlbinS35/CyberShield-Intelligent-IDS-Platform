"""
Detection Celery Tasks
ML classification of network events and automated playbook execution engine.
"""

import logging
import subprocess
import shlex
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger("cybershield.detection.tasks")


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def classify_network_event(self, event_id: str):
    """
    Celery task: Run ML inference on a NetworkEvent and create an Alert if threat detected.

    Pipeline:
    1. Load NetworkEvent by ID
    2. Extract feature vector from raw_data
    3. Run Random Forest classifier
    4. Update NetworkEvent with classification result
    5. If threat detected → create Alert record
    6. Broadcast Alert via WebSocket to tenant group
    7. Log inference in MLInferenceLog
    """
    from ingestion.models import NetworkEvent
    from .models import Alert, MLInferenceLog
    from .core_ml.inference import classifier

    try:
        event = NetworkEvent.objects.select_related("tenant").get(id=event_id)
    except NetworkEvent.DoesNotExist:
        logger.error(f"NetworkEvent {event_id} not found.")
        return

    if not classifier.is_loaded:
        classifier.load()

    # Build feature dict from raw_data (best-effort extraction)
    features = _extract_features(event.raw_data)

    import time
    start = time.perf_counter()
    prediction, confidence = classifier.predict(features)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Update the NetworkEvent record
    is_threat = prediction != "NORMAL"
    NetworkEvent.objects.filter(id=event_id).update(
        ml_classification=prediction,
        ml_confidence=confidence,
        is_threat=is_threat,
    )

    # Log inference
    MLInferenceLog.objects.create(
        network_event=event,
        input_features=features,
        prediction=prediction,
        confidence=confidence,
        inference_time_ms=round(elapsed_ms, 2),
    )

    # Create Alert if threat detected
    if is_threat:
        severity = _confidence_to_severity(prediction, confidence)
        alert = Alert.objects.create(
            tenant=event.tenant,
            network_event=event,
            title=f"{prediction} Attack Detected from {event.source_ip or 'Unknown'}",
            description=(
                f"ML classifier identified {prediction} attack pattern "
                f"with {confidence:.1%} confidence."
            ),
            severity=severity,
            attack_type=prediction,
            source_ip=event.source_ip,
            destination_ip=event.destination_ip,
            ml_confidence=confidence,
        )
        logger.info(f"Alert created: [{severity}] {alert.title}")

        # Broadcast via WebSocket
        _broadcast_alert(alert)

        # Auto-trigger playbooks if any match this severity
        _auto_trigger_playbooks(alert)

    return {"prediction": prediction, "confidence": confidence, "is_threat": is_threat}


def _extract_features(raw_data: dict) -> dict:
    """Extract ML feature values from Wazuh raw_data payload."""
    data = raw_data.get("data", {})
    return {
        "duration": float(data.get("duration", 0)),
        "src_bytes": float(data.get("src_bytes", raw_data.get("src_bytes", 0))),
        "dst_bytes": float(data.get("dst_bytes", raw_data.get("dst_bytes", 0))),
        "land": float(data.get("land", 0)),
        "wrong_fragment": float(data.get("wrong_fragment", 0)),
        "urgent": float(data.get("urgent", 0)),
        "hot": float(data.get("hot", 0)),
        "logged_in": float(data.get("logged_in", 0)),
        "count": float(data.get("count", 0)),
        "srv_count": float(data.get("srv_count", 0)),
        "serror_rate": float(data.get("serror_rate", 0)),
        "same_srv_rate": float(data.get("same_srv_rate", 0)),
        "diff_srv_rate": float(data.get("diff_srv_rate", 0)),
        "dst_host_count": float(data.get("dst_host_count", 0)),
        "dst_host_srv_count": float(data.get("dst_host_srv_count", 0)),
    }


def _confidence_to_severity(attack_type: str, confidence: float) -> str:
    """Map attack type and ML confidence to Alert severity."""
    if attack_type in ("U2R", "R2L") or confidence > 0.95:
        return "CRITICAL"
    elif attack_type == "DOS" or confidence > 0.85:
        return "HIGH"
    elif attack_type == "PROBE" or confidence > 0.70:
        return "MEDIUM"
    return "LOW"


def _broadcast_alert(alert) -> None:
    """Send new alert to Django Channels tenant group via Redis."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from .serializers import AlertSerializer

        channel_layer = get_channel_layer()
        group_name = f"alerts_{alert.tenant_id}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "alert.new",
                "alert": AlertSerializer(alert).data,
            },
        )
    except Exception as exc:
        logger.warning(f"WebSocket broadcast failed: {exc}")


def _auto_trigger_playbooks(alert) -> None:
    """Auto-execute any playbooks configured for this severity level."""
    from .models import Playbook
    auto_playbooks = Playbook.objects.filter(
        tenant=alert.tenant,
        trigger_mode=Playbook.TriggerMode.AUTO,
        trigger_severity=alert.severity,
        is_active=True,
    )
    for playbook in auto_playbooks:
        execute_playbook.delay(str(playbook.id), str(alert.id), alert.source_ip)


@shared_task(bind=True, max_retries=1)
def execute_playbook(self, playbook_id: str, alert_id: str = None, target_ip: str = None, dry_run: bool = False):
    """
    Celery task: Execute a security response playbook.

    Runs each command in the playbook's command list sequentially,
    substituting {ip} with target_ip where applicable.
    Full stdout/stderr are captured and saved to PlaybookExecution.
    """
    from .models import Playbook, PlaybookExecution, Alert

    try:
        playbook = Playbook.objects.get(id=playbook_id)
    except Playbook.DoesNotExist:
        logger.error(f"Playbook {playbook_id} not found.")
        return

    alert = None
    if alert_id:
        alert = Alert.objects.filter(id=alert_id).first()

    execution = PlaybookExecution.objects.create(
        playbook=playbook,
        alert=alert,
        target_ip=target_ip,
        status=PlaybookExecution.ExecStatus.RUNNING if not dry_run else PlaybookExecution.ExecStatus.DRY_RUN,
        is_dry_run=dry_run,
    )

    combined_stdout = []
    combined_stderr = []
    final_exit_code = 0

    try:
        for raw_cmd in playbook.commands:
            # Substitute {ip} placeholder with target IP
            cmd = raw_cmd.format(ip=target_ip or "0.0.0.0")
            logger.info(f"[Playbook '{playbook.name}'] Running: {cmd}" + (" (DRY RUN)" if dry_run else ""))

            if dry_run:
                combined_stdout.append(f"[DRY RUN] Would execute: {cmd}")
                continue

            result = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=30,
            )
            combined_stdout.append(f"$ {cmd}\n{result.stdout}")
            if result.stderr:
                combined_stderr.append(result.stderr)
            if result.returncode != 0:
                final_exit_code = result.returncode

        final_status = PlaybookExecution.ExecStatus.SUCCESS if final_exit_code == 0 else PlaybookExecution.ExecStatus.FAILED
        execution.status = final_status if not dry_run else PlaybookExecution.ExecStatus.DRY_RUN
        execution.stdout = "\n".join(combined_stdout)
        execution.stderr = "\n".join(combined_stderr)
        execution.exit_code = final_exit_code
        execution.completed_at = datetime.now(tz=timezone.utc)
        execution.save()

        # If successful and target IP provided, add to blocklist
        if final_exit_code == 0 and target_ip and not dry_run:
            from .models import IPBlocklist
            IPBlocklist.objects.get_or_create(
                tenant=playbook.tenant,
                ip_address=target_ip,
                defaults={
                    "reason": f"Auto-blocked by playbook: {playbook.name}",
                    "playbook_execution": execution,
                    "is_active": True,
                },
            )

    except Exception as exc:
        execution.status = PlaybookExecution.ExecStatus.FAILED
        execution.stderr = str(exc)
        execution.completed_at = datetime.now(tz=timezone.utc)
        execution.save()
        logger.error(f"Playbook execution failed: {exc}")

    return str(execution.id)
