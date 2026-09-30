"""
Authentication Utilities
Helper functions for tenant validation, user profile enrichment,
and role-based access control (RBAC) checks used across the platform.
"""

import logging
from typing import Optional

logger = logging.getLogger("cybershield.authentication.utils")


# ── Role Hierarchy ────────────────────────────────────────────────────────────
# Defines the privilege ordering for role-based access control.
# Higher index = higher privilege. Used for role comparison checks.
ROLE_HIERARCHY = [
    "ANALYST",          # Security Analyst — read alerts, manage incidents
    "INVESTIGATOR",     # Forensic Investigator — manage cases and evidence
    "SYS_ADMIN",        # System Administrator — manage assets, alert rules
    "ORG_MANAGER",      # Organisation Manager — view reports, compliance
    "SUPER_ADMIN",      # Full platform access
]

ROLE_DISPLAY_NAMES = {
    "ANALYST":      "Security Analyst",
    "INVESTIGATOR": "Forensic Investigator",
    "SYS_ADMIN":    "System Administrator",
    "ORG_MANAGER":  "Organisation Manager",
    "SUPER_ADMIN":  "Super Administrator",
}

# Roles allowed to view the Live Threat Dashboard
DASHBOARD_ROLES = frozenset(["ANALYST", "SYS_ADMIN", "SUPER_ADMIN"])

# Roles allowed to manage forensic cases
FORENSICS_ROLES = frozenset(["INVESTIGATOR", "SYS_ADMIN", "SUPER_ADMIN"])

# Roles allowed to generate compliance reports
COMPLIANCE_ROLES = frozenset(["ORG_MANAGER", "SYS_ADMIN", "SUPER_ADMIN"])


def has_minimum_role(user_role: str, minimum_role: str) -> bool:
    """
    Check if a user's role is at or above the required minimum privilege level.

    Args:
        user_role: The role string from the User model (e.g., 'ANALYST').
        minimum_role: The minimum required role (e.g., 'SYS_ADMIN').

    Returns:
        True if user_role >= minimum_role in the ROLE_HIERARCHY, else False.

    Example:
        has_minimum_role('SYS_ADMIN', 'ANALYST')  → True
        has_minimum_role('ANALYST', 'SYS_ADMIN')  → False
    """
    try:
        user_idx = ROLE_HIERARCHY.index(user_role)
        min_idx = ROLE_HIERARCHY.index(minimum_role)
        return user_idx >= min_idx
    except ValueError:
        logger.warning(f"Unknown role in RBAC check: user_role={user_role!r}, minimum={minimum_role!r}")
        return False


def get_role_display(role: str) -> str:
    """
    Return the human-readable display name for a role code.

    Args:
        role: Role code string (e.g., 'SYS_ADMIN').

    Returns:
        Display name string (e.g., 'System Administrator').
    """
    return ROLE_DISPLAY_NAMES.get(role, role)


def can_access_forensics(user) -> bool:
    """
    Check if a user has access to the Forensics module.

    Args:
        user: Authenticated Django User instance with a 'role' attribute.

    Returns:
        True if user's role is in FORENSICS_ROLES.
    """
    return getattr(user, "role", None) in FORENSICS_ROLES


def can_access_compliance(user) -> bool:
    """
    Check if a user can view and generate compliance reports.

    Args:
        user: Authenticated Django User instance.

    Returns:
        True if user's role is in COMPLIANCE_ROLES.
    """
    return getattr(user, "role", None) in COMPLIANCE_ROLES


def get_user_dashboard_scope(user) -> dict:
    """
    Return a dict describing which dashboard modules the user can access.

    Used by the frontend to conditionally render navigation menu items
    and route guards based on the authenticated user's role.

    Args:
        user: Authenticated Django User instance.

    Returns:
        Dict with boolean flags for each major module:
        {
            "can_view_alerts": bool,
            "can_manage_incidents": bool,
            "can_manage_forensics": bool,
            "can_view_compliance": bool,
            "can_manage_users": bool,
            "role_display": str,
        }
    """
    role = getattr(user, "role", "")
    return {
        "can_view_alerts":       role in DASHBOARD_ROLES,
        "can_manage_incidents":  has_minimum_role(role, "ANALYST"),
        "can_manage_forensics":  can_access_forensics(user),
        "can_view_compliance":   can_access_compliance(user),
        "can_manage_users":      has_minimum_role(role, "SYS_ADMIN"),
        "role_display":          get_role_display(role),
    }
