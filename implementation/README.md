# Role-Specific Dashboards — Implementation Plan

This folder contains the **execution and implementation plan** for building separate dashboards for:

- **Police Officers**
- **Forensic Analysts**
- **BCC Admins**
- **Judiciary / Magistrates**

Feature and dashboard requirements are taken from **`text.text`** (project root). The current codebase has a single shared dashboard; this plan refactors and extends it into role-specific homes and feature sets.

## Document Index

| Document | Purpose |
|----------|---------|
| [01-execution-plan.md](01-execution-plan.md) | High-level execution order, phases, dependencies |
| [02-role-dashboards-spec.md](02-role-dashboards-spec.md) | Per-role feature spec (from text.text) + quick decision matrix |
| [03-implementation-phases.md](03-implementation-phases.md) | Detailed phases: routing, views, URLs, templates, services |
| [04-url-and-access-matrix.md](04-url-and-access-matrix.md) | URL layout and which roles can access which routes |

## How to Use

1. **Scope** — Read `02-role-dashboards-spec.md` to see exactly what each role gets.
2. **Order** — Read `01-execution-plan.md` to see phases and what to build first.
3. **Build** — Follow `03-implementation-phases.md` for tasks, files, and code-level steps.
4. **Guard** — Use `04-url-and-access-matrix.md` when adding routes and permission decorators.

## References

- **Audit:** `audit/` folder (codebase state, models, APIs, services).
- **Requirements:** `text.text` (role features and quick decision summary).
