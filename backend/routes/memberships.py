"""Routes for Membership management"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta
from database import get_db
from models import Staff, StaffRole
from schemas.members import MembershipResponse
from auth import require_role

router = APIRouter()


@router.post("/members/{member_id}/enroll", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def enroll_member_plan(
    member_id: int,
    plan_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Enroll a member in a membership plan"""
    member = db.execute(
        text("SELECT member_id FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    plan = db.execute(
        text("SELECT plan_id, duration FROM member_plan WHERE plan_id = :id"),
        {"id": plan_id}
    ).mappings().fetchone()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    start_date = date.today()
    end_date = start_date + timedelta(days=plan["duration"] * 30)

    row = db.execute(
        text("""
            INSERT INTO membership (member_id, plan_id, start_date, end_date, is_active)
            VALUES (:member_id, :plan_id, :start_date, :end_date, TRUE)
            RETURNING member_id, plan_id, start_date, end_date, is_active, created_at
        """),
        {
            "member_id": member_id,
            "plan_id": plan_id,
            "start_date": start_date,
            "end_date": end_date
        }
    ).mappings().fetchone()
    db.commit()
    return dict(row)


@router.get("/members/{member_id}/current", response_model=MembershipResponse)
async def get_current_membership(
    member_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get current active membership for a member"""
    row = db.execute(
        text("""
            SELECT member_id, plan_id, start_date, end_date, is_active, created_at
            FROM membership
            WHERE member_id = :member_id
              AND is_active = TRUE
              AND end_date >= CURRENT_DATE
            ORDER BY end_date DESC
            LIMIT 1
        """),
        {"member_id": member_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active membership found")
    return dict(row)


@router.put("/members/{member_id}/{plan_id}/renew", response_model=MembershipResponse)
async def renew_membership(
    member_id: int,
    plan_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Renew a membership identified by member_id + plan_id"""
    old = db.execute(
        text("""
            SELECT member_id, plan_id, end_date FROM membership
            WHERE member_id = :member_id AND plan_id = :plan_id
            ORDER BY end_date DESC LIMIT 1
        """),
        {"member_id": member_id, "plan_id": plan_id}
    ).mappings().fetchone()
    if not old:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    plan = db.execute(
        text("SELECT duration FROM member_plan WHERE plan_id = :id"),
        {"id": plan_id}
    ).mappings().fetchone()

    start_date = date.today()
    end_date = start_date + timedelta(days=plan["duration"] * 30)

    # Deactivate the old membership row
    db.execute(
        text("UPDATE membership SET is_active = FALSE WHERE member_id = :mid AND plan_id = :pid AND end_date = :ed"),
        {"mid": old["member_id"], "pid": old["plan_id"], "ed": old["end_date"]}
    )

    # Insert the renewed membership
    row = db.execute(
        text("""
            INSERT INTO membership (member_id, plan_id, start_date, end_date, is_active)
            VALUES (:member_id, :plan_id, :start_date, :end_date, TRUE)
            RETURNING member_id, plan_id, start_date, end_date, is_active, created_at
        """),
        {
            "member_id": member_id,
            "plan_id": plan_id,
            "start_date": start_date,
            "end_date": end_date
        }
    ).mappings().fetchone()
    db.commit()
    return dict(row)
