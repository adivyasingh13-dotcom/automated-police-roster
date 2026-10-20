def calculate_candidate_penalty(
    total_hours: float,
    consecutive_days: int,
    night_shifts_count: int,
    emergency_duties_count: int,
    overtime_hours: float,
    is_assigning_night_shift: bool = False,
    weight_workload: float = 1.0,
    weight_consecutive: float = 2.0,
    weight_night: float = 3.0,
    weight_emergency: float = 2.5,
    weight_overtime: float = 1.5
) -> dict:
    """
    Transparent soft penalty scoring system for candidate preference ordering.
    Lower penalty score indicates a candidate with lower operational burden.
    """
    p_workload = total_hours * weight_workload
    p_consecutive = (consecutive_days ** 2) * weight_consecutive
    p_night = night_shifts_count * weight_night
    p_emergency = emergency_duties_count * weight_emergency
    p_overtime = overtime_hours * weight_overtime
    
    p_additional_night = 5.0 * (night_shifts_count + 1) if is_assigning_night_shift else 0.0

    total_penalty = p_workload + p_consecutive + p_night + p_emergency + p_overtime + p_additional_night

    return {
        'total_penalty': round(total_penalty, 2),
        'breakdown': {
            'workload_penalty': round(p_workload, 2),
            'consecutive_day_penalty': round(p_consecutive, 2),
            'night_shift_penalty': round(p_night, 2),
            'emergency_duty_penalty': round(p_emergency, 2),
            'overtime_penalty': round(p_overtime, 2),
            'additional_night_penalty': round(p_additional_night, 2)
        }
    }
