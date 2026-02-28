# Execution Plan — Role-Specific Dashboards

High-level order of execution. Each phase builds on the previous; finish foundation before role-specific features.

---

## Phase 0: Foundation (Do First)

**Goal:** Fix routing and access so we can safely add role-specific views.

| Task | Description |
|------|-------------|
| 0.1 | Mount dashboard under `/dashboard/` in `core/urls.py` so LOGIN_URL and redirects work. |
| 0.2 | Add `DashboardForbiddenView` and route `forbidden/` (for role_required redirect). |
| 0.3 | Implement role-based home redirect: after login, send user to role-specific landing (e.g. `/dashboard/police/`, `/dashboard/forensic/`, `/dashboard/bcc/`, `/dashboard/judiciary/`). |
| 0.4 | Use `get_evidence_queryset_for_role()` in all case/certificate list views so Police see upazila-scoped and Judiciary see only submitted. (Depends on 1.1 for police upazila.) |

**Exit condition:** Login → correct role home; forbidden works; case lists filtered by role.

---

## Phase 1: Data & Backend Prerequisites

**Goal:** Data model and services needed by multiple dashboards.

| Task | Description |
|------|-------------|
| 1.1 | **Police jurisdiction:** Add a way to associate evidence with an upazila (e.g. `Evidence.assigned_upazila` or `Evidence.reporter_upazila`). Populate from app at upload or from NID lookup; use in `get_evidence_queryset_for_role()` for Police. |
| 1.2 | **Verdict/disposition:** Add field(s) to Evidence (e.g. `verdict`, `verdict_at`, `verdict_by`) and/or a small VerdictLog model. Judiciary view writes here; optionally append a ForensicLog TRANSFER or new event type for “verdict recorded”. |
| 1.3 | **Purge requests (BCC):** Add model e.g. `EvidencePurgeRequest` (evidence FK, requested_by, reason, status, reviewed_by, reviewed_at). Victim flow can be added later; BCC dashboard lists and approves/denies. |
| 1.4 | **Admin audit log:** Add model e.g. `AdminAuditLog` (actor_user_id, action, target_user_id or target_type/id, timestamp). BCC user create/deactivate/role-change actions write here. |

**Exit condition:** Upazila on evidence (or equivalent), verdict storage, purge-request and admin-audit models exist and are migrated.

---

## Phase 2: Shared & Role-Agnostic Views

**Goal:** Views that all (or most) roles use, with permission decorators.

| Task | Description |
|------|-------------|
| 2.1 | **Case list (inbox):** Single view with role-based queryset (already in Phase 0). Optional: separate “inbox” template per role (e.g. police inbox vs judiciary submitted only). |
| 2.2 | **Case detail:** Evidence detail + chain verification. Use `get_evidence_queryset_for_role()` so only allowed evidence is visible. |
| 2.3 | **65B certificate:** Generate PDF (e.g. ReportLab or WeasyPrint). Shared “certificate view” + “certificate download” URL; Police can generate, all others can view/download. |
| 2.4 | **Victim identity lookup:** View or section on case detail: reporter’s NID hash (masked if needed), nid_verified. Police only (or Police + BCC). |

**Exit condition:** Case list, detail, certificate (view + PDF), and victim identity are wired and permissioned.

---

## Phase 3: Police-Only Features

**Goal:** Police dashboard and actions.

| Task | Description |
|------|-------------|
| 3.1 | Police home view + template: Upazila case stats, case inbox link, quick chain status. |
| 3.2 | “Mark for Court Submission” action: POST or form that sets evidence status to submitted; only Police; add ForensicLog entry if desired. |
| 3.3 | 65B certificate generation from Police dashboard (button/link to certificate view + PDF). |
| 3.4 | Ensure case inbox and stats only show evidence for police’s `assigned_upazila`. |

**Exit condition:** Police can do everything in the Police spec (inbox, detail, victim lookup, mark submitted, generate 65B).

---

## Phase 4: Forensic Analyst–Only Features

