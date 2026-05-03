"""Routes for Staff management and authentication"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import Staff, StaffRole
from schemas.staff import StaffCreate, StaffResponse, StaffLogin, StaffLoginResponse
from auth import hash_password, verify_password, get_current_staff, require_role

router = APIRouter()


@router.post("/register", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def register_staff(
    staff: StaffCreate,
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Register a new staff account (Manager only)"""
    existing = db.execute(
        text("SELECT staff_id FROM staff WHERE email = :email"),
        {"email": staff.email.lower()}
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    row = db.execute(
        text("""
            INSERT INTO staff (first_name, last_name, email, role, password_hash, is_active)
            VALUES (:first_name, :last_name, :email, :role, :password_hash, TRUE)
            RETURNING staff_id, first_name, last_name, email, role, is_active, created_at, updated_at
        """),
        {
            "first_name": staff.first_name,
            "last_name": staff.last_name,
            "email": staff.email.lower(),
            "role": staff.role.value if hasattr(staff.role, "value") else staff.role,
            "password_hash": hash_password(staff.password)
        }
    ).mappings().fetchone()
    db.commit()
    return dict(row)


@router.post("/login", response_model=StaffLoginResponse)
async def login(credentials: StaffLogin, db: Session = Depends(get_db)):
    """Staff login endpoint"""
    row = db.execute(
        text("""
            SELECT staff_id, first_name, last_name, email, role, password_hash, is_active
            FROM staff
            WHERE email = :email
        """),
        {"email": credentials.email.lower()}
    ).mappings().fetchone()

    if not row or not verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account is inactive"
        )

    # Update updated_at timestamp on successful login
    db.execute(
        text("UPDATE staff SET updated_at = NOW() WHERE staff_id = :staff_id"),
        {"staff_id": row["staff_id"]}
    )
    db.commit()

    # Convert role - try by name first (if stored as "MANAGER"), then by value
    role_str = row["role"]
    try:
        # Try accessing by enum member name (e.g., "MANAGER")
        role_enum = StaffRole[role_str.upper()]
    except KeyError:
        # Fall back to enum value (e.g., "Manager")
        role_enum = StaffRole(role_str)
    
    return StaffLoginResponse(
        staff_id=row["staff_id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        role=role_enum.value.capitalize(),  # Normalize to mixed-case: "MANAGER" -> "Manager"
        is_active=row["is_active"]
    )


@router.get("/", response_model=list[StaffResponse])
async def list_staff(
    current_staff: Staff = Depends(require_role(StaffRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """Get all staff accounts (Manager only)"""
    rows = db.execute(
        text("""
            SELECT staff_id, first_name, last_name, email, role, is_active, created_at, updated_at
            FROM staff
            WHERE is_active = TRUE
            ORDER BY staff_id
        """)
    ).mappings().fetchall()
    return [dict(row) for row in rows]


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: int,
    current_staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get staff details by ID"""
    row = db.execute(
        text("""
            SELECT staff_id, first_name, last_name, email, role, is_active, created_at, updated_at
            FROM staff
            WHERE staff_id = :staff_id
        """),
        {"staff_id": staff_id}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID {staff_id} not found"
        )
    return dict(row)


@router.get("/me", response_model=StaffResponse)
async def get_current_staff_info(current_staff: Staff = Depends(get_current_staff)):
    """Get current logged-in staff information"""
    return current_staff
