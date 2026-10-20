import sys
import os
from datetime import date, time, datetime, timedelta
from app import create_app
from app.models import db, User, Officer, Department, Shift, LeaveRequest, Attendance, EmergencyDuty, BurnoutAssessment

app = create_app()

def seed_database():
    with app.app_context():
        db.create_all()

        if User.query.first():
            print("Database already contains data. Skipping auto-seeding.")
            return

        print("Seeding database with realistic demonstration data...")

        # 1. Departments
        d1 = Department(code='CP-01', name='Central Precinct', description='Main city precinct handling general patrol and emergency response', location='100 Metro Plaza')
        d2 = Department(code='HP-02', name='Traffic & Highway Patrol', description='Specialized highway surveillance and traffic enforcement unit', location='45 Highway Boulevard')
        d3 = Department(code='SO-03', name='Special Operations', description='Tactical emergency response and crowd management division', location='12 Security Complex')

        db.session.add_all([d1, d2, d3])
        db.session.commit()

        # 2. Officers (Fictional Demo Officers O001 - O008)
        o1 = Officer(badge_number='O001', first_name='James', last_name='Miller', rank='Constable', department_id=d1.id, is_active=True, phone='555-0101', email='james.miller@police.gov', date_joined=date(2021, 3, 15))
        o2 = Officer(badge_number='O002', first_name='Sarah', last_name='Jenkins', rank='Sergeant', department_id=d1.id, is_active=True, phone='555-0102', email='sarah.jenkins@police.gov', date_joined=date(2019, 6, 10))
        o3 = Officer(badge_number='O003', first_name='David', last_name='Vance', rank='Constable', department_id=d1.id, is_active=True, phone='555-0103', email='david.vance@police.gov', date_joined=date(2022, 1, 20))
        o4 = Officer(badge_number='O004', first_name='Alex', last_name='Rivera', rank='Constable', department_id=d2.id, is_active=True, phone='555-0104', email='alex.rivera@police.gov', date_joined=date(2020, 11, 5))
        o5 = Officer(badge_number='O005', first_name='Marcus', last_name='Chen', rank='Senior Constable', department_id=d2.id, is_active=True, phone='555-0105', email='marcus.chen@police.gov', date_joined=date(2018, 9, 12))
        o6 = Officer(badge_number='O006', first_name='Robert', last_name='Taylor', rank='Inspector', department_id=d3.id, is_active=True, phone='555-0106', email='robert.taylor@police.gov', date_joined=date(2015, 4, 1))
        o7 = Officer(badge_number='O007', first_name='Elena', last_name='Rostova', rank='Constable', department_id=d1.id, is_active=True, phone='555-0107', email='elena.rostova@police.gov', date_joined=date(2023, 2, 18))
        o8 = Officer(badge_number='O008', first_name='Thomas', last_name='Wright', rank='Constable', department_id=d1.id, is_active=False, phone='555-0108', email='thomas.wright@police.gov', date_joined=date(2021, 8, 22))

        db.session.add_all([o1, o2, o3, o4, o5, o6, o7, o8])
        db.session.commit()

        # 3. User Accounts
        # Admin
        u_admin = User(username='admin', email='admin@police.gov', role='ADMIN')
        u_admin.set_password('admin123')

        # Supervisor
        u_sup = User(username='supervisor', email='supervisor@police.gov', role='SUPERVISOR', officer_id=o2.id)
        u_sup.set_password('super123')

        # Officer Users
        u_o1 = User(username='officer1', email='officer1@police.gov', role='OFFICER', officer_id=o1.id)
        u_o1.set_password('officer123')

        u_o3 = User(username='officer3', email='officer3@police.gov', role='OFFICER', officer_id=o3.id)
        u_o3.set_password('officer123')

        u_o4 = User(username='officer4', email='officer4@police.gov', role='OFFICER', officer_id=o4.id)
        u_o4.set_password('officer123')

        u_o7 = User(username='officer7', email='officer7@police.gov', role='OFFICER', officer_id=o7.id)
        u_o7.set_password('officer123')

        db.session.add_all([u_admin, u_sup, u_o1, u_o3, u_o4, u_o7])
        db.session.commit()

        # 4. Shifts
        s_morn = Shift(name='Morning Shift', shift_type='MORNING', start_time=time(6, 0), end_time=time(14, 0), duration_hours=8.0, required_staffing=2, department_id=d1.id)
        s_eve = Shift(name='Evening Shift', shift_type='EVENING', start_time=time(14, 0), end_time=time(22, 0), duration_hours=8.0, required_staffing=2, department_id=d1.id)
        s_night = Shift(name='Night Shift', shift_type='NIGHT', start_time=time(22, 0), end_time=time(6, 0), duration_hours=8.0, required_staffing=1, department_id=d1.id)

        db.session.add_all([s_morn, s_eve, s_night])
        db.session.commit()

        # 5. Leave Requests
        l1 = LeaveRequest(officer_id=o7.id, start_date=date.today() + timedelta(days=2), end_date=date.today() + timedelta(days=4), reason='Annual Leave', status='APPROVED', reviewed_by=u_sup.id, reviewed_at=datetime.utcnow())
        l2 = LeaveRequest(officer_id=o3.id, start_date=date.today() + timedelta(days=5), end_date=date.today() + timedelta(days=6), reason='Family Commitment', status='PENDING')
        l3 = LeaveRequest(officer_id=o4.id, start_date=date.today() - timedelta(days=2), end_date=date.today() - timedelta(days=1), reason='Personal Leave', status='REJECTED', reviewed_by=u_sup.id, reviewed_at=datetime.utcnow())

        db.session.add_all([l1, l2, l3])
        db.session.commit()

        # 6. Emergency Duties
        e1 = EmergencyDuty(officer_id=o2.id, date=date.today() - timedelta(days=1), start_time=time(18, 0), end_time=time(22, 0), duration_hours=4.0, reason='Downtown Public Event Security Reinforcement', logged_by=u_sup.id)
        e2 = EmergencyDuty(officer_id=o5.id, date=date.today() - timedelta(days=2), start_time=time(20, 0), end_time=time(0, 0), duration_hours=4.0, reason='Severe Storm Emergency Traffic Control', logged_by=u_sup.id)

        db.session.add_all([e1, e2])
        db.session.commit()

        # 7. Initial Burnout Assessments
        today = date.today()
        b1 = BurnoutAssessment(officer_id=o1.id, assessment_date=today, total_hours=32.0, overtime_hours=0.0, consecutive_days=3, night_shifts_count=0, emergency_duties_count=0, risk_level='LOW', risk_score=15, reasoning='Workload parameters are within standard baseline limits.')
        b2 = BurnoutAssessment(officer_id=o2.id, assessment_date=today, total_hours=46.0, overtime_hours=6.0, consecutive_days=5, night_shifts_count=2, emergency_duties_count=1, risk_level='HIGH', risk_score=72, reasoning='High weekly hours (46h) and 5 consecutive working days.')
        b3 = BurnoutAssessment(officer_id=o3.id, assessment_date=today, total_hours=54.0, overtime_hours=10.0, consecutive_days=6, night_shifts_count=3, emergency_duties_count=0, risk_level='CRITICAL', risk_score=92, reasoning='Critical weekly hours (54h) and 6 consecutive days reached limit.')
        b4 = BurnoutAssessment(officer_id=o4.id, assessment_date=today, total_hours=40.0, overtime_hours=2.0, consecutive_days=4, night_shifts_count=1, emergency_duties_count=0, risk_level='MODERATE', risk_score=40, reasoning='Workload is moderate with 4 consecutive working days.')

        db.session.add_all([b1, b2, b3, b4])
        db.session.commit()

        print("Seed data creation completed successfully.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    if '--seed' in sys.argv:
        seed_database()

    # Auto seed if empty
    with app.app_context():
        if not User.query.first():
            seed_database()

    print("Starting Automated Police Roster & Burnout Management System...")
    app.run(host='0.0.0.0', port=5000, debug=True)