**Goal:** Analyst dashboard and tools.

| Task | Description |
|------|-------------|
| 4.1 | Forensic home view + template: Flagged cases queue, link to full chain audit. |
| 4.2 | Full chain audit view: Block-by-block list with raw hashes, recomputed hash, comparison. Analyst-only. |
| 4.3 | Hash re-verification tool: Service that re-downloads from MinIO, decrypts, re-hashes, compares; returns report. View to trigger + display report. |
| 4.4 | Encryption integrity report: Compare stored nonce/size with actual file in MinIO. Analyst (and optionally BCC). |
| 4.5 | Tamper event log: Query ForensicLog (or a derived table) for blocks where verification failed; show vault_id, timestamp. |
| 4.6 | Expert report export: PDF with hashes, block numbers, nonce (forensic-grade). |

**Exit condition:** Analysts have flagged queue, full chain audit, hash re-verify, encryption report, tamper log, expert PDF.

---

## Phase 5: BCC Admin–Only Features

**Goal:** BCC dashboard and system operations.

| Task | Description |
|------|-------------|
| 5.1 | BCC home view + template: System health (blocks, evidence count, MinIO usage, last genesis). |
| 5.2 | Full chain integrity monitor (reuse verify_chain_integrity; BCC-only view). |
| 5.3 | User management: List users, create (police/analyst/judiciary), deactivate, assign role. Write to AdminAuditLog. |
| 5.4 | Storage vault monitor: MinIO stats (total files, size); optionally list orphaned files (in bucket but no Evidence). |
| 5.5 | Blockchain block explorer: Paginated list of all ForensicLog blocks with full metadata. |
| 5.6 | Audit log of admin actions: List AdminAuditLog. |
| 5.7 | Evidence purge requests: List PurgeRequest; approve/deny; if approve, implement deletion policy (soft delete or chain note). |

**Exit condition:** BCC has health, chain monitor, user management, storage monitor, block explorer, admin audit log, purge requests.

---

## Phase 6: Judiciary-Only Features

**Goal:** Judiciary dashboard and court-facing features.

| Task | Description |
|------|-------------|
| 6.1 | Judiciary home view + template: Submitted cases only; link to certificate viewer. |
| 6.2 | Submitted cases view: Only status=submitted; use get_evidence_queryset_for_role(). |
| 6.3 | 65B certificate viewer: Inline + print/download (reuse certificate view; Judiciary read-only). |
| 6.4 | Chain of custody timeline: Clean timeline template (event names, timestamps, roles; no raw hashes). |
| 6.5 | Evidence authentication summary: One-page view with three checks (hash verified, chain intact, device identified). |
| 6.6 | Cross-reference search: Search by NID hash; list all evidence from that reporter. |
| 6.7 | Verdict/disposition marking: Form to set verdict; save to Evidence (and optionally ForensicLog). |

**Exit condition:** Judiciary sees only submitted cases, certificate, timeline, auth summary, NID search, and can record verdict.

---

## Summary Order

1. **Phase 0** — Routing, forbidden, role-based home, queryset filtering.  
2. **Phase 1** — Upazila, verdict, purge request, admin audit models.  
3. **Phase 2** — Shared case list, detail, certificate (view + PDF), victim identity.  
4. **Phase 3** — Police home + mark submitted + 65B.  
5. **Phase 4** — Forensic home + chain audit + re-verify + encryption report + tamper log + expert PDF.  
6. **Phase 5** — BCC home + user management + storage + block explorer + admin audit + purge.  
7. **Phase 6** — Judiciary home + submitted view + certificate + timeline + auth summary + NID search + verdict.

---

## Dependencies

- **Phase 2** depends on **Phase 0** and **Phase 1** (queryset, optional verdict/purge).  
- **Phases 3–6** depend on **Phase 2** for shared case/certificate and on **Phase 1** for their specific data (verdict, purge, admin audit).  
- **Phase 1.1** (upazila) is required for Police inbox and stats in Phase 3.
