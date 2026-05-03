"""Routes for Manager Dashboard and Analytics"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from database import get_db
from models import Staff, StaffRole
from auth import require_role

router = APIRouter()


@router.get("/dashboard/overview", response_model=dict)
async def get_dashboard_overview(
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get manager dashboard overview statistics"""
    row = db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM member)                             AS total_members,
                (SELECT COUNT(*) FROM member m WHERE m.status != 'SUSPENDED' AND EXISTS (
                    SELECT 1 FROM membership ms WHERE ms.member_id = m.member_id
                    AND ms.is_active = TRUE AND ms.end_date >= CURRENT_DATE
                )) AS active_members,
                (SELECT COUNT(*) FROM staff WHERE is_active = TRUE)        AS total_staff,
                (SELECT COUNT(*) FROM machine)                             AS total_machines,
                (SELECT COUNT(*) FROM machine WHERE status = 'AVAILABLE')  AS available_machines,
                (SELECT COUNT(*) FROM "class")                             AS total_classes
        """)
    ).mappings().fetchone()

    r = dict(row)
    return {
        "total_members":          r["total_members"],
        "active_members":         r["active_members"],
        "inactive_members":       r["total_members"] - r["active_members"],
        "total_staff":            r["total_staff"],
        "total_machines":         r["total_machines"],
        "available_machines":     r["available_machines"],
        "machines_in_maintenance": r["total_machines"] - r["available_machines"],
        "total_classes":          r["total_classes"],
        "timestamp":              datetime.now()
    }


@router.get("/analytics/machine-usage", response_model=list[dict])
async def get_machine_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get machine usage analytics"""
    start_date = datetime.now() - timedelta(days=days)
    rows = db.execute(
        text("""
            SELECT m.machine_id,
                   m.machine_name,
                   m.category,
                   COUNT(u.usage_id)                    AS total_usages,
                   COALESCE(SUM(u.duration_minutes), 0) AS total_minutes,
                   COUNT(DISTINCT u.member_id)          AS unique_members
            FROM machine m
            LEFT JOIN machine_usage u
                   ON m.machine_id = u.machine_id
                  AND u.start_time >= :start_date
            GROUP BY m.machine_id, m.machine_name, m.category
            ORDER BY total_usages DESC
        """),
        {"start_date": start_date}
    ).mappings().fetchall()

    return [
        {
            "machine_id":     r["machine_id"],
            "machine_name":   r["machine_name"],
            "category":       r["category"],
            "total_usages":   r["total_usages"] or 0,
            "total_hours":    round((r["total_minutes"] or 0) / 60, 2),
            "unique_members": r["unique_members"] or 0
        }
        for r in rows
    ]


@router.get("/analytics/class-enrollment", response_model=list[dict])
async def get_class_enrollment_analytics(
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get class enrollment statistics"""
    rows = db.execute(
        text("""
            SELECT c.class_id, c.class_name, c.type, c.capacity, c.trainer_id,
                   COUNT(ce.member_id) AS enrolled_count
            FROM "class" c
            LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
            GROUP BY c.class_id, c.class_name, c.type, c.capacity, c.trainer_id
            ORDER BY c.class_id
        """)
    ).mappings().fetchall()

    return [
        {
            "class_id":             r["class_id"],
            "class_name":           r["class_name"],
            "type":                 r["type"],
            "enrolled_count":       r["enrolled_count"] or 0,
            "capacity":             r["capacity"],
            "occupancy_percentage": round((r["enrolled_count"] or 0) / r["capacity"] * 100, 2) if r["capacity"] > 0 else 0,
            "trainer_id":           r["trainer_id"]
        }
        for r in rows
    ]


@router.get("/analytics/membership-status", response_model=dict)
async def get_membership_status_analytics(
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get membership status statistics"""
    row = db.execute(
        text("""
            SELECT
                COUNT(*)                                                          AS total_members,
                COUNT(*) FILTER (WHERE m.status = 'SUSPENDED')                    AS suspended,
                COUNT(*) FILTER (WHERE m.status != 'SUSPENDED' AND EXISTS (
                    SELECT 1 FROM membership ms WHERE ms.member_id = m.member_id
                    AND ms.is_active = TRUE AND ms.end_date >= CURRENT_DATE
                ))                                                                AS active,
                COUNT(*) FILTER (WHERE m.status != 'SUSPENDED' AND NOT EXISTS (
                    SELECT 1 FROM membership ms WHERE ms.member_id = m.member_id
                    AND ms.is_active = TRUE AND ms.end_date >= CURRENT_DATE
                ))                                                                AS inactive
            FROM member m
        """)
    ).mappings().fetchone()

    r = dict(row)
    total = r["total_members"] or 0
    return {
        "total_members":    total,
        "active":           r["active"],
        "inactive":         r["inactive"],
        "suspended":        r["suspended"],
        "active_percentage": round((r["active"] / total * 100), 2) if total > 0 else 0
    }


@router.get("/analytics/staff-roles", response_model=list[dict])
async def get_staff_role_distribution(
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get staff distribution by role"""
    rows = db.execute(
        text("""
            SELECT role, COUNT(staff_id) AS count
            FROM staff
            WHERE is_active = TRUE
            GROUP BY role
            ORDER BY role
        """)
    ).mappings().fetchall()
    return [{"role": r["role"], "count": r["count"]} for r in rows]


@router.get("/analytics/top-members", response_model=list[dict])
async def get_top_members_by_usage(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365),
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get top members by machine usage"""
    start_date = datetime.now() - timedelta(days=days)
    rows = db.execute(
        text("""
            SELECT m.member_id, m.first_name, m.last_name,
                   COUNT(u.usage_id)                    AS session_count,
                   COALESCE(SUM(u.duration_minutes), 0) AS total_minutes
            FROM member m
            JOIN machine_usage u ON m.member_id = u.member_id
            WHERE u.start_time >= :start_date
            GROUP BY m.member_id, m.first_name, m.last_name
            ORDER BY session_count DESC
            LIMIT :lim
        """),
        {"start_date": start_date, "lim": limit}
    ).mappings().fetchall()

    return [
        {
            "member_id":     r["member_id"],
            "name":          f"{r['first_name']} {r['last_name']}",
            "session_count": r["session_count"] or 0,
            "total_hours":   round((r["total_minutes"] or 0) / 60, 2)
        }
        for r in rows
    ]
