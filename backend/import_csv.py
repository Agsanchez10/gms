"""
Import data from CSV files into the database.

Run from the backend directory:
    cd backend
    python import_csv.py

Staff accounts are created with the default password: password123
"""
import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, '.')

from database import SessionLocal, init_db
from models import (
    Member, Staff, MemberPlan, Membership, Class, Machine, MachineUsage,
    MemberStatus, StaffRole, MachineCategory, MachineStatus, MemberPlanType,
    class_enrollment_table,
)
from auth import hash_password
from sqlalchemy import text

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data_files'))


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_csv(filename: str):
    with open(f"{DATA_DIR}\\{filename}", newline='', encoding='utf-8') as f:
        return list(csv.reader(f))

def parse_date(s: str, fmt: str = '%m/%d/%Y'):
    return datetime.strptime(s.strip(), fmt).date()

def parse_datetime(date_str: str, time_str: str, date_fmt: str = '%m/%d/%Y'):
    return datetime.strptime(f"{date_str.strip()} {time_str.strip()}", f"{date_fmt} %H:%M:%S")

def parse_datetime_auto(date_str: str, time_str: str):
    """Parse datetime trying ISO (YYYY-MM-DD) then US (M/D/YYYY) date format."""
    d = date_str.strip()
    t = time_str.strip()
    fmt = '%Y-%m-%d' if '-' in d and len(d.split('-')[0]) == 4 else '%m/%d/%Y'
    return datetime.strptime(f"{d} {t}", f"{fmt} %H:%M:%S")

def to_bool(s: str) -> bool:
    return s.strip().upper() == 'TRUE'


# ── Run import ────────────────────────────────────────────────────────────────

db = SessionLocal()

