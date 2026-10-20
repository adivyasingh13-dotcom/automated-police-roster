import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'police-roster-secret-key-super-secure-2026')
    
    # Database Configuration (MySQL / SQLite fallback)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'police_roster.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Roster Scheduling Engine Rules (Hard Constraints)
    MIN_REST_HOURS = int(os.getenv('MIN_REST_HOURS', 11))
    MAX_WEEKLY_HOURS = int(os.getenv('MAX_WEEKLY_HOURS', 48))
    MAX_CONSECUTIVE_DAYS = int(os.getenv('MAX_CONSECUTIVE_DAYS', 6))
    
    # Soft Penalty Scoring Weights (Configurable Heuristic Parameters)
    PENALTY_WEIGHT_WORKLOAD = float(os.getenv('PENALTY_WEIGHT_WORKLOAD', 1.0))
    PENALTY_WEIGHT_CONSECUTIVE = float(os.getenv('PENALTY_WEIGHT_CONSECUTIVE', 2.0))
    PENALTY_WEIGHT_NIGHT = float(os.getenv('PENALTY_WEIGHT_NIGHT', 3.0))
    PENALTY_WEIGHT_EMERGENCY = float(os.getenv('PENALTY_WEIGHT_EMERGENCY', 2.5))
    PENALTY_WEIGHT_OVERTIME = float(os.getenv('PENALTY_WEIGHT_OVERTIME', 1.5))
    
    # Operational Workload Risk Thresholds (Operational Indicators)
    RISK_HOURS_MODERATE = 36
    RISK_HOURS_HIGH = 44
    RISK_HOURS_CRITICAL = 52

    RISK_DAYS_MODERATE = 4
    RISK_DAYS_HIGH = 5
    RISK_DAYS_CRITICAL = 6
