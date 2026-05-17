# BIU Smart Hostel Key Management Portal — Backend API

Backend-only MVP for Benson Idahosa University students to digitally drop and collect **shared hostel room keys** using static QR codes. The frontend sends only `qr_code_id` on scan; the backend derives student, room, hostel, action, and timestamp.

**Stack:** Python, Django 5, Django REST Framework, JWT (SimpleJWT), Django email, SQLite (dev) / PostgreSQL-ready.

---

## Quick start

### 1. Install dependencies

```bash
cd "c:\Users\USER\Documents\dev\biu portal"
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
```

### 2. Create `.env`

Copy the example file and edit as needed:

```bash
copy .env.example .env
```

### 3. Required `.env` keys

| Key | Description | Example |
|-----|-------------|---------|
| `SECRET_KEY` | Django secret key | `your-long-random-secret` |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL (optional; omit for SQLite) | `postgres://user:pass@localhost:5432/biu_portal` |
| `EMAIL_BACKEND` | Django email backend | `django.core.mail.backends.console.EmailBackend` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | |
| `EMAIL_HOST_PASSWORD` | SMTP password | |
| `EMAIL_USE_TLS` | Use TLS | `True` |
| `DEFAULT_FROM_EMAIL` | From address | `BIU Hostel Keys <noreply@biu.edu.ng>` |

For local development, use the console email backend so OTP and notifications print in the terminal:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Seed MVP QR codes

```bash
python manage.py seed_mvp_data
```

This creates 10 QR code records (DROP + COLLECT per known hostel name). QR IDs are printed in the terminal. It does **not** expose hostels to the frontend — the dropdown is hard-coded in the client app.

### 6. Create a superuser (Django admin / staff QR endpoint)

```bash
python manage.py createsuperuser
```

You will be prompted for **email**, **matric number**, **full name**, and **password**.

Example:

- Email: `admin@biu.edu.ng`
- Matric: `BIU/ADMIN/001`
- Full name: `Portal Admin`

### 7. Run the development server

```bash
python manage.py runserver
```

Base URL: `http://127.0.0.1:8000`

---

## Authentication

Protected endpoints require a JWT in the header:

```http
Authorization: Bearer <access_token>
```

Tokens are returned by `POST /api/auth/login/`. Access tokens are valid for 7 days (configurable in `config/settings.py`).

---

## Testing values (mock data)

### Mock matric numbers

| Matric | Name | Email |
|--------|------|-------|
| `BIU/23/CSC/001` | Samuel Asije | samuel.asije@example.com |
| `BIU/23/CSC/002` | Jane Doe | jane.doe@example.com |
| `BIU/23/CSC/003` | David Johnson | david.johnson@example.com |

### Sample password

`Password123!` (must meet Django password validators)

### Frontend hostel names (hard-coded on client — not from API)

The backend does **not** provide a hostel list endpoint. The frontend should hard-code:

- Hope Hostel
- Above Only Hostel
- Peace Hostel
- Balm of Gilead
- Grace Hostel

Send the selected name as `"hostel": "Hope Hostel"` during registration. The backend stores it as a string on `Room` and compares it case-insensitively during QR scans.

### Hope Hostel QR code IDs (examples)

| Action | `qr_code_id` |
|--------|----------------|
| DROP | `qr_live_hope_drop_9F3K92XQ1PZ7` |
| COLLECT | `qr_live_hope_collect_B82K10QZ91MN` |

Run `python manage.py seed_mvp_data` to see all hostel QR IDs.

### Auth token format

JWT string, e.g. `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

---

## Recommended end-to-end test flow

1. **Start server**

   ```bash
   python manage.py runserver
   ```

2. **Seed QR codes**

   ```bash
   python manage.py seed_mvp_data
   ```

3. **Lookup mock student**

   `POST http://127.0.0.1:8000/api/auth/lookup-student/`

   ```json
   {
     "matric_number": "BIU/23/CSC/001"
   }
   ```

4. **Register student** (hostel name from frontend dropdown)

   `POST http://127.0.0.1:8000/api/auth/register/`

   ```json
   {
     "matric_number": "BIU/23/CSC/001",
     "hostel": "Hope Hostel",
     "room_number": "14",
     "password": "Password123!",
     "confirm_password": "Password123!"
   }
   ```

5. **Check console** for the 6-digit OTP email.

6. **Verify email**

   `POST http://127.0.0.1:8000/api/auth/verify-email/`

   ```json
   {
     "matric_number": "BIU/23/CSC/001",
     "otp": "123456"
   }
   ```

   Replace `123456` with the OTP from the console.

7. **Login**

   `POST http://127.0.0.1:8000/api/auth/login/`

   ```json
   {
     "identifier": "BIU/23/CSC/001",
     "password": "Password123!"
   }
   ```

8. **Copy** the `token` from the response.

9. **Get dashboard**

    `GET http://127.0.0.1:8000/api/dashboard/`

    Header: `Authorization: Bearer TOKEN_HERE`

