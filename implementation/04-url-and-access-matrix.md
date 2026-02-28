# URL and Access Matrix

Use this when adding routes and `role_required` decorators. Base path: **`/dashboard/`** (after Phase 0).

---

## URL Layout (Target)

| Path | Name | Roles | Purpose |
|------|------|--------|---------|
| `/dashboard/login/` | dashboard-login | — | Login (any dashboard role) |
| `/dashboard/logout/` | dashboard-logout | All | Logout |
| `/dashboard/forbidden/` | dashboard-forbidden | — | Permission denied (role_required redirect) |
| `/dashboard/` | dashboard-home | All | Redirect to role-specific home |
| **Police** | | | |
| `/dashboard/police/` | dashboard-police-home | Police | Police home (inbox, stats) |
| `/dashboard/police/inbox/` | dashboard-police-inbox | Police | Case inbox (upazila-filtered) |
| `/dashboard/police/submit/<vault_id>/` | dashboard-mark-submitted | Police | Mark for court submission (POST) |
| **Forensic** | | | |
| `/dashboard/forensic/` | dashboard-forensic-home | Forensic | Analyst home (flagged queue) |
| `/dashboard/forensic/flagged/` | dashboard-forensic-flagged | Forensic | Flagged cases list |
| `/dashboard/forensic/chain-audit/` | dashboard-chain-audit | Forensic | Full chain block-by-block |
| `/dashboard/forensic/reverify/<vault_id>/` | dashboard-hash-reverify | Forensic | Hash re-verification tool |
| `/dashboard/forensic/tamper-log/` | dashboard-tamper-log | Forensic | Tamper event log |
| **BCC** | | | |
| `/dashboard/bcc/` | dashboard-bcc-home | BCC | BCC home (system health) |
| `/dashboard/bcc/health/` | dashboard-bcc-health | BCC | System health overview |
| `/dashboard/bcc/chain/` | dashboard-bcc-chain | BCC | Full chain integrity |
| `/dashboard/bcc/users/` | dashboard-bcc-users | BCC | User management |
| `/dashboard/bcc/storage/` | dashboard-bcc-storage | BCC | Storage vault monitor |
| `/dashboard/bcc/blocks/` | dashboard-bcc-blocks | BCC | Block explorer |
| `/dashboard/bcc/audit/` | dashboard-bcc-audit | BCC | Admin action audit log |
| `/dashboard/bcc/purge-requests/` | dashboard-bcc-purge | BCC | Evidence purge requests |
| **Judiciary** | | | |
| `/dashboard/judiciary/` | dashboard-judiciary-home | Judiciary | Judiciary home |
| `/dashboard/judiciary/cases/` | dashboard-judiciary-cases | Judiciary | Submitted cases only |
| `/dashboard/judiciary/verdict/<vault_id>/` | dashboard-verdict | Judiciary | Verdict/disposition form |
| `/dashboard/judiciary/search/` | dashboard-nid-search | Judiciary | Cross-reference by NID hash |
| **Shared (role-filtered)** | | | |
| `/dashboard/cases/` | dashboard-cases | Police, Forensic, BCC | Case list (filtered by role) |
| `/dashboard/cases/<vault_id>/` | dashboard-case-detail | All | Case detail (queryset check) |
| `/dashboard/certificates/` | dashboard-certificates | All | Certificate list (filtered) |
| `/dashboard/certificates/<vault_id>/` | dashboard-certificate | All | 65B certificate view |
| `/dashboard/certificates/<vault_id>/pdf/` | dashboard-certificate-pdf | All | PDF download |

---

## Access Rules (Quick Reference)

- **Case list:** Police (upazila), Forensic (all), BCC (all), Judiciary (submitted only). Use `get_evidence_queryset_for_role()`.
- **Case detail:** Only if evidence is in the user’s allowed queryset (same filter).
- **Mark for submission:** Police only; `role_required(User.UserRole.POLICE)`.
- **Hash re-verify / Chain audit / Tamper log / Expert PDF:** Forensic (and optionally BCC for re-verify). `role_required(User.UserRole.FORENSIC_ANALYST)` or include BCC.
- **User management, storage, block explorer, admin audit, purge:** BCC only. `role_required(User.UserRole.BCC_ADMIN)`.
- **Verdict marking:** Judiciary only. `role_required(User.UserRole.JUDICIARY)`.
- **65B certificate generate:** Police; **view/download:** All dashboard roles (subject to case access).

---

## Implementation Notes

- After login, redirect to `/dashboard/`; view checks `request.user.role` and redirects to `/dashboard/police/`, `/dashboard/forensic/`, `/dashboard/bcc/`, or `/dashboard/judiciary/`.
- Use `@method_decorator(role_required(...), name="dispatch")` on class-based views for role-specific routes.
- For shared routes (e.g. case detail), use `get_evidence_queryset_for_role()` and filter by `vault_id`; return 404 if evidence not in queryset.
