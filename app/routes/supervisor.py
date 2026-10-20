from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.routes.auth import role_required
from app.models import db, Officer, Shift, LeaveRequest, RosterAssignment, Attendance, EmergencyDuty, BurnoutAssessment, Department
from app.services.roster_service import run_roster_generation, save_draft_roster, publish_roster
from app.services.workload_service import recalculate_officer_workload
from core.simulator import validate_supervisor_override

supervisor_bp = Blueprint('supervisor', __name__)

@supervisor_bp.route('/dashboard')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def dashboard():
    today = date.today()
    total_officers = Officer.query.count()
    active_officers = Officer.query.filter_by(is_active=True).count()
    
    officers_on_leave = LeaveRequest.query.filter(
        LeaveRequest.status == 'APPROVED',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).count()

    pending_leaves_count = LeaveRequest.query.filter_by(status='PENDING').count()

    # Assessments overview
    assessments = BurnoutAssessment.query.filter_by(assessment_date=today).all()
    if not assessments:
        # Initial populate for demo if missing
        for off in Officer.query.filter_by(is_active=True).all():
            recalculate_officer_workload(off.id, today)
        assessments = BurnoutAssessment.query.filter_by(assessment_date=today).all()

    high_risk_count = sum(1 for a in assessments if a.risk_level == 'HIGH')
    critical_risk_count = sum(1 for a in assessments if a.risk_level == 'CRITICAL')
    moderate_risk_count = sum(1 for a in assessments if a.risk_level == 'MODERATE')
    low_risk_count = sum(1 for a in assessments if a.risk_level == 'LOW')

    # Total Overtime in last 7 days
    recent_start = today - timedelta(days=7)
    attendance_recs = Attendance.query.filter(Attendance.date >= recent_start).all()
    total_overtime = sum(a.overtime_hours or 0.0 for a in attendance_recs)

    # Upcoming Published Shifts
    upcoming_shifts = RosterAssignment.query.filter(
        RosterAssignment.date >= today,
        RosterAssignment.date <= today + timedelta(days=3)
    ).order_by(RosterAssignment.date, RosterAssignment.start_datetime).limit(10).all()

    high_risk_officers = [a for a in assessments if a.risk_level in ['HIGH', 'CRITICAL']]

    return render_template(
        'dashboard/supervisor_dashboard.html',
        total_officers=total_officers,
        active_officers=active_officers,
        officers_on_leave=officers_on_leave,
        pending_leaves_count=pending_leaves_count,
        high_risk_count=high_risk_count,
        critical_risk_count=critical_risk_count,
        moderate_risk_count=moderate_risk_count,
        low_risk_count=low_risk_count,
        total_overtime=total_overtime,
        upcoming_shifts=upcoming_shifts,
        high_risk_officers=high_risk_officers
    )

@supervisor_bp.route('/leave', methods=['GET', 'POST'])
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def leave_management():
    if request.method == 'POST':
        request_id = request.form.get('request_id')
        action = request.form.get('action') # 'APPROVE' or 'REJECT'
        
        leave_req = LeaveRequest.query.get_or_404(request_id)
        if action == 'APPROVE':
            leave_req.status = 'APPROVED'
            leave_req.reviewed_by = current_user.id
            leave_req.reviewed_at = datetime.utcnow()
            flash(f"Leave request for {leave_req.officer.full_name} APPROVED.", "success")
        elif action == 'REJECT':
            leave_req.status = 'REJECTED'
            leave_req.reviewed_by = current_user.id
            leave_req.reviewed_at = datetime.utcnow()
            flash(f"Leave request for {leave_req.officer.full_name} REJECTED.", "info")
            
        db.session.commit()
        return redirect(url_for('supervisor.leave_management'))

    pending_requests = LeaveRequest.query.filter_by(status='PENDING').order_by(LeaveRequest.created_at.desc()).all()
    approved_requests = LeaveRequest.query.filter_by(status='APPROVED').order_by(LeaveRequest.start_date.desc()).limit(15).all()
    rejected_requests = LeaveRequest.query.filter_by(status='REJECTED').order_by(LeaveRequest.start_date.desc()).limit(15).all()

    return render_template(
        'leave/supervisor_index.html',
        pending_requests=pending_requests,
        approved_requests=approved_requests,
        rejected_requests=rejected_requests
    )

@supervisor_bp.route('/roster/generate', methods=['GET', 'POST'])
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def generate_roster():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        horizon_days = int(request.form.get('horizon_days', 7))

        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        result = run_roster_generation(start_date=start_dt, days=horizon_days)

        # Save as draft roster
        save_draft_roster(result['assignments'], status='DRAFT')

        flash(f"Automated Roster generated for {horizon_days} days starting {start_date_str}. Draft saved for supervisor review.", "success")
        return redirect(url_for('supervisor.review_roster', start_date=start_date_str, days=horizon_days))

    today_str = date.today().strftime('%Y-%m-%d')
    return render_template('roster/generate.html', default_start_date=today_str)

