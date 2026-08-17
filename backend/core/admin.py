"""
CyberShield Core Admin
========================
Registers all 7 tbl_ models in the Django admin with organized fieldsets,
list_display, search_fields, and list_filter for efficient management.
"""

from django.contrib import admin
from .models import (
    Organization,
    CoreUser,
    Login,
    NetworkAsset,
    ForensicCase,
    NetworkEvent,
    ContainmentAction,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display   = ["org_id", "org_name", "domain_name", "status", "created_at"]
    list_filter    = ["status"]
    search_fields  = ["org_name", "domain_name"]
    ordering       = ["org_name"]
    readonly_fields = ["org_id", "created_at"]

    fieldsets = (
        ("Identity", {"fields": ("org_name", "domain_name")}),
        ("Status",   {"fields": ("status",)}),
        ("Audit",    {"fields": ("org_id", "created_at"), "classes": ("collapse",)}),
    )


@admin.register(CoreUser)
class CoreUserAdmin(admin.ModelAdmin):
    list_display   = ["user_id", "full_name", "phone_no", "org", "created_at"]
    list_filter    = ["org"]
    search_fields  = ["full_name", "phone_no"]
    ordering       = ["full_name"]
    readonly_fields = ["user_id", "created_at"]

    fieldsets = (
        ("Identity",      {"fields": ("full_name", "phone_no")}),
        ("Organization",  {"fields": ("org",)}),
        ("Audit",         {"fields": ("user_id", "created_at"), "classes": ("collapse",)}),
    )


@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display   = ["login_id", "email", "role", "status", "user"]
    list_filter    = ["role", "status"]
    search_fields  = ["email"]
    readonly_fields = ["login_id", "password_hash"]

    fieldsets = (
        ("Credentials", {"fields": ("user", "email", "password_hash")}),
        ("RBAC",        {"fields": ("role", "status")}),
        ("Audit",       {"fields": ("login_id",), "classes": ("collapse",)}),
    )


@admin.register(NetworkAsset)
class NetworkAssetAdmin(admin.ModelAdmin):
    list_display   = ["asset_id", "asset_name", "ip_address", "os_type", "org", "status"]
    list_filter    = ["status", "org", "os_type"]
    search_fields  = ["asset_name", "ip_address", "wazuh_agent_id"]
    ordering       = ["asset_name"]
    readonly_fields = ["asset_id"]

    fieldsets = (
        ("Identity",    {"fields": ("asset_name", "ip_address", "os_type")}),
        ("Organization",{"fields": ("org",)}),
        ("Integration", {"fields": ("wazuh_agent_id",)}),
        ("Status",      {"fields": ("status",)}),
        ("Audit",       {"fields": ("asset_id",), "classes": ("collapse",)}),
    )


@admin.register(ForensicCase)
class ForensicCaseAdmin(admin.ModelAdmin):
    list_display   = ["case_id", "case_title", "status", "created_by", "created_at"]
    list_filter    = ["status"]
    search_fields  = ["case_title", "description"]
    ordering       = ["-created_at"]
    readonly_fields = ["case_id", "created_at"]

    fieldsets = (
        ("Case",       {"fields": ("case_title", "description")}),
        ("Status",     {"fields": ("status", "created_by")}),
        ("Audit",      {"fields": ("case_id", "created_at"), "classes": ("collapse",)}),
    )


@admin.register(NetworkEvent)
class NetworkEventAdmin(admin.ModelAdmin):
    list_display  = [
        "event_id", "asset", "source_ip", "destination_ip",
        "threat_classification", "confidence_score", "timestamp",
    ]
    list_filter   = ["threat_classification", "asset"]
    search_fields = ["source_ip", "destination_ip", "threat_classification", "sha256_hash"]
    ordering      = ["-timestamp"]
    readonly_fields = ["event_id", "timestamp", "sha256_hash"]

    fieldsets = (
        ("Network",    {"fields": ("asset", "source_ip", "destination_ip")}),
        ("Telemetry",  {"fields": ("raw_telemetry",)}),
        ("Threat",     {"fields": ("threat_classification", "confidence_score")}),
        ("Integrity",  {"fields": ("sha256_hash",)}),
        ("Audit",      {"fields": ("event_id", "timestamp"), "classes": ("collapse",)}),
    )


@admin.register(ContainmentAction)
class ContainmentActionAdmin(admin.ModelAdmin):
    list_display  = [
        "action_id", "event", "action_type",
        "target_ip", "execution_status", "executed_at",
    ]
    list_filter   = ["execution_status", "action_type"]
    search_fields = ["target_ip", "action_type"]
    ordering      = ["-executed_at"]
    readonly_fields = ["action_id", "executed_at"]

    fieldsets = (
        ("Action",    {"fields": ("event", "action_type", "target_ip")}),
        ("Result",    {"fields": ("execution_status",)}),
        ("Audit",     {"fields": ("action_id", "executed_at"), "classes": ("collapse",)}),
    )
