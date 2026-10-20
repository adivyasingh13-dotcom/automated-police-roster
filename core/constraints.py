from datetime import datetime, timedelta

def check_active_status(is_active: bool) -> tuple[bool, str]:
    """Check if the officer is active."""
    if not is_active:
        return False, "Officer is inactive."
    return True, "Active."

def check_leave(shift_date, approved_leave_dates: set) -> tuple[bool, str]:
    """Check if the officer has approved leave on shift_date."""
    # shift_date can be date object or string 'YYYY-MM-DD'
    date_str = shift_date.strftime('%Y-%m-%d') if hasattr(shift_date, 'strftime') else str(shift_date)
    if date_str in approved_leave_dates:
        return False, f"Officer is on approved leave on {date_str}."
    return True, "No leave conflict."

def check_daily_overlap(shift_date, assigned_dates: set) -> tuple[bool, str]:
    """Check if officer is already assigned a shift on this date."""
    date_str = shift_date.strftime('%Y-%m-%d') if hasattr(shift_date, 'strftime') else str(shift_date)
    if date_str in assigned_dates:
        return False, f"Officer already assigned to a shift on {date_str}."
    return True, "No daily overlap."

def check_rest_period(shift_start_dt: datetime, last_shift_end_dt: datetime, min_rest_hours: float = 11.0) -> tuple[bool, str]:
    """
    Check if minimum rest period between last shift end and next shift start is respected.
    Example: Night shift 22:00-06:00 next day morning 06:00-14:00 has 0 hours rest -> FAILS.
    """
    if last_shift_end_dt is None:
        return True, "First assignment."
    
    rest_duration = (shift_start_dt - last_shift_end_dt).total_seconds() / 3600.0
    if rest_duration < min_rest_hours:
        return False, f"Insufficient rest period ({rest_duration:.1f} hours rest, required: {min_rest_hours:.1f} hours)."
    return True, "Rest period satisfied."

def check_consecutive_days(current_consecutive: int, max_consecutive_days: int = 6) -> tuple[bool, str]:
    """Check if assigning another day exceeds maximum consecutive working days."""
    if current_consecutive >= max_consecutive_days:
        return False, f"Maximum consecutive working days reached ({current_consecutive}/{max_consecutive_days})."
    return True, "Consecutive days limit satisfied."

def check_max_hours(current_weekly_hours: float, shift_duration: float, max_weekly_hours: float = 48.0) -> tuple[bool, str]:
    """Check if assigning this shift exceeds weekly hard working-hour cap."""
    if current_weekly_hours + shift_duration > max_weekly_hours:
        return False, f"Exceeds max weekly hours limit ({current_weekly_hours + shift_duration:.1f}h > {max_weekly_hours:.1f}h)."
    return True, "Working hours limit satisfied."

def is_hard_constraint_satisfied(
    is_active: bool,
    shift_date,
    shift_start_dt: datetime,
    shift_duration: float,
    approved_leave_dates: set,
    assigned_dates: set,
    last_shift_end_dt: datetime,
    current_consecutive: int,
    current_weekly_hours: float,
    min_rest_hours: float = 11.0,
    max_consecutive_days: int = 6,
    max_weekly_hours: float = 48.0
) -> tuple[bool, str]:
    """
    Unified hard constraint checker.
    Returns (True, "OK") if all hard constraints pass, or (False, reason) if any fails.
    """
    ok, msg = check_active_status(is_active)
    if not ok: return False, msg

    ok, msg = check_leave(shift_date, approved_leave_dates)
    if not ok: return False, msg

    ok, msg = check_daily_overlap(shift_date, assigned_dates)
    if not ok: return False, msg

    ok, msg = check_rest_period(shift_start_dt, last_shift_end_dt, min_rest_hours)
    if not ok: return False, msg

    ok, msg = check_consecutive_days(current_consecutive, max_consecutive_days)
    if not ok: return False, msg

    ok, msg = check_max_hours(current_weekly_hours, shift_duration, max_weekly_hours)
    if not ok: return False, msg

    return True, "All hard constraints satisfied."
