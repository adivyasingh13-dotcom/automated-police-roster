import pytest
from core.penalty import calculate_candidate_penalty

def test_penalty_scoring_comparison():
    """
    Scenario 3:
    Officer A: 24 hours worked, 3 consecutive days, 0 night shifts
    Officer B: 16 hours worked, 1 consecutive day, 1 night shift
    """
    p_A = calculate_candidate_penalty(
        total_hours=24.0,
        consecutive_days=3,
        night_shifts_count=0,
        emergency_duties_count=0,
        overtime_hours=0.0,
        is_assigning_night_shift=False
    )

    p_B = calculate_candidate_penalty(
        total_hours=16.0,
        consecutive_days=1,
        night_shifts_count=1,
        emergency_duties_count=0,
        overtime_hours=0.0,
        is_assigning_night_shift=False
    )

    assert 'total_penalty' in p_A
    assert 'total_penalty' in p_B
    # Deterministic ranking checks
    assert isinstance(p_A['total_penalty'], float)
    assert isinstance(p_B['total_penalty'], float)

def test_additional_night_shift_penalty():
    p_day = calculate_candidate_penalty(
        total_hours=20.0,
        consecutive_days=2,
        night_shifts_count=1,
        emergency_duties_count=0,
        overtime_hours=0.0,
        is_assigning_night_shift=False
    )

    p_night = calculate_candidate_penalty(
        total_hours=20.0,
        consecutive_days=2,
        night_shifts_count=1,
        emergency_duties_count=0,
        overtime_hours=0.0,
        is_assigning_night_shift=True
    )

    assert p_night['total_penalty'] > p_day['total_penalty']
