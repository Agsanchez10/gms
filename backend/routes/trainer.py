"""Routes for Trainer Dashboard"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import Staff, StaffRole
from auth import require_role

router = APIRouter()


@router.get("/my-classes", response_model=list[dict])
async def get_trainer_classes(
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER)),
    db: Session = Depends(get_db)
):
    """Get all classes taught by the current trainer"""
    rows = db.execute(
        text("""
            SELECT c.class_id, c.class_name, c.type, c.capacity,
                   c.start_time, c.end_time,
                   COUNT(ce.member_id) AS enrolled_count
            FROM "class" c
            LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
            WHERE c.trainer_id = :trainer_id
            GROUP BY c.class_id
            ORDER BY c.start_time
        """),
        {"trainer_id": current_staff.staff_id}
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/classes/{class_id}/roster", response_model=dict)
async def get_class_roster(
    class_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER, StaffRole.RECEPTION)),
    db: Session = Depends(get_db)
):
    """Get detailed roster for a class"""
    cls = db.execute(
        text("""
            SELECT class_id, class_name, type, capacity, start_time, end_time, trainer_id
            FROM "class"
            WHERE class_id = :class_id
        """),
        {"class_id": class_id}
    ).mappings().fetchone()

    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    if current_staff.role == StaffRole.TRAINER and cls["trainer_id"] != current_staff.staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own class rosters"
        )

    member_rows = db.execute(
        text("""
            SELECT m.member_id, m.first_name, m.last_name, m.email, m.phone_number, m.status
            FROM member m
            JOIN class_enrollment ce ON m.member_id = ce.member_id
            WHERE ce.class_id = :class_id
            ORDER BY m.last_name, m.first_name
        """),
        {"class_id": class_id}
    ).mappings().fetchall()

    members = [dict(r) for r in member_rows]
    return {
        "class_id":      cls["class_id"],
        "class_name":    cls["class_name"],
        "type":          cls["type"],
        "capacity":      cls["capacity"],
        "start_time":    cls["start_time"],
        "end_time":      cls["end_time"],
        "enrolled_count": len(members),
        "members":       members
    }


@router.get("/classes/{class_id}/attendance", response_model=dict)
async def get_class_attendance(
    class_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get attendance stats for a class"""
    cls = db.execute(
        text("""
            SELECT class_id, class_name, capacity, trainer_id
            FROM "class"
            WHERE class_id = :class_id
        """),
        {"class_id": class_id}
    ).mappings().fetchone()

    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    if current_staff.role == StaffRole.TRAINER and cls["trainer_id"] != current_staff.staff_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own class attendance"
        )

    row = db.execute(
        text("""
            SELECT
                COUNT(*)                                       AS total_enrolled,
                COUNT(*) FILTER (WHERE is_checked_in = TRUE)  AS checked_in
            FROM class_enrollment
            WHERE class_id = :class_id
        """),
        {"class_id": class_id}
    ).mappings().fetchone()

    total_enrolled = row["total_enrolled"] or 0
    return {
        "class_id":        cls["class_id"],
        "class_name":      cls["class_name"],
        "total_enrolled":  total_enrolled,
        "total_capacity":  cls["capacity"],
        "checked_in":      row["checked_in"] or 0,
        "occupancy_rate":  round((total_enrolled / cls["capacity"] * 100), 2) if cls["capacity"] > 0 else 0
    }
