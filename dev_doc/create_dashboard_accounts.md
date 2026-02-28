# How to Create Police, Forensic, and Judiciary Accounts

Dashboard users (Police, Forensic Analyst, Judiciary, and BCC Admin) do **not** register through the mobile app. They are created by an administrator—either in **Django Admin** or via **Django shell**. Victims register via the API (`POST /api/v1/auth/register/`).

---

## Option 1: Django Admin (recommended)

### 1. Log in to Admin

1. Start the server:  
   `python manage.py runserver --settings=core.settings.local`  
   (from the `src/` directory.)
2. Open: **http://127.0.0.1:8000/admin/**
3. Log in with a **superuser** account.  
   (Create one if needed: `python manage.py createsuperuser --settings=core.settings.local`.)

### 2. Add a new user

1. Go to **Nirvhoy Users** (under **ACCOUNTS**).
2. Click **Add Nirvhoy User**.

### 3. Required and role-specific fields

| Field | Required | Notes |
|-------|----------|--------|
| **Username** | Yes | Unique; used to log in to the dashboard. |
| **Password** | Yes | Enter twice on the “Add” form. Stored hashed. |
| **Role** | Yes | Choose: **Police Officer**, **Forensic Analyst**, **BCC / System Admin**, or **Judiciary / Magistrate**. |
| **Phone number** | No | Optional (e.g. +880XXXXXXXXXX). |
| **NID hash** | No | Leave blank for staff. Only victims have NID hashed. |
| **NID verified** | No | Leave unchecked for staff. |
| **Police badge ID** | Police only | Optional; official badge/ID (e.g. `BADGE-001`). |
| **Assigned upazila** | Police only | Optional; upazila name (e.g. `Dhaka`, `Chittagong`). Police see only evidence for this upazila when set. |

**Email** can be left blank unless you use it elsewhere.

### 4. Example values by role

**Police Officer**

- Username: `police_officer` (or e.g. `officer_rahman`)
- Password: (your choice, e.g. `police123`)
- Role: **Police Officer**
- Police badge ID: `BADGE-001` (optional)
- Assigned upazila: `Dhaka` (optional; leave blank to see all evidence)

**Forensic Analyst**

- Username: `forensic_analyst` (or e.g. `analyst_sara`)
- Password: (your choice, e.g. `forensic123`)
- Role: **Forensic Analyst**
- No need to set police badge or upazila.

**Judiciary / Magistrate**

- Username: `magistrate_khan` (or e.g. `judge_ahmed`)
- Password: (your choice, e.g. `judiciary123`)
- Role: **Judiciary / Magistrate**
- No need to set police badge or upazila.

**BCC Admin**

- Username: `bcc_admin`
- Password: (your choice, e.g. `bccadmin123`)
- Role: **BCC / System Admin**

### 5. Save

Click **Save**. The user can log in at **http://127.0.0.1:8000/dashboard/login/** with the username and password you set.

---

## Option 2: Django shell

Use this to create users from the command line (e.g. for testing or scripts).

From the `src/` directory:

```bash
python manage.py shell --settings=core.settings.local
```

Then run (adjust usernames/passwords as needed):

```python
from apps.accounts.models import User

# Police Officer (optional: badge and upazila)
User.objects.create_user(
    username="police_officer",
    password="police123",
    role=User.UserRole.POLICE,
    police_badge_id="BADGE-001",
    assigned_upazila="Dhaka",
)

# Forensic Analyst
User.objects.create_user(
    username="forensic_analyst",
    password="forensic123",
    role=User.UserRole.FORENSIC_ANALYST,
)

# Judiciary / Magistrate
User.objects.create_user(
    username="magistrate_khan",
    password="judiciary123",
    role=User.UserRole.JUDICIARY,
)

# BCC Admin (optional)
User.objects.create_user(
    username="bcc_admin",
    password="bccadmin123",
    role=User.UserRole.BCC_ADMIN,
)

print("Dashboard accounts created.")
```

Exit the shell: `exit()`.

**Notes:**

- Passwords are hashed by `create_user`.
- For police, omit `police_badge_id` and `assigned_upazila` if not needed.
- `nid_hash` and `nid_verified` are for victims; leave them unset for staff.

---

## After creating accounts

| Role | Dashboard URL | What they can do |
|------|----------------|------------------|
| Police | http://127.0.0.1:8000/dashboard/login/ | Police home, case inbox (by upazila if set), chain verify, 65B certificates, mark for court submission, victim identity on case detail. |
| Forensic Analyst | Same | Forensic home, flagged cases, full chain audit, hash re-verify, encryption integrity, tamper log, expert report PDF. |
| Judiciary | Same | Judiciary home, submitted cases only, 65B certificate viewer, chain timeline, verdict marking (when implemented). |
| BCC Admin | Same | BCC home; Phase 5 adds user management, system health, storage, block explorer, audit log, purge requests. |

All of these roles log in at the same URL; after login they are redirected to their role-specific dashboard (e.g. `/dashboard/police/`, `/dashboard/forensic/`, `/dashboard/judiciary/`, `/dashboard/bcc/`).

---

## Quick reference: role values

When using the shell or API, use these exact role values:

| Role | Value (code) |
|------|------------------|
| Victim | `victim` |
| Police Officer | `police` |
| Forensic Analyst | `forensic_analyst` |
| BCC / System Admin | `bcc_admin` |
| Judiciary / Magistrate | `judiciary` |

Victims are created via **POST /api/v1/auth/register/** (mobile app); do not create them as “dashboard” users unless you need a test victim that can also use the dashboard (not the normal flow).
