"""Routes for Member Plans"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import Staff, StaffRole
from schemas.members import MemberPlanCreate, MemberPlanResponse
from auth import require_role

router = APIRouter()


@router.get("/", response_model=list[MemberPlanResponse])
async def list_plans(db: Session = Depends(get_db)):
    """Get all membership plans"""
    rows = db.execute(
        text("""
            SELECT plan_id, type, price, duration, description, created_at, updated_at
            FROM member_plan
            ORDER BY plan_id
        """)
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/{plan_id}", response_model=MemberPlanResponse)
async def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get membership plan by ID"""
    row = db.execute(
        text("""
            SELECT plan_id, type, price, duration, description, created_at, updated_at
            FROM member_plan
            WHERE plan_id = :plan_id
        """),
        {"plan_id": plan_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found"
        )
    return dict(row)


@router.post("/", response_model=MemberPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan: MemberPlanCreate,
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Create a new membership plan (Manager only)"""
    row = db.execute(
        text("""
            INSERT INTO member_plan (type, price, duration, description)
            VALUES (:type, :price, :duration, :description)
            RETURNING plan_id, type, price, duration, description, created_at, updated_at
        """),
        {
            "type": plan.type,
            "price": plan.price,
            "duration": plan.duration,
            "description": plan.description
        }
    ).mappings().fetchone()
    db.commit()
    return dict(row)


@router.put("/{plan_id}", response_model=MemberPlanResponse)
async def update_plan(
    plan_id: int,
    plan_update: MemberPlanCreate,
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Update membership plan (Manager only)"""
    row = db.execute(
        text("""
            UPDATE member_plan
            SET type = :type, price = :price, duration = :duration,
                description = :description, updated_at = NOW()
            WHERE plan_id = :plan_id
            RETURNING plan_id, type, price, duration, description, created_at, updated_at
        """),
        {
            "plan_id": plan_id,
            "type": plan_update.type,
            "price": plan_update.price,
            "duration": plan_update.duration,
            "description": plan_update.description
        }
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found"
        )
    db.commit()
    return dict(row)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Delete a membership plan (Manager only)"""
    result = db.execute(
        text("DELETE FROM member_plan WHERE plan_id = :plan_id"),
        {"plan_id": plan_id}
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {plan_id} not found"
        )
    db.commit()
    return None
