"""
Detection Celery Tasks
ML classification of network events, SHAP explanation generation,
confidence-gated automated playbook execution engine.

Drawback mitigations implemented here:
  1. Confidence Gate: AUTO playbooks only fire at confidence ≥ 0.85 AND
     severity HIGH/CRITICAL — preventing false-positive business disruptions.
  2. Async SHAP: Explanations are computed in a separate Celery task so they
     never block the <50ms inference latency budget.
"""

import logging
import ipaddress
import subprocess
import shlex
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger("cybershield.detection.tasks")

# ── Confidence Gate Configuration ─────────────────────────────────────────────
# AUTO playbooks only fire when BOTH conditions are met:
#   1. confidence >= AUTO_PLAYBOOK_MIN_CONFIDENCE
#   2. severity in AUTO_PLAYBOOK_MIN_SEVERITIES
# Alerts below this threshold are created but held for analyst review,
# with playbook_gated=True flag set on the Alert.
AUTO_PLAYBOOK_MIN_CONFIDENCE = 0.85
AUTO_PLAYBOOK_MIN_SEVERITIES = {"HIGH", "CRITICAL"}


@shared_task(bind=True, max_retries=2, default_retry_delay=5)
def classify_network_event(self, event_id: str):
    """
    Celery task: Run ML inference on a NetworkEvent and create an Alert if threat detected.

    Pipeline:
    1. Load NetworkEvent by ID
    2. Extract feature vector from raw_data
    3. Run Random Forest classifier (predict)
    4. Update NetworkEvent with classification result
    5. If threat detected → create Alert record
    6. Broadcast Alert via WebSocket to tenant group
    7. Log inference in MLInferenceLog
    8. Dispatch async SHAP explanation task
    9. Apply confidence gate before firing auto-playbooks
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

    # ── Feature extraction ────────────────────────────────────────────────────
    features = _extract_features(event.raw_data)

    import time
    start = time.perf_counter()
    prediction, confidence = classifier.predict(features)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # ── Update NetworkEvent ───────────────────────────────────────────────────
    is_threat = prediction != "NORMAL"
    NetworkEvent.objects.filter(id=event_id).update(
        ml_classification=prediction,
        ml_confidence=confidence,
        is_threat=is_threat,
    )

    # ── Log inference ─────────────────────────────────────────────────────────
    log_entry = MLInferenceLog.objects.create(
        network_event=event,
        input_features=features,
        prediction=prediction,
        confidence=confidence,
        inference_time_ms=round(elapsed_ms, 2),
        dataset_source=classifier.dataset_source,
        # shap_explanation is populated asynchronously below
    )

    # ── Dispatch async SHAP explanation (non-blocking) ────────────────────────
    generate_shap_explanation.delay(str(log_entry.id), features)

    # ── Create Alert if threat detected ──────────────────────────────────────
    if is_threat:
        severity = _confidence_to_severity(prediction, confidence)
        gated = _should_gate_playbook(severity, confidence)

        alert = Alert.objects.create(
            tenant=event.tenant,
            network_event=event,
            title=f"{prediction} Attack Detected from {event.source_ip or 'Unknown'}",
            description=(
                f"ML classifier identified {prediction} attack pattern "
                f"with {confidence:.1%} confidence "
                f"[{classifier.dataset_source} model]."
                + (
                    f" ⚠️ Auto-response held: confidence {confidence:.1%} below "
                    f"{AUTO_PLAYBOOK_MIN_CONFIDENCE:.0%} threshold — analyst review required."
                    if gated else ""
                )
            ),
            severity=severity,
            attack_type=prediction,
            source_ip=event.source_ip,
            destination_ip=event.destination_ip,
            ml_confidence=confidence,
            playbook_gated=gated,
        )
        logger.info(
            f"Alert created: [{severity}] {alert.title} "
            f"(confidence={confidence:.2f}, gated={gated})"
        )

        # Broadcast via WebSocket
        _broadcast_alert(alert)

        # ── Confidence Gate: only fire AUTO playbooks when safe ───────────────
        if not gated:
            _auto_trigger_playbooks(alert)
        else:
            logger.info(
                f"[Gate] Auto-playbook suppressed for alert {alert.id} — "
                f"confidence {confidence:.2f} < {AUTO_PLAYBOOK_MIN_CONFIDENCE} "
                f"or severity '{severity}' not in {AUTO_PLAYBOOK_MIN_SEVERITIES}"
            )

    return {"prediction": prediction, "confidence": confidence, "is_threat": is_threat}


@shared_task(bind=True, max_retries=1, default_retry_delay=10)
def generate_shap_explanation(self, log_entry_id: str, features: dict):
    """
    Async Celery task: Compute SHAP explanation for a completed inference log.

    Runs AFTER the main classification task returns so it never blocks
    the <50ms inference latency budget. Stores results in MLInferenceLog.shap_explanation.
    """
    from .models import MLInferenceLog
    from .core_ml.inference import classifier

    try:
        log_entry = MLInferenceLog.objects.get(id=log_entry_id)
    except MLInferenceLog.DoesNotExist:
        logger.warning(f"MLInferenceLog {log_entry_id} not found for SHAP.")
        return

    if not classifier.is_loaded:
        classifier.load()

    try:
        explanation = classifier.explain(features, top_n=10)
        if explanation:
            log_entry.shap_explanation = explanation
            log_entry.save(update_fields=["shap_explanation"])
            logger.debug(f"SHAP explanation stored for log {log_entry_id}")
    except Exception as exc:
        logger.warning(f"SHAP explanation failed for log {log_entry_id}: {exc}")


def _extract_features(raw_data: dict) -> dict:
    """Extract ML feature values from Wazuh/Suricata raw_data payload."""
    data = raw_data.get("data", {})
    # Suricata eve.json uses different key names — normalise both
    suricata = raw_data.get("flow", {})

    # CIC-IDS2017 protocol numeric encoding (IANA assigned protocol numbers)
    _PROTO_MAP = {"TCP": 6.0, "UDP": 17.0, "ICMP": 1.0, "HOPOPT": 0.0}
    proto_raw = str(raw_data.get("proto", data.get("protocol_type", ""))).upper()
    proto_numeric = _PROTO_MAP.get(proto_raw, 0.0)

    return {
        "duration":             float(data.get("duration",             suricata.get("duration", 0))),
        "src_bytes":            float(data.get("src_bytes",            raw_data.get("src_bytes", suricata.get("bytes_toserver", 0)))),
        "dst_bytes":            float(data.get("dst_bytes",            raw_data.get("dst_bytes", suricata.get("bytes_toclient", 0)))),
        "src_port":             float(raw_data.get("src_port",         raw_data.get("sport",     0))),
        "dst_port":             float(raw_data.get("dest_port",        raw_data.get("dport",     0))),
        "land":                 float(data.get("land",                 0)),
        "wrong_fragment":       float(data.get("wrong_fragment",       0)),
        "urgent":               float(data.get("urgent",               0)),
        "hot":                  float(data.get("hot",                  0)),
        "logged_in":            float(data.get("logged_in",            0)),
        "count":                float(data.get("count",                0)),
        "srv_count":            float(data.get("srv_count",            0)),
        "serror_rate":          float(data.get("serror_rate",          0)),
        "same_srv_rate":        float(data.get("same_srv_rate",        0)),
        "diff_srv_rate":        float(data.get("diff_srv_rate",        0)),
        "dst_host_count":       float(data.get("dst_host_count",       0)),
        "dst_host_srv_count":   float(data.get("dst_host_srv_count",   0)),
        # CIC-IDS2017 flow features (populated from Suricata)
        "protocol":             proto_numeric,                         # IANA numeric: TCP=6, UDP=17, ICMP=1
        "fwd_packets":          float(suricata.get("pkts_toserver",    0)),
        "bwd_packets":          float(suricata.get("pkts_toclient",    0)),
        "syn_flag_count":       float(raw_data.get("tcp", {}).get("syn", 0)),
        "fin_flag_count":       float(raw_data.get("tcp", {}).get("fin", 0)),
        "rst_flag_count":       float(raw_data.get("tcp", {}).get("rst", 0)),
        "ack_flag_count":       float(raw_data.get("tcp", {}).get("ack", 0)),
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


def _should_gate_playbook(severity: str, confidence: float) -> bool:
    """
    Determine whether an auto-playbook should be suppressed (gated).

    Returns True (gate/suppress) if:
      - confidence is below AUTO_PLAYBOOK_MIN_CONFIDENCE, OR
      - severity is not in AUTO_PLAYBOOK_MIN_SEVERITIES (HIGH/CRITICAL)

    This prevents false-positive iptables blocks from disrupting business
    operations when the ML model is less certain about its classification.
    """
    return confidence < AUTO_PLAYBOOK_MIN_CONFIDENCE or severity not in AUTO_PLAYBOOK_MIN_SEVERITIES


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
                "type":  "alert.new",
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

    Note: This task is only called by _auto_trigger_playbooks() when the
    confidence gate passes (confidence >= 0.85 AND severity HIGH/CRITICAL),
    preventing false-positive business disruption.
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
            # ── IP Sanitization: strict validation before any shell substitution ─
            if target_ip:
                try:
                    safe_ip = str(ipaddress.ip_address(target_ip))
                except ValueError:
                    logger.error(
                        f"[Playbook '{playbook.name}'] BLOCKED: target_ip '{target_ip}' "
                        f"is not a valid IP address. Possible injection attempt. Aborting."
                    )
                    execution.status = PlaybookExecution.ExecStatus.FAILED
                    execution.stderr = f"Security error: invalid target_ip '{target_ip}' rejected by IP sanitizer."
                    execution.completed_at = datetime.now(tz=timezone.utc)
                    execution.save()
                    return str(execution.id)
            else:
                safe_ip = "0.0.0.0"

            # Substitute {ip} placeholder with the validated, normalised IP
            cmd = raw_cmd.format(ip=safe_ip)
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
                    "reason":             f"Auto-blocked by playbook: {playbook.name}",
                    "playbook_execution": execution,
                    "is_active":          True,
                },
            )

    except Exception as exc:
        execution.status = PlaybookExecution.ExecStatus.FAILED
        execution.stderr = str(exc)
        execution.completed_at = datetime.now(tz=timezone.utc)
        execution.save()
        logger.error(f"Playbook execution failed: {exc}")

    return str(execution.id)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def rehash_event_batch(self, event_ids: list):
    """
    Async SHA-256 batch hasher — overhead mitigation.

    Called after bulk_create to compute log_hash values outside the hot
    ingestion path. This prevents SHA-256 computation from blocking
    high-throughput event ingestion.

    Args:
        event_ids: List of NetworkEvent UUID strings to hash.
    """
    import hashlib
    import json
    from ingestion.models import NetworkEvent

    try:
        events = NetworkEvent.objects.filter(id__in=event_ids, log_hash="")
        updates = []
        for event in events:
            raw = json.dumps(event.raw_data, sort_keys=True, separators=(",", ":"))
            event.log_hash = hashlib.sha256(raw.encode()).hexdigest()
            updates.append(event)

        if updates:
            NetworkEvent.objects.bulk_update(updates, ["log_hash"], batch_size=100)
            logger.info(f"[Hash] SHA-256 computed for {len(updates)} events.")

    except Exception as exc:
        logger.error(f"[Hash] Batch rehash failed: {exc}")
        raise self.retry(exc=exc)
