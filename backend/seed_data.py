"""
Database seeding script - populates demo data for testing
Run after database tables are created:
  python seed_data.py
"""

import sys
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path to import models
sys.path.insert(0, '.')

from database import SessionLocal, init_db, engine
from models import (
    Member, Staff, MemberPlan, Membership, Class, Machine,
    MemberStatus, StaffRole, MachineCategory, MachineStatus, MemberPlanType
)
from auth import hash_password


def seed_database():
    """
    Populate database with demo data
    """
    # Initialize database (create tables)
    init_db()
    
    db = SessionLocal()
    
    try:
        print("🌱 Starting database seeding...")
        
        # ============ Create Staff Accounts ============
        print("📝 Creating staff accounts...")
        
        staff_data = [
            {
                'first_name': 'Admin',
                'last_name': 'Manager',
                'email': 'manager@gym.com',
                'role': StaffRole.MANAGER,
                'password': 'password123'
            },
            {
                'first_name': 'John',
                'last_name': 'Trainer',
                'email': 'trainer@gym.com',
                'role': StaffRole.TRAINER,
                'password': 'password123'
            },
            {
                'first_name': 'Jane',
                'last_name': 'Reception',
                'email': 'reception@gym.com',
                'role': StaffRole.RECEPTION,
                'password': 'password123'
            }
        ]
        
        staff_accounts = []
        for staff_info in staff_data:
            staff = Staff(
                first_name=staff_info['first_name'],
                last_name=staff_info['last_name'],
                email=staff_info['email'],
                role=staff_info['role'],
                password_hash=hash_password(staff_info['password']),
                is_active=True
            )
            db.add(staff)
            staff_accounts.append(staff)
        
        db.commit()
        print(f"✅ Created {len(staff_accounts)} staff accounts")
        
        # ============ Create Member Plans ============
        print("📋 Creating membership plans...")
        
        plans_data = [
            {'type': MemberPlanType.BASIC, 'price': 29.99, 'duration': 1},
            {'type': MemberPlanType.PREMIUM, 'price': 49.99, 'duration': 1},
            {'type': MemberPlanType.VIP, 'price': 79.99, 'duration': 1},
        ]
        
        plans = []
        for plan_info in plans_data:
            plan = MemberPlan(
                type=plan_info['type'],
                price=plan_info['price'],
                duration=plan_info['duration'],
                description=f"{plan_info['type'].value} Membership"
            )
            db.add(plan)
            plans.append(plan)
        
        db.commit()
        print(f"✅ Created {len(plans)} membership plans")
        
        # ============ Create Sample Members ============
        print("👥 Creating sample members...")
        
        members_data = [
            {'first_name': 'Alice', 'last_name': 'Smith', 'email': 'alice@example.com', 'phone': '5551001001'},
            {'first_name': 'Bob', 'last_name': 'Johnson', 'email': 'bob@example.com', 'phone': '5551001002'},
            {'first_name': 'Carol', 'last_name': 'Williams', 'email': 'carol@example.com', 'phone': '5551001003'},
            {'first_name': 'David', 'last_name': 'Brown', 'email': 'david@example.com', 'phone': '5551001004'},
            {'first_name': 'Eve', 'last_name': 'Davis', 'email': 'eve@example.com', 'phone': '5551001005'},
        ]
        
        members = []
        for member_info in members_data:
            member = Member(
                first_name=member_info['first_name'],
                last_name=member_info['last_name'],
                email=member_info['email'],
                phone_number=member_info['phone'],
                birth_date=date(1990, 1, 1),
                status=MemberStatus.ACTIVE
            )
            db.add(member)
            members.append(member)
        
        db.commit()
        print(f"✅ Created {len(members)} members")
        
        # ============ Create Memberships ============
        print("💳 Creating memberships...")
        
        memberships = []
        for i, member in enumerate(members):
            plan = plans[i % len(plans)]
            start_date = date.today()
            end_date = start_date + timedelta(days=plan.duration * 30)
            
            membership = Membership(
                member_id=member.member_id,
                plan_id=plan.plan_id,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            db.add(membership)
            memberships.append(membership)
        
        db.commit()
        print(f"✅ Created {len(memberships)} memberships")
        
        # ============ Create Classes ============
        print("🏋️ Creating fitness classes...")
        
        trainer = staff_accounts[1]  # John Trainer
        
        classes_data = [
            {
                'name': 'Morning Yoga',
                'type': 'Yoga',
                'capacity': 20,
                'start_time': datetime.now().replace(hour=7, minute=0, second=0),
                'end_time': datetime.now().replace(hour=8, minute=0, second=0),
            },
            {
                'name': 'HIIT Training',
                'type': 'Cardio',
                'capacity': 15,
                'start_time': datetime.now().replace(hour=17, minute=0, second=0),
                'end_time': datetime.now().replace(hour=18, minute=0, second=0),
            },
            {
                'name': 'Strength Training',
                'type': 'Strength',
                'capacity': 12,
                'start_time': datetime.now().replace(hour=18, minute=0, second=0),
                'end_time': datetime.now().replace(hour=19, minute=0, second=0),
            },
        ]
        
        classes = []
        for class_info in classes_data:
            cls = Class(
                trainer_id=trainer.staff_id,
                class_name=class_info['name'],
                type=class_info['type'],
                capacity=class_info['capacity'],
                start_time=class_info['start_time'],
                end_time=class_info['end_time']
            )
            db.add(cls)
            classes.append(cls)
        
        db.commit()
        print(f"✅ Created {len(classes)} classes")
        
        # ============ Enroll Members in Classes ============
        print("📚 Enrolling members in classes...")
        
        for i, cls in enumerate(classes):
            for member in members[:3]:  # Enroll first 3 members
                if member not in cls.members:
                    cls.members.append(member)
        
        db.commit()
        print(f"✅ Enrolled members in classes")
        
        # ============ Create Machines ============
        print("🏃 Creating fitness machines...")
        
        machines_data = [
            {'name': 'Treadmill 1', 'category': MachineCategory.CARDIO},
            {'name': 'Treadmill 2', 'category': MachineCategory.CARDIO},
            {'name': 'Stationary Bike', 'category': MachineCategory.CARDIO},
            {'name': 'Bench Press', 'category': MachineCategory.STRENGTH},
            {'name': 'Squat Rack', 'category': MachineCategory.STRENGTH},
            {'name': 'Rowing Machine', 'category': MachineCategory.CARDIO},
            {'name': 'Medicine Balls', 'category': MachineCategory.FUNCTIONAL},
            {'name': 'TRX System', 'category': MachineCategory.FUNCTIONAL},
        ]
        
        machines = []
        for machine_info in machines_data:
            machine = Machine(
                machine_name=machine_info['name'],
                category=machine_info['category'],
                purchase_date=date.today() - timedelta(days=365),
                status=MachineStatus.AVAILABLE if len(machines) % 3 != 0 else MachineStatus.MAINTENANCE
            )
            db.add(machine)
            machines.append(machine)
        
        db.commit()
        print(f"✅ Created {len(machines)} machines")
        
        print("\n✨ Database seeding completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Staff accounts: {len(staff_accounts)}")
        print(f"   - Members: {len(members)}")
        print(f"   - Membership plans: {len(plans)}")
        print(f"   - Classes: {len(classes)}")
        print(f"   - Machines: {len(machines)}")
        print("\n🔐 Demo Login Credentials:")
        print("   - Manager: manager@gym.com / password123")
        print("   - Trainer: trainer@gym.com / password123")
        print("   - Reception: reception@gym.com / password123")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_database()
