"""
Authentication Admin Registration
Exposes Tenant and User models with rich list views in Django Admin.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display  = ["name", "slug", "industry", "contact_email", "is_active", "created_at"]
    list_filter   = ["is_active", "industry"]
    search_fields = ["name", "slug", "contact_email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Organization Info", {"fields": ("id", "name", "slug", "description", "industry", "contact_email")}),
        ("Wazuh Integration",  {"fields": ("wazuh_manager_url", "wazuh_api_user", "wazuh_api_password"),
                                "classes": ("collapse",)}),
        ("Status",             {"fields": ("is_active", "created_at", "updated_at")}),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ["email", "get_full_name", "role", "tenant", "is_active", "date_joined"]
    list_filter   = ["role", "is_active", "tenant"]
    search_fields = ["email", "first_name", "last_name"]
    ordering      = ["-date_joined"]
    readonly_fields = ["id", "date_joined", "last_login_ip"]

    fieldsets = (
        ("Credentials",  {"fields": ("email", "password")}),
        ("Personal",     {"fields": ("first_name", "last_name")}),
        ("RBAC",         {"fields": ("role", "tenant")}),
        ("Permissions",  {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Audit",        {"fields": ("date_joined", "last_login_ip")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "role", "tenant", "password1", "password2"),
        }),
    )
