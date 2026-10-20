from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    officers = db.relationship('Officer', backref='department', lazy=True)
    shifts = db.relationship('Shift', backref='department', lazy=True)

class Officer(db.Model):
    __tablename__ = 'officers'
    
    id = db.Column(db.Integer, primary_key=True)
    badge_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    rank = db.Column(db.String(50), default='Constable')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100), unique=True)
    date_joined = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='officer', uselist=False)
    leave_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.officer_id', backref='officer', lazy=True)
    roster_assignments = db.relationship('RosterAssignment', foreign_keys='RosterAssignment.officer_id', backref='officer', lazy=True)
    attendance_records = db.relationship('Attendance', backref='officer', lazy=True)
    emergency_duties = db.relationship('EmergencyDuty', foreign_keys='EmergencyDuty.officer_id', backref='officer', lazy=True)
    burnout_assessments = db.relationship('BurnoutAssessment', backref='officer', lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'ADMIN', 'SUPERVISOR', 'OFFICER'
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Shift(db.Model):
    __tablename__ = 'shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    shift_type = db.Column(db.String(20), nullable=False) # 'MORNING', 'EVENING', 'NIGHT'
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Float, default=8.0)
    required_staffing = db.Column(db.Integer, default=2)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roster_assignments = db.relationship('RosterAssignment', backref='shift', lazy=True)

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='PENDING') # 'PENDING', 'APPROVED', 'REJECTED'
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RosterAssignment(db.Model):
    __tablename__ = 'roster_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='DRAFT') # 'DRAFT', 'PUBLISHED'
    penalty_score = db.Column(db.Float, default=0.0)
    override_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    override_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    scheduled_shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'))
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)
    working_hours = db.Column(db.Float, default=0.0)
    overtime_hours = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='PRESENT') # 'PRESENT', 'ABSENT', 'LATE', 'ON_LEAVE', 'EMERGENCY_DUTY'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyDuty(db.Model):
    __tablename__ = 'emergency_duties'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    logged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BurnoutAssessment(db.Model):
    __tablename__ = 'burnout_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'), nullable=False)
    assessment_date = db.Column(db.Date, nullable=False)
    total_hours = db.Column(db.Float, default=0.0)
    overtime_hours = db.Column(db.Float, default=0.0)
    consecutive_days = db.Column(db.Integer, default=0)
    night_shifts_count = db.Column(db.Integer, default=0)
    emergency_duties_count = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), nullable=False) # 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
    risk_score = db.Column(db.Integer, default=0)
    reasoning = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='GENERAL')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
