"""Routes for Machine Usage tracking"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from database import get_db
from models import Staff, StaffRole
from schemas.machines import MachineUsageResponse
from auth import get_current_staff, require_role

router = APIRouter()


@router.post("/machines/{machine_id}/start", status_code=status.HTTP_201_CREATED)
async def start_machine_usage(
    machine_id: int,
    member_id: int = Query(..., gt=0),
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Member signs in to a machine"""
    machine = db.execute(
        text("SELECT machine_id FROM machine WHERE machine_id = :id"),
        {"id": machine_id}
    ).fetchone()
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    member = db.execute(
        text("SELECT member_id, status FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if member.status == "Suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member account is suspended")

    if member.status == "Inactive":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member account is inactive")

    row = db.execute(
        text("""
            INSERT INTO machine_usage (machine_id, member_id, start_time)
            VALUES (:machine_id, :member_id, NOW())
            RETURNING usage_id, machine_id, member_id, start_time
        """),
        {"machine_id": machine_id, "member_id": member_id}
    ).mappings().fetchone()
    db.commit()

    return {
        "usage_id":   row["usage_id"],
        "machine_id": row["machine_id"],
        "member_id":  row["member_id"],
        "start_time": row["start_time"],
        "message":    f"Member {member_id} signed in to machine {machine_id}"
    }


@router.put("/machines/{machine_id}/end/{usage_id}")
async def end_machine_usage(
    machine_id: int,
    usage_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.TRAINER, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Member signs out from a machine"""
    usage = db.execute(
        text("""
            SELECT usage_id, machine_id, member_id, start_time, end_time
            FROM machine_usage
            WHERE usage_id = :usage_id
        """),
        {"usage_id": usage_id}
    ).mappings().fetchone()

    if not usage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage record not found")

    if usage["machine_id"] != machine_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Machine ID does not match usage record")

    if usage["end_time"] is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usage already ended")

    end_time = datetime.now()
    duration = int((end_time - usage["start_time"]).total_seconds() // 60)

    updated = db.execute(
        text("""
            UPDATE machine_usage
            SET end_time = :end_time, duration_minutes = :duration
            WHERE usage_id = :usage_id
            RETURNING usage_id, machine_id, member_id, start_time, end_time, duration_minutes
        """),
        {"end_time": end_time, "duration": duration, "usage_id": usage_id}
    ).mappings().fetchone()
    db.commit()

    return {
        "usage_id":         updated["usage_id"],
        "machine_id":       updated["machine_id"],
        "member_id":        updated["member_id"],
        "start_time":       updated["start_time"],
        "end_time":         updated["end_time"],
        "duration_minutes": updated["duration_minutes"],
        "message":          f"Member {updated['member_id']} signed out from machine {machine_id}"
    }


@router.get("/machines/{machine_id}/usage", response_model=list[MachineUsageResponse])
async def get_machine_usage_history(
    machine_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get usage history for a machine"""
    machine = db.execute(
        text("SELECT machine_id FROM machine WHERE machine_id = :id"),
        {"id": machine_id}
    ).fetchone()
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    rows = db.execute(
        text("""
            SELECT usage_id, machine_id, member_id, start_time, end_time, duration_minutes
            FROM machine_usage
            WHERE machine_id = :machine_id
            ORDER BY start_time DESC
            OFFSET :skip LIMIT :lim
        """),
        {"machine_id": machine_id, "skip": skip, "lim": limit}
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/members/{member_id}/usage", response_model=list[MachineUsageResponse])
async def get_member_usage_history(
    member_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get machine usage history for a member"""
    member = db.execute(
        text("SELECT member_id FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    rows = db.execute(
        text("""
            SELECT usage_id, machine_id, member_id, start_time, end_time, duration_minutes
            FROM machine_usage
            WHERE member_id = :member_id
            ORDER BY start_time DESC
            OFFSET :skip LIMIT :lim
        """),
        {"member_id": member_id, "skip": skip, "lim": limit}
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/stats/machine/{machine_id}")
async def get_machine_usage_stats(
    machine_id: int,
    days: int = Query(30, ge=1, le=365),
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a machine"""
    machine = db.execute(
        text("SELECT machine_id, machine_name FROM machine WHERE machine_id = :id"),
        {"id": machine_id}
    ).mappings().fetchone()
    if not machine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine not found")

    start_date = datetime.now() - timedelta(days=days)

    stats = db.execute(
        text("""
            SELECT
                COUNT(usage_id)          AS total_usages,
                COALESCE(SUM(duration_minutes), 0) AS total_minutes
            FROM machine_usage
            WHERE machine_id = :machine_id
              AND start_time >= :start_date
              AND end_time IS NOT NULL
        """),
        {"machine_id": machine_id, "start_date": start_date}
    ).mappings().fetchone()

    total_usages  = stats["total_usages"]  or 0
    total_minutes = stats["total_minutes"] or 0

    return {
        "machine_id":               machine_id,
        "machine_name":             machine["machine_name"],
        "period_days":              days,
        "total_usages":             total_usages,
        "total_hours":              round(total_minutes / 60, 2),
        "average_session_minutes":  round(total_minutes / total_usages, 2) if total_usages > 0 else 0
    }


@router.get("/stats/member/{member_id}")
async def get_member_usage_stats(
    member_id: int,
    days: int = Query(30, ge=1, le=365),
    current_staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get usage statistics for a member"""
    member = db.execute(
        text("SELECT member_id, first_name, last_name FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).mappings().fetchone()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    start_date = datetime.now() - timedelta(days=days)

    stats = db.execute(
        text("""
            SELECT
                COUNT(usage_id)                AS total_sessions,
                COALESCE(SUM(duration_minutes), 0) AS total_minutes,
                AVG(duration_minutes)          AS avg_session,
                COUNT(DISTINCT machine_id)     AS unique_machines
            FROM machine_usage
            WHERE member_id = :member_id
              AND start_time >= :start_date
              AND end_time IS NOT NULL
        """),
        {"member_id": member_id, "start_date": start_date}
    ).mappings().fetchone()

    total_sessions = stats["total_sessions"] or 0
    total_minutes  = stats["total_minutes"]  or 0

    return {
        "member_id":               member_id,
        "member_name":             f"{member['first_name']} {member['last_name']}",
        "period_days":             days,
        "total_sessions":          total_sessions,
        "total_hours":             round(total_minutes / 60, 2),
        "average_session_minutes": round(float(stats["avg_session"]), 2) if stats["avg_session"] else 0,
        "unique_machines_used":    stats["unique_machines"] or 0
    }
