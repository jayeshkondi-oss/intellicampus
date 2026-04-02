"""
Run this ONCE after importing schema.sql to set real password hashes.
Usage:  python utils/seed_passwords.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
from app import app
from db import get_db

DEMO_USERS = [
    ('admin@college.edu',  'Admin@123'),
    ('sharma@college.edu', 'Teacher@123'),
    ('rohan@college.edu',  'Student@123'),
]

with app.app_context():
    db  = get_db()
    cur = db.cursor()
    for email, password in DEMO_USERS:
        pw_hash = generate_password_hash(password)
        cur.execute("UPDATE users SET password_hash=%s WHERE email=%s", (pw_hash, email))
        print(f"  OK  {email}")
    db.commit()
    cur.close()
    print("\nDone! Run: python app.py")
