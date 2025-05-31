"""
Admin Interface Module
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from .database import get_db
from .models import User, DeadmanSwitch, CheckIn, Notification, SystemSettings, UserRole, SwitchStatus
from .auth import get_admin_user

# Templates
templates = Jinja2Templates(directory="templates")

# Router
router = APIRouter()


# Pydantic models
class DashboardStats(BaseModel):
    total_users: int
    active_switches: int
    triggered_switches: int
    recent_check_ins: int
    pending_notifications: int


class UserStats(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    switch_count: int
    last_check_in: Optional[datetime]
    created_at: datetime


# Utility functions
async def get_dashboard_stats(db: AsyncSession) -> DashboardStats:
    """Get dashboard statistics"""
    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar()
    
    # Active switches
    active_switches_result = await db.execute(
        select(func.count(DeadmanSwitch.id)).where(
            DeadmanSwitch.status == SwitchStatus.ACTIVE,
            DeadmanSwitch.is_enabled == True
        )
    )
    active_switches = active_switches_result.scalar()
    
    # Triggered switches
    triggered_switches_result = await db.execute(
        select(func.count(DeadmanSwitch.id)).where(
            DeadmanSwitch.status == SwitchStatus.TRIGGERED
        )
    )
    triggered_switches = triggered_switches_result.scalar()
    
    # Recent check-ins (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_check_ins_result = await db.execute(
        select(func.count(CheckIn.id)).where(CheckIn.check_in_time >= yesterday)
    )
    recent_check_ins = recent_check_ins_result.scalar()
    
    # Pending notifications
    pending_notifications_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.status == "pending"
        )
    )
    pending_notifications = pending_notifications_result.scalar()
    
    return DashboardStats(
        total_users=total_users,
        active_switches=active_switches,
        triggered_switches=triggered_switches,
        recent_check_ins=recent_check_ins,
        pending_notifications=pending_notifications
    )


# Routes
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin dashboard"""
    stats = await get_dashboard_stats(db)
    
    # Recent triggered switches
    triggered_switches_result = await db.execute(
        select(DeadmanSwitch)
        .options(selectinload(DeadmanSwitch.user))
        .where(DeadmanSwitch.status == SwitchStatus.TRIGGERED)
        .order_by(desc(DeadmanSwitch.updated_at))
        .limit(10)
    )
    triggered_switches = triggered_switches_result.scalars().all()

    # Recent check-ins
    recent_check_ins_result = await db.execute(
        select(CheckIn)
        .options(selectinload(CheckIn.user), selectinload(CheckIn.deadman_switch))
        .order_by(desc(CheckIn.check_in_time))
        .limit(10)
    )
    recent_check_ins = recent_check_ins_result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": admin_user,
            "stats": stats,
            "triggered_switches": triggered_switches,
            "recent_check_ins": recent_check_ins
        }
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin users management"""
    # Get all users with their switch counts and last check-in
    users_result = await db.execute(
        select(User)
        .order_by(desc(User.created_at))
    )
    users = users_result.scalars().all()
    
    # Get additional stats for each user
    user_stats = []
    for user in users:
        # Count switches
        switch_count_result = await db.execute(
            select(func.count(DeadmanSwitch.id)).where(DeadmanSwitch.user_id == user.id)
        )
        switch_count = switch_count_result.scalar()
        
        # Last check-in
        last_check_in_result = await db.execute(
            select(CheckIn.check_in_time)
            .where(CheckIn.user_id == user.id)
            .order_by(desc(CheckIn.check_in_time))
            .limit(1)
        )
        last_check_in = last_check_in_result.scalar()
        
        user_stats.append(UserStats(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            switch_count=switch_count,
            last_check_in=last_check_in,
            created_at=user.created_at
        ))
    
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": admin_user,
            "users": user_stats
        }
    )


@router.get("/switches", response_class=HTMLResponse)
async def admin_switches(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin switches management"""
    switches_result = await db.execute(
        select(DeadmanSwitch)
        .order_by(desc(DeadmanSwitch.created_at))
    )
    switches = switches_result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/switches.html",
        {
            "request": request,
            "user": admin_user,
            "switches": switches
        }
    )


@router.get("/notifications", response_class=HTMLResponse)
async def admin_notifications(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin notifications management"""
    notifications_result = await db.execute(
        select(Notification)
        .order_by(desc(Notification.created_at))
        .limit(100)
    )
    notifications = notifications_result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/notifications.html",
        {
            "request": request,
            "user": admin_user,
            "notifications": notifications
        }
    )


@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin system settings"""
    settings_result = await db.execute(select(SystemSettings))
    settings = settings_result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "user": admin_user,
            "settings": settings
        }
    )


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle user active status"""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    await db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/switches/{switch_id}/toggle-enabled")
async def toggle_switch_enabled(
    switch_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle switch enabled status"""
    switch_result = await db.execute(select(DeadmanSwitch).where(DeadmanSwitch.id == switch_id))
    switch = switch_result.scalar_one_or_none()
    
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    
    switch.is_enabled = not switch.is_enabled
    if not switch.is_enabled:
        switch.status = SwitchStatus.DISABLED
    else:
        switch.status = SwitchStatus.ACTIVE
    
    await db.commit()

    return RedirectResponse(url="/admin/switches", status_code=302)


@router.post("/switches/{switch_id}/delete")
async def delete_switch_admin(
    switch_id: int,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a switch (admin only)"""
    # Get switch
    result = await db.execute(
        select(DeadmanSwitch).where(DeadmanSwitch.id == switch_id)
    )
    switch = result.scalar_one_or_none()

    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")

    # Delete the switch
    await db.execute(
        DeadmanSwitch.__table__.delete().where(DeadmanSwitch.id == switch_id)
    )
    await db.commit()

    return RedirectResponse(url="/admin/switches", status_code=302)


@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin settings page"""
    # Get system settings
    settings_result = await db.execute(
        select(SystemSettings).order_by(SystemSettings.key)
    )
    settings = settings_result.scalars().all()

    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "user": admin_user,
            "settings": settings
        }
    )


@router.post("/settings/update")
async def update_settings(
    request: Request,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update system settings"""
    form = await request.form()
    
    for key, value in form.items():
        if key.startswith("setting_"):
            setting_key = key.replace("setting_", "")
            
            # Check if setting exists
            setting_result = await db.execute(
                select(SystemSettings).where(SystemSettings.key == setting_key)
            )
            setting = setting_result.scalar_one_or_none()
            
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
            else:
                # Create new setting
                new_setting = SystemSettings(
                    key=setting_key,
                    value=value,
                    description=f"Setting for {setting_key}"
                )
                db.add(new_setting)
    
    await db.commit()
    
    return RedirectResponse(url="/admin/settings", status_code=302)