@supervisor_bp.route('/roster/review')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def review_roster():
    start_date_str = request.args.get('start_date', date.today().strftime('%Y-%m-%d'))
    days = int(request.args.get('days', 7))

    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_dt = start_dt + timedelta(days=days)

    assignments = RosterAssignment.query.filter(
        RosterAssignment.date >= start_dt,
        RosterAssignment.date < end_dt
    ).order_by(RosterAssignment.date, RosterAssignment.start_datetime).all()

    officers = Officer.query.filter_by(is_active=True).all()
    shifts = Shift.query.all()

    # Re-run simulation to get shortfalls & risk assessments
    sim_result = run_roster_generation(start_date=start_dt, days=days)

    return render_template(
        'roster/review.html',
        start_date=start_date_str,
        days=days,
        assignments=assignments,
        shortfalls=sim_result['shortfalls'],
        risk_assessments=sim_result['risk_assessments'],
        officers=officers,
        shifts=shifts
    )

@supervisor_bp.route('/roster/override', methods=['POST'])
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def override_assignment():
    assignment_id = request.form.get('assignment_id')
    new_officer_id = request.form.get('new_officer_id')
    reason = request.form.get('override_reason', '').strip()

    asgn = RosterAssignment.query.get_or_404(assignment_id)
    new_off = Officer.query.get_or_404(new_officer_id)

    # Validate replacement using simulator validator
    all_officers = [
        {'id': o.id, 'full_name': o.full_name, 'badge_number': o.badge_number, 'is_active': o.is_active}
        for o in Officer.query.all()
    ]
    
    existing_asgns = [
        {
            'officer_id': a.officer_id,
            'date': a.date.strftime('%Y-%m-%d'),
            'start_datetime': a.start_datetime.isoformat(),
            'end_datetime': a.end_datetime.isoformat()
        }
        for a in RosterAssignment.query.filter(RosterAssignment.id != assignment_id).all()
    ]

    asgn_dict = {
        'officer_id': asgn.officer_id,
        'date': asgn.date.strftime('%Y-%m-%d'),
        'start_datetime': asgn.start_datetime.isoformat(),
        'end_datetime': asgn.end_datetime.isoformat(),
        'shift_type': asgn.shift.shift_type if asgn.shift else 'MORNING'
    }

    validation = validate_supervisor_override(
        assignment_to_replace=asgn_dict,
        new_officer={'id': new_off.id, 'full_name': new_off.full_name, 'is_active': new_off.is_active},
        all_officers=all_officers,
        existing_assignments=existing_asgns
    )

    if not validation['is_valid']:
        flash(f"Override Failed: {validation['validation_message']}", "danger")
    else:
        asgn.officer_id = new_off.id
        asgn.override_by = current_user.id
        asgn.override_reason = reason
        db.session.commit()
        
        recalculate_officer_workload(new_off.id, asgn.date)
        flash(f"Assignment updated successfully to Officer {new_off.full_name} ({new_off.badge_number}).", "success")

    return redirect(url_for('supervisor.review_roster', start_date=asgn.date.strftime('%Y-%m-%d')))

@supervisor_bp.route('/roster/publish', methods=['POST'])
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def publish_roster_action():
    start_date_str = request.form.get('start_date')
    days = int(request.form.get('days', 7))

    start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    published_count = publish_roster(start_date=start_dt, days=days)

    flash(f"Roster successfully PUBLISHED! {published_count} shift assignments broadcasted to officers.", "success")
    return redirect(url_for('supervisor.dashboard'))

@supervisor_bp.route('/workload')
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def workload_dashboard():
    today = date.today()
    officers = Officer.query.filter_by(is_active=True).all()

    assessments = []
    for off in officers:
        ass = BurnoutAssessment.query.filter_by(officer_id=off.id, assessment_date=today).first()
        if not ass:
            ass = recalculate_officer_workload(off.id, today)
        assessments.append({
            'officer': off,
            'assessment': ass
        })

    return render_template('workload/supervisor_index.html', assessments=assessments, today=today)

@supervisor_bp.route('/emergency', methods=['GET', 'POST'])
@login_required
@role_required('SUPERVISOR', 'ADMIN')
def emergency_duties():
    officers = Officer.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        officer_id = request.form.get('officer_id')
        duty_date_str = request.form.get('date')
        start_t_str = request.form.get('start_time')
        end_t_str = request.form.get('end_time')
        reason = request.form.get('reason', '').strip()

        duty_date = datetime.strptime(duty_date_str, '%Y-%m-%d').date()
        start_t = datetime.strptime(start_t_str, '%H:%M').time()
        end_t = datetime.strptime(end_t_str, '%H:%M').time()

        dummy = date.today()
        dt_start = datetime.combine(dummy, start_t)
        if end_t <= start_t:
            dt_end = datetime.combine(dummy + timedelta(days=1), end_t)
        else:
            dt_end = datetime.combine(dummy, end_t)
        duration = (dt_end - dt_start).total_seconds() / 3600.0

        duty = EmergencyDuty(
            officer_id=int(officer_id),
            date=duty_date,
            start_time=start_t,
            end_time=end_t,
            duration_hours=duration,
            reason=reason,
            logged_by=current_user.id
        )
        db.session.add(duty)
        db.session.commit()

        # Immediate workload recalculation
        recalculate_officer_workload(int(officer_id), duty_date)

        flash("Emergency duty logged successfully. Workload risk metrics updated.", "success")
        return redirect(url_for('supervisor.emergency_duties'))

    duties = EmergencyDuty.query.order_by(EmergencyDuty.date.desc()).all()
    return render_template('emergency/index.html', duties=duties, officers=officers)
