"""
Client Interface Module
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from .database import get_db
from .models import User, DeadmanSwitch, CheckIn, EmergencyContact, SwitchStatus
from .auth import get_current_active_user

# Templates
templates = Jinja2Templates(directory="templates")

# Router
router = APIRouter()


# Pydantic models
class SwitchCreate(BaseModel):
    name: str
    description: Optional[str] = None
    check_in_interval_hours: int = 24
    grace_period_hours: int = 2


class EmergencyContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_relationship: Optional[str] = None
    priority: int = 1


# Utility functions
async def calculate_next_check_in(switch: DeadmanSwitch) -> datetime:
    """Calculate next check-in time"""
    if switch.last_check_in:
        return switch.last_check_in + switch.check_in_interval
    else:
        return datetime.utcnow() + switch.check_in_interval


async def is_switch_overdue(switch: DeadmanSwitch) -> bool:
    """Check if switch is overdue"""
    if not switch.last_check_in:
        # If never checked in, consider overdue after interval + grace period
        created_deadline = switch.created_at + switch.check_in_interval + switch.grace_period
        return datetime.utcnow() > created_deadline
    
    deadline = switch.last_check_in + switch.check_in_interval + switch.grace_period
    return datetime.utcnow() > deadline


# Routes
@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Client dashboard"""
    # Get user's switches
    switches_result = await db.execute(
        select(DeadmanSwitch)
        .where(DeadmanSwitch.user_id == current_user.id)
        .order_by(desc(DeadmanSwitch.created_at))
    )
    switches = switches_result.scalars().all()
    
    # Calculate status for each switch
    switch_data = []
    for switch in switches:
        next_check_in = await calculate_next_check_in(switch)
        is_overdue = await is_switch_overdue(switch)
        
        switch_data.append({
            "switch": switch,
            "next_check_in": next_check_in,
            "is_overdue": is_overdue,
            "time_until_due": next_check_in - datetime.utcnow() if not is_overdue else None
        })
    
    # Get recent check-ins
    recent_check_ins_result = await db.execute(
        select(CheckIn)
        .where(CheckIn.user_id == current_user.id)
        .order_by(desc(CheckIn.check_in_time))
        .limit(10)
    )
    recent_check_ins = recent_check_ins_result.scalars().all()
    
    return templates.TemplateResponse(
        "client/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "switches": switch_data,
            "recent_check_ins": recent_check_ins
        }
    )


@router.get("/switches", response_class=HTMLResponse)
async def client_switches(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Client switches management"""
    switches_result = await db.execute(
        select(DeadmanSwitch)
        .where(DeadmanSwitch.user_id == current_user.id)
        .order_by(desc(DeadmanSwitch.created_at))
    )
    switches = switches_result.scalars().all()
    
    return templates.TemplateResponse(
        "client/switches.html",
        {
            "request": request,
            "user": current_user,
            "switches": switches
        }
    )


@router.get("/switches/create", response_class=HTMLResponse)
async def create_switch_form(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Create switch form"""
    return templates.TemplateResponse(
        "client/create_switch.html",
        {"request": request, "user": current_user}
    )


@router.post("/switches/create")
async def create_switch(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    check_in_interval_hours: int = Form(24),
    grace_period_hours: int = Form(2),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new deadman switch"""
    # Validation
    if check_in_interval_hours < 1:
        return templates.TemplateResponse(
            "client/create_switch.html",
            {
                "request": request,
                "user": current_user,
                "error": "Check-in interval must be at least 1 hour"
            }
        )
    
    if grace_period_hours < 0:
        return templates.TemplateResponse(
            "client/create_switch.html",
            {
                "request": request,
                "user": current_user,
                "error": "Grace period cannot be negative"
            }
        )
    
    # Create switch
    switch = DeadmanSwitch(
        user_id=current_user.id,
        name=name,
        description=description if description else None,
        check_in_interval=timedelta(hours=check_in_interval_hours),
        grace_period=timedelta(hours=grace_period_hours),
        status=SwitchStatus.ACTIVE,
        is_enabled=True,
        next_check_in_due=datetime.utcnow() + timedelta(hours=check_in_interval_hours)
    )
    
    db.add(switch)
    await db.commit()
    await db.refresh(switch)
    
    return RedirectResponse(url="/client/switches", status_code=302)


@router.get("/switches/{switch_id}", response_class=HTMLResponse)
async def switch_detail(
    switch_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Switch detail page"""
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
    
    # Get emergency contacts
    contacts_result = await db.execute(
        select(EmergencyContact)
        .where(EmergencyContact.deadman_switch_id == switch_id)
        .order_by(EmergencyContact.priority)
    )
    contacts = contacts_result.scalars().all()
    
    # Get check-in history
    check_ins_result = await db.execute(
        select(CheckIn)
        .where(CheckIn.deadman_switch_id == switch_id)
        .order_by(desc(CheckIn.check_in_time))
        .limit(20)
    )
    check_ins = check_ins_result.scalars().all()
    
    # Calculate status
    next_check_in = await calculate_next_check_in(switch)
    is_overdue = await is_switch_overdue(switch)
    
    return templates.TemplateResponse(
        "client/switch_detail.html",
        {
            "request": request,
            "user": current_user,
            "switch": switch,
            "contacts": contacts,
            "check_ins": check_ins,
            "next_check_in": next_check_in,
            "is_overdue": is_overdue
        }
    )


@router.post("/switches/{switch_id}/check-in")
async def check_in(
    switch_id: int,
    notes: str = Form(""),
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
        notes=notes if notes else None
    )
    
    # Update switch
    switch.last_check_in = datetime.utcnow()
    switch.next_check_in_due = datetime.utcnow() + switch.check_in_interval
    if switch.status == SwitchStatus.TRIGGERED:
        switch.status = SwitchStatus.ACTIVE
        switch.triggered_at = None
    
    db.add(check_in_record)
    await db.commit()
    
    return RedirectResponse(url=f"/client/switches/{switch_id}", status_code=302)


@router.post("/switches/{switch_id}/contacts/add")
async def add_emergency_contact(
    switch_id: int,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    contact_relationship: str = Form(""),
    priority: int = Form(1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add emergency contact to switch"""
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
        name=name,
        email=email if email else None,
        phone=phone if phone else None,
        contact_relationship=contact_relationship if contact_relationship else None,
        priority=priority
    )
    
    db.add(contact)
    await db.commit()
    
    return RedirectResponse(url=f"/client/switches/{switch_id}", status_code=302)


@router.post("/switches/{switch_id}/toggle")
async def toggle_switch(
    switch_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle switch enabled/disabled"""
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
    
    switch.is_enabled = not switch.is_enabled
    if not switch.is_enabled:
        switch.status = SwitchStatus.PAUSED
    else:
        switch.status = SwitchStatus.ACTIVE
        switch.next_check_in_due = datetime.utcnow() + switch.check_in_interval
    
    await db.commit()
    
    return RedirectResponse(url="/client/switches", status_code=302)
