"""
Detection Admin Registration
"""

from django.contrib import admin
from .models import Alert, Incident, Playbook, PlaybookExecution, IPBlocklist, MLInferenceLog


class AlertInline(admin.TabularInline):
    model = Incident.alerts.through
    extra = 0


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display  = ["title", "tenant", "severity", "status", "attack_type",
                     "source_ip", "ml_confidence", "assigned_to", "created_at"]
    list_filter   = ["severity", "status", "attack_type", "tenant"]
    search_fields = ["title", "source_ip", "destination_ip", "affected_asset"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    raw_id_fields  = ["assigned_to", "network_event"]

    fieldsets = (
        ("Alert Info", {
            "fields": ("tenant", "title", "description", "severity", "status", "attack_type")
        }),
        ("Network Context", {"fields": ("source_ip", "destination_ip", "affected_asset", "network_event")}),
        ("ML Data",         {"fields": ("ml_confidence",)}),
        ("Assignment",      {"fields": ("assigned_to", "resolved_at")}),
        ("Timestamps",      {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display  = ["title", "tenant", "status", "severity", "lead_analyst", "created_at"]
    list_filter   = ["status", "severity", "tenant"]
    search_fields = ["title", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    filter_horizontal = ["alerts"]


@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    list_display  = ["name", "tenant", "trigger_mode", "trigger_severity", "is_active", "created_at"]
    list_filter   = ["trigger_mode", "trigger_severity", "is_active", "tenant"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at"]


@admin.register(PlaybookExecution)
class PlaybookExecutionAdmin(admin.ModelAdmin):
    list_display  = ["playbook", "alert", "status", "target_ip", "is_dry_run",
                     "exit_code", "executed_at"]
    list_filter   = ["status", "is_dry_run"]
    readonly_fields = ["id", "executed_at", "completed_at"]
    ordering = ["-executed_at"]


@admin.register(IPBlocklist)
class IPBlocklistAdmin(admin.ModelAdmin):
    list_display  = ["ip_address", "tenant", "is_active", "blocked_by", "blocked_at", "expires_at"]
    list_filter   = ["is_active", "tenant"]
    search_fields = ["ip_address", "reason"]
    readonly_fields = ["id", "blocked_at"]


@admin.register(MLInferenceLog)
class MLInferenceLogAdmin(admin.ModelAdmin):
    list_display  = ["prediction", "confidence", "model_version", "inference_time_ms", "inferred_at"]
    list_filter   = ["prediction", "model_version"]
    readonly_fields = ["id", "inferred_at"]
    ordering = ["-inferred_at"]
