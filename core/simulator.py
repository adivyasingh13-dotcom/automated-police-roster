from datetime import datetime
from core.constraints import is_hard_constraint_satisfied
from core.penalty import calculate_candidate_penalty

def calculate_workload_risk(
    total_hours: float,
    consecutive_days: int,
    night_shifts_count: int,
    emergency_duties_count: int,
    overtime_hours: float
) -> dict:
    """
    Evaluates Operational Workload Risk (LOW, MODERATE, HIGH, CRITICAL)
    based on objective operational scheduling parameters.
    """
    reasons = []

    # Check Critical Criteria
    if total_hours >= 52.0:
        reasons.append(f"{total_hours:.0f} weekly hours (exceeds 52h cap)")
    if consecutive_days >= 6:
        reasons.append(f"{consecutive_days} consecutive days limit reached")
    if night_shifts_count >= 4 and total_hours >= 44.0:
        reasons.append(f"{night_shifts_count} night shifts with {total_hours:.0f}h workload")
    if emergency_duties_count >= 3 and total_hours >= 44.0:
        reasons.append(f"{emergency_duties_count} emergency duties with heavy hours")

    if reasons:
        return {
            'risk_level': 'CRITICAL',
            'risk_score': 90,
            'reasoning': '; '.join(reasons) + '.',
            'explanation': 'Operational workload is significantly above threshold. Requires prompt operational review.'
        }

    # Check High Criteria
    if total_hours >= 44.0:
        reasons.append(f"{total_hours:.0f} weekly hours")
    if consecutive_days >= 5:
        reasons.append(f"{consecutive_days} consecutive days")
    if night_shifts_count >= 3:
        reasons.append(f"{night_shifts_count} night shifts")
    if overtime_hours >= 12.0:
        reasons.append(f"{overtime_hours:.0f}h overtime")

    if reasons:
        return {
            'risk_level': 'HIGH',
            'risk_score': 70,
            'reasoning': '; '.join(reasons) + '.',
            'explanation': 'Operational workload exceeds baseline threshold. Supervisor review recommended.'
        }

    # Check Moderate Criteria
    if total_hours >= 36.0:
        reasons.append(f"{total_hours:.0f} weekly hours")
    if consecutive_days >= 4:
        reasons.append(f"{consecutive_days} consecutive days")
    if night_shifts_count >= 2:
        reasons.append(f"{night_shifts_count} night shifts")
    if emergency_duties_count >= 1:
        reasons.append(f"{emergency_duties_count} emergency duty")

    if reasons:
        return {
            'risk_level': 'MODERATE',
            'risk_score': 40,
            'reasoning': '; '.join(reasons) + '.',
            'explanation': 'Operational workload has increased and requires routine monitoring.'
        }

    # Low Risk Default
    return {
        'risk_level': 'LOW',
        'risk_score': 15,
        'reasoning': 'Workload within standard baseline limits.',
        'explanation': 'Current workload is within normal operational limits.'
    }

