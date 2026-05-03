"""Pydantic schemas for analytics"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any


class MachineUsageStats(BaseModel):
    """Machine usage statistics"""
    machine_id: int
    machine_name: str
    total_usages: int
    total_duration_hours: float
    last_used: datetime
    average_session_minutes: float


class ClassEnrollmentStats(BaseModel):
    """Class enrollment statistics"""
    class_id: int
    class_name: str
    enrolled_count: int
    capacity: int
    occupancy_percentage: float
    checked_in_count: int


class MembershipStats(BaseModel):
    """Membership statistics"""
    total_members: int
    active_members: int
    inactive_members: int
    suspended_members: int


class ManagerDashboardStats(BaseModel):
    """Manager dashboard overview"""
    total_members: int
    active_memberships: int
    total_staff: int
    total_machines: int
    available_machines: int
    total_classes: int
    timestamp: datetime
