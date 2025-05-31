#!/usr/bin/env python3
"""
Script to create an admin user for the Deadman Switch application
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deadman_switch.database import get_async_session
from deadman_switch.models import User, UserRole
from deadman_switch.auth import get_password_hash


async def create_admin_user():
    """Create an admin user"""
    async for session in get_async_session():
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@deadmanswitch.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"Admin user created successfully!")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Password: admin123")
        print(f"Please change the password after first login.")
        
        break


if __name__ == "__main__":
    asyncio.run(create_admin_user())