def validate_supervisor_override(
    assignment_to_replace: dict,
    new_officer: dict,
    all_officers: list[dict],
    existing_assignments: list[dict],
    config=None
) -> dict:
    """
    Validates a supervisor manual override (replacing an officer in a roster entry with new_officer).
    """
    min_rest = getattr(config, 'MIN_REST_HOURS', 11.0)
    max_weekly = getattr(config, 'MAX_WEEKLY_HOURS', 48.0)
    max_consecutive = getattr(config, 'MAX_CONSECUTIVE_DAYS', 6)

    shift_date_str = assignment_to_replace['date']
    shift_date = datetime.strptime(shift_date_str, '%Y-%m-%d').date() if isinstance(shift_date_str, str) else shift_date_str
    
    start_dt = datetime.fromisoformat(assignment_to_replace['start_datetime']) if isinstance(assignment_to_replace['start_datetime'], str) else assignment_to_replace['start_datetime']
    end_dt = datetime.fromisoformat(assignment_to_replace['end_datetime']) if isinstance(assignment_to_replace['end_datetime'], str) else assignment_to_replace['end_datetime']
    shift_duration = (end_dt - start_dt).total_seconds() / 3600.0

    # Collect new_officer's current assigned dates & last shift end
    assigned_dates = set()
    last_shift_end_dt = None
    new_off_weekly_hours = float(new_officer.get('historical_hours', 0.0))
    consecutive_days = int(new_officer.get('historical_consecutive', 0))

    for asgn in existing_assignments:
        if asgn['officer_id'] == new_officer['id']:
            assigned_dates.add(asgn['date'])
            asgn_end_dt = datetime.fromisoformat(asgn['end_datetime']) if isinstance(asgn['end_datetime'], str) else asgn['end_datetime']
            
            new_off_weekly_hours += (asgn_end_dt - datetime.fromisoformat(asgn['start_datetime']) if isinstance(asgn['start_datetime'], str) else asgn['start_datetime']).total_seconds() / 3600.0
            if last_shift_end_dt is None or asgn_end_dt > last_shift_end_dt:
                last_shift_end_dt = asgn_end_dt

    approved_leave_dates = set(new_officer.get('approved_leaves', []))

    # Evaluate hard constraint
    is_valid, error_reason = is_hard_constraint_satisfied(
        is_active=new_officer.get('is_active', True),
        shift_date=shift_date,
        shift_start_dt=start_dt,
        shift_duration=shift_duration,
        approved_leave_dates=approved_leave_dates,
        assigned_dates=assigned_dates,
        last_shift_end_dt=last_shift_end_dt,
        current_consecutive=consecutive_days,
        current_weekly_hours=new_off_weekly_hours,
        min_rest_hours=min_rest,
        max_consecutive_days=max_consecutive,
        max_weekly_hours=max_weekly
    )

    # Projected workload risk if reassignment proceeds
    projected_hours = new_off_weekly_hours + shift_duration
    projected_risk = calculate_workload_risk(
        total_hours=projected_hours,
        consecutive_days=consecutive_days + 1,
        night_shifts_count=int(new_officer.get('historical_nights', 0)) + (1 if assignment_to_replace.get('shift_type') == 'NIGHT' else 0),
        emergency_duties_count=int(new_officer.get('historical_emergencies', 0)),
        overtime_hours=float(new_officer.get('historical_overtime', 0.0))
    )

    # Find alternative candidate officers
    alternative_suggestions = []
    for candidate in all_officers:
        if candidate['id'] == new_officer['id'] or candidate['id'] == assignment_to_replace['officer_id']:
            continue
        
        c_assigned_dates = set(a['date'] for a in existing_assignments if a['officer_id'] == candidate['id'])
        c_approved_leaves = set(candidate.get('approved_leaves', []))
        c_hours = float(candidate.get('historical_hours', 0.0))
        
        c_valid, _ = is_hard_constraint_satisfied(
            is_active=candidate.get('is_active', True),
            shift_date=shift_date,
            shift_start_dt=start_dt,
            shift_duration=shift_duration,
            approved_leave_dates=c_approved_leaves,
            assigned_dates=c_assigned_dates,
            last_shift_end_dt=None,
            current_consecutive=int(candidate.get('historical_consecutive', 0)),
            current_weekly_hours=c_hours,
            min_rest_hours=min_rest,
            max_consecutive_days=max_consecutive,
            max_weekly_hours=max_weekly
        )
        if c_valid:
            alternative_suggestions.append({
                'officer_id': candidate['id'],
                'full_name': candidate.get('full_name', ''),
                'badge_number': candidate.get('badge_number', '')
            })

    return {
        'is_valid': is_valid,
        'validation_message': 'Override proposal is valid and compliant.' if is_valid else error_reason,
        'projected_risk': projected_risk,
        'alternative_suggestions': alternative_suggestions[:3]
    }
