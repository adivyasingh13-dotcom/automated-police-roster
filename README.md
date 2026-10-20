# AUTOMATED POLICE ROSTER AND BURNOUT MANAGEMENT SYSTEM

A web-based software engineering system for managing police personnel, station shifts, automated constraint-aware duty rosters, leave applications, attendance, emergency duty callouts, and operational workload-risk indicators.

---

## 1. Project Overview

The **Automated Police Roster and Burnout Management System** is an operational administrative application designed to assist police station supervisors in generating fair, deterministic, and constraint-aware duty rosters while monitoring operational workload accumulation across personnel.

---

## 2. Problem Statement

Manual scheduling in police departments often leads to scheduling conflicts, insufficient rest periods between shifts, illegal quick turnarounds (such as assigning a morning shift immediately after a night shift), and unmonitored consecutive duty days. This project provides an automated rule-based heuristic scheduler and a transparent operational workload-risk calculation engine to prevent operational exhaustion and ensure minimum rest compliance.

---

## 3. Project Objectives

- **Automated Roster Generation**: Eliminate manual scheduling errors using a rule-based greedy heuristic algorithm with hard constraint filtering and soft penalty scoring.
- **Operational Workload Risk Assessment**: Evaluate measurable scheduling factors (working hours, overtime, consecutive days, night shifts, emergency duties) and categorize risk into LOW, MODERATE, HIGH, and CRITICAL indicators.
- **Supervisor Overrides & Revalidation**: Allow manual assignment adjustments while enforcing hard constraint revalidation and future conflict detection.
- **Role-Based Workflows**: Provide dedicated operational portals for Administrators, Station Supervisors, and Police Officers.
- **Reporting & Compliance**: Provide printable operational reports for roster schedules, staffing shortfalls, overtime analysis, and workload audits.

---

## 4. Features & Key Modules

1. **Authentication & RBAC**: Secure login, session management, password hashing, and role protection for Admin, Supervisor, and Officer roles.
2. **Officer Management**: Personnel directory, badge tracking, department assignments, and active/inactive status toggling.
3. **Station & Shift Management**: Configurable station definitions and shift schedules (Morning, Evening, Night).
4. **Leave Management**: Officer leave request submission with supervisor approval/rejection workflows; approved leave acts as a strict scheduling constraint.
5. **Automated Roster Generator**: Deterministic candidate selection over 7 or 14-day horizons with shortfall tracking.
6. **Pre-Publish Simulation & Review**: Draft roster review displaying staffing shortfalls, projected workload risk, and warning banners prior to publishing.
7. **Supervisor Overrides**: Manual reassignment validator detecting rest violations and cascade conflicts.
8. **Attendance & Overtime Tracking**: Check-in/check-out timestamp logging with automatic working hours and overtime calculation.
9. **Emergency Duty Deployments**: Logging unscheduled emergency callouts with instant workload risk recalculation.
10. **In-App Notifications**: Alerts for roster publishing, leave decisions, and high operational workload risk.
11. **Operational Reports**: Print-ready views for rosters, shortfalls, overtime analysis, and workload audits.

---

## 5. User Roles

- **Administrator**:
  - Manage officers, departments/stations, and shift definitions.
  - Configure global system settings and user accounts.
  - View overall system audit metrics and operational reports.

- **Supervisor / Station Head**:
  - Review and approve/reject leave requests.
  - Run the automated roster generation engine.
  - Inspect draft rosters, shortfalls, and projected workload risks.
  - Perform manual assignment overrides and revalidate constraints.
  - Log emergency duty callouts and attendance entries.
  - Publish rosters and broadcast notifications.

- **Police Officer**:
  - View personal duty schedule grid and upcoming shifts.
  - Apply for leave and track request status.
  - View personal operational workload risk indicators.
  - Receive system notifications.

---

## 6. Technology Stack

- **Backend**: Python 3.14+, Flask, Flask-SQLAlchemy, Flask-Login
- **Database**: MySQL / SQLite fallback (PyMySQL driver)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Data Visualization**: Chart.js
- **Testing**: Pytest

---

## 7. Roster Generation Engine & Hard/Soft Constraints

The core component `core.RosterGenerator` uses a **Rule-Based Greedy Heuristic** with **Hard Constraint Filtering** and **Soft Penalty Scoring**:

