"""Routes for Class management"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import Staff, StaffRole
from schemas.classes import ClassCreate, ClassResponse, ClassUpdate, ClassDetailedResponse
from auth import get_current_staff, require_role

router = APIRouter()


def _class_row(row: dict) -> dict:
    """Normalise a class mapping row, adding member_count default."""
    d = dict(row)
    d.setdefault("member_count", 0)
    d.setdefault("members", [])
    return d


@router.get("/", response_model=list[ClassResponse])
async def list_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    trainer_id: int = Query(None),
    db: Session = Depends(get_db)
):
    """Get all classes with pagination"""
    if trainer_id:
        rows = db.execute(
            text("""
                SELECT c.class_id, c.trainer_id, c.class_name, c.type, c.capacity,
                       c.start_time, c.end_time, c.description,
                       COALESCE(c.created_at, NOW()) AS created_at,
                       COALESCE(c.updated_at, NOW()) AS updated_at,
                       COUNT(ce.member_id) AS member_count
                FROM "class" c
                LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
                WHERE c.trainer_id = :trainer_id
                GROUP BY c.class_id
                ORDER BY c.class_id
                OFFSET :skip LIMIT :lim
            """),
            {"trainer_id": trainer_id, "skip": skip, "lim": limit}
        ).mappings().fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT c.class_id, c.trainer_id, c.class_name, c.type, c.capacity,
                       c.start_time, c.end_time, c.description,
                       COALESCE(c.created_at, NOW()) AS created_at,
                       COALESCE(c.updated_at, NOW()) AS updated_at,
                       COUNT(ce.member_id) AS member_count
                FROM "class" c
                LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
                GROUP BY c.class_id
                ORDER BY c.class_id
                OFFSET :skip LIMIT :lim
            """),
            {"skip": skip, "lim": limit}
        ).mappings().fetchall()
    return [_class_row(row) for row in rows]


