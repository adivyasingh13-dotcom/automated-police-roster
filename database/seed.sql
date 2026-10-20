-- AUTOMATED POLICE ROSTER AND BURNOUT MANAGEMENT SYSTEM
-- Seed Data SQL Script

-- 1. Departments
INSERT INTO departments (id, code, name, description, location) VALUES
(1, 'CP-01', 'Central Station', 'Main city precinct handling general patrol and emergency responses', '100 Metro Plaza'),
(2, 'HP-02', 'Traffic & Highway Patrol', 'Specialized highway surveillance and traffic enforcement unit', '45 Highway Boulevard'),
(3, 'SO-03', 'Special Operations', 'Tactical emergency response and crowd management division', '12 Security Complex');

-- 2. Officers (Fictional Demo Officers O001 - O008)
INSERT INTO officers (id, badge_number, first_name, last_name, rank, department_id, is_active, phone, email, date_joined) VALUES
(1, 'O001', 'James', 'Miller', 'Constable', 1, 1, '555-0101', 'james.miller@police.gov', '2021-03-15'),
(2, 'O002', 'Sarah', 'Jenkins', 'Sergeant', 1, 1, '555-0102', 'sarah.jenkins@police.gov', '2019-06-10'),
(3, 'O003', 'David', 'Vance', 'Constable', 1, 1, '555-0103', 'david.vance@police.gov', '2022-01-20'),
(4, 'O004', 'Alex', 'Rivera', 'Constable', 2, 1, '555-0104', 'alex.rivera@police.gov', '2020-11-05'),
(5, 'O005', 'Marcus', 'Chen', 'Senior Constable', 2, 1, '555-0105', 'marcus.chen@police.gov', '2018-09-12'),
(6, 'O006', 'Robert', 'Taylor', 'Inspector', 3, 1, '555-0106', 'robert.taylor@police.gov', '2015-04-01'),
(7, 'O007', 'Elena', 'Rostova', 'Constable', 1, 1, '555-0107', 'elena.rostova@police.gov', '2023-02-18'),
(8, 'O008', 'Thomas', 'Wright', 'Constable', 1, 0, '555-0108', 'thomas.wright@police.gov', '2021-08-22'); -- Inactive Officer

-- 3. Users (Passwords hashed via Werkzeug generate_password_hash in python initializer)
-- Admin: admin@police.gov / admin123
-- Supervisor: supervisor@police.gov / super123
-- Officer 1: officer1@police.gov / officer123

-- 4. Shifts
INSERT INTO shifts (id, name, shift_type, start_time, end_time, duration_hours, required_staffing, department_id) VALUES
(1, 'Morning Shift', 'MORNING', '06:00:00', '14:00:00', 8.0, 2, 1),
(2, 'Evening Shift', 'EVENING', '14:00:00', '22:00:00', 8.0, 2, 1),
(3, 'Night Shift', 'NIGHT', '22:00:00', '06:00:00', 8.0, 1, 1);

-- 5. Leave Requests
INSERT INTO leave_requests (id, officer_id, start_date, end_date, reason, status) VALUES
(1, 7, '2026-09-22', '2026-09-24', 'Annual Leave', 'APPROVED'),
(2, 3, '2026-09-25', '2026-09-26', 'Personal Family Leave', 'PENDING'),
(3, 4, '2026-09-18', '2026-09-19', 'Medical Checkup', 'REJECTED');

-- 6. Emergency Duties
INSERT INTO emergency_duties (id, officer_id, date, start_time, end_time, duration_hours, reason) VALUES
(1, 2, '2026-09-18', '18:00:00', '22:00:00', 4.0, 'Downtown Public Event Security Reinforcement'),
(2, 5, '2026-09-17', '20:00:00', '00:00:00', 4.0, 'Severe Storm Emergency Traffic Control');

-- 7. Workload Risk Initial Assessment
INSERT INTO burnout_assessments (officer_id, assessment_date, total_hours, overtime_hours, consecutive_days, night_shifts_count, emergency_duties_count, risk_level, risk_score, reasoning) VALUES
(1, '2026-09-19', 32.0, 0.0, 3, 0, 0, 'LOW', 15, 'Workload parameters are within standard baseline limits.'),
(2, '2026-09-19', 46.0, 6.0, 5, 2, 1, 'HIGH', 72, 'High weekly hours (46h) and 5 consecutive working days.'),
(3, '2026-09-19', 54.0, 10.0, 6, 3, 0, 'CRITICAL', 92, 'Critical weekly hours (54h) and 6 consecutive days reached limit.'),
(4, '2026-09-19', 40.0, 2.0, 4, 1, 0, 'MODERATE', 40, 'Workload is moderate with 4 consecutive working days.'),
(5, '2026-09-19', 42.0, 4.0, 4, 2, 1, 'MODERATE', 45, 'Assigned to emergency duty with moderate night shifts.');
