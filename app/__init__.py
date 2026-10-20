import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from config import Config
from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance directory exists for SQLite
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    # Custom Jinja filters
    @app.template_filter('risk_badge_class')
    def risk_badge_class(risk_level):
        mapping = {
            'LOW': 'bg-success text-white',
            'MODERATE': 'bg-warning text-dark',
            'HIGH': 'bg-danger-dark text-white',
            'CRITICAL': 'bg-critical text-white'
        }
        return mapping.get(str(risk_level).upper(), 'bg-secondary text-white')

    @app.template_filter('status_badge_class')
    def status_badge_class(status):
        mapping = {
            'APPROVED': 'bg-success text-white',
            'PENDING': 'bg-warning text-dark',
            'REJECTED': 'bg-danger text-white',
            'PUBLISHED': 'bg-primary text-white',
            'DRAFT': 'bg-secondary text-white',
            'PRESENT': 'bg-success text-white',
            'ABSENT': 'bg-danger text-white',
            'ON_LEAVE': 'bg-info text-dark'
        }
        return mapping.get(str(status).upper(), 'bg-secondary text-white')

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.supervisor import supervisor_bp
    from app.routes.officer import officer_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
    app.register_blueprint(officer_bp, url_prefix='/officer')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'SUPERVISOR':
            return redirect(url_for('supervisor.dashboard'))
        else:
            return redirect(url_for('officer.dashboard'))

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