@router.get("/{class_id}", response_model=ClassDetailedResponse)
async def get_class(class_id: int, db: Session = Depends(get_db)):
    """Get class details including roster"""
    row = db.execute(
        text("""
            SELECT c.class_id, c.trainer_id, c.class_name, c.type, c.capacity,
                   c.start_time, c.end_time, c.description,
                   COALESCE(c.created_at, NOW()) AS created_at,
                   COALESCE(c.updated_at, NOW()) AS updated_at,
                   COUNT(ce.member_id) AS member_count
            FROM "class" c
            LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
            WHERE c.class_id = :class_id
            GROUP BY c.class_id
        """),
        {"class_id": class_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with ID {class_id} not found"
        )

    cls = _class_row(row)
    member_rows = db.execute(
        text("""
            SELECT m.member_id, m.first_name, m.last_name, m.email,
                   m.phone_number,
                   CASE
                       WHEN m.status = 'SUSPENDED' THEN 'Suspended'
                       WHEN EXISTS (
                           SELECT 1 FROM membership ms
                           WHERE ms.member_id = m.member_id
                             AND ms.is_active = TRUE
                             AND ms.end_date >= CURRENT_DATE
                       ) THEN 'Active'
                       ELSE 'Inactive'
                   END AS status
            FROM member m
            JOIN class_enrollment ce ON m.member_id = ce.member_id
            WHERE ce.class_id = :class_id
        """),
        {"class_id": class_id}
    ).mappings().fetchall()
    cls["members"] = [dict(m) for m in member_rows]
    return cls


@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Create a new class (Trainer or Manager)"""
    trainer = db.execute(
        text("SELECT staff_id, role FROM staff WHERE staff_id = :id"),
        {"id": class_data.trainer_id}
    ).fetchone()
    if not trainer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trainer not found")
    if trainer.role != StaffRole.TRAINER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Staff member is not a trainer")

    existing = db.execute(
        text('SELECT class_id FROM "class" WHERE class_name = :name'),
        {"name": class_data.class_name}
    ).fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class name already exists")

    row = db.execute(
        text("""
            INSERT INTO "class" (trainer_id, class_name, type, capacity, start_time, end_time, description)
            VALUES (:trainer_id, :class_name, :type, :capacity, :start_time, :end_time, :description)
            RETURNING class_id, trainer_id, class_name, type, capacity,
                      start_time, end_time, description,
                      COALESCE(created_at, NOW()) AS created_at,
                      COALESCE(updated_at, NOW()) AS updated_at
        """),
        {
            "trainer_id":  class_data.trainer_id,
            "class_name":  class_data.class_name,
            "type":        class_data.type,
            "capacity":    class_data.capacity,
            "start_time":  class_data.start_time,
            "end_time":    class_data.end_time,
            "description": class_data.description
        }
    ).mappings().fetchone()
    db.commit()
    return _class_row(row)


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_update: ClassUpdate,
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Update class details"""
    existing = db.execute(
        text('SELECT class_id FROM "class" WHERE class_id = :id'),
        {"id": class_id}
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with ID {class_id} not found")

    updates = {}
    if class_update.class_name:
        updates["class_name"] = class_update.class_name
    if class_update.type:
        updates["type"] = class_update.type
    if class_update.capacity:
        updates["capacity"] = class_update.capacity
    if class_update.start_time:
        updates["start_time"] = class_update.start_time
    if class_update.end_time:
        updates["end_time"] = class_update.end_time
    if class_update.description is not None:
        updates["description"] = class_update.description

    if updates:
        set_clause = ", ".join(f'{col} = :{col}' for col in updates)
        updates["class_id"] = class_id
        db.execute(
            text(f'UPDATE "class" SET {set_clause}, updated_at = NOW() WHERE class_id = :class_id'),
            updates
        )
        db.commit()

    row = db.execute(
        text("""
            SELECT c.class_id, c.trainer_id, c.class_name, c.type, c.capacity,
                   c.start_time, c.end_time, c.description,
                   COALESCE(c.created_at, NOW()) AS created_at,
                   COALESCE(c.updated_at, NOW()) AS updated_at,
                   COUNT(ce.member_id) AS member_count
            FROM "class" c
            LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
            WHERE c.class_id = :class_id
            GROUP BY c.class_id
        """),
        {"class_id": class_id}
    ).mappings().fetchone()
    return _class_row(row)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Delete a class"""
    result = db.execute(
        text('DELETE FROM "class" WHERE class_id = :id'),
        {"id": class_id}
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with ID {class_id} not found")
    db.commit()
    return None


@router.post("/{class_id}/enroll/{member_id}", status_code=status.HTTP_201_CREATED)
async def enroll_member_class(
    class_id: int,
    member_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Enroll a member in a class"""
    cls = db.execute(
        text('SELECT class_id, capacity FROM "class" WHERE class_id = :id'),
        {"id": class_id}
    ).mappings().fetchone()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    member = db.execute(
        text("SELECT member_id FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    already_enrolled = db.execute(
        text("SELECT 1 FROM class_enrollment WHERE class_id = :cid AND member_id = :mid"),
        {"cid": class_id, "mid": member_id}
    ).fetchone()
    if already_enrolled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Member already enrolled in this class")

    enrolled_count = db.execute(
        text("SELECT COUNT(*) AS cnt FROM class_enrollment WHERE class_id = :cid"),
        {"cid": class_id}
    ).mappings().fetchone()["cnt"]
    if enrolled_count >= cls["capacity"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class is at full capacity")

    db.execute(
        text("INSERT INTO class_enrollment (class_id, member_id) VALUES (:cid, :mid)"),
        {"cid": class_id, "mid": member_id}
    )
    db.commit()
    return {"message": f"Member {member_id} enrolled in class {class_id}"}


@router.delete("/{class_id}/enroll/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_class(
    class_id: int,
    member_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Remove member from class"""
    result = db.execute(
        text("DELETE FROM class_enrollment WHERE class_id = :cid AND member_id = :mid"),
        {"cid": class_id, "mid": member_id}
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member enrollment not found")
    db.commit()
    return None


@router.put("/{class_id}/checkin/{member_id}")
async def checkin_member_to_class(
    class_id: int,
    member_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.TRAINER, StaffRole.RECEPTION)),
    db: Session = Depends(get_db)
):
    """Mark member as checked in to class"""
    result = db.execute(
        text("""
            UPDATE class_enrollment
            SET is_checked_in = TRUE, check_in_time = NOW()
            WHERE class_id = :cid AND member_id = :mid
        """),
        {"cid": class_id, "mid": member_id}
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member enrollment not found"
        )
    db.commit()
    return {"message": f"Member {member_id} checked in to class {class_id}"}