10. **Get generated QR codes** (staff/superuser token)

    `GET http://127.0.0.1:8000/api/setup/qr-codes/`

    Use superuser JWT or log in as staff.

11. **Scan collect QR**

    `POST http://127.0.0.1:8000/api/keys/scan/`

    Header: `Authorization: Bearer TOKEN_HERE`

    ```json
    {
      "qr_code_id": "qr_live_hope_collect_B82K10QZ91MN"
    }
    ```

12. **Confirm** key status is `WITH_STUDENT` via `GET /api/keys/status/`.

13. **Scan drop QR**

    ```json
    {
      "qr_code_id": "qr_live_hope_drop_9F3K92XQ1PZ7"
    }
    ```

14. **Confirm** key status is `AT_PORTER`.

---

## API endpoints (11 total)

There is **no** `GET /api/hostels/` endpoint. The frontend owns the hostel dropdown.

All JSON responses use a `success` boolean unless noted. Errors return HTTP 400 with `{ "success": false, "message": "..." }` unless otherwise stated.

### 1. `POST /api/auth/lookup-student/`

**Auth:** None

**Description:** Verify matric number against the student registry (mock service for MVP).

**Body:**

```json
{
  "matric_number": "BIU/23/CSC/001"
}
```

**Success (200):**

```json
{
  "success": true,
  "student": {
    "full_name": "Samuel Asije",
    "email": "samuel.asije@example.com",
    "matric_number": "BIU/23/CSC/001"
  }
}
```

**Error (400):**

```json
{
  "success": false,
  "message": "Student record not found."
}
```

---

### 2. `POST /api/auth/register/`

**Auth:** None

**Description:** Complete registration with **hostel name string** and room number from the frontend. Creates inactive user, room key status (`AT_PORTER`), and sends email OTP. Hostel and room cannot be changed after registration in MVP.

**Body:**

```json
{
  "matric_number": "BIU/23/CSC/001",
  "hostel": "Hope Hostel",
  "room_number": "14",
  "password": "Password123!",
  "confirm_password": "Password123!"
}
```

**Success (200):**

```json
{
  "success": true,
  "message": "Account created. Verification code sent to your email."
}
```

**Errors (400):**

```json
{ "success": false, "message": "Student record not found." }
```

```json
{ "success": false, "message": "An account already exists for this matric number." }
```

---

### 3. `POST /api/auth/verify-email/`

**Auth:** None

**Description:** Verify email with 6-digit OTP (expires in 10 minutes).

**Body:**

```json
{
  "matric_number": "BIU/23/CSC/001",
  "otp": "123456"
}
```

**Success (200):**

```json
{
  "success": true,
  "message": "Email verified successfully."
}
```

**Errors (400):**

```json
{ "success": false, "message": "Invalid verification code." }
```

```json
{ "success": false, "message": "Verification code has expired. Please request a new one." }
```

---

### 4. `POST /api/auth/resend-otp/`

**Auth:** None

**Description:** Resend verification OTP to official email.

**Body:**

```json
{
  "matric_number": "BIU/23/CSC/001"
}
```

**Success (200):**

```json
{
  "success": true,
  "message": "A new verification code has been sent to your email."
}
```

**Error (400) — already verified:**

```json
{
  "success": false,
  "message": "Email is already verified."
}
```

---

### 5. `POST /api/auth/login/`

**Auth:** None

**Description:** Login with **email or matric number** + password. Requires verified email.

**Body:**

```json
{
  "identifier": "samuel.asije@example.com",
  "password": "Password123!"
}
```

or:

```json
{
  "identifier": "BIU/23/CSC/001",
  "password": "Password123!"
}
```

**Success (200):**

```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "full_name": "Samuel Asije",
    "email": "samuel.asije@example.com",
    "matric_number": "BIU/23/CSC/001",
    "hostel": "Hope Hostel",
    "room_number": "14"
  }
}
```

**Errors (400):**

```json
{ "success": false, "message": "Please verify your email before logging in." }
```

```json
{ "success": false, "message": "Invalid credentials." }
```

---

### 6. `GET /api/auth/me/`

**Auth:** Bearer JWT (verified user)

**Description:** Current user profile.

**Success (200):**

```json
{
  "success": true,
  "user": {
    "full_name": "Samuel Asije",
    "email": "samuel.asije@example.com",
    "matric_number": "BIU/23/CSC/001",
    "hostel": "Hope Hostel",
    "room_number": "14",
    "is_email_verified": true
  }
}
```

---

### 7. `GET /api/dashboard/`

**Auth:** Bearer JWT (verified user)

**Description:** Student dashboard — profile, room key status, recent activity (last 10).

**Success (200):**

```json
{
  "success": true,
  "user": {
    "full_name": "Samuel Asije",
    "matric_number": "BIU/23/CSC/001",
    "email": "samuel.asije@example.com",
    "hostel": "Hope Hostel",
    "room_number": "14"
  },
  "key_status": {
    "status": "AT_PORTER",
    "label": "Key currently at the porter's lodge",
    "last_updated": "2026-05-17T08:45:00+01:00",
    "last_action_by": "Samuel Asije"
  },
  "recent_activity": [
    {
      "action_type": "DROP",
      "label": "Dropped Key",
      "student": "Samuel Asije",
      "timestamp": "2026-05-17T08:45:00+01:00",
      "resulting_status": "AT_PORTER"
    }
  ]
}
```

