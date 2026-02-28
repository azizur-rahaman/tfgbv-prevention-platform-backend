# Role Dashboards — Feature Spec (from text.text)

This document is the **authoritative feature list** per role, derived from `text.text`. Use it to decide what each dashboard shows and what each role can do.

---

## Police Officer Dashboard

**Primary job:** First responder to digital evidence. Receives cases, verifies integrity, forwards to court.

| Feature | Description |
|--------|-------------|
| **Case Inbox** | Newly submitted evidence **assigned to their upazila**. Triage view filtered by jurisdiction, not global list. |
| **Evidence Detail + Chain Verification** | Per-case GREEN/RED integrity status. Confirm evidence not tampered before acting. |
| **Victim Identity Lookup** | View reporter’s NID hash and verification status. Confirm complainant is real, verified person. |
| **Mark for Court Submission** | Status change: evidence "verified" → "submitted". Police gatekeep what reaches judiciary. |
| **Generate 65B Certificate** | Legally required under Bangladesh Evidence Act 2022. Primary legal output. |
| **Upazila Case Stats** | Counts: pending, verified, flagged in their zone. Operational awareness. |

---

## Forensic Analyst Dashboard

**Primary job:** Deep technical examination. Called when integrity is questionable or case contested.

| Feature | Description |
|--------|-------------|
| **Full Chain Audit View** | Block-by-block cryptographic breakdown of every ForensicLog entry. Raw hash comparisons, more technical than police view. |
| **Flagged Cases Queue** | Dedicated view of all evidence with status=flagged. Core queue for analysts. |
| **Hash Re-verification Tool** | Server-side: re-download from MinIO, decrypt, re-hash, compare to stored file_hash. Formal verification report. |
| **Encryption Integrity Report** | Confirm AES-256-GCM nonce and stored size match upload record. Detects storage-layer tampering. |
| **Tamper Event Log** | Filtered view of blockchain blocks where hash mismatches detected system-wide; timestamps and affected vault IDs. |
| **Expert Report Export** | PDF for forensic testimony: raw hashes, block numbers, nonce metadata (more technical than 65B certificate). |

---

## BCC Admin Dashboard

**Primary job:** System operator. Platform health, audits, user management.

| Feature | Description |
|--------|-------------|
| **System Health Overview** | Total blocks, total evidence, MinIO storage usage, last genesis block timestamp. |
| **Full Chain Integrity Monitor** | Global GREEN/RED status for entire system. Highest-level view. |
| **User Management** | Create, deactivate, assign roles for police, analysts, judiciary. Victims self-register; BCC provisions others. |
| **Storage Vault Monitor** | MinIO bucket: total files, total encrypted size, orphaned files (in MinIO but no Evidence record). |
| **Blockchain Block Explorer** | Browse every ForensicLog block with full metadata. System audits and legal compliance. |
| **Audit Log of Admin Actions** | Who created which users, when. Accountability for court challenges. |
| **Evidence Purge Requests** | Victim requests deletion; BCC reviews and approves/denies (touches chain of custody). |

---

## Judiciary / Magistrate Dashboard

**Primary job:** Consume and evaluate evidence for court. Mostly read-only.

| Feature | Description |
|--------|-------------|
| **Submitted Cases View** | Only evidence with status=submitted. No pending or flagged. |
| **65B Certificate Viewer** | Render certificate inline; print/download. Primary document. |
| **Chain of Custody Timeline** | Clean, non-technical timeline of blockchain events: event names, timestamps, actor roles; no raw hashes. |
| **Evidence Authentication Summary** | One-page: hash verified? chain intact? device identified? Green/red per criterion. |
| **Cross-Reference Search** | Search by NID hash: all evidence from same reporter across cases (trafficking/abuse patterns). |
| **Verdict/Disposition Marking** | Record outcome (admitted, rejected, under review). Writes final ForensicLog entry. |

---

## Quick Decision Summary (from text.text)

| Feature | Police | Analyst | BCC | Judiciary |
|---------|--------|---------|-----|-----------|
| Case inbox | Yes | Yes | Yes | Yes (submitted only) |
| Chain integrity | Basic | Deep | Global | Read |
| 65B certificate | Generate | View | View | View |
| User management | No | No | Yes | No |
| Hash re-verify tool | No | Yes | Yes | No |
| Mark for submission | Yes | No | No | No |
| Verdict marking | No | No | No | Yes |
| Storage monitor | No | No | Yes | No |

Use this matrix when implementing URL permissions and role_required decorators.