### Hard Constraints (Mandatory - Zero Violation Allowed):
1. **Active Personnel**: Officer must be active (`is_active == True`).
2. **Approved Leave**: Officer must not have approved leave on the shift date.
3. **Daily Overlap**: Officer cannot be assigned multiple shifts on the same calendar day.
4. **Minimum Rest Period**: Enforces an 11-hour minimum gap between the end of the officer's last assigned shift and the start of the next shift. (e.g., Night shift ending at 06:00 followed by a Morning shift at 06:00 has 0h rest $\rightarrow$ REJECTED).
5. **Maximum Consecutive Days**: Maximum 6 consecutive working days cap.
6. **Maximum Weekly Hours**: Maximum 48-hour hard weekly cap.

### Soft Penalty Scoring (Candidate Ranking):
$$\text{Total Penalty} = (H \times W_h) + (D^2 \times W_d) + (N \times W_n) + (E \times W_e) + (O \times W_o) + P_{night}$$

Where:
- $H$: Accumulated working hours
- $D$: Consecutive working days
- $N$: Accumulated night shift count
- $E$: Emergency duties count
- $O$: Overtime hours
- $P_{night}$: Additional penalty if assigning another night shift

Lower penalty score = Preferred candidate.

---

## 8. Operational Workload-Risk Assessment Criteria

> **Note**: Workload assessment in this system is strictly an **operational workload-risk indicator** based on measurable scheduling parameters and does not represent a medical or psychological diagnosis.

- **LOW**: Workload parameters are within standard baseline limits.
- **MODERATE**: Workload has increased (36–44h or 4 consecutive days) and should be monitored routinely.
- **HIGH**: Workload exceeds standard thresholds (44–52h, 5 consecutive days, or $\ge 3$ night shifts). Rotation recommended.
- **CRITICAL**: Workload significantly exceeds thresholds ($\ge 52$h or 6 consecutive days). Prompt supervisor intervention required.

---

## 9. Installation & Local Setup

### 1. Clone Repository & Setup Environment
```powershell
git clone https://github.com/your-repo/automated-police-roster.git
cd automated-police-roster
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

### 3. Database Initialization & Seeding
To run with SQLite out-of-the-box:
```powershell
python run.py --seed
```

To run with MySQL, configure `DATABASE_URL` in `.env`:
```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/police_roster_db
```
Then execute DDL in `database/schema.sql` and data in `database/seed.sql`.

---

## 10. Running the Application & Tests

### Start Development Server:
```powershell
python run.py
```
Open your browser at `http://localhost:5000`.

### Running Automated Test Suite:
```powershell
python -m pytest tests/ -v
```

---

## 11. Demonstration Credentials

| Role | Username / Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` or `admin@police.gov` | `admin123` |
| **Supervisor** | `supervisor` or `supervisor@police.gov` | `super123` |
| **Police Officer 1** | `officer1` or `officer1@police.gov` | `officer123` |
| **Police Officer 3** | `officer3` or `officer3@police.gov` | `officer123` |

---

## 12. Project Structure

```
automated-police-roster/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── routes/
│   │   ├── admin.py
│   │   ├── attendance.py
│   │   ├── auth.py
│   │   ├── officer.py
│   │   ├── reports.py
│   │   └── supervisor.py
│   ├── services/
│   │   ├── notification_service.py
│   │   ├── roster_service.py
│   │   └── workload_service.py
│   ├── static/
│   │   ├── css/
│   │   │   └── custom.css
│   │   └── js/
│   │       ├── dashboard.js
│   │       └── roster.js
│   └── templates/
│       ├── admin/
│       ├── attendance/
│       ├── auth/
│       ├── dashboard/
│       ├── emergency/
│       ├── errors/
│       ├── leave/
│       ├── officers/
│       ├── reports/
│       ├── roster/
│       ├── workload/
│       └── base.html
├── core/
│   ├── __init__.py
│   ├── constraints.py
│   ├── engine.py
│   ├── penalty.py
│   └── simulator.py
├── database/
│   ├── schema.sql
│   └── seed.sql
├── tests/
│   ├── test_edge_cases.py
│   ├── test_hard_constraints.py
│   └── test_penalty_scoring.py
├── config.py
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 13. Limitations & Future Scope

### Current Limitations:
- The rule-based engine operates deterministically on configured hard/soft parameters without external calendar integrations.
- Notifications are stored within the application database without SMS or external SMTP email gateways.

### Future Scope:
- Integration with biometric hardware attendance devices.
- Mobile native application for officers.
- Multi-precinct cross-station transfer scheduling.
- Real-time SMS alert integration via Twilio API.

---

## 14. Author

**ADIVYA KUMAR SINGH**

## 15. License

Released under the MIT License. See `LICENSE`.
