"""
CyberShield Authentication Models
Defines multi-tenant organization (Tenant) and RBAC-enabled User model.

Roles:
    ANALYST           → Security Analyst Workspace
    INVESTIGATOR      → Digital Forensic Investigator Workspace
    SYS_ADMIN         → System Administrator Workspace
    ORG_MANAGER       → Organization Management Workspace
    SUPER_ADMIN       → Platform-level superuser
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class Tenant(models.Model):
    """
    Represents an organization/department in the multi-tenant platform.
    All security data is scoped to a tenant for isolation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Contact & metadata
    contact_email = models.EmailField(blank=True)
    industry = models.CharField(max_length=100, blank=True, help_text="e.g. Banking, Healthcare")

    # Wazuh integration credentials per tenant
    wazuh_manager_url = models.CharField(max_length=255, blank=True)
    wazuh_api_user = models.CharField(max_length=100, blank=True)
    wazuh_api_password = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cs_tenants"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Custom manager for the CyberShield User model."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    CyberShield custom User model.
    Scoped to a Tenant, with a specific RBAC role governing dashboard access.
    """

    class Role(models.TextChoices):
        ANALYST = "ANALYST", "Security Analyst"
        INVESTIGATOR = "INVESTIGATOR", "Digital Forensic Investigator"
        SYS_ADMIN = "SYS_ADMIN", "System Administrator"
        ORG_MANAGER = "ORG_MANAGER", "Organization Manager"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Administrator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )

    # Staff flags
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Audit timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "cs_users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.get_full_name()} ({self.role}) — {self.tenant}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_analyst(self):
        return self.role == self.Role.ANALYST

    @property
    def is_investigator(self):
        return self.role == self.Role.INVESTIGATOR

    @property
    def is_sys_admin(self):
        return self.role == self.Role.SYS_ADMIN

    @property
    def is_org_manager(self):
        return self.role == self.Role.ORG_MANAGER
