"""
Forensics Admin Registration
"""

from django.contrib import admin
from .models import ForensicCase, Evidence, CaseTimeline, ChainOfCustody


class EvidenceInline(admin.TabularInline):
    model = Evidence
    extra = 0
    readonly_fields = ["sha256_hash", "file_name", "file_size_bytes", "uploaded_at"]
    fields = ["evidence_type", "title", "file", "sha256_hash", "uploaded_by", "uploaded_at"]


class TimelineInline(admin.TabularInline):
    model = CaseTimeline
    extra = 0
    readonly_fields = ["recorded_at"]
    fields = ["category", "title", "source_ip", "target_ip", "event_time"]


@admin.register(ForensicCase)
class ForensicCaseAdmin(admin.ModelAdmin):
    list_display  = ["case_number", "title", "tenant", "status", "classification",
                     "lead_investigator", "legal_hold", "created_at"]
    list_filter   = ["status", "classification", "legal_hold", "tenant"]
    search_fields = ["case_number", "title", "description"]
    readonly_fields = ["id", "case_number", "created_at", "updated_at"]
    ordering = ["-created_at"]
    inlines = [EvidenceInline, TimelineInline]

    fieldsets = (
        ("Case Info", {
            "fields": ("id", "case_number", "tenant", "title", "description",
                       "status", "classification", "legal_hold")
        }),
        ("Investigation", {
            "fields": ("related_incident", "lead_investigator", "attack_vector", "affected_systems")
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at", "closed_at")}),
    )


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display  = ["title", "case", "evidence_type", "file_name", "file_size_bytes",
                     "sha256_hash", "uploaded_by", "uploaded_at"]
    list_filter   = ["evidence_type", "case__tenant"]
    search_fields = ["title", "sha256_hash", "file_name"]
    readonly_fields = ["id", "sha256_hash", "file_name", "file_size_bytes", "uploaded_at"]


class ChainOfCustodyInline(admin.TabularInline):
    model = ChainOfCustody
    extra = 0
    readonly_fields = ["timestamp"]


@admin.register(CaseTimeline)
class CaseTimelineAdmin(admin.ModelAdmin):
    list_display  = ["title", "case", "category", "source_ip", "target_ip",
                     "event_time", "recorded_by"]
    list_filter   = ["category", "case__tenant"]
    search_fields = ["title", "description", "source_ip", "target_ip"]
    readonly_fields = ["id", "recorded_at"]
    ordering = ["event_time"]


@admin.register(ChainOfCustody)
class ChainOfCustodyAdmin(admin.ModelAdmin):
    list_display  = ["evidence", "action", "performed_by", "location", "timestamp"]
    list_filter   = ["action"]
    readonly_fields = ["id", "timestamp"]
    ordering = ["timestamp"]
