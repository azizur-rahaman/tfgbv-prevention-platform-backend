# 08 — Gaps and Recommendations

## Gaps (current state)

### 1. Dashboard URL prefix vs LOGIN_URL

- **core/urls.py** mounts dashboard with `path("", include("apps.dashboard.urls"))`, so dashboard routes are at **root**: `/login/`, `/`, `/cases/`, etc.
- **Settings** use `LOGIN_URL = "/dashboard/login/"`, `LOGIN_REDIRECT_URL = "/dashboard/"`, `LOGOUT_REDIRECT_URL = "/dashboard/login/"`.
- **Effect:** Redirects to `/dashboard/login/` or `/dashboard/` will 404 unless you add a prefix.  
**Recommendation:** Either (a) add `path("dashboard/", include("apps.dashboard.urls"))` and keep dashboard paths relative (login/, cases/, ...) so they become `/dashboard/login/`, etc., or (b) change LOGIN_URL and related settings to `/login/`, `/`, `/login/` to match current URLconf.

### 2. Missing route: `/dashboard/forbidden/`

- **permissions.role_required** redirects to `/dashboard/forbidden/`.
- Template **dashboard/forbidden.html** exists.
- **dashboard/urls.py** does not define a view or path for `forbidden/`.  
**Recommendation:** Add a view that renders `dashboard/forbidden.html` and register it at `forbidden/` (and if dashboard is under prefix `dashboard/`, the full path will be `/dashboard/forbidden/`).

### 3. Templates without views/URLs

- **user_management.html**, **user_detail.html**, **system_health.html** exist but have no corresponding views or URL patterns.  
**Recommendation:** Either add views/URLs when implementing those features or remove/rename templates to avoid confusion.

### 4. No dependency list in repo

- No **requirements.txt**, **pyproject.toml**, or **Pipfile**.  
**Recommendation:** Add at least **requirements.txt** (or pyproject.toml) with pinned versions. Inferred packages: django, djangorestframework, djangorestframework-simplejwt, django-storages, django-crispy-forms, crispy-tailwind, cryptography, django-environ.

### 5. Evidence list and role-based filtering

- **get_evidence_queryset_for_role()** in dashboard permissions exists but is **not used** by DashboardCasesView or other list views. Police/judiciary scoping (e.g. by upazila or submitted status) is not applied.  
**Recommendation:** Use this helper (or equivalent) in dashboard evidence list and detail access so police see only their scope and judiciary only submitted cases.

### 6. Certificate view and PDF

- **DashboardCertificateView** currently renders the same case_detail template; comment in code says “Part 3 will replace this with PDF generation”.  
**Recommendation:** When implementing certificates, add a PDF generation path (e.g. ReportLab or WeasyPrint) and optionally a separate template or response type for download.

### 7. Blockchain evidence endpoint access

- **GET api/v1/blockchain/evidence/<vault_id>/** allows any authenticated user to query chain for any vault_id. No check that the user is the reporter or has a police/forensic/admin/judiciary role.  
**Recommendation:** Restrict to reporter (owner) or allowed roles (e.g. POLICE, FORENSIC_ANALYST, BCC_ADMIN, JUDICIARY) if that matches product requirements.

---

## Extension hints

- **New API version:** Add another include under e.g. `api/v2/` and keep v1 as-is for backward compatibility.
- **New evidence event types:** Add a new `ForensicLog.EventType` and create blocks from the appropriate service (e.g. when evidence is verified or submitted to court).
- **NID verification:** Integrate real NIDW Partner API and set `nid_verified` on success; keep NID hashing server-side only.
- **Upazila filtering:** Use `User.assigned_upazila` and evidence location (or a new geo field) in `get_evidence_queryset_for_role()` and dashboard/API.
- **Tests:** apps have tests.py; expand with tests for ingest_evidence, chain verification, and API permissions.
- **Audit trail:** ForensicLog already provides an audit trail; for dashboard actions consider adding ACCESS or similar events when police/analysts view sensitive data.
