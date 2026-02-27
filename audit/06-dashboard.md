# 06 — Dashboard

The dashboard is a **session-based** web UI for police, forensic analysts, BCC admins, and judiciary. It is separate from the JWT-based mobile API.

## Auth & Access

- **Login:** Django session (username + password). Only users with role in **DASHBOARD_ROLES** (POLICE, FORENSIC_ANALYST, BCC_ADMIN, JUDICIARY) can log in; victims cannot.
- **Views:** All main views use `@login_required(login_url="/dashboard/login/")` (method_decorator on dispatch).
- **Role-based redirect:** `apps.dashboard.permissions.role_required(*allowed_roles)` redirects to `/dashboard/forbidden/` if the user’s role is not in the list. **Note:** The route `forbidden/` is not defined in `dashboard/urls.py`; the template `dashboard/forbidden.html` exists. See **08-gaps-and-recommendations.md**.

## URLs (dashboard app)

**Defined in:** `apps.dashboard.urls`  
**Mounted at:** `""` in root URLconf, so these paths are at **site root** (e.g. `/login/`, `/cases/`, `/chain/`).

| Path | Name | View |
|------|------|------|
| login/ | dashboard-login | DashboardLoginView |
| logout/ | dashboard-logout | DashboardLogoutView |
| (empty) | dashboard-home | DashboardHomeView |
| cases/ | dashboard-cases | DashboardCasesView |
| cases/<uuid:vault_id>/ | dashboard-case-detail | DashboardCaseDetailView |
| chain/ | dashboard-chain-verify | DashboardChainVerifyView |
| certificates/ | dashboard-certificates | DashboardCertificatesView |
| certificates/<uuid:vault_id>/ | dashboard-certificate | DashboardCertificateView |

**Not in urlpatterns:** `forbidden/`, `user_management/`, `system_health/` — templates exist for these but no routes (see **08-gaps**).

## Views

**File:** `src/apps/dashboard/views.py`

- **DashboardLoginView** — GET: if authenticated redirect to home, else render login; POST: authenticate, if success and role in DASHBOARD_ROLES then login and redirect home, else re-render with errors.
- **DashboardLogoutView** — GET: logout, redirect to login.
- **DashboardHomeView** — Stats (total/verified/pending/flagged evidence), full chain integrity via `verify_chain_integrity()`, recent evidence (10). Renders `dashboard/home.html`.
- **DashboardCasesView** — List evidence; optional filters `status`, `harm_type`. Renders `dashboard/cases.html`.
- **DashboardCaseDetailView** — get_object_or_404(Evidence, vault_id); `verify_single_evidence_chain(vault_id)`; renders `dashboard/case_detail.html`.
- **DashboardChainVerifyView** — `verify_chain_integrity()`; renders `dashboard/chain_verify.html`.
- **DashboardCertificatesView** — Evidence with status=verified; renders `dashboard/certificates.html`.
- **DashboardCertificateView** — Same as case detail (evidence + chain result); renders `dashboard/case_detail.html` (comment: “Part 3 will replace this with PDF generation”).

## Permissions module

**File:** `src/apps/dashboard/permissions.py`

- **Role groups:** POLICE_AND_ABOVE, FORENSIC_AND_ABOVE, BCC_ONLY, COURT_ROLES (lists of User.UserRole).
- **role_required(*allowed_roles)** — Decorator: redirect to login if not authenticated; redirect to `/dashboard/forbidden/` if role not in allowed_roles.
- **get_evidence_queryset_for_role(user, base_queryset)** — Police: currently returns all (comment: “in production filter by upazila”); Forensic/BCC: all; Judiciary: filter status=SUBMITTED. **Note:** Dashboard list views do not currently use this helper; they use unfiltered or status/harm_type filters only.

## Templates

**Base:** `templates/base.html`  
**Dashboard:** `templates/dashboard/*.html`

| Template | Purpose |
|----------|---------|
| login.html | Login form |
| home.html | Home with stats, chain status, recent evidence |
| cases.html | Evidence list with filters |
| case_detail.html | Single case + chain result |
| chain_verify.html | Full chain verification result |
| certificates.html | List of verified evidence |
| forbidden.html | Shown when role_required redirects (no URL yet) |
| user_management.html | Present; no view/URL |
| user_detail.html | Present; no view/URL |
| system_health.html | Present; no view/URL |

Crispy Forms with Tailwind are used for forms (base settings).
