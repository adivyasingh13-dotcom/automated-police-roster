import pytest
from datetime import date, time, datetime
from core.engine import RosterGenerator
from core.simulator import validate_supervisor_override

def test_staffing_shortfall_handling():
    """
    Scenario 4: Required = 2 officers, but only 1 eligible candidate exists.
    System should assign the 1 eligible officer and record a staffing shortfall without crashing.
    """
    generator = RosterGenerator()
    start_date = date(2026, 9, 20)
    
    officers_data = [
        {
            'id': 1,
            'badge_number': 'O001',
            'full_name': 'Officer 1',
            'is_active': True,
            'approved_leaves': [],
            'historical_hours': 0.0,
            'historical_consecutive': 0,
            'historical_nights': 0,
            'historical_emergencies': 0,
            'last_shift_end_dt': None
        }
    ]

    shifts_data = [
        {
            'id': 1,
            'name': 'Morning Patrol',
            'shift_type': 'MORNING',
            'start_time': time(6, 0),
            'end_time': time(14, 0),
            'duration_hours': 8.0,
            'required_staffing': 2 # Requires 2, but only 1 officer available
        }
    ]

    result = generator.generate(start_date=start_date, days=1, officers_data=officers_data, shifts_data=shifts_data)

    assert result['status'] == 'SUCCESS'
    assert len(result['assignments']) == 1
    assert len(result['shortfalls']) == 1
    assert result['shortfalls'][0]['uncovered_count'] == 1
    assert "requires 2 officers, but only 1 eligible" in result['shortfalls'][0]['message']

def test_supervisor_override_validation():
    """
    Scenario 5: Supervisor manually replaces an officer in a shift.
    Validator checks hard constraints and calculates projected risk.
    """
    assignment_to_replace = {
        'officer_id': 1,
        'date': '2026-09-20',
        'start_datetime': '2026-09-20T06:00:00',
        'end_datetime': '2026-09-20T14:00:00',
        'shift_type': 'MORNING'
    }

    new_officer = {
        'id': 2,
        'full_name': 'Officer 2',
        'is_active': True,
        'approved_leaves': [],
        'historical_hours': 20.0,
        'historical_consecutive': 2
    }

    all_officers = [
        {'id': 1, 'full_name': 'Officer 1', 'badge_number': 'O001', 'is_active': True},
        {'id': 2, 'full_name': 'Officer 2', 'badge_number': 'O002', 'is_active': True}
    ]

    validation = validate_supervisor_override(
        assignment_to_replace=assignment_to_replace,
        new_officer=new_officer,
        all_officers=all_officers,
        existing_assignments=[]
    )

    assert validation['is_valid'] is True
    assert 'projected_risk' in validation
    assert validation['projected_risk']['risk_level'] in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
