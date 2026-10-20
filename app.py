import os
from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

# Mock dummy data for realistic demonstration (6-8 officers)
MOCK_OFFICERS = [
    {
        "badge": "O001",
        "name": "Constable Officer 1",
        "rank": "Constable",
        "station": "Central Precinct",
        "hours": 32.0,
        "overtime": 0.0,
        "consecutive_days": 3,
        "night_shifts": 0,
        "emergency_duties": 0,
        "pbri_score": 15,
        "risk_level": "Low"
    },
    {
        "badge": "O002",
        "name": "Sergeant Officer 2",
        "rank": "Sergeant",
        "station": "Central Precinct",
        "hours": 46.0,
        "overtime": 6.0,
        "consecutive_days": 5,
        "night_shifts": 2,
        "emergency_duties": 1,
        "pbri_score": 72,
        "risk_level": "High"
    },
    {
        "badge": "O003",
        "name": "Constable Officer 3",
        "rank": "Constable",
        "station": "Central Precinct",
        "hours": 54.0,
        "overtime": 10.0,
        "consecutive_days": 6,
        "night_shifts": 3,
        "emergency_duties": 0,
        "pbri_score": 92,
        "risk_level": "Critical"
    },
    {
        "badge": "O004",
        "name": "Constable Officer 4",
        "rank": "Constable",
        "station": "Highway Patrol",
        "hours": 40.0,
        "overtime": 2.0,
        "consecutive_days": 4,
        "night_shifts": 1,
        "emergency_duties": 0,
        "pbri_score": 40,
        "risk_level": "Moderate"
    },
    {
        "badge": "O005",
        "name": "Senior Constable Officer 5",
        "rank": "Senior Constable",
        "station": "Highway Patrol",
        "hours": 42.0,
        "overtime": 4.0,
        "consecutive_days": 4,
        "night_shifts": 2,
        "emergency_duties": 1,
        "pbri_score": 48,
        "risk_level": "Moderate"
    },
    {
        "badge": "O006",
        "name": "Inspector Officer 6",
        "rank": "Inspector",
        "station": "Special Operations",
        "hours": 36.0,
        "overtime": 0.0,
        "consecutive_days": 2,
        "night_shifts": 0,
        "emergency_duties": 0,
        "pbri_score": 18,
        "risk_level": "Low"
    },
    {
        "badge": "O007",
        "name": "Constable Officer 7",
        "rank": "Constable",
        "station": "Central Precinct",
        "hours": 28.0,
        "overtime": 0.0,
        "consecutive_days": 2,
        "night_shifts": 0,
        "emergency_duties": 0,
        "pbri_score": 12,
        "risk_level": "Low"
    }
]

MOCK_ROSTER = [
    {"date": "2026-09-20", "day": "Monday", "shift": "Morning Shift (06:00 - 14:00)", "shift_type": "Morning", "officer": "Constable Officer 1", "badge": "O001", "status": "Published"},
    {"date": "2026-09-20", "day": "Monday", "shift": "Morning Shift (06:00 - 14:00)", "shift_type": "Morning", "officer": "Sergeant Officer 2", "badge": "O002", "status": "Published"},
    {"date": "2026-09-20", "day": "Monday", "shift": "Evening Shift (14:00 - 22:00)", "shift_type": "Evening", "officer": "Constable Officer 3", "badge": "O003", "status": "Published"},
    {"date": "2026-09-20", "day": "Monday", "shift": "Evening Shift (14:00 - 22:00)", "shift_type": "Evening", "officer": "Constable Officer 4", "badge": "O004", "status": "Published"},
    {"date": "2026-09-20", "day": "Monday", "shift": "Night Shift (22:00 - 06:00)", "shift_type": "Night", "officer": "Senior Constable Officer 5", "badge": "O005", "status": "Published"},
    {"date": "2026-09-21", "day": "Tuesday", "shift": "Morning Shift (06:00 - 14:00)", "shift_type": "Morning", "officer": "Inspector Officer 6", "badge": "O006", "status": "Published"},
    {"date": "2026-09-21", "day": "Tuesday", "shift": "Morning Shift (06:00 - 14:00)", "shift_type": "Morning", "officer": "Constable Officer 7", "badge": "O007", "status": "Published"},
    {"date": "2026-09-21", "day": "Tuesday", "shift": "Evening Shift (14:00 - 22:00)", "shift_type": "Evening", "officer": "Constable Officer 1", "badge": "O001", "status": "Published"},
    {"date": "2026-09-21", "day": "Tuesday", "shift": "Night Shift (22:00 - 06:00)", "shift_type": "Night", "officer": "Constable Officer 4", "badge": "O004", "status": "Published"}
]

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    total_officers = len(MOCK_OFFICERS)
    high_critical_risk = sum(1 for o in MOCK_OFFICERS if o['risk_level'] in ['High', 'Critical'])
    total_overtime = sum(o['overtime'] for o in MOCK_OFFICERS)
    on_leave = 1
    
    risk_counts = {
        'Low': sum(1 for o in MOCK_OFFICERS if o['risk_level'] == 'Low'),
        'Moderate': sum(1 for o in MOCK_OFFICERS if o['risk_level'] == 'Moderate'),
        'High': sum(1 for o in MOCK_OFFICERS if o['risk_level'] == 'High'),
        'Critical': sum(1 for o in MOCK_OFFICERS if o['risk_level'] == 'Critical')
    }

    return render_template(
        'dashboard.html',
        officers=MOCK_OFFICERS,
        roster=MOCK_ROSTER[:5],
        total_officers=total_officers,
        high_critical_risk=high_critical_risk,
        total_overtime=total_overtime,
        on_leave=on_leave,
        risk_counts=risk_counts
    )

@app.route('/roster')
def roster():
    return render_template('roster.html', roster=MOCK_ROSTER)

@app.route('/burnout')
def burnout():
    return render_template('burnout.html', officers=MOCK_OFFICERS)

if __name__ == '__main__':
    print("Starting Police Roster & Workload System Standalone Server...")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(host='127.0.0.1', port=5000, debug=True)
