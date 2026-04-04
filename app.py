from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from db import get_db, init_app as init_db
from models.user import User
import os, datetime

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    db  = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s AND is_active=1", (user_id,))
    row = cur.fetchone()
    cur.close()
    return User(row) if row else None

# Import blueprints AFTER app and login_manager are created
from routes.auth    import auth_bp
from routes.admin   import admin_bp
from routes.teacher import teacher_bp
from routes.student import student_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp,   url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(student_bp, url_prefix='/student')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    return redirect(url_for('auth.login'))

@app.context_processor
def inject_globals():
    return dict(
        app_name="IntelliCampus ERP",
        college_name="Universal College of Engineering",
        now=datetime.datetime.now(),
    )

from flask import make_response

@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://intellicampus.me/</loc></url>
  <url><loc>https://intellicampus.me/login</loc></url>
</urlset>"""
    response = make_response(xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/robots.txt')
def robots():
    content = "User-agent: *\nAllow: /\nSitemap: https://intellicampus.me/sitemap.xml"
    return content, 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
