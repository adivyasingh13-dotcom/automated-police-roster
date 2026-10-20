-- AUTOMATED POLICE ROSTER AND BURNOUT MANAGEMENT SYSTEM
-- Relational Database Schema DDL (MySQL & SQLite Compatible)

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    badge_number VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    rank VARCHAR(50) DEFAULT 'Constable',
    department_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    date_joined DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'SUPERVISOR', 'OFFICER')),
    officer_id INTEGER UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    shift_type VARCHAR(20) NOT NULL CHECK (shift_type IN ('MORNING', 'EVENING', 'NIGHT')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_hours REAL NOT NULL DEFAULT 8.0,
    required_staffing INTEGER NOT NULL DEFAULT 2,
    department_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    reviewed_by INTEGER,
    reviewed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS roster_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id INTEGER NOT NULL,
    shift_id INTEGER NOT NULL,
    date DATE NOT NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'PUBLISHED')),
    penalty_score REAL DEFAULT 0.0,
    override_by INTEGER,
    override_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE CASCADE,
    FOREIGN KEY (override_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(officer_id, date)
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id INTEGER NOT NULL,
    date DATE NOT NULL,
    scheduled_shift_id INTEGER,
    check_in DATETIME,
    check_out DATETIME,
    working_hours REAL DEFAULT 0.0,
    overtime_hours REAL DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'PRESENT' CHECK (status IN ('PRESENT', 'ABSENT', 'LATE', 'ON_LEAVE', 'EMERGENCY_DUTY')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE,
    FOREIGN KEY (scheduled_shift_id) REFERENCES shifts(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS emergency_duties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id INTEGER NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_hours REAL NOT NULL,
    reason TEXT NOT NULL,
    logged_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE,
    FOREIGN KEY (logged_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS burnout_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id INTEGER NOT NULL,
    assessment_date DATE NOT NULL,
    total_hours REAL NOT NULL DEFAULT 0.0,
    overtime_hours REAL NOT NULL DEFAULT 0.0,
    consecutive_days INTEGER NOT NULL DEFAULT 0,
    night_shifts_count INTEGER NOT NULL DEFAULT 0,
    emergency_duties_count INTEGER NOT NULL DEFAULT 0,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
    risk_score INTEGER NOT NULL DEFAULT 0,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'GENERAL',
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
