# BIU Smart Hostel Key Management Portal — API Documentation

This document outlines the available endpoints for the BIU Smart Hostel Key Management Portal backend.

### **Interactive Documentation**
For a live, interactive experience where you can test endpoints directly from your browser, use:
- **Swagger UI**: `/api/docs/swagger/`
- **Redoc**: `/api/docs/redoc/`

**Base URL:** `https://<your-app-name>.onrender.com` (Production) or `http://127.0.0.1:8000` (Local)

---

## **Authentication**

### **1. Register Student**
- **URL:** `/api/auth/register/`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body (Multipart/Form-Data):**
  | Field | Type | Description |
  |-------|------|-------------|
  | `matric_number` | string | Student matric number |
  | `email` | string | Student email |
  | `first_name` | string | First name |
  | `last_name` | string | Last name |
  | `hostel` | string | Hostel name (e.g., "Hope Hostel") |
  | `room_number` | string | Room number |
  | `flat_number` | string | Flat number |
  | `password` | string | Min 8 characters |
  | `confirm_password` | string | Must match password |
  | `profile_picture` | file | Optional (JPEG/PNG/WebP, max 5MB) |

### **2. Verify Email (OTP)**
- **URL:** `/api/auth/verify-email/`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body (JSON):**
  ```json
  {
    "matric_number": "BIU/23/CSC/001",
    "otp": "123456"
  }
  ```

### **3. Resend OTP**
- **URL:** `/api/auth/resend-otp/`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body (JSON):**
  ```json
  {
    "matric_number": "BIU/23/CSC/001"
  }
  ```

### **4. Login**
- **URL:** `/api/auth/login/`
- **Method:** `POST`
- **Auth Required:** No
- **Request Body (JSON):**
  ```json
  {
    "identifier": "BIU/23/CSC/001",
    "password": "Password123!"
  }
  ```
- **Response:** Returns `token` (JWT Access Token) and `user` profile.

### **5. Get Current User (Me)**
- **URL:** `/api/auth/me/`
- **Method:** `GET`
- **Auth Required:** Yes (`Bearer <token>`)

---

## **Student Lookup**

### **1. External Portal Lookup**
- **URL:** `/api/auth/student-lookup/`
- **Method:** `GET`
- **Auth Required:** No
- **Query Params:** `?matric_no=SCN/CSC/220689`
- **Success Response (200):**
  ```json
  {
    "success": true,
    "source": "biu_portal",
    "matric_no": "SCN/CSC/220689",
    "data": {
      "full_name": "...",
      "department": "...",
      "faculty": "...",
      "programme": "...",
      "level": "...",
      "hostel": "...",
      "room_number": "...",
      "email": "...",
      "phone": "..."
    }
  }
  ```

---

## **Key Management**

### **1. Dashboard Summary**
- **URL:** `/api/dashboard/`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Returns user profile, current key status of their room, and 10 most recent activities.

### **2. Scan QR Code**
- **URL:** `/api/keys/scan/`
- **Method:** `POST`
- **Auth Required:** Yes
- **Request Body (JSON):**
  ```json
  {
    "qr_code_id": "qr_live_collect_B82K10QZ91MN"
  }
  ```

### **3. Key Status**
- **URL:** `/api/keys/status/`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Returns the current status of the user's room key (`AT_PORTER` or `WITH_STUDENT`).

### **4. Full Activity Feed**
- **URL:** `/api/keys/activity/`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Returns the full history of key actions for the user's room.

---

## **Setup (Admin Only)**

### **1. QR Code List**
- **URL:** `/api/setup/qr-codes/`
- **Method:** `GET`
- **Auth Required:** Yes (Staff/Admin)
