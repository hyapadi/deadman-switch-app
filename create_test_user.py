#!/usr/bin/env python3
"""
Create a test user for the Deadman Switch application
"""
import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deadman_switch.database import get_async_session
from deadman_switch.models import User, UserRole
from deadman_switch.auth import get_password_hash


async def create_test_user():
    """Create a test user"""
    async for session in get_async_session():
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "user"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Test user 'user' already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Username: {existing_user.username}")
            print(f"Email: {existing_user.email}")
            print(f"Role: {existing_user.role}")
            print(f"Active: {existing_user.is_active}")
            return

        # Create new test user
        test_user = User(
            username="user",
            email="user@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("user123"),
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=True
        )

        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)

        print("✅ Test user created successfully!")
        print(f"Username: {test_user.username}")
        print(f"Password: user123")
        print(f"Email: {test_user.email}")
        print(f"Full Name: {test_user.full_name}")
        print(f"Role: {test_user.role}")
        print(f"User ID: {test_user.id}")
        print()
        print("🌐 You can now login with:")
        print("   Username: user")
        print("   Password: user123")

        break


if __name__ == "__main__":
    asyncio.run(create_test_user())
