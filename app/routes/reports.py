from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request
from flask_login import login_required
from app.routes.auth import role_required
from app.models import db, Officer, RosterAssignment, Attendance, LeaveRequest, BurnoutAssessment, EmergencyDuty

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def index():
    return render_template('reports/index.html')

@reports_bp.route('/roster')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def roster_report():
    start_date_str = request.args.get('start_date', date.today().strftime('%Y-%m-%d'))
    days = int(request.args.get('days', 7))

    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_dt = start_dt + timedelta(days=days)

    assignments = RosterAssignment.query.filter(
        RosterAssignment.date >= start_dt,
        RosterAssignment.date < end_dt
    ).order_by(RosterAssignment.date, RosterAssignment.start_datetime).all()

    return render_template(
        'reports/roster_report.html',
        assignments=assignments,
        start_date=start_date_str,
        days=days
    )

@reports_bp.route('/workload-risk')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def workload_risk_report():
    today = date.today()
    assessments = BurnoutAssessment.query.filter_by(assessment_date=today).all()

    return render_template('reports/workload_risk_report.html', assessments=assessments, today=today)

@reports_bp.route('/overtime')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def overtime_report():
    recent_start = date.today() - timedelta(days=30)
    attendance_records = Attendance.query.filter(
        Attendance.date >= recent_start,
        Attendance.overtime_hours > 0
    ).order_by(Attendance.date.desc()).all()

    return render_template('reports/overtime_report.html', records=attendance_records)

@reports_bp.route('/leave')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def leave_report():
    leaves = LeaveRequest.query.order_by(LeaveRequest.start_date.desc()).all()
    return render_template('reports/leave_report.html', leaves=leaves)
