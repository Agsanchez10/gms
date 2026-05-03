from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import Staff, StaffRole
from database import get_db
from typing import Optional
import hashlib


class AuthException(HTTPException):
    """Custom authentication exception"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationException(HTTPException):
    """Custom authorization exception"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


def hash_password(password: str) -> str:
    """Hash password using SHA256 (for demo; use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password


def authenticate_staff(
    email: str,
    password: str,
    db: Session = Depends(get_db)
) -> Staff:
    """Authenticate staff by email and password"""
    staff = db.query(Staff).filter(Staff.email == email).first()
    
    if not staff or not verify_password(password, staff.password_hash):
        raise AuthException("Invalid email or password")
    
    if not staff.is_active:
        raise AuthException("Staff account is inactive")
    
    return staff


def get_current_staff(
    staff_id: int,
    db: Session = Depends(get_db)
) -> Staff:
    """Get current authenticated staff (used as dependency in protected routes)"""
    staff = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    
    if not staff:
        raise AuthException("Staff not found")
    
    if not staff.is_active:
        raise AuthException("Staff account is inactive")
    
    return staff


def require_role(*roles: StaffRole):
    """Dependency factory to require specific roles"""
    def check_role(staff: Staff = Depends(get_current_staff)) -> Staff:
        if staff.role not in roles:
            raise AuthorizationException(f"This action requires one of these roles: {', '.join([r.value for r in roles])}")
        return staff
    return check_role
