from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Enum, ForeignKey, Table, Text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime, date
import enum


# Enum Classes
class MemberStatus(str, enum.Enum):
    """Member status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class MemberPlanType(str, enum.Enum):
    """Member plan type enumeration"""
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    VIP = "VIP"


class StaffRole(str, enum.Enum):
    """Staff role enumeration"""
    RECEPTION = "RECEPTION"
    TRAINER = "TRAINER"
    MANAGER = "MANAGER"


class MachineCategory(str, enum.Enum):
    """Machine category enumeration"""
    CARDIO = "CARDIO"
    STRENGTH = "STRENGTH"
    FUNCTIONAL = "FUNCTIONAL"


class MachineStatus(str, enum.Enum):
    """Machine status enumeration"""
    AVAILABLE = "AVAILABLE"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"


# Association tables for many-to-many relationships
class_enrollment_table = Table(
    'class_enrollment',
    Base.metadata,
    Column('member_id', Integer, ForeignKey('member.member_id', ondelete='CASCADE'), primary_key=True),
    Column('class_id', Integer, ForeignKey('class.class_id', ondelete='CASCADE'), primary_key=True),
    Column('signup_date', DateTime, default=func.now()),
    Column('is_checked_in', Boolean, default=False),
    Column('check_in_time', DateTime, nullable=True)
)


# Models
class Member(Base):
    __tablename__ = "member"
    
    member_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=False)
    join_date = Column(DateTime, default=func.now(), nullable=False)
    status = Column(Enum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    memberships = relationship("Membership", back_populates="member", cascade="all, delete-orphan")
    machine_usage = relationship("MachineUsage", back_populates="member", cascade="all, delete-orphan")
    classes = relationship("Class", secondary=class_enrollment_table, back_populates="members")
    
    def __repr__(self):
        return f"<Member(member_id={self.member_id}, name={self.first_name} {self.last_name})>"


class MemberPlan(Base):
    __tablename__ = "member_plan"
    
    plan_id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(MemberPlanType), nullable=False)
    price = Column(Float, nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in months
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    memberships = relationship("Membership", back_populates="plan")
    
    def __repr__(self):
        return f"<MemberPlan(plan_id={self.plan_id}, type={self.type}, duration={self.duration}m)>"


class Membership(Base):
    __tablename__ = "membership"
    __table_args__ = (
        PrimaryKeyConstraint('member_id', 'plan_id', 'end_date'),
    )

    member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("member_plan.plan_id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    member = relationship("Member", back_populates="memberships")
    plan = relationship("MemberPlan", back_populates="memberships")

    def __repr__(self):
        return f"<Membership(member_id={self.member_id}, plan_id={self.plan_id}, end_date={self.end_date}, active={self.is_active})>"


class Staff(Base):
    __tablename__ = "staff"
    
    staff_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(StaffRole), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    classes = relationship("Class", back_populates="trainer")
    
    def __repr__(self):
        return f"<Staff(staff_id={self.staff_id}, name={self.first_name} {self.last_name}, role={self.role})>"


class Class(Base):
    __tablename__ = "class"
    
    class_id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("staff.staff_id", ondelete="SET NULL"), nullable=True)
    class_name = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    trainer = relationship("Staff", back_populates="classes")
    members = relationship("Member", secondary=class_enrollment_table, back_populates="classes")
    
    def __repr__(self):
        return f"<Class(class_id={self.class_id}, name={self.class_name}, capacity={self.capacity})>"


class Machine(Base):
    __tablename__ = "machine"
    
    machine_id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(Enum(MachineCategory), nullable=False)
    purchase_date = Column(Date, nullable=False)
    status = Column(Enum(MachineStatus), default=MachineStatus.AVAILABLE, nullable=False)
    maintenance_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    usage = relationship("MachineUsage", back_populates="machine", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Machine(machine_id={self.machine_id}, name={self.machine_name}, status={self.status})>"


class MachineUsage(Base):
    __tablename__ = "machine_usage"
    
    usage_id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machine.machine_id", ondelete="CASCADE"), nullable=False)
    member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False, default=func.now())
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Calculated: end_time - start_time
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    machine = relationship("Machine", back_populates="usage")
    member = relationship("Member", back_populates="machine_usage")
    
    def __repr__(self):
        return f"<MachineUsage(usage_id={self.usage_id}, member={self.member_id}, machine={self.machine_id})>"
