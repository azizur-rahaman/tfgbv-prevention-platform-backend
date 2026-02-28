# Implementation Phases — Detailed Task Breakdown

Concrete tasks, files to create or modify, and implementation notes for each phase. Use with **01-execution-plan.md** and **04-url-and-access-matrix.md**.

---

## Phase 0: Foundation

### 0.1 Mount dashboard under `/dashboard/`

- **File:** `src/core/urls.py`
- **Change:** Replace `path("", include("apps.dashboard.urls"))` with `path("dashboard/", include("apps.dashboard.urls"))`.
- **Effect:** All dashboard URLs become `/dashboard/login/`, `/dashboard/...`. Aligns with `LOGIN_URL` and `LOGIN_REDIRECT_URL` in settings.

### 0.2 Add Forbidden view and URL

- **File:** `src/apps/dashboard/views.py`  
  Add a simple view that renders `dashboard/forbidden.html`.
- **File:** `src/apps/dashboard/urls.py`  
  Add `path("forbidden/", DashboardForbiddenView.as_view(), name="dashboard-forbidden")`.
- **Template:** `templates/dashboard/forbidden.html` (already exists).

### 0.3 Role-based home redirect

- **Current:** Single `DashboardHomeView` at `""`; all roles see same home.
- **Change:**  
  - Rename or keep `DashboardHomeView` at `""` (path `dashboard/`). In `get()`: check `request.user.role` and `redirect()` to:
    - Police → `/dashboard/police/`
    - Forensic → `/dashboard/forensic/`
    - BCC → `/dashboard/bcc/`
    - Judiciary → `/dashboard/judiciary/`
  - Create placeholder views for each role home (can render minimal template or reuse a shared “under construction” until Phase 3–6).
- **URLs:** Add `path("police/", ...)`, `path("forensic/", ...)`, `path("bcc/", ...)`, `path("judiciary/", ...)`.

### 0.4 Apply role-based evidence filtering

- **Files:** `src/apps/dashboard/views.py`
- **Views to update:** `DashboardCasesView`, `DashboardCertificatesView`, `DashboardCaseDetailView`, `DashboardCertificateView`.
- **Change:** Before using Evidence queryset:
  - Get base queryset (e.g. `Evidence.objects.all()` or `.filter(...)` for status).
  - Call `get_evidence_queryset_for_role(request.user, base_queryset)` from `apps.dashboard.permissions`.
  - Use returned queryset for list and for get_object_or_404 (e.g. ensure vault_id is in that queryset).
- **Note:** Police filtering by upazila will only work after Phase 1.1 (evidence–upazila link). Until then, `get_evidence_queryset_for_role` for Police can remain “all” or filter by a placeholder field.

---

## Phase 1: Data & Backend Prerequisites

### 1.1 Evidence–Upazila association (Police jurisdiction)

- **Option A:** Add `Evidence.assigned_upazila` (CharField, null=True). Set on upload from app (victim’s area) or when police assign; filter in `get_evidence_queryset_for_role()` for Police by `assigned_upazila=user.assigned_upazila`.
- **Option B:** Add `Evidence.reporter_upazila` (from NID lookup or app). Same filtering idea.
- **File:** `src/apps/evidence/models.py` — add field; create and run migration.
- **File:** `src/apps/dashboard/permissions.py` — in `get_evidence_queryset_for_role()` for Police, filter by upazila when field exists.

### 1.2 Verdict / disposition (Judiciary)

- **Option A:** Add to Evidence: `verdict` (CharField: admitted, rejected, under_review, null/blank), `verdict_at` (DateTimeField, null=True), `verdict_by` (FK User, null=True).
- **Option B:** New model `EvidenceVerdict` (evidence FK, verdict, recorded_at, recorded_by) for history. Judiciary view writes here; optionally append ForensicLog entry (new event type e.g. VERDICT).
- **Files:** `src/apps/evidence/models.py` (and migrations). Optional: `src/apps/blockchain/models.py` (new EventType) and service to append block.

### 1.3 Purge requests (BCC)

- **Model:** e.g. `EvidencePurgeRequest` in `evidence` or new app: evidence FK, requested_by (User), reason (TextField), status (pending, approved, denied), reviewed_by, reviewed_at.
- **Files:** New model; migrations; admin optional. BCC dashboard (Phase 5) will list and approve/deny.

### 1.4 Admin audit log (BCC)

- **Model:** e.g. `AdminAuditLog`: actor_user_id (CharField/UUID), action (CharField: user_created, user_deactivated, role_changed), target_user_id or generic target info, timestamp (auto).
- **Files:** New model (e.g. in `accounts` or `dashboard`); migrations. In BCC user create/deactivate/role-change views, create an AdminAuditLog entry.

---

## Phase 2: Shared & Role-Agnostic Views

### 2.1 Case list (inbox)

- **View:** Reuse/enhance `DashboardCasesView`. Already filtered by role (Phase 0.4). Optional: different template per role (e.g. `dashboard/police/inbox.html` vs `dashboard/cases.html`) or single template with role-based subtitle/empty states.
- **URL:** Keep `/dashboard/cases/`; ensure only allowed roles can access (decorator or dispatch check).

### 2.2 Case detail

- **View:** `DashboardCaseDetailView`. Ensure evidence is fetched via role-filtered queryset (Phase 0.4); 404 if not in set. Add context for “victim identity” (reporter’s nid_hash, nid_verified) for Police (and BCC if desired).
- **Template:** `dashboard/case_detail.html` — add block or include for victim identity (show only for Police/BCC).

