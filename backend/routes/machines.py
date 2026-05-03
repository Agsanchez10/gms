"""Routes for Machine management"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from datetime import date as date_type
from models import Staff, StaffRole, MachineStatus
from schemas.machines import MachineCreate, MachineResponse, MachineUpdate
from auth import get_current_staff, require_role

router = APIRouter()


@router.get("/", response_model=list[MachineResponse])
async def list_machines(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: str = Query(None),
    category_filter: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get all machines with optional filters"""
    conditions = []
    params: dict = {"skip": skip, "lim": limit}
    if status_filter:
        conditions.append("status = :status")
        params["status"] = status_filter
    if category_filter:
        conditions.append("category = :category")
        params["category"] = category_filter
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = db.execute(
        text(f"""
            SELECT machine_id, machine_name, category, purchase_date,
                   status, maintenance_notes,
                   COALESCE(created_at, NOW()) AS created_at,
                   COALESCE(updated_at, NOW()) AS updated_at
            FROM machine
            {where}
            ORDER BY machine_id
            OFFSET :skip LIMIT :lim
        """),
        params
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/{machine_id}", response_model=MachineResponse)
async def get_machine(machine_id: int, db: Session = Depends(get_db)):
    """Get machine details by ID"""
    row = db.execute(
        text("""
            SELECT machine_id, machine_name, category, purchase_date,
                   status, maintenance_notes,
                   COALESCE(created_at, NOW()) AS created_at,
                   COALESCE(updated_at, NOW()) AS updated_at
            FROM machine
            WHERE machine_id = :machine_id
        """),
        {"machine_id": machine_id}
    ).mappings().fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine with ID {machine_id} not found"
        )
    return dict(row)


@router.post("/", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def create_machine(
    machine: MachineCreate,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Add a new machine (Reception or Manager)"""
    existing = db.execute(
        text("SELECT machine_id FROM machine WHERE machine_name = :name"),
        {"name": machine.machine_name}
    ).fetchone()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Machine name already exists")

    row = db.execute(
        text("""
            INSERT INTO machine (machine_name, category, purchase_date, status, maintenance_notes)
            VALUES (:machine_name, :category, :purchase_date, :status, :maintenance_notes)
            RETURNING machine_id, machine_name, category, purchase_date,
                      status, maintenance_notes,
                      COALESCE(created_at, NOW()) AS created_at,
                      COALESCE(updated_at, NOW()) AS updated_at
        """),
        {
            "machine_name":       machine.machine_name,
            "category":           machine.category.value if hasattr(machine.category, "value") else machine.category,
            "purchase_date":      machine.purchase_date or date_type.today(),
            "status":             (machine.status or MachineStatus.AVAILABLE).value,
            "maintenance_notes":  machine.maintenance_notes
        }
    ).mappings().fetchone()
    db.commit()
    return dict(row)


@router.put("/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: int,
    machine_update: MachineUpdate,
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Update machine status or details (Manager only)"""
    existing = db.execute(
        text("SELECT machine_id FROM machine WHERE machine_id = :id"),
        {"id": machine_id}
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine with ID {machine_id} not found")

    updates = {}
    if machine_update.status:
        updates["status"] = machine_update.status.value if hasattr(machine_update.status, "value") else machine_update.status
    if machine_update.maintenance_notes is not None:
        updates["maintenance_notes"] = machine_update.maintenance_notes
    if machine_update.category:
        updates["category"] = machine_update.category.value if hasattr(machine_update.category, "value") else machine_update.category

    if updates:
        set_clause = ", ".join(f"{col} = :{col}" for col in updates)
        updates["machine_id"] = machine_id
        db.execute(
            text(f"UPDATE machine SET {set_clause}, updated_at = NOW() WHERE machine_id = :machine_id"),
            updates
        )
        db.commit()

    row = db.execute(
        text("""
            SELECT machine_id, machine_name, category, purchase_date,
                   status, maintenance_notes,
                   COALESCE(created_at, NOW()) AS created_at,
                   COALESCE(updated_at, NOW()) AS updated_at
            FROM machine WHERE machine_id = :id
        """),
        {"id": machine_id}
    ).mappings().fetchone()
    return dict(row)


@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_id: int,
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Delete a machine (soft delete - mark as retired)"""
    result = db.execute(
        text("UPDATE machine SET status = 'RETIRED', updated_at = NOW() WHERE machine_id = :id"),
        {"id": machine_id}
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine with ID {machine_id} not found")
    db.commit()
    return None


@router.get("/{machine_id}/status", response_model=dict)
async def get_machine_status(machine_id: int, db: Session = Depends(get_db)):
    """Get current status of a machine"""
    row = db.execute(
        text("SELECT machine_id, machine_name, status, category FROM machine WHERE machine_id = :id"),
        {"id": machine_id}
    ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine with ID {machine_id} not found")
    return {
        "machine_id":   row["machine_id"],
        "machine_name": row["machine_name"],
        "status":       row["status"],
        "category":     row["category"],
        "available":    row["status"] == "Available"
    }


@router.patch("/{machine_id}/status", response_model=MachineResponse)
async def update_machine_status(
    machine_id: int,
    new_status: MachineStatus,
    current_staff: Staff = Depends(require_role(StaffRole.RECEPTION, StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Update machine status (Reception or Manager)"""
    result = db.execute(
        text("UPDATE machine SET status = :status, updated_at = NOW() WHERE machine_id = :id"),
        {"status": new_status.value, "id": machine_id}
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine with ID {machine_id} not found")
    db.commit()
    row = db.execute(
        text("""
            SELECT machine_id, machine_name, category, purchase_date,
                   status, maintenance_notes, created_at, updated_at
            FROM machine WHERE machine_id = :id
        """),
        {"id": machine_id}
    ).mappings().fetchone()
    return dict(row)
