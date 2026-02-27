# 01 — Overview

## Project Purpose

**TFGBV Prevention Platform (Nirvhoy)** is a backend for a technology-based gender-based violence (TFGBV) prevention system. It supports:

1. **Victims** — Register (via NID hash), log in, and upload digital evidence (photos, videos, audio, etc.) from a mobile app.
2. **Police / Forensic Analysts / BCC Admins / Judiciary** — Use a web dashboard to view cases, verify evidence integrity, and check the forensic (blockchain) chain of custody.
3. **Legal compliance** — Evidence handling is designed around **Section 65B** of the Bangladesh Evidence Act 2022 (admissibility of electronic evidence, chain of custody).

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Django 4.x+ |
| API | Django REST Framework (DRF) |
| Auth (API) | JWT (django-rest-framework-simplejwt) |
| Auth (Dashboard) | Session-based (Django auth) |
| Database | SQLite (default; configurable via `DATABASE_URL`) |
| File storage | django-storages + S3 (MinIO in local/dev) |
| Crypto | cryptography (AES-256-GCM), hashlib (SHA-256) |
| Frontend (dashboard) | Server-rendered HTML + Crispy Forms (Tailwind) |

## High-Level Flows

1. **Mobile app (Flutter)** → JWT login/register → upload evidence (multipart) → backend hashes, encrypts, stores in MinIO, creates `Evidence` and `ForensicLog` blocks.
2. **Dashboard** → Session login (police/analyst/admin/judiciary) → view cases, chain verify (full or per evidence), certificates.
3. **Blockchain** — Internal “blockchain” = tamper-evident hash chain (not a public crypto blockchain). Each block links to the previous; any modification breaks the chain and verification shows RED.

## Key Concepts

- **NID:** Bangladesh National ID. Only a **SHA-256 hash** of the NID is stored; raw NID is never persisted.
- **Vault ID:** UUID primary key of an `Evidence` record; used as the stable reference in storage and APIs.
- **Forensic log:** `ForensicLog` model — linked list of blocks (previous_hash, block_hash, block_number) sealing events (capture, vault_ingest, access, verification, transfer, genesis).

## Repository Layout (Outside `src`)

- `audit/` — This audit (outside `src`).
- `dev_doc/` — Developer notes (setup, API tests, evidence architecture, kill showcase).
- `mcps/` — MCP tool descriptors (e.g. cursor-ide-browser).

All application code lives under **`src/`**.
