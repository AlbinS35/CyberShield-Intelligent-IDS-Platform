# CyberShield Architecture & Recent Fixes Notes

This document contains important context about the platform's architecture and recent bug fixes, intended for future developers or AI agents working on the repository.

## 1. Authentication Architecture Split

The platform uses two disjoint authentication/user domains that have been recently bridged:

*   **New Architecture (`authentication` app):**
    *   Uses `authentication.User` for authentication.
    *   Multi-tenant via `authentication.Tenant`.
    *   Registration endpoint (`UserRegistrationView`) creates a `User` and `Tenant`.
*   **Legacy Architecture (`core` app):**
    *   Uses `core.CoreUser` (identity) and `core.Login` (credentials).
    *   Uses `core.Organization` (tenant isolation).
    *   The frontend (e.g., PlaybookManager, AssetRegistry) heavily relies on the `core` endpoints (`/api/core/logins/`, `/api/core/users/`, `/api/core/organizations/`, `/api/assets/`).

### How they are bridged
Because the legacy endpoints were returning seed data from `tbl_login` and `tbl_user` (e.g., "CyberShield Demo Bank"), the UI was showing incorrect data for newly registered users (like the "Ey" organization).

We implemented the following bridges:
1.  **Organization Auto-Syncing:** In `backend/authentication/serializers.py`, when a new `Tenant` is created during signup, a legacy `core.Organization` is automatically created with the exact same name. 
2.  **Organization List Endpoint:** In `backend/core/views.py` (`OrganizationListView`), the `get_queryset` method dynamically intercepts the request and will auto-create the legacy `Organization` if it was somehow missed, and filters the dropdown strictly by the active `request.user.tenant.name`.
3.  **Asset Filtering:** `AssetListCreateView` enforces isolation by filtering `NetworkAsset.objects` by `org__org_name=request.user.tenant.name`.
4.  **User Management Dropdown & Tables:** 
    *   `CoreUserListView` (`/api/core/users/`) now queries `authentication.User` instead of `core.CoreUser` and uses a custom `AuthUserCoreUserSerializer` to map the fields for the frontend dropdown.
    *   `LoginListView` (`/api/core/logins/`) does the exact same for the main user table using `AuthUserLoginSerializer`.
    *   **POST to `/api/core/logins/`:** The "Add User Credentials" modal previously tried to create a disconnected legacy `Login`. It now updates the existing `authentication.User` profile with the entered role, email, and password.

## 2. React Frontend Bug Fixes

*   **Evidence Vault File Upload (`frontend/src/pages/Investigator/EvidenceVault.jsx`):** 
    *   Fixed a React bug where the `<input type="file" />` wasn't allowing the user to select the same file twice. A `useRef` was added to forcefully reset `fileRef.current.value = ''` upon both successful and failed upload attempts.

## 3. Temporary Security Bypasses

*   **Clearance Code:** 
    *   In `backend/authentication/serializers.py`, the `admin_clearance` check for privileged roles (`SYS_ADMIN`, `ORG_MANAGER`) is currently commented out for demo/testing purposes. *This should be reverted before production deployment.*
