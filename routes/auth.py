"""Authentication routes — login / logout / change password"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models.user import User
from db import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}.dashboard'))
    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        db  = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND is_active=1", (email,))
        row = cur.fetchone()
        cur.close()
        if row and check_password_hash(row['password_hash'], password):
            user = User(row)
            login_user(user, remember=bool(request.form.get('remember')))
            cur2 = db.cursor()
            cur2.execute("UPDATE users SET last_login=NOW() WHERE id=%s", (user.id,))
            db.commit()
            cur2.close()
            nxt = request.args.get('next')
            return redirect(nxt or url_for(f'{user.role}.dashboard'))
        error = 'Invalid email or password. Please try again.'
    return render_template('auth/login.html', error=error)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    error = success = None
    if request.method == 'POST':
        old_pw  = request.form.get('old_password', '')
        new_pw  = request.form.get('new_password', '')
        conf_pw = request.form.get('confirm_password', '')
        db  = get_db()
        cur = db.cursor()
        cur.execute("SELECT password_hash FROM users WHERE id=%s", (current_user.id,))
        row = cur.fetchone()
        cur.close()
        if not check_password_hash(row['password_hash'], old_pw):
            error = 'Current password is incorrect.'
        elif new_pw != conf_pw:
            error = 'New passwords do not match.'
        elif len(new_pw) < 8:
            error = 'Password must be at least 8 characters.'
        else:
            cur2 = db.cursor()
            cur2.execute("UPDATE users SET password_hash=%s WHERE id=%s",
                         (generate_password_hash(new_pw), current_user.id))
            db.commit()
            cur2.close()
            success = 'Password changed successfully!'
    return render_template('auth/change_password.html', error=error, success=success)
