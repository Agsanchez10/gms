"""Routes for Member management"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta
from database import get_db
from schemas.members import MemberCreate, MemberResponse, MemberUpdate, MemberDetailedResponse

router = APIRouter()


@router.get("/", response_model=list[MemberResponse])
async def list_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=1000),
    status_filter: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get all members with pagination"""
    params: dict = {"skip": skip, "lim": limit}
    where_clause = ""
    if status_filter:
        filter_map = {"active": "Active", "inactive": "Inactive", "suspended": "Suspended"}
        params["sf"] = filter_map.get(status_filter.lower(), status_filter)
        where_clause = "WHERE d.status = :sf"
    rows = db.execute(
        text(f"""
            WITH d AS (
                SELECT m.member_id, m.first_name, m.last_name, m.phone_number, m.email,
                       m.birth_date, m.join_date, m.created_at, m.updated_at,
                       CASE
                           WHEN m.status = 'SUSPENDED' THEN 'Suspended'
                           WHEN ms_cur.plan_id IS NOT NULL THEN 'Active' 
                           ELSE 'Inactive'
                       END                      AS status,
                       mp.type                  AS plan_type,
                       ms_cur.end_date          AS membership_end_date
                FROM member m
                LEFT JOIN LATERAL (
                    SELECT ms.plan_id, ms.end_date
                    FROM   membership ms
                    WHERE  ms.member_id = m.member_id
                      AND  ms.is_active = TRUE
                      AND  ms.end_date >= CURRENT_DATE
                    ORDER BY ms.end_date DESC
                    LIMIT 1
                ) ms_cur ON TRUE
                LEFT JOIN member_plan mp ON ms_cur.plan_id = mp.plan_id
            )
            SELECT * FROM d
            {where_clause}
            ORDER BY member_id
            OFFSET :skip LIMIT :lim
        """),
        params
    ).mappings().fetchall()
    return [dict(row) | {"memberships": []} for row in rows]


