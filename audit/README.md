# TFGBV Prevention Platform Backend — Codebase Audit

This folder contains a **complete audit** of the backend codebase. The audit is intended for:

- **Understanding** the current state of the code and architecture
- **Onboarding** new developers or AI assistants
- **Extending** the platform (new features, APIs, or integrations)

## Audit Date

**Generated:** February 2026

## Document Index

| Document | Purpose |
|----------|---------|
| [01-overview.md](01-overview.md) | Project purpose, tech stack, high-level summary |
| [02-architecture.md](02-architecture.md) | Directory structure, apps, data flow, URL layout |
| [03-models.md](03-models.md) | All Django models, fields, relationships, indexes |
| [04-apis.md](04-apis.md) | REST API endpoints, auth, request/response shapes |
| [05-services.md](05-services.md) | Business logic: evidence ingest, encryption, blockchain |
| [06-dashboard.md](06-dashboard.md) | Web dashboard (session auth), views, templates, permissions |
| [07-config-and-deployment.md](07-config-and-deployment.md) | Settings, environment variables, deployment notes |
| [08-gaps-and-recommendations.md](08-gaps-and-recommendations.md) | Missing routes, dependency list, extension hints |

## How to Use This Audit

1. **New to the project?** Start with `01-overview.md` and `02-architecture.md`.
2. **Adding an API or changing data?** Use `03-models.md` and `04-apis.md`.
3. **Changing evidence flow or crypto?** Use `05-services.md`.
4. **Changing the police/analyst UI?** Use `06-dashboard.md`.
5. **Deploying or configuring?** Use `07-config-and-deployment.md`.
6. **Planning next steps?** Use `08-gaps-and-recommendations.md`.

All paths in this audit are relative to the repository root unless stated otherwise. The application code lives under `src/`.
