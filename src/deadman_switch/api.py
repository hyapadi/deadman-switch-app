"""
API Module for Mobile App Integration
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from .database import get_db
from .models import User, DeadmanSwitch, CheckIn, EmergencyContact, SwitchStatus
from .auth import get_current_active_user

# Router
router = APIRouter()


# Pydantic models for API
class SwitchResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    check_in_interval_hours: int
    grace_period_hours: int
    status: str
    is_enabled: bool
    last_check_in: Optional[datetime]
    next_check_in_due: Optional[datetime]
    created_at: datetime
    is_overdue: bool

    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    id: int
    check_in_time: datetime
    notes: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


class EmergencyContactResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    contact_relationship: Optional[str]
    priority: int

    class Config:
        from_attributes = True


class SwitchCreate(BaseModel):
    name: str
    description: Optional[str] = None
    check_in_interval_hours: int = 24
    grace_period_hours: int = 2


class CheckInCreate(BaseModel):
    notes: Optional[str] = None
    location: Optional[str] = None


class EmergencyContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_relationship: Optional[str] = None
    priority: int = 1


# Utility functions
async def calculate_switch_status(switch: DeadmanSwitch) -> dict:
    """Calculate switch status and timing"""
    now = datetime.utcnow()
    
    if not switch.last_check_in:
        # If never checked in, use creation time
        deadline = switch.created_at + switch.check_in_interval + switch.grace_period
        next_due = switch.created_at + switch.check_in_interval
    else:
        deadline = switch.last_check_in + switch.check_in_interval + switch.grace_period
        next_due = switch.last_check_in + switch.check_in_interval
    
    is_overdue = now > deadline
    
    return {
        "next_check_in_due": next_due,
        "is_overdue": is_overdue,
        "deadline": deadline
    }


# API Routes
@router.get("/switches", response_model=List[SwitchResponse])
async def get_switches(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all switches for current user"""
    switches_result = await db.execute(
        select(DeadmanSwitch)
        .where(DeadmanSwitch.user_id == current_user.id)
        .order_by(desc(DeadmanSwitch.created_at))
    )
    switches = switches_result.scalars().all()
    
    # Add calculated fields
    switch_responses = []
    for switch in switches:
        status_info = await calculate_switch_status(switch)
        
        switch_response = SwitchResponse(
            id=switch.id,
            name=switch.name,
            description=switch.description,
            check_in_interval_hours=int(switch.check_in_interval.total_seconds() // 3600),
            grace_period_hours=int(switch.grace_period.total_seconds() // 3600),
            status=switch.status,
            is_enabled=switch.is_enabled,
            last_check_in=switch.last_check_in,
            next_check_in_due=status_info["next_check_in_due"],
            created_at=switch.created_at,
            is_overdue=status_info["is_overdue"]
        )
        switch_responses.append(switch_response)
    
    return switch_responses


@router.get("/switches/{switch_id}", response_model=SwitchResponse)
async def get_switch(
    switch_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific switch"""
    switch_result = await db.execute(
        select(DeadmanSwitch)
        .where(
            DeadmanSwitch.id == switch_id,
            DeadmanSwitch.user_id == current_user.id
        )
    )
    switch = switch_result.scalar_one_or_none()
    
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    
    status_info = await calculate_switch_status(switch)
    
    return SwitchResponse(
        id=switch.id,
        name=switch.name,
        description=switch.description,
        check_in_interval_hours=int(switch.check_in_interval.total_seconds() // 3600),
        grace_period_hours=int(switch.grace_period.total_seconds() // 3600),
        status=switch.status,
        is_enabled=switch.is_enabled,
        last_check_in=switch.last_check_in,
        next_check_in_due=status_info["next_check_in_due"],
        created_at=switch.created_at,
        is_overdue=status_info["is_overdue"]
    )


@router.post("/switches", response_model=SwitchResponse)
async def create_switch(
    switch_data: SwitchCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new deadman switch"""
    # Validation
    if switch_data.check_in_interval_hours < 1:
        raise HTTPException(
            status_code=400,
            detail="Check-in interval must be at least 1 hour"
        )
    
    if switch_data.grace_period_hours < 0:
        raise HTTPException(
            status_code=400,
            detail="Grace period cannot be negative"
        )
    
    # Create switch
    switch = DeadmanSwitch(
        user_id=current_user.id,
        name=switch_data.name,
        description=switch_data.description,
        check_in_interval=timedelta(hours=switch_data.check_in_interval_hours),
        grace_period=timedelta(hours=switch_data.grace_period_hours),
        status=SwitchStatus.ACTIVE,
        is_enabled=True,
        next_check_in_due=datetime.utcnow() + timedelta(hours=switch_data.check_in_interval_hours)
    )
    
    db.add(switch)
    await db.commit()
    await db.refresh(switch)
    
    status_info = await calculate_switch_status(switch)
    
    return SwitchResponse(
        id=switch.id,
        name=switch.name,
        description=switch.description,
        check_in_interval_hours=switch_data.check_in_interval_hours,
        grace_period_hours=switch_data.grace_period_hours,
        status=switch.status,
        is_enabled=switch.is_enabled,
        last_check_in=switch.last_check_in,
        next_check_in_due=status_info["next_check_in_due"],
        created_at=switch.created_at,
        is_overdue=status_info["is_overdue"]
    )


@router.post("/switches/{switch_id}/check-in", response_model=CheckInResponse)
async def check_in(
    switch_id: int,
    check_in_data: CheckInCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform check-in for a switch"""
    switch_result = await db.execute(
        select(DeadmanSwitch)
        .where(
            DeadmanSwitch.id == switch_id,
            DeadmanSwitch.user_id == current_user.id
        )
    )
    switch = switch_result.scalar_one_or_none()
    
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    
    if not switch.is_enabled:
        raise HTTPException(status_code=400, detail="Switch is disabled")
    
    # Create check-in record
    check_in_record = CheckIn(
        user_id=current_user.id,
        deadman_switch_id=switch_id,
        check_in_time=datetime.utcnow(),
        notes=check_in_data.notes,
        location=check_in_data.location
    )
    
    # Update switch
    switch.last_check_in = datetime.utcnow()
    switch.next_check_in_due = datetime.utcnow() + switch.check_in_interval
    if switch.status == SwitchStatus.TRIGGERED:
        switch.status = SwitchStatus.ACTIVE
        switch.triggered_at = None
    
    db.add(check_in_record)
    await db.commit()
    await db.refresh(check_in_record)
    
    return CheckInResponse(
        id=check_in_record.id,
        check_in_time=check_in_record.check_in_time,
        notes=check_in_record.notes,
        location=check_in_record.location
    )


@router.get("/switches/{switch_id}/check-ins", response_model=List[CheckInResponse])
async def get_check_ins(
    switch_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get check-in history for a switch"""
    # Verify switch ownership
    switch_result = await db.execute(
        select(DeadmanSwitch)
        .where(
            DeadmanSwitch.id == switch_id,
            DeadmanSwitch.user_id == current_user.id
        )
    )
    switch = switch_result.scalar_one_or_none()
    
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    
    check_ins_result = await db.execute(
        select(CheckIn)
        .where(CheckIn.deadman_switch_id == switch_id)
        .order_by(desc(CheckIn.check_in_time))
        .limit(limit)
    )
    check_ins = check_ins_result.scalars().all()
    
    return [
        CheckInResponse(
            id=check_in.id,
            check_in_time=check_in.check_in_time,
            notes=check_in.notes,
            location=check_in.location
        )
        for check_in in check_ins
    ]


@router.get("/switches/{switch_id}/contacts", response_model=List[EmergencyContactResponse])
async def get_emergency_contacts(
    switch_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get emergency contacts for a switch"""
    # Verify switch ownership
    switch_result = await db.execute(
        select(DeadmanSwitch)
        .where(
            DeadmanSwitch.id == switch_id,
            DeadmanSwitch.user_id == current_user.id
        )
    )
    switch = switch_result.scalar_one_or_none()
    
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    
    contacts_result = await db.execute(
        select(EmergencyContact)
        .where(EmergencyContact.deadman_switch_id == switch_id)
        .order_by(EmergencyContact.priority)
    )
    contacts = contacts_result.scalars().all()
    
    return [
        EmergencyContactResponse(
            id=contact.id,
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            contact_relationship=contact.contact_relationship,
            priority=contact.priority
        )
        for contact in contacts
    ]


@router.post("/switches/{switch_id}/contacts", response_model=EmergencyContactResponse)
async def add_emergency_contact(
    switch_id: int,
    contact_data: EmergencyContactCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add emergency contact to switch"""
    # Verify switch ownership
    switch_result = await db.execute(
        select(DeadmanSwitch)
        .where(
            DeadmanSwitch.id == switch_id,
            DeadmanSwitch.user_id == current_user.id
        )
    )
    switch = switch_result.scalar_one_or_none()
    
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    
    contact = EmergencyContact(
        deadman_switch_id=switch_id,
        name=contact_data.name,
        email=contact_data.email,
        phone=contact_data.phone,
        contact_relationship=contact_data.contact_relationship,
        priority=contact_data.priority
    )
    
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    
    return EmergencyContactResponse(
        id=contact.id,
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        contact_relationship=contact.contact_relationship,
        priority=contact.priority
    )