@router.get("/{member_id}", response_model=MemberDetailedResponse)
async def get_member(member_id: int, db: Session = Depends(get_db)):
    """Get member details by ID"""
    row = db.execute(
        text("""
            SELECT m.member_id, m.first_name, m.last_name, m.phone_number, m.email,
                   m.birth_date, m.join_date, m.created_at, m.updated_at,
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
            WHERE m.member_id = :member_id
        """),
        {"member_id": member_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found"
        )

    member = dict(row)
    membership_rows = db.execute(
        text("""
            SELECT ms.member_id, ms.plan_id,
                   ms.start_date, ms.end_date, ms.is_active, ms.created_at,
                   mp.type, mp.price, mp.duration, mp.description,
                   mp.created_at  AS plan_created_at,
                   mp.updated_at  AS plan_updated_at
            FROM membership ms
            JOIN member_plan mp ON ms.plan_id = mp.plan_id
            WHERE ms.member_id = :member_id
            ORDER BY ms.start_date DESC
        """),
        {"member_id": member_id}
    ).mappings().fetchall()

    member["memberships"] = [
        {
            "member_id":     m["member_id"],
            "plan_id":       m["plan_id"],
            "start_date":    m["start_date"],
            "end_date":      m["end_date"],
            "is_active":     m["is_active"],
            "created_at":    m["created_at"],
            "plan": {
                "plan_id":     m["plan_id"],
                "type":        m["type"],
                "price":       m["price"],
                "duration":    m["duration"],
                "description": m["description"],
                "created_at":  m["plan_created_at"],
                "updated_at":  m["plan_updated_at"]
            }
        }
        for m in membership_rows
    ]
    return member


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Register a new member and create their initial membership"""
    if member.email:
        existing = db.execute(
            text("SELECT member_id FROM member WHERE email = :email"),
            {"email": member.email}
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Validate plan exists and get duration
    plan = db.execute(
        text("SELECT plan_id, duration FROM member_plan WHERE plan_id = :plan_id"),
        {"plan_id": member.plan_id}
    ).mappings().fetchone()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan with ID {member.plan_id} not found"
        )

    row = db.execute(
        text("""
            INSERT INTO member (first_name, last_name, phone_number, email, birth_date, status, join_date, created_at, updated_at)
            VALUES (:first_name, :last_name, :phone_number, :email, :birth_date, 'ACTIVE', CURRENT_DATE, NOW(), NOW())
            RETURNING member_id, first_name, last_name, phone_number, email,
                      birth_date, join_date, status, created_at, updated_at
        """),
        {
            "first_name":   member.first_name,
            "last_name":    member.last_name,
            "phone_number": member.phone_number,
            "email":        member.email,
            "birth_date":   member.birth_date
        }
    ).mappings().fetchone()

    # Create membership for the new member
    start_date = date.today()
    end_date = start_date + timedelta(days=plan["duration"] * 30)
    db.execute(
        text("""
            INSERT INTO membership (member_id, plan_id, start_date, end_date, is_active)
            VALUES (:member_id, :plan_id, :start_date, :end_date, TRUE)
        """),
        {
            "member_id":  row["member_id"],
            "plan_id":    member.plan_id,
            "start_date": start_date,
            "end_date":   end_date
        }
    )

    db.commit()
    return dict(row) | {"memberships": []}


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    member_update: MemberUpdate,
    db: Session = Depends(get_db)
):
    """Update member information"""
    existing = db.execute(
        text("SELECT member_id FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).fetchone()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found"
        )

    updates = {}
    if member_update.first_name:
        updates["first_name"] = member_update.first_name
    if member_update.last_name:
        updates["last_name"] = member_update.last_name
    if member_update.phone_number:
        updates["phone_number"] = member_update.phone_number
    if member_update.email:
        updates["email"] = member_update.email
    if member_update.status:
        updates["status"] = member_update.status.value if hasattr(member_update.status, "value") else member_update.status

    if updates:
        set_clause = ", ".join(f"{col} = :{col}" for col in updates)
        updates["member_id"] = member_id
        row = db.execute(
            text(f"""
                UPDATE member
                SET {set_clause}, updated_at = NOW()
                WHERE member_id = :member_id
                RETURNING member_id, first_name, last_name, phone_number, email,
                          birth_date, join_date, status, created_at, updated_at
            """),
            updates
        ).mappings().fetchone()
        db.commit()
        return dict(row) | {"memberships": []}

    row = db.execute(
        text("""
            SELECT member_id, first_name, last_name, phone_number, email,
                   birth_date, join_date, status, created_at, updated_at
            FROM member WHERE member_id = :id
        """),
        {"id": member_id}
    ).mappings().fetchone()
    return dict(row) | {"memberships": []}


@router.patch("/{member_id}/status", response_model=MemberResponse)
async def update_member_status(
    member_id: int,
    new_status: str = Query(...),
    db: Session = Depends(get_db)
):
    """Set a member's raw status (ACTIVE | INACTIVE | SUSPENDED)"""
    valid = {"ACTIVE", "INACTIVE", "SUSPENDED"}
    normalised = new_status.upper()
    if normalised not in valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {sorted(valid)}"
        )
    result = db.execute(
        text("UPDATE member SET status = :s, updated_at = NOW() WHERE member_id = :id"),
        {"s": normalised, "id": member_id}
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found"
        )
    db.commit()
    row = db.execute(
        text("""
            SELECT m.member_id, m.first_name, m.last_name, m.phone_number, m.email,
                   m.birth_date, m.join_date, m.created_at, m.updated_at,
                   CASE
                       WHEN m.status = 'SUSPENDED' THEN 'Suspended'
                       WHEN ms_a.plan_id IS NOT NULL THEN 'Active'
                       ELSE 'Inactive'
                   END AS status,
                   mp.type AS plan_type, ms_a.end_date AS membership_end_date
            FROM member m
            LEFT JOIN LATERAL (
                SELECT ms.end_date, ms.plan_id FROM membership ms
                WHERE ms.member_id = m.member_id
                  AND ms.is_active = TRUE AND ms.end_date >= CURRENT_DATE
                ORDER BY ms.end_date DESC LIMIT 1
            ) ms_a ON TRUE
            LEFT JOIN member_plan mp ON ms_a.plan_id = mp.plan_id
            WHERE m.member_id = :id
        """),
        {"id": member_id}
    ).mappings().fetchone()
    return dict(row) | {"memberships": []}


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: int, db: Session = Depends(get_db)):
    """Soft delete member (mark as inactive)"""
    result = db.execute(
        text("""
            UPDATE member
            SET status = 'INACTIVE', updated_at = NOW()
            WHERE member_id = :member_id
        """),
        {"member_id": member_id}
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found"
        )
    db.commit()
    return None


@router.get("/{member_id}/memberships/", response_model=list)
async def get_member_memberships(member_id: int, db: Session = Depends(get_db)):
    """Get all memberships for a member"""
    member_exists = db.execute(
        text("SELECT member_id FROM member WHERE member_id = :id"),
        {"id": member_id}
    ).fetchone()
    if not member_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with ID {member_id} not found"
        )

    rows = db.execute(
        text("""
            SELECT ms.member_id, ms.plan_id,
                   ms.start_date, ms.end_date, ms.is_active, ms.created_at,
                   mp.type, mp.price, mp.duration, mp.description
            FROM membership ms
            JOIN member_plan mp ON ms.plan_id = mp.plan_id
            WHERE ms.member_id = :member_id
            ORDER BY ms.start_date DESC
        """),
        {"member_id": member_id}
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/{member_id}/current-membership/", response_model=dict)
async def get_current_membership(member_id: int, db: Session = Depends(get_db)):
    """Get current active membership for a member"""
    row = db.execute(
        text("""
            SELECT ms.member_id, ms.start_date, ms.end_date,
                   mp.plan_id, mp.type, mp.price, mp.duration,
                   (ms.end_date - CURRENT_DATE) AS days_remaining
            FROM membership ms
            JOIN member_plan mp ON ms.plan_id = mp.plan_id
            WHERE ms.member_id = :member_id
              AND ms.is_active = TRUE
              AND ms.end_date >= CURRENT_DATE
            ORDER BY ms.end_date DESC
            LIMIT 1
        """),
        {"member_id": member_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active membership found"
        )
    r = dict(row)
    return {
        "member_id":      r["member_id"],
        "plan": {
            "plan_id":  r["plan_id"],
            "type":     r["type"],
            "price":    r["price"],
            "duration": r["duration"]
        },
        "start_date":     r["start_date"],
        "end_date":       r["end_date"],
        "days_remaining": r["days_remaining"]
    }
