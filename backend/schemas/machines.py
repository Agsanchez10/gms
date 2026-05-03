"""Pydantic schemas for Machine entity"""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from models import MachineCategory, MachineStatus


class MachineBase(BaseModel):
    """Base Machine schema"""
    machine_name: str = Field(..., min_length=1, max_length=100)
    category: MachineCategory
    purchase_date: Optional[date] = None
    status: Optional[MachineStatus] = MachineStatus.AVAILABLE
    maintenance_notes: Optional[str] = None


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    """Schema for updating machine"""
    status: Optional[MachineStatus] = None
    maintenance_notes: Optional[str] = None
    category: Optional[MachineCategory] = None


class MachineResponse(MachineBase):
    """Response schema for Machine"""
    machine_id: int
    purchase_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MachineUsageBase(BaseModel):
    """Base MachineUsage schema"""
    start_time: datetime
    end_time: Optional[datetime] = None


class MachineUsageStart(BaseModel):
    """Schema for starting machine usage"""
    member_id: int = Field(..., gt=0)


class MachineUsageEnd(BaseModel):
    """Schema for ending machine usage"""
    pass


class MachineUsageResponse(BaseModel):
    """Response schema for MachineUsage"""
    usage_id: int
    machine_id: int
    member_id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    
    class Config:
        from_attributes = True
