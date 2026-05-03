"""Pydantic schemas for Class entity"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class MemberInClassResponse(BaseModel):
    """Minimal member info embedded in class roster"""
    member_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone_number: str
    status: str

    class Config:
        from_attributes = True


class ClassBase(BaseModel):
    """Base Class schema"""
    class_name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    capacity: int = Field(..., gt=0)
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None


class ClassCreate(ClassBase):
    """Schema for creating a class"""
    trainer_id: int


class ClassUpdate(BaseModel):
    """Schema for updating a class"""
    class_name: Optional[str] = None
    type: Optional[str] = None
    capacity: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None


class ClassResponse(ClassBase):
    """Response schema for Class"""
    class_id: int
    trainer_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    member_count: int = 0  # Will be populated from query
    
    class Config:
        from_attributes = True


class ClassDetailedResponse(ClassResponse):
    """Detailed response with enrollment info"""
    members: Optional[List[MemberInClassResponse]] = []
