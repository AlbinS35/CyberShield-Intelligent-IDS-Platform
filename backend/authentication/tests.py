"""
Test Suite 1 — Authentication Module
Tests: User model creation, tenant scoping, RBAC roles, JWT login API,
       registration, profile retrieval, and permission enforcement.

Week 11-12 Scrum Register Requirement:
  "Software testing with Automation Tools & Testing Report"
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from authentication.models import Tenant, User


# ─── Fixtures / Helpers ───────────────────────────────────────────────────────

def make_tenant(name="Test Org", slug="test-org"):
    """Helper: create a Tenant for use in tests."""
    return Tenant.objects.create(name=name, slug=slug, contact_email="admin@test.org")


def make_user(tenant, email="analyst@test.org", role=User.Role.ANALYST, password="SecurePass123!"):
    """Helper: create a User attached to a Tenant."""
    return User.objects.create_user(
        email=email,
        password=password,
        first_name="Test",
        last_name="Analyst",
        role=role,
        tenant=tenant,
    )


# ─── Test Classes ─────────────────────────────────────────────────────────────

class TenantModelTest(TestCase):
    """Unit tests for the Tenant model."""

    def setUp(self):
        self.tenant = make_tenant()

    def test_tenant_creation(self):
        """Tenant should be created with correct fields."""
        self.assertEqual(self.tenant.name, "Test Org")
        self.assertEqual(self.tenant.slug, "test-org")
        self.assertTrue(self.tenant.is_active)

    def test_tenant_str_representation(self):
        """Tenant __str__ should return the tenant name."""
        self.assertEqual(str(self.tenant), "Test Org")

    def test_tenant_has_uuid_primary_key(self):
        """Tenant primary key should be a UUID (not an integer)."""
        self.assertIsNotNone(self.tenant.pk)
        self.assertEqual(len(str(self.tenant.pk)), 36)  # UUID format


class UserModelTest(TestCase):
    """Unit tests for the custom User model and RBAC role properties."""

    def setUp(self):
        self.tenant = make_tenant()
        self.analyst = make_user(self.tenant, email="analyst@test.org", role=User.Role.ANALYST)
        self.admin = make_user(self.tenant, email="admin@test.org", role=User.Role.SYS_ADMIN)
        self.investigator = make_user(self.tenant, email="inv@test.org", role=User.Role.INVESTIGATOR)

    def test_analyst_role_property(self):
        """Analyst user's is_analyst property must return True."""
        self.assertTrue(self.analyst.is_analyst)
        self.assertFalse(self.analyst.is_sys_admin)

    def test_sys_admin_role_property(self):
        """SysAdmin user's is_sys_admin property must return True."""
        self.assertTrue(self.admin.is_sys_admin)
        self.assertFalse(self.admin.is_analyst)

    def test_investigator_role_property(self):
        """Investigator role property must be correct."""
        self.assertTrue(self.investigator.is_investigator)

    def test_user_full_name(self):
        """get_full_name() should return 'First Last' string."""
        self.assertEqual(self.analyst.get_full_name(), "Test Analyst")

    def test_user_str_representation(self):
        """User __str__ includes role and tenant."""
        self.assertIn("ANALYST", str(self.analyst))
        self.assertIn("Test Org", str(self.analyst))

    def test_user_uuid_primary_key(self):
        """User primary key should be a UUID."""
        self.assertEqual(len(str(self.analyst.pk)), 36)

    def test_user_email_is_username_field(self):
        """Email should be the USERNAME_FIELD."""
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_tenant_scoping(self):
        """Users created under same tenant should share the same tenant FK."""
        self.assertEqual(self.analyst.tenant, self.admin.tenant)
        self.assertEqual(self.analyst.tenant.name, "Test Org")

    def test_password_is_hashed(self):
        """Raw password must NOT be stored — Django should hash it."""
        self.assertNotEqual(self.analyst.password, "SecurePass123!")
        self.assertTrue(self.analyst.password.startswith("pbkdf2_"))


class JWTLoginAPITest(TestCase):
    """
    Integration tests for the JWT login endpoint.
    POST /api/auth/login/
    """

    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant()
        self.user = make_user(self.tenant, email="login_test@test.org", password="SecurePass123!")
        self.login_url = "/api/auth/login/"

    def test_valid_login_returns_tokens(self):
        """Valid credentials should return 200 with access and refresh tokens."""
        response = self.client.post(self.login_url, {
            "email": "login_test@test.org",
            "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_valid_login_returns_user_profile(self):
        """Login response should include embedded user profile object."""
        response = self.client.post(self.login_url, {
            "email": "login_test@test.org",
            "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "login_test@test.org")
        self.assertEqual(response.data["user"]["role"], User.Role.ANALYST)

    def test_invalid_password_returns_401(self):
        """Wrong password should return 401 Unauthorized."""
        response = self.client.post(self.login_url, {
            "email": "login_test@test.org",
            "password": "WrongPassword!",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user_returns_401(self):
        """Login attempt with unknown email should return 401."""
        response = self.client.post(self.login_url, {
            "email": "ghost@test.org",
            "password": "anything",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_credentials_returns_400(self):
        """Empty request body should return 400 Bad Request."""
        response = self.client.post(self.login_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITest(TestCase):
    """
    Integration tests for the user profile endpoint.
    GET /api/auth/me/
    """

    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant()
        self.user = make_user(self.tenant, email="profile_test@test.org")
        self.client.force_authenticate(user=self.user)
        self.profile_url = "/api/auth/me/"

    def test_authenticated_user_can_retrieve_profile(self):
        """Authenticated user should get 200 with their own profile."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile_test@test.org")

    def test_unauthenticated_request_returns_401(self):
        """Unauthenticated request to /me/ should return 401."""
        unauthenticated_client = APIClient()
        response = unauthenticated_client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_contains_role(self):
        """Profile response must include the user's RBAC role."""
        response = self.client.get(self.profile_url)
        self.assertIn("role", response.data)
        self.assertEqual(response.data["role"], "ANALYST")


class RBACPermissionTest(TestCase):
    """
    Tests for Role-Based Access Control enforcement on API endpoints.
    Verifies that lower-privilege roles cannot access restricted endpoints.
    """

    def setUp(self):
        self.client = APIClient()
        self.tenant = make_tenant()
        self.analyst = make_user(self.tenant, email="a@test.org", role=User.Role.ANALYST)
        self.sys_admin = make_user(self.tenant, email="sa@test.org", role=User.Role.SYS_ADMIN)

    def test_analyst_cannot_list_all_tenants(self):
        """Analyst should NOT be able to access the tenant list (SysAdmin only)."""
        self.client.force_authenticate(user=self.analyst)
        response = self.client.get("/api/auth/tenants/")
        # Should be 403 Forbidden (has auth but lacks permission)
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])

    def test_unauthenticated_cannot_access_any_api(self):
        """No token = no access to any protected endpoint."""
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
