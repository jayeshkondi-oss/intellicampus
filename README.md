# EduCore ERP — College ERP System

Full-stack College ERP built with **Flask + PyMySQL** (pure Python — no C compiler needed on Windows).

---

## ✅ Requirements
- Python 3.9 or newer (including 3.14)
- MySQL 8.0+
- No Visual Studio / build tools needed

---

## 🚀 Setup (Windows / Mac / Linux)

### Step 1 — Install Python packages
```
pip install -r requirements.txt
```

### Step 2 — Create the database
Open MySQL Workbench or MySQL Shell and run:
```
mysql -u root -p < schema.sql
```
This creates the `college_erp` database with all tables and seed data.

### Step 3 — Configure your database password
Create a file called `.env` in the project root:
```
SECRET_KEY=any-random-string-here
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password_here
MYSQL_DB=college_erp
```

### Step 4 — Set demo passwords (run once)
```
python utils/seed_passwords.py
```

### Step 5 — Start the server
```
python app.py
```
Open your browser: **http://localhost:5000**

---

## 🔐 Demo Logins

| Role    | Email                  | Password    |
|---------|------------------------|-------------|
| Admin   | admin@college.edu      | Admin@123   |
| Teacher | sharma@college.edu     | Teacher@123 |
| Student | rohan@college.edu      | Student@123 |

---

## 📁 Project Structure

```
college_erp/
├── app.py              ← Flask entry point
├── config.py           ← Settings (reads from .env)
├── db.py               ← PyMySQL connection helper
├── schema.sql          ← MySQL schema + seed data
├── requirements.txt    ← 6 packages only
├── .env.example        ← Copy to .env and fill in
│
├── routes/
│   ├── auth.py         ← Login / logout / change password
│   ├── admin.py        ← Admin portal (8 routes)
│   ├── teacher.py      ← Teacher portal (12 routes)
│   └── student.py      ← Student portal (10 routes)
│
├── static/
│   ├── css/main.css    ← Full design system
│   ├── css/auth.css    ← Login page style
│   ├── js/main.js      ← Sidebar & UI helpers
│   └── uploads/        ← Uploaded files go here
│
├── templates/
│   ├── base.html       ← Sidebar layout (shared)
│   ├── auth/           ← login.html, change_password.html
│   ├── admin/          ← 9 admin pages
│   ├── teacher/        ← 11 teacher pages
│   └── student/        ← 9 student pages
│
└── utils/
    ├── helpers.py      ← File upload helper
    └── seed_passwords.py ← Run once to set demo passwords
```

---

## ⚙️ Why PyMySQL instead of mysqlclient?

`mysqlclient` requires a C compiler (Visual Studio on Windows, gcc on Linux).  
`PyMySQL` is 100% pure Python — just `pip install` and go.

---

## 🧩 Tech Stack

| Layer     | Technology                  |
|-----------|-----------------------------|
| Backend   | Python 3 + Flask 3.1        |
| Database  | MySQL 8 via PyMySQL 1.1     |
| Auth      | Flask-Login 0.6             |
| Frontend  | HTML5 + CSS3 (custom design)|
| Fonts     | DM Sans + Playfair Display  |
| Icons     | Font Awesome 6              |
