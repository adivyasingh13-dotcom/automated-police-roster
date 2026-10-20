from datetime import datetime, timedelta, date
from app.models import db, Officer, RosterAssignment, Attendance, EmergencyDuty, BurnoutAssessment
from core.simulator import calculate_workload_risk
from app.services.notification_service import create_notification

def recalculate_officer_workload(officer_id: int, target_date: date = None) -> BurnoutAssessment:
    """
    Recalculates operational workload metrics for an officer over the recent 7-day window.
    Saves/updates BurnoutAssessment record and sends notifications if risk is HIGH or CRITICAL.
    """
    if target_date is None:
        target_date = date.today()

    officer = db.session.get(Officer, officer_id)
    if not officer:
        return None

    window_start = target_date - timedelta(days=6)

    # 1. Calculate assigned roster hours
    assignments = RosterAssignment.query.filter(
        RosterAssignment.officer_id == officer_id,
        RosterAssignment.date >= window_start,
        RosterAssignment.date <= target_date
    ).all()

    total_hours = 0.0
    night_shifts_count = 0
    assigned_dates = set()

    for asgn in assignments:
        assigned_dates.add(asgn.date)
        duration = (asgn.end_datetime - asgn.start_datetime).total_seconds() / 3600.0
        total_hours += duration
        if asgn.shift and asgn.shift.shift_type == 'NIGHT':
            night_shifts_count += 1

    # 2. Attendance & Overtime
    attendance_recs = Attendance.query.filter(
        Attendance.officer_id == officer_id,
        Attendance.date >= window_start,
        Attendance.date <= target_date
    ).all()

    overtime_hours = sum(a.overtime_hours or 0.0 for a in attendance_recs)

    # 3. Emergency duties
    emergencies = EmergencyDuty.query.filter(
        EmergencyDuty.officer_id == officer_id,
        EmergencyDuty.date >= window_start,
        EmergencyDuty.date <= target_date
    ).all()

    emergency_duties_count = len(emergencies)
    emergency_hours = sum(e.duration_hours for e in emergencies)
    total_hours += emergency_hours

    # 4. Calculate consecutive working days
    consecutive_days = 0
    curr = target_date
    while curr >= window_start:
        if curr in assigned_dates or any(e.date == curr for e in emergencies):
            consecutive_days += 1
            curr -= timedelta(days=1)
        else:
            break

    # 5. Evaluate Workload Risk
    risk_info = calculate_workload_risk(
        total_hours=total_hours,
        consecutive_days=consecutive_days,
        night_shifts_count=night_shifts_count,
        emergency_duties_count=emergency_duties_count,
        overtime_hours=overtime_hours
    )

    # 6. Save/update BurnoutAssessment record
    assessment = BurnoutAssessment.query.filter_by(
        officer_id=officer_id,
        assessment_date=target_date
    ).first()

    if not assessment:
        assessment = BurnoutAssessment(
            officer_id=officer_id,
            assessment_date=target_date
        )
        db.session.add(assessment)

    assessment.total_hours = total_hours
    assessment.overtime_hours = overtime_hours
    assessment.consecutive_days = consecutive_days
    assessment.night_shifts_count = night_shifts_count
    assessment.emergency_duties_count = emergency_duties_count
    assessment.risk_level = risk_info['risk_level']
    assessment.risk_score = risk_info['risk_score']
    assessment.reasoning = risk_info['reasoning']
    
    db.session.commit()

    # Trigger notification if risk is HIGH or CRITICAL
    if officer.user and risk_info['risk_level'] in ['HIGH', 'CRITICAL']:
        create_notification(
            user_id=officer.user.id,
            title=f"Workload Warning: {risk_info['risk_level']} Workload Risk",
            message=f"Your operational workload has been evaluated as {risk_info['risk_level']}. {risk_info['reasoning']}",
            category="WORKLOAD_ALERT"
        )

    return assessment
