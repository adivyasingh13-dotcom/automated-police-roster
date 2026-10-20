from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in roles:
                flash("Access denied. You do not have permission to view this page.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid username/email or password. Please try again.", "danger")
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.username}! Signed in as {user.role}.", "success")

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            return redirect(url_for('index'))
        return redirect(next_page)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        if not current_user.check_password(current_pw):
            flash("Current password incorrect.", "danger")
        elif new_pw != confirm_pw:
            flash("New passwords do not match.", "danger")
        elif len(new_pw) < 6:
            flash("New password must be at least 6 characters.", "warning")
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash("Your password has been updated successfully.", "success")

    return render_template('auth/profile.html', user=current_user)