### 2.3 65B certificate (view + PDF)

- **View:** `DashboardCertificateView` — keep HTML view for inline display. Add a second view or same view with `?format=pdf` / separate URL for PDF download.
- **PDF:** Use ReportLab or WeasyPrint; render certificate content (evidence id, hash, chain status, dates, etc.). Return `HttpResponse` with `content_type='application/pdf'` and `Content-Disposition: attachment`.
- **URLs:** e.g. `/dashboard/certificates/<vault_id>/` (view), `/dashboard/certificates/<vault_id>/pdf/` (download). Restrict to dashboard roles; case must be in user’s queryset.

### 2.4 Victim identity lookup

- **Implementation:** Part of case detail (2.2): pass `reporter` (evidence.reporter) to template; show `reporter.nid_hash` (masked if needed), `reporter.nid_verified`. Restrict visibility in template by role (Police, BCC) or restrict route with `role_required(POLICE, BCC_ADMIN)` if on a separate page.

---

## Phase 3: Police-Only Features

- **Views:** Create under `apps.dashboard.views` or `apps.dashboard.views.police`: PoliceHomeView, MarkForSubmissionView (POST).
- **Templates:** `templates/dashboard/police/home.html`, optionally `inbox.html` (or reuse cases with police context).
- **URLs:** `path("police/", PoliceHomeView.as_view(), name="dashboard-police-home")`, `path("police/submit/<uuid:vault_id>/", MarkForSubmissionView.as_view(), name="dashboard-mark-submitted")`.
- **Decorators:** `@method_decorator(role_required(User.UserRole.POLICE), name="dispatch")`.
- **Mark for submission:** In view, get evidence (must be in police queryset), set `status=Evidence.EvidenceStatus.SUBMITTED`, save; optionally add ForensicLog event; redirect to case detail or inbox.

---

## Phase 4: Forensic Analyst–Only Features

- **Views:** ForensicHomeView, FlaggedCasesView, ChainAuditView (block-by-block with hashes), HashReverifyView (calls service, shows report), EncryptionIntegrityView, TamperLogView, ExpertReportPdfView.
- **Services:** In `evidence` or `blockchain`: e.g. `reverify_evidence_hash(vault_id)` — download from storage, decrypt, re-hash, compare; return dict. Tamper log: query or derive from verification runs / chain integrity results (e.g. store verification failures or recompute on demand).
- **Templates:** `dashboard/forensic/home.html`, `flagged.html`, `chain_audit.html`, `reverify_report.html`, `tamper_log.html`. Expert PDF: similar to 65B but with raw hashes, block numbers, nonce.
- **URLs:** All under `forensic/`, with `role_required(User.UserRole.FORENSIC_ANALYST)` (and optionally BCC for re-verify/chain audit).

---

## Phase 5: BCC Admin–Only Features

- **Views:** BccHomeView, SystemHealthView (blocks count, evidence count, MinIO stats, last genesis), FullChainIntegrityView (reuse verify_chain_integrity), UserManagementView (list, create, deactivate, assign role), StorageVaultView (MinIO list/size; orphan detection), BlockExplorerView (paginated ForensicLog), AdminAuditLogView, PurgeRequestsView (list, approve/deny).
- **User management:** Use Django forms or DRF; on create/update write to AdminAuditLog. Only allow creating police/analyst/judiciary (not victims; they self-register).
- **Templates:** Use existing `user_management.html`, `system_health.html`; add BCC-specific home and others as needed.
- **URLs:** All under `bcc/`, `role_required(User.UserRole.BCC_ADMIN)`.

---

## Phase 6: Judiciary-Only Features

- **Views:** JudiciaryHomeView, JudiciaryCasesView (submitted only — use get_evidence_queryset_for_role), CertificateView (reuse), ChainTimelineView (same chain data, template with non-technical timeline), AuthSummaryView (one-page three checks), NidSearchView (form: NID hash input; list evidence where reporter.nid_hash = value), VerdictView (GET form, POST save verdict).
- **Templates:** `dashboard/judiciary/home.html`, `judiciary/cases.html`, timeline and auth summary fragments or pages, `verdict_form.html`.
- **URLs:** All under `judiciary/`, `role_required(User.UserRole.JUDICIARY)` for verdict and NID search.

---

## File Checklist (Summary)

| Phase | Files to create/modify |
|-------|-------------------------|
| 0 | `core/urls.py`, `dashboard/urls.py`, `dashboard/views.py` (forbidden, home redirect, apply get_evidence_queryset_for_role in case views) |
| 1 | `evidence/models.py` (upazila, optional verdict/purge/audit models or in separate app), migrations |
| 2 | `dashboard/views.py`, `dashboard/urls.py`, certificate PDF view + template or WeasyPrint/ReportLab, `case_detail.html` (victim block) |
| 3 | `dashboard/views.py` (police views), `dashboard/urls.py`, `templates/dashboard/police/*.html` |
| 4 | `dashboard/views.py` (forensic views), `evidence/services/reverify.py` or similar, `blockchain/services.py` (tamper query), `templates/dashboard/forensic/*.html` |
| 5 | `dashboard/views.py` (BCC views), user CRUD, `templates/dashboard/bcc/*.html`, optional `user_management.html` wiring |
| 6 | `dashboard/views.py` (judiciary views), `templates/dashboard/judiciary/*.html` |

Use **02-role-dashboards-spec.md** for exact feature list and **04-url-and-access-matrix.md** for URL and permission consistency.