try:
    init_db()
    print("Tables ensured.\n")

    # ── Staff ─────────────────────────────────────────────────────────────────
    # CSV columns: staff_id, first_name, last_name, role, password_hash
    # Generated:   email = firstname.lastname@gym.com
    #              password reset to hash of 'password123'
    print("Importing staff...")
    ROLE_MAP = {
        'MANAGER':   StaffRole.MANAGER,
        'TRAINER':   StaffRole.TRAINER,
        'RECEPTION': StaffRole.RECEPTION,
    }
    default_pw = hash_password('password123')
    for row in read_csv('staff.csv'):
        staff_id, first_name, last_name, role_raw, _ = row
        if db.query(Staff).filter_by(staff_id=int(staff_id)).first():
            print(f"  Skipping staff {staff_id} (already exists)")
            continue
        email = f"{first_name.strip().lower()}.{last_name.strip().lower()}@gym.com"
        db.add(Staff(
            staff_id=int(staff_id),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=ROLE_MAP[role_raw.strip().upper()],
            email=email,
            password_hash=default_pw,
            is_active=True,
        ))
    db.commit()
    print("  Done.\n")

    # ── Members ───────────────────────────────────────────────────────────────
    # CSV columns: member_id, first_name, last_name, phone_number, email,
    #              birth_date, join_date, status
    print("Importing members...")
    STATUS_MAP = {
        'ACTIVE':    MemberStatus.ACTIVE,
        'INACTIVE':  MemberStatus.INACTIVE,
        'SUSPENDED': MemberStatus.SUSPENDED,
    }
    for row in read_csv('member.csv'):
        member_id, first_name, last_name, phone, email, birth_date, join_date, status_raw = row
        if db.query(Member).filter_by(member_id=int(member_id)).first():
            print(f"  Skipping member {member_id} (already exists)")
            continue
        db.add(Member(
            member_id=int(member_id),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone_number=phone.strip(),
            email=email.strip() or None,
            birth_date=parse_date(birth_date),
            join_date=datetime.strptime(join_date.strip(), '%m/%d/%Y'),
            status=STATUS_MAP[status_raw.strip().upper()],
        ))
    db.commit()
    print("  Done.\n")

    # ── Member Plans ──────────────────────────────────────────────────────────
    # CSV columns: plan_id, price, type, duration
    print("Importing member plans...")
    PLAN_TYPE_MAP = {
        'BASIC':   MemberPlanType.BASIC,
        'PREMIUM': MemberPlanType.PREMIUM,
        'VIP':     MemberPlanType.VIP,
    }
    PLAN_DESCRIPTIONS = {
        'BASIC':   'Basic monthly access to gym facilities.',
        'PREMIUM': 'Premium access including group classes.',
        'VIP':     'All-inclusive VIP membership with personal training.',
    }
    for row in read_csv('memberplan.csv'):
        plan_id, price, type_raw, duration = row
        if db.query(MemberPlan).filter_by(plan_id=int(plan_id)).first():
            print(f"  Skipping plan {plan_id} (already exists)")
            continue
        t = type_raw.strip().upper()
        db.add(MemberPlan(
            plan_id=int(plan_id),
            price=float(price),
            type=PLAN_TYPE_MAP[t],
            duration=int(duration),
            description=PLAN_DESCRIPTIONS.get(t),
        ))
    db.commit()
    print("  Done.\n")

    # ── Memberships ───────────────────────────────────────────────────────────
    # CSV columns: membership_id, member_id, start_date, end_date, is_active
    # membership_id is ignored — PK is now (member_id, plan_id, end_date)
    print("Importing memberships...")
    seen_memberships = set()  # track duplicates within the CSV itself
    for row in read_csv('membership.csv'):
        member_id, plan_id, start_date, end_date, is_active_raw = row
        key = (int(member_id), int(plan_id), parse_date(end_date))
        if key in seen_memberships:
            print(f"  Skipping duplicate in CSV: member {member_id}, plan {plan_id}, end {end_date}")
            continue
        seen_memberships.add(key)
        if db.query(Membership).filter_by(member_id=key[0], plan_id=key[1], end_date=key[2]).first():
            print(f"  Skipping membership for member {member_id} end_date {end_date} (already exists)")
            continue
        db.add(Membership(
            member_id=key[0],
            plan_id=key[1],
            start_date=parse_date(start_date),
            end_date=key[2],
            is_active=to_bool(is_active_raw),
        ))
    db.commit()
    print("  Done.\n")

    # ── Classes ───────────────────────────────────────────────────────────────
    # CSV columns: class_id, trainer_id, class_name, type, capacity,
    #              date, start_time, end_time
    print("Importing classes...")
    for row in read_csv('class.csv'):
        class_id, trainer_id, class_name, type_raw, capacity, date_str, start_t, end_t = row
        if db.query(Class).filter_by(class_id=int(class_id)).first():
            print(f"  Skipping class {class_id} (already exists)")
            continue
        db.add(Class(
            class_id=int(class_id),
            trainer_id=int(trainer_id) if trainer_id.strip() else None,
            class_name=class_name.strip(),
            type=type_raw.strip(),
            capacity=int(capacity),
            start_time=parse_datetime(date_str, start_t),
            end_time=parse_datetime(date_str, end_t),
        ))
    db.commit()
    print("  Done.\n")

    # ── Machines ──────────────────────────────────────────────────────────────
    # CSV columns: machine_id, machine_name, purchase_date, category, status
    # Note: machine_name has a unique constraint — duplicates get a suffix (#2, #3 …)
    print("Importing machines...")
    CAT_MAP = {
        'CARDIO':     MachineCategory.CARDIO,
        'STRENGTH':   MachineCategory.STRENGTH,
        'FUNCTIONAL': MachineCategory.FUNCTIONAL,
    }
    MSTATUS_MAP = {
        'AVAILABLE':  MachineStatus.AVAILABLE,
        'MAINTENANCE': MachineStatus.MAINTENANCE,
        'RETIRED':    MachineStatus.RETIRED,
    }
    # Pre-load names already in the DB so we can avoid conflicts
    existing_machine_names: set[str] = {
        r[0] for r in db.execute(text("SELECT machine_name FROM machine")).fetchall()
    }
    seen_machine_names: dict[str, int] = {}
    for row in read_csv('machine.csv'):
        machine_id, machine_name_raw, purchase_date, category_raw, status_raw = row
        if db.query(Machine).filter_by(machine_id=int(machine_id)).first():
            print(f"  Skipping machine {machine_id} (already exists)")
            continue
        base_name = machine_name_raw.strip()
        seen_machine_names[base_name] = seen_machine_names.get(base_name, 0) + 1
        count = seen_machine_names[base_name]
        candidate = base_name if count == 1 else f"{base_name} #{count}"
        # Keep incrementing suffix until we find a name not in the DB
        suffix = count
        while candidate in existing_machine_names:
            suffix += 1
            candidate = f"{base_name} #{suffix}"
        unique_name = candidate
        existing_machine_names.add(unique_name)
        db.add(Machine(
            machine_id=int(machine_id),
            machine_name=unique_name,
            purchase_date=parse_date(purchase_date),
            category=CAT_MAP[category_raw.strip().upper()],
            status=MSTATUS_MAP[status_raw.strip().upper()],
        ))
    db.commit()
    print("  Done.\n")

    # ── Machine Usage ─────────────────────────────────────────────────────────
    # CSV columns: machine_id, member_id, date (YYYY-MM-DD), start_time (H:MM:SS)
    # end_time and duration_minutes are nullable — left as None
    print("Importing machine usage...")
    for row in read_csv('machineusage.csv'):
        machine_id, member_id, date_str, start_time_str = row
        start_dt = parse_datetime_auto(date_str, start_time_str)
        db.add(MachineUsage(
            machine_id=int(machine_id),
            member_id=int(member_id),
            start_time=start_dt,
        ))
    db.commit()
    print("  Done.\n")

    # ── Class Signups ─────────────────────────────────────────────────────────
    # CSV columns: member_id, class_id, is_checked_in
    print("Importing class signups...")
    valid_class_ids = {
        r[0] for r in db.execute(text("SELECT class_id FROM class")).fetchall()
    }
    valid_member_ids = {
        r[0] for r in db.execute(text("SELECT member_id FROM member")).fetchall()
    }
    existing_enrollments = set(
        db.execute(text("SELECT member_id, class_id FROM class_enrollment")).fetchall()
    )
    skipped_signups = 0
    for row in read_csv('classsignup.csv'):
        member_id, class_id, is_checked_in_raw = row
        mid, cid = int(member_id), int(class_id)
        if cid not in valid_class_ids or mid not in valid_member_ids:
            skipped_signups += 1
            continue
        key = (mid, cid)
        if key in existing_enrollments:
            continue
        is_checked = to_bool(is_checked_in_raw)
        db.execute(
            class_enrollment_table.insert().values(
                member_id=mid,
                class_id=cid,
                is_checked_in=is_checked,
                check_in_time=datetime.now() if is_checked else None,
            )
        )
    if skipped_signups:
        print(f"  Skipped {skipped_signups} signup(s) referencing non-existent classes/members.")
    db.commit()
    print("  Done.\n")

    print("=" * 50)
    print("[OK] All data imported successfully!")
    print()
    print("Staff login credentials (all accounts):")
    print("  Password: password123")
    print("  Emails generated as: firstname.lastname@gym.com")
    print("    e.g.  john.smith@gym.com  /  password123")
    print("=" * 50)

except Exception as e:
    db.rollback()
    print(f"\n[ERROR] Import failed: {e}")
    raise
finally:
    db.close()
