from datetime import datetime, date, timedelta
from app.models import db, Officer, Shift, LeaveRequest, RosterAssignment, User
from core.engine import RosterGenerator
from config import Config
from app.services.notification_service import create_notification
from app.services.workload_service import recalculate_officer_workload

def run_roster_generation(start_date: date, days: int = 7) -> dict:
    """
    Service wrapper that pulls active database models, formats input data structures,
    invokes core.RosterGenerator, and returns draft assignments & shortfall reports.
    """
    officers = Officer.query.filter_by(is_active=True).all()
    shifts = Shift.query.all()

    # Build officers payload for engine
    officers_payload = []
    for off in officers:
        # Collect approved leaves
        approved_leaves = [
            l.start_date.strftime('%Y-%m-%d')
            for l in LeaveRequest.query.filter(
                LeaveRequest.officer_id == off.id,
                LeaveRequest.status == 'APPROVED'
            ).all()
        ]

        # Calculate recent historical metrics (last 7 days)
        recent_start = start_date - timedelta(days=7)
        past_assignments = RosterAssignment.query.filter(
            RosterAssignment.officer_id == off.id,
            RosterAssignment.date >= recent_start,
            RosterAssignment.date < start_date
        ).all()

        h_hours = sum((a.end_datetime - a.start_datetime).total_seconds() / 3600.0 for a in past_assignments)
        h_nights = sum(1 for a in past_assignments if a.shift and a.shift.shift_type == 'NIGHT')
        
        last_shift_end = None
        if past_assignments:
            last_shift_end = max(a.end_datetime for a in past_assignments)

        officers_payload.append({
            'id': off.id,
            'badge_number': off.badge_number,
            'full_name': off.full_name,
            'is_active': off.is_active,
            'approved_leaves': approved_leaves,
            'historical_hours': h_hours,
            'historical_consecutive': 0,
            'historical_nights': h_nights,
            'historical_emergencies': 0,
            'last_shift_end_dt': last_shift_end
        })

    # Build shifts payload for engine
    shifts_payload = []
    for s in shifts:
        shifts_payload.append({
            'id': s.id,
            'name': s.name,
            'shift_type': s.shift_type,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'duration_hours': s.duration_hours,
            'required_staffing': s.required_staffing
        })

    generator = RosterGenerator(config=Config)
    result = generator.generate(
        start_date=start_date,
        days=days,
        officers_data=officers_payload,
        shifts_data=shifts_payload
    )

    return result

def save_draft_roster(result_assignments: list[dict], status: str = 'DRAFT') -> int:
    """
    Saves generated assignments into roster_assignments table.
    """
    saved_count = 0
    for asgn in result_assignments:
        off_id = asgn['officer_id']
        s_id = asgn['shift_id']
        dt = datetime.strptime(asgn['date'], '%Y-%m-%d').date()

        # Check existing assignment
        existing = RosterAssignment.query.filter_by(officer_id=off_id, date=dt).first()
        if existing:
            existing.shift_id = s_id
            existing.start_datetime = datetime.fromisoformat(asgn['start_datetime'])
            existing.end_datetime = datetime.fromisoformat(asgn['end_datetime'])
            existing.status = status
            existing.penalty_score = asgn['penalty_score']
        else:
            new_asgn = RosterAssignment(
                officer_id=off_id,
                shift_id=s_id,
                date=dt,
                start_datetime=datetime.fromisoformat(asgn['start_datetime']),
                end_datetime=datetime.fromisoformat(asgn['end_datetime']),
                status=status,
                penalty_score=asgn['penalty_score']
            )
            db.session.add(new_asgn)
        saved_count += 1

    db.session.commit()
    return saved_count

def publish_roster(start_date: date, days: int) -> int:
    """
    Publishes draft roster assignments and sends notifications to assigned officers.
    """
    end_date = start_date + timedelta(days=days)
    drafts = RosterAssignment.query.filter(
        RosterAssignment.date >= start_date,
        RosterAssignment.date < end_date,
        RosterAssignment.status == 'DRAFT'
    ).all()

    published_count = 0
    officer_ids_to_recalculate = set()

    for asgn in drafts:
        asgn.status = 'PUBLISHED'
        published_count += 1
        officer_ids_to_recalculate.add(asgn.officer_id)

        # Send notification to officer user account
        if asgn.officer and asgn.officer.user:
            create_notification(
                user_id=asgn.officer.user.id,
                title="New Duty Roster Published",
                message=f"You have been assigned to '{asgn.shift.name}' on {asgn.date.strftime('%d %b %Y')}.",
                category="ROSTER_PUBLISHED"
            )

    db.session.commit()

    # Recalculate operational workload risk for affected officers
    for off_id in officer_ids_to_recalculate:
        recalculate_officer_workload(off_id, target_date=start_date)

    return published_count
