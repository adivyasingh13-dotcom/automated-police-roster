from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.routes.auth import role_required
from app.models import db, Attendance, Officer, Shift, RosterAssignment
from app.services.workload_service import recalculate_officer_workload

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@login_required
def index():
    filter_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
    
    officer_id = request.args.get('officer_id')

    query = Attendance.query.filter_by(date=filter_date)
    if officer_id:
        query = query.filter_by(officer_id=int(officer_id))

    records = query.order_by(Attendance.created_at.desc()).all()
    officers = Officer.query.filter_by(is_active=True).all()
    shifts = Shift.query.all()

    return render_template(
        'attendance/index.html',
        records=records,
        officers=officers,
        shifts=shifts,
        selected_date=filter_date_str
    )

@attendance_bp.route('/log', methods=['POST'])
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def log_attendance():
    officer_id = request.form.get('officer_id')
    att_date_str = request.form.get('date')
    shift_id = request.form.get('scheduled_shift_id')
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')
    status = request.form.get('status', 'PRESENT')

    att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date()

    check_in_dt = None
    check_out_dt = None
    working_hours = 0.0
    overtime_hours = 0.0

    if check_in_str:
        check_in_dt = datetime.strptime(f"{att_date_str} {check_in_str}", '%Y-%m-%d %H:%M')
    if check_out_str:
        check_out_dt = datetime.strptime(f"{att_date_str} {check_out_str}", '%Y-%m-%d %H:%M')
        if check_out_dt <= check_in_dt:
            check_out_dt += timedelta(days=1)

    if check_in_dt and check_out_dt:
        working_hours = (check_out_dt - check_in_dt).total_seconds() / 3600.0
        if working_hours > 8.0:
            overtime_hours = round(working_hours - 8.0, 1)

    existing = Attendance.query.filter_by(officer_id=int(officer_id), date=att_date).first()
    if existing:
        existing.scheduled_shift_id = int(shift_id) if shift_id else None
        existing.check_in = check_in_dt
        existing.check_out = check_out_dt
        existing.working_hours = working_hours
        existing.overtime_hours = overtime_hours
        existing.status = status
    else:
        new_att = Attendance(
            officer_id=int(officer_id),
            date=att_date,
            scheduled_shift_id=int(shift_id) if shift_id else None,
            check_in=check_in_dt,
            check_out=check_out_dt,
            working_hours=working_hours,
            overtime_hours=overtime_hours,
            status=status
        )
        db.session.add(new_att)

    db.session.commit()

    # Immediate workload recalculation
    recalculate_officer_workload(int(officer_id), att_date)

    flash("Attendance log updated successfully.", "success")
    return redirect(url_for('attendance.index', date=att_date_str))
