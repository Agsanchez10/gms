"""Pydantic schemas for Staff entity"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from models import StaffRole


class StaffBase(BaseModel):
    """Base Staff schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=100)
    role: StaffRole
    
    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        """Convert role to proper enum value (case-insensitive)"""
        if isinstance(v, str):
            # Map uppercase/lowercase inputs to proper enum values
            role_map = {
                'RECEPTION': 'Reception',
                'TRAINER': 'Trainer',
                'MANAGER': 'Manager',
            }
            v = role_map.get(v.upper(), v)
        return v


class StaffCreate(StaffBase):
    """Schema for creating staff account"""
    password: str = Field(..., min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class StaffLogin(BaseModel):
    """Schema for staff login"""
    email: str
    password: str


class StaffResponse(StaffBase):
    """Response schema for Staff"""
    staff_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StaffLoginResponse(BaseModel):
    """Response after successful login"""
    staff_id: int
    first_name: str
    last_name: str
    email: str
    role: str  # Return as string value
    is_active: bool
    message: str = "Login successful"
