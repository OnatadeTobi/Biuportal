# BIU Smart Hostel Key Management Portal — Backend API

Backend-only MVP for Benson Idahosa University students to digitally drop and collect **shared hostel room keys** using static QR codes.

**Stack:** Python, Django 5, Django REST Framework, JWT, Docker, Gunicorn, WhiteNoise.

---

## 📖 API Documentation

- **Interactive Swagger UI**: `http://127.0.0.1:8000/api/docs/swagger/`
- **Clean Redoc**: `http://127.0.0.1:8000/api/docs/redoc/`
- **Static Documentation**: See [API_DOCS.md](./API_DOCS.md) for a manual breakdown.

---

## 🚀 Deployment (Render)

This project is configured for one-click deployment on Render using Docker.

### **1. Setup on Render**
- Create a new **Web Service**.
- Connect this GitHub repo.
- Select **Language: Docker**.
- Add the following **Environment Variables**:
  - `SECRET_KEY`: Your Django secret key.
  - `DEBUG`: `False`.
  - `ALLOWED_HOSTS`: `<your-app-name>.onrender.com`.
  - `DATABASE_URL`: (Optional) Your PostgreSQL URL.
  - `EMAIL_HOST_PASSWORD`: Your Brevo SMTP API Key.
  - (Other SMTP keys as per `.env.example`)

### **2. Automated Setup**
The included `entrypoint.sh` will automatically:
1. Run migrations.
2. Seed global QR codes (`qr_live_collect_B82K10QZ91MN` and `qr_live_drop_9F3K92XQ1PZ7`).
3. Collect static files.
4. Start the Gunicorn server.

---

## 💻 Local Development

### **1. Install Dependencies**
```bash
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### **2. Environment Setup**
Copy `.env.example` to `.env` and fill in your credentials.

### **3. Run Commands**
```bash
python manage.py migrate
python manage.py seed_mvp_data
python manage.py runserver
```

---

## 🛠 Features
- **Student Lookup**: Real-time student verification via the BIU Portal.
- **Key Tracking**: Real-time status (`AT PORTER` / `COLLECTED`) for every room.
- **Activity Feed**: Detailed logs of who collected or dropped keys and when.
- **Email Notifications**: Instant OTPs and room-wide key action alerts via Brevo.
- **Production Ready**: Dockerized with Gunicorn and WhiteNoise for static file serving.
