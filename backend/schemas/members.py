"""Pydantic schemas for Member entity"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime, date
from typing import Optional, List
from models import MemberStatus


class MemberPlanBase(BaseModel):
    """Base MemberPlan schema"""
    type: str  # Will validate against enum
    price: float = Field(..., gt=0)
    duration: int = Field(..., gt=0)
    description: Optional[str] = None


class MemberPlanCreate(MemberPlanBase):
    pass


class MemberPlanResponse(MemberPlanBase):
    plan_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MembershipBase(BaseModel):
    """Base Membership schema"""
    plan_id: int = Field(..., gt=0)


class MembershipCreate(MembershipBase):
    pass


class MembershipResponse(MembershipBase):
    member_id: int
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    plan: Optional[MemberPlanResponse] = None

    class Config:
        from_attributes = True


class MemberBase(BaseModel):
    """Base Member schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    birth_date: date
    
    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v):
        if v >= date.today():
            raise ValueError('Birth date must be in the past')
        return v


class MemberCreate(MemberBase):
    plan_id: int = Field(..., gt=0)


class MemberUpdate(BaseModel):
    """Schema for updating member"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[str] = None
    status: Optional[MemberStatus] = None


class MemberResponse(MemberBase):
    """Response schema for Member with all details"""
    member_id: int
    status: str  # Derived from membership entity: Active | Inactive | Suspended
    join_date: datetime
    created_at: datetime
    updated_at: datetime
    memberships: Optional[List[MembershipResponse]] = []
    plan_type: Optional[str] = None
    membership_end_date: Optional[date] = None
    
    class Config:
        from_attributes = True


class MemberDetailedResponse(MemberResponse):
    """Detailed response with membership and usage info"""
    pass