---

### 8. `GET /api/keys/status/`

**Auth:** Bearer JWT (verified user)

**Description:** Current shared key status for the student's room.

**Success (200):**

```json
{
  "success": true,
  "key_status": {
    "hostel": "Hope Hostel",
    "room_number": "14",
    "status": "AT_PORTER",
    "label": "Key currently at the porter's lodge",
    "last_updated": "2026-05-17T08:45:00+01:00",
    "last_action_by": "Samuel Asije"
  }
}
```

---

### 9. `GET /api/keys/activity/`

**Auth:** Bearer JWT (verified user)

**Description:** Full key activity history for the student's room (includes roommates).

**Success (200):**

```json
{
  "success": true,
  "activities": [
    {
      "action_type": "DROP",
      "label": "Dropped Key",
      "student": "Samuel Asije",
      "hostel": "Hope Hostel",
      "room_number": "14",
      "timestamp": "2026-05-17T08:45:00+01:00",
      "resulting_status": "AT_PORTER"
    }
  ]
}
```

---

### 10. `POST /api/keys/scan/`

**Auth:** Bearer JWT (verified user)

**Description:** Process QR scan. **Request body must only contain `qr_code_id`.** Backend derives action, room, hostel, and timestamp.

**Body:**

```json
{
  "qr_code_id": "qr_live_hope_collect_B82K10QZ91MN"
}
```

**Success (200):**

```json
{
  "success": true,
  "message": "Key collected successfully.",
  "action_type": "COLLECT",
  "key_status": "WITH_STUDENT",
  "student": "Samuel Asije",
  "hostel": "Hope Hostel",
  "room_number": "14",
  "timestamp": "2026-05-17T08:45:00+01:00"
}
```

**Errors (400):**

| Message |
|---------|
| `Invalid or inactive QR code.` |
| `This QR code does not belong to your hostel.` |
| `This key is already at the porter's lodge.` |
| `This key has already been collected.` |

After success, email is sent to all **verified** students in the same room.

---

### 11. `GET /api/setup/qr-codes/`

**Auth:** Staff/superuser JWT (`is_staff=True`)

**Description:** List QR code IDs for designers to encode into printed QR images.

**Success (200):**

```json
{
  "success": true,
  "qr_codes": [
    {
      "hostel": "Hope Hostel",
      "action_type": "DROP",
      "qr_code_id": "qr_live_hope_drop_9F3K92XQ1PZ7",
      "is_active": true
    },
    {
      "hostel": "Hope Hostel",
      "action_type": "COLLECT",
      "qr_code_id": "qr_live_hope_collect_B82K10QZ91MN",
      "is_active": true
    }
  ]
}
```

---

## Key status rules

| Current status | QR action | Result |
|----------------|-----------|--------|
| `AT_PORTER` | COLLECT | `WITH_STUDENT` |
| `WITH_STUDENT` | DROP | `AT_PORTER` |
| `AT_PORTER` | DROP | Rejected |
| `WITH_STUDENT` | COLLECT | Rejected |

Initial status for every room: `AT_PORTER`.

---

## Project structure

```
config/           # Django settings & root URLs
accounts/         # User, StudentProfile, OTP, auth APIs
  services/
    student_lookup.py   # Mock matric lookup (swap for real API)
    otp.py
    email.py
hostels/          # Room model (hostel stored as string)
  utils.py        # Hostel name normalization / comparison
  rooms.py        # find_or_create_room()
keys/             # QRCode, KeyStatus, KeyActivity, scan & dashboard
  services/
    key_scan.py
    notifications.py
  management/commands/seed_mvp_data.py
```

---

## Django admin

`http://127.0.0.1:8000/admin/` — inspect users, rooms, QR codes, key status, activity, and OTP records.

---

## PostgreSQL

Set `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgres://USER:PASSWORD@localhost:5432/biu_portal
```

Then run `python manage.py migrate`.

---

## Running tests

```bash
python manage.py test
```

---

## Replacing mock student lookup

Edit `accounts/services/student_lookup.py` and replace `fetch_student_by_matric()` with a call to the official BIU student API. Keep the return shape:

```python
{
    "full_name": "...",
    "email": "...",
    "matric_number": "...",
}
```

---

## Security notes (MVP)

- **No hostel list API** — frontend hard-codes hostel names; backend stores the submitted string on `Room`.
- QR scan compares `QRCode.hostel` with `user.profile.room.hostel` using trimmed, case-insensitive matching.
- QR scan accepts **only** `qr_code_id`.
- Student identity comes from the authenticated user and `StudentProfile`.
- `action_type` and QR hostel come from the `QRCode` record.
- Timestamps are server-generated.
- Passwords are hashed with Django’s default hasher.
- OTPs are stored hashed; they expire after 10 minutes.
- Login and scan require verified email.
