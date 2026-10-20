from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.routes.auth import role_required
from app.models import db, Officer, RosterAssignment, LeaveRequest, Attendance, EmergencyDuty, BurnoutAssessment, Notification
from app.services.workload_service import recalculate_officer_workload

officer_bp = Blueprint('officer', __name__)

@officer_bp.route('/dashboard')
@login_required
@role_required('OFFICER', 'SUPERVISOR', 'ADMIN')
def dashboard():
    officer = current_user.officer
    if not officer:
        flash("No officer profile attached to this user account.", "warning")
        return render_template('dashboard/officer_dashboard.html', officer=None)

    today = date.today()

    # Next upcoming shift
    next_shift = RosterAssignment.query.filter(
        RosterAssignment.officer_id == officer.id,
        RosterAssignment.date >= today,
        RosterAssignment.status == 'PUBLISHED'
    ).order_by(RosterAssignment.date, RosterAssignment.start_datetime).first()

    # Upcoming 7-day schedule
    upcoming_schedule = RosterAssignment.query.filter(
        RosterAssignment.officer_id == officer.id,
        RosterAssignment.date >= today,
        RosterAssignment.date <= today + timedelta(days=7),
        RosterAssignment.status == 'PUBLISHED'
    ).order_by(RosterAssignment.date).all()

    # Current workload assessment
    assessment = BurnoutAssessment.query.filter_by(
        officer_id=officer.id,
        assessment_date=today
    ).first()

    if not assessment:
        assessment = recalculate_officer_workload(officer.id, today)

    # Personal notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard/officer_dashboard.html',
        officer=officer,
        next_shift=next_shift,
        upcoming_schedule=upcoming_schedule,
        assessment=assessment,
        notifications=notifications
    )

@officer_bp.route('/leave', methods=['GET', 'POST'])
@login_required
@role_required('OFFICER', 'SUPERVISOR', 'ADMIN')
def leave():
    officer = current_user.officer
    if not officer:
        flash("No officer profile linked.", "warning")
        return redirect(url_for('officer.dashboard'))

    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        reason = request.form.get('reason', '').strip()

        start_d = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_d = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if end_d < start_d:
            flash("Leave end date cannot be earlier than start date.", "danger")
        elif start_d < date.today():
            flash("Leave request cannot be in the past.", "warning")
        else:
            req = LeaveRequest(
                officer_id=officer.id,
                start_date=start_d,
                end_date=end_d,
                reason=reason,
                status='PENDING'
            )
            db.session.add(req)
            db.session.commit()
            flash("Leave request submitted successfully for supervisor approval.", "success")
            return redirect(url_for('officer.leave'))

    my_leaves = LeaveRequest.query.filter_by(officer_id=officer.id).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('leave/officer_index.html', my_leaves=my_leaves)

@officer_bp.route('/workload')
@login_required
@role_required('OFFICER', 'SUPERVISOR', 'ADMIN')
def workload():
    officer = current_user.officer
    if not officer:
        flash("No officer profile linked.", "warning")
        return redirect(url_for('officer.dashboard'))

    today = date.today()
    assessment = BurnoutAssessment.query.filter_by(officer_id=officer.id, assessment_date=today).first()
    if not assessment:
        assessment = recalculate_officer_workload(officer.id, today)

    history = BurnoutAssessment.query.filter_by(officer_id=officer.id).order_by(BurnoutAssessment.assessment_date.desc()).limit(10).all()

    return render_template('workload/officer_index.html', officer=officer, assessment=assessment, history=history)

@officer_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return jsonify({'status': 'SUCCESS'})
