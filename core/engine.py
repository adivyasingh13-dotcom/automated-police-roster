from datetime import datetime, timedelta, date, time
from core.constraints import is_hard_constraint_satisfied
from core.penalty import calculate_candidate_penalty

class RosterGenerator:
    """
    Rule-based deterministic roster generator using hard constraint filtering
    and soft penalty scoring.
    """

    def __init__(self, config=None):
        self.min_rest_hours = getattr(config, 'MIN_REST_HOURS', 11.0)
        self.max_weekly_hours = getattr(config, 'MAX_WEEKLY_HOURS', 48.0)
        self.max_consecutive_days = getattr(config, 'MAX_CONSECUTIVE_DAYS', 6)
        
        self.weight_workload = getattr(config, 'PENALTY_WEIGHT_WORKLOAD', 1.0)
        self.weight_consecutive = getattr(config, 'PENALTY_WEIGHT_CONSECUTIVE', 2.0)
        self.weight_night = getattr(config, 'PENALTY_WEIGHT_NIGHT', 3.0)
        self.weight_emergency = getattr(config, 'PENALTY_WEIGHT_EMERGENCY', 2.5)
        self.weight_overtime = getattr(config, 'PENALTY_WEIGHT_OVERTIME', 1.5)

    def generate(self, start_date: date, days: int, officers_data: list[dict], shifts_data: list[dict]) -> dict:
        """
        Generate roster over planning horizon.
        """
        assignments = []
        shortfalls = []
        
        # Initialize internal state trackers per officer
        trackers = {}
        for off in officers_data:
            trackers[off['id']] = {
                'id': off['id'],
                'badge_number': off.get('badge_number', ''),
                'full_name': off.get('full_name', ''),
                'is_active': off.get('is_active', True),
                'approved_leave_dates': set(off.get('approved_leaves', [])),
                'assigned_dates': set(),
                'total_hours': float(off.get('historical_hours', 0.0)),
                'consecutive_days': int(off.get('historical_consecutive', 0)),
                'night_shifts_count': int(off.get('historical_nights', 0)),
                'emergency_duties_count': int(off.get('historical_emergencies', 0)),
                'overtime_hours': float(off.get('historical_overtime', 0.0)),
                'last_shift_end_dt': off.get('last_shift_end_dt', None)
            }

        end_date = start_date + timedelta(days=days)
        current_day = start_date

        while current_day < end_date:
            day_str = current_day.strftime('%Y-%m-%d')
            officers_assigned_today = set()

            for shift in shifts_data:
                shift_id = shift['id']
                shift_name = shift['name']
                shift_type = shift.get('shift_type', 'MORNING')
                required_count = int(shift.get('required_staffing', 1))
                duration = float(shift.get('duration_hours', 8.0))

                # Parse start & end datetime for shift on current_day
                start_t = shift.get('start_time')
                end_t = shift.get('end_time')

                if isinstance(start_t, str):
                    start_t = datetime.strptime(start_t, '%H:%M:%S').time() if len(start_t.split(':')) == 3 else datetime.strptime(start_t, '%H:%M').time()
                if isinstance(end_t, str):
                    end_t = datetime.strptime(end_t, '%H:%M:%S').time() if len(end_t.split(':')) == 3 else datetime.strptime(end_t, '%H:%M').time()

                shift_start_dt = datetime.combine(current_day, start_t)
                
                # Check overnight shift
                if end_t <= start_t:
                    shift_end_dt = datetime.combine(current_day + timedelta(days=1), end_t)
                else:
                    shift_end_dt = datetime.combine(current_day, end_t)

                is_night = (shift_type.upper() == 'NIGHT') or (start_t.hour >= 20 or start_t.hour < 5)

                # Filter candidate list
                candidates = []
                for off_id, tracker in trackers.items():
                    satisfied, reason = is_hard_constraint_satisfied(
                        is_active=tracker['is_active'],
                        shift_date=current_day,
                        shift_start_dt=shift_start_dt,
                        shift_duration=duration,
                        approved_leave_dates=tracker['approved_leave_dates'],
                        assigned_dates=tracker['assigned_dates'],
                        last_shift_end_dt=tracker['last_shift_end_dt'],
                        current_consecutive=tracker['consecutive_days'],
                        current_weekly_hours=tracker['total_hours'],
                        min_rest_hours=self.min_rest_hours,
                        max_consecutive_days=self.max_consecutive_days,
                        max_weekly_hours=self.max_weekly_hours
                    )

                    if not satisfied:
                        continue

                    # Soft penalty evaluation
                    penalty_result = calculate_candidate_penalty(
                        total_hours=tracker['total_hours'],
                        consecutive_days=tracker['consecutive_days'],
                        night_shifts_count=tracker['night_shifts_count'],
                        emergency_duties_count=tracker['emergency_duties_count'],
                        overtime_hours=tracker['overtime_hours'],
                        is_assigning_night_shift=is_night,
                        weight_workload=self.weight_workload,
                        weight_consecutive=self.weight_consecutive,
                        weight_night=self.weight_night,
                        weight_emergency=self.weight_emergency,
                        weight_overtime=self.weight_overtime
                    )

                    candidates.append({
                        'officer_id': off_id,
                        'tracker': tracker,
                        'penalty': penalty_result['total_penalty'],
                        'breakdown': penalty_result['breakdown']
                    })

                # Sort candidate list by soft penalty (lowest score preferred)
                candidates.sort(key=lambda x: x['penalty'])

                # Assign required candidates or record shortfall
                assigned_this_shift = candidates[:required_count]
                actual_assigned_count = len(assigned_this_shift)

                for c in assigned_this_shift:
                    off_id = c['officer_id']
                    t = c['tracker']
                    
                    # Record assignment
                    assignments.append({
                        'officer_id': off_id,
                        'officer_name': t['full_name'],
                        'badge_number': t['badge_number'],
                        'shift_id': shift_id,
                        'shift_name': shift_name,
                        'shift_type': shift_type,
                        'date': day_str,
                        'start_datetime': shift_start_dt.isoformat(),
                        'end_datetime': shift_end_dt.isoformat(),
                        'penalty_score': c['penalty'],
                        'penalty_breakdown': c['breakdown']
                    })

                    # Update officer's tracking state
                    t['total_hours'] += duration
                    t['consecutive_days'] += 1
                    t['assigned_dates'].add(day_str)
                    t['last_shift_end_dt'] = shift_end_dt
                    if is_night:
                        t['night_shifts_count'] += 1

                    officers_assigned_today.add(off_id)

                # Check for staffing shortfall
                if actual_assigned_count < required_count:
                    uncovered = required_count - actual_assigned_count
                    shortfalls.append({
                        'date': day_str,
                        'shift_id': shift_id,
                        'shift_name': shift_name,
                        'required_count': required_count,
                        'assigned_count': actual_assigned_count,
                        'uncovered_count': uncovered,
                        'message': f"Shift '{shift_name}' on {day_str} requires {required_count} officers, but only {actual_assigned_count} eligible officers were available."
                    })

            # Reset consecutive days for officers unassigned today (rest day)
            for off_id, tracker in trackers.items():
                if off_id not in officers_assigned_today:
                    tracker['consecutive_days'] = 0

            current_day += timedelta(days=1)

        # Build workload risk assessments for all officers
        from core.simulator import calculate_workload_risk
        risk_assessments = []
        for off_id, tracker in trackers.items():
            risk_info = calculate_workload_risk(
                total_hours=tracker['total_hours'],
                consecutive_days=tracker['consecutive_days'],
                night_shifts_count=tracker['night_shifts_count'],
                emergency_duties_count=tracker['emergency_duties_count'],
                overtime_hours=tracker['overtime_hours']
            )
            risk_assessments.append({
                'officer_id': off_id,
                'full_name': tracker['full_name'],
                'badge_number': tracker['badge_number'],
                'total_hours': tracker['total_hours'],
                'consecutive_days': tracker['consecutive_days'],
                'night_shifts_count': tracker['night_shifts_count'],
                'emergency_duties_count': tracker['emergency_duties_count'],
                'overtime_hours': tracker['overtime_hours'],
                'risk_level': risk_info['risk_level'],
                'risk_score': risk_info['risk_score'],
                'reasoning': risk_info['reasoning']
            })

        return {
            'status': 'SUCCESS',
            'assignments': assignments,
            'shortfalls': shortfalls,
            'risk_assessments': risk_assessments,
            'summary': {
                'total_assignments': len(assignments),
                'total_shortfalls': len(shortfalls),
                'planning_days': days,
                'high_risk_officers_count': sum(1 for r in risk_assessments if r['risk_level'] in ['HIGH', 'CRITICAL'])
            }
        }
