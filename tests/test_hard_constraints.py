import pytest
from datetime import datetime, date, time
from core.constraints import (
    check_active_status,
    check_leave,
    check_daily_overlap,
    check_rest_period,
    check_consecutive_days,
    check_max_hours,
    is_hard_constraint_satisfied
)

def test_inactive_officer_rejected():
    satisfied, reason = check_active_status(is_active=False)
    assert satisfied is False
    assert "inactive" in reason.lower()

def test_approved_leave_conflict():
    leave_dates = {'2026-09-20', '2026-09-21'}
    satisfied, reason = check_leave('2026-09-20', leave_dates)
    assert satisfied is False
    assert "approved leave" in reason.lower()

    satisfied, _ = check_leave('2026-09-22', leave_dates)
    assert satisfied is True

def test_daily_overlap_rejection():
    assigned_dates = {'2026-09-20'}
    satisfied, reason = check_daily_overlap('2026-09-20', assigned_dates)
    assert satisfied is False
    assert "already assigned" in reason.lower()

def test_insufficient_rest_period_night_to_morning():
    """
    Scenario 2: Officer works Night shift 22:00-06:00 (ends 2026-09-21 06:00:00).
    Next Morning shift starts 2026-09-21 06:00:00. Rest = 0 hours < 11 hours -> MUST FAIL.
    """
    last_shift_end = datetime(2026, 9, 21, 6, 0, 0)
    next_shift_start = datetime(2026, 9, 21, 6, 0, 0)

    satisfied, reason = check_rest_period(next_shift_start, last_shift_end, min_rest_hours=11.0)
    assert satisfied is False
    assert "Insufficient rest" in reason

def test_insufficient_rest_period_night_to_evening():
    """
    Night shift ends 2026-09-21 06:00:00.
    Next Evening shift starts 2026-09-21 14:00:00. Rest = 8 hours < 11 hours -> MUST FAIL.
    """
    last_shift_end = datetime(2026, 9, 21, 6, 0, 0)
    next_shift_start = datetime(2026, 9, 21, 14, 0, 0)

    satisfied, reason = check_rest_period(next_shift_start, last_shift_end, min_rest_hours=11.0)
    assert satisfied is False
    assert "8.0 hours rest" in reason

def test_consecutive_days_limit():
    satisfied, reason = check_consecutive_days(current_consecutive=6, max_consecutive_days=6)
    assert satisfied is False
    assert "Maximum consecutive" in reason

    satisfied, _ = check_consecutive_days(current_consecutive=4, max_consecutive_days=6)
    assert satisfied is True

def test_max_weekly_hours_cap():
    satisfied, reason = check_max_hours(current_weekly_hours=42.0, shift_duration=8.0, max_weekly_hours=48.0)
    assert satisfied is False
    assert "Exceeds max weekly hours" in reason

    satisfied, _ = check_max_hours(current_weekly_hours=38.0, shift_duration=8.0, max_weekly_hours=48.0)
    assert satisfied is True
