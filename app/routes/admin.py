from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.routes.auth import role_required
from app.models import db, User, Officer, Department, Shift, RosterAssignment, LeaveRequest, BurnoutAssessment

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('ADMIN')
def dashboard():
    total_officers = Officer.query.count()
    active_officers = Officer.query.filter_by(is_active=True).count()
    inactive_officers = Officer.query.filter_by(is_active=False).count()
    departments_count = Department.query.count()
    shifts_count = Shift.query.count()

    today = date.today()
    officers_on_leave = LeaveRequest.query.filter(
        LeaveRequest.status == 'APPROVED',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).count()

    # Risk level breakdown
    assessments = BurnoutAssessment.query.filter_by(assessment_date=today).all()
    risk_counts = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
    for a in assessments:
        if a.risk_level in risk_counts:
            risk_counts[a.risk_level] += 1

    recent_officers = Officer.query.order_by(Officer.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard/admin_dashboard.html',
        total_officers=total_officers,
        active_officers=active_officers,
        inactive_officers=inactive_officers,
        departments_count=departments_count,
        shifts_count=shifts_count,
        officers_on_leave=officers_on_leave,
        risk_counts=risk_counts,
        recent_officers=recent_officers
    )

@admin_bp.route('/officers')
@login_required
@role_required('ADMIN')
def officers_list():
    query = Officer.query
    dept_id = request.args.get('department_id')
    status = request.args.get('status')
    search = request.args.get('search', '').strip()

    if dept_id:
        query = query.filter_by(department_id=dept_id)
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    if search:
        query = query.filter(
            (Officer.first_name.ilike(f"%{search}%")) |
            (Officer.last_name.ilike(f"%{search}%")) |
            (Officer.badge_number.ilike(f"%{search}%"))
        )

    officers = query.order_by(Officer.badge_number).all()
    departments = Department.query.all()
    return render_template('officers/admin_list.html', officers=officers, departments=departments)

@admin_bp.route('/officers/add', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def add_officer():
    departments = Department.query.all()
    if request.method == 'POST':
        badge = request.form.get('badge_number').strip()
        first_name = request.form.get('first_name').strip()
        last_name = request.form.get('last_name').strip()
        rank = request.form.get('rank').strip()
        dept_id = request.form.get('department_id')
        phone = request.form.get('phone').strip()
        email = request.form.get('email').strip()
        create_user = True if request.form.get('create_user_account') else False
        role = request.form.get('user_role', 'OFFICER')

        if Officer.query.filter_by(badge_number=badge).first():
            flash(f"Officer with badge number '{badge}' already exists.", "danger")
            return render_template('officers/form.html', departments=departments)

        officer = Officer(
            badge_number=badge,
            first_name=first_name,
            last_name=last_name,
            rank=rank,
            department_id=int(dept_id) if dept_id else None,
            phone=phone,
            email=email,
            date_joined=date.today()
        )
        db.session.add(officer)
        db.session.commit()

        if create_user:
            username = badge.lower()
            if not User.query.filter_by(username=username).first():
                user = User(
                    username=username,
                    email=email if email else f"{username}@police.gov",
                    role=role,
                    officer_id=officer.id
                )
                user.set_password('officer123')
                db.session.add(user)
                db.session.commit()

        flash(f"Officer {officer.full_name} ({badge}) added successfully.", "success")
        return redirect(url_for('admin.officers_list'))

    return render_template('officers/form.html', departments=departments, officer=None)

@admin_bp.route('/officers/toggle-status/<int:officer_id>', methods=['POST'])
@login_required
@role_required('ADMIN')
def toggle_officer_status(officer_id):
    officer = Officer.query.get_or_404(officer_id)
    officer.is_active = not officer.is_active
    db.session.commit()
    status_str = "activated" if officer.is_active else "deactivated"
    flash(f"Officer {officer.full_name} has been {status_str}.", "info")
    return redirect(url_for('admin.officers_list'))

@admin_bp.route('/departments', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def departments():
    if request.method == 'POST':
        code = request.form.get('code').strip().upper()
        name = request.form.get('name').strip()
        desc = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()

        if Department.query.filter_by(code=code).first():
            flash(f"Department code '{code}' already exists.", "danger")
        else:
            dept = Department(code=code, name=name, description=desc, location=location)
            db.session.add(dept)
            db.session.commit()
            flash(f"Department '{name}' added successfully.", "success")

    depts = Department.query.all()
    return render_template('admin/departments.html', departments=depts)

@admin_bp.route('/shifts', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def shifts():
    departments = Department.query.all()
    if request.method == 'POST':
        name = request.form.get('name').strip()
        shift_type = request.form.get('shift_type').strip().upper()
        start_t = request.form.get('start_time')
        end_t = request.form.get('end_time')
        staffing = int(request.form.get('required_staffing', 2))
        dept_id = request.form.get('department_id')

        from datetime import datetime
        start_time_obj = datetime.strptime(start_t, '%H:%M').time()
        end_time_obj = datetime.strptime(end_t, '%H:%M').time()

        # Duration
        dummy_date = date.today()
        dt_start = datetime.combine(dummy_date, start_time_obj)
        if end_time_obj <= start_time_obj:
            dt_end = datetime.combine(dummy_date + timedelta(days=1), end_time_obj)
        else:
            dt_end = datetime.combine(dummy_date, end_time_obj)
        duration = (dt_end - dt_start).total_seconds() / 3600.0

        shift = Shift(
            name=name,
            shift_type=shift_type,
            start_time=start_time_obj,
            end_time=end_time_obj,
            duration_hours=duration,
            required_staffing=staffing,
            department_id=int(dept_id) if dept_id else None
        )
        db.session.add(shift)
        db.session.commit()
        flash(f"Shift '{name}' created successfully.", "success")

    shifts_list = Shift.query.all()
    return render_template('admin/shifts.html', shifts=shifts_list, departments=departments)
