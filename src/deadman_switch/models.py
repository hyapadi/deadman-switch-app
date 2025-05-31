"""
Database Models for Deadman Switch Application
"""
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Interval
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserRole(str, Enum):
    ADMIN = "admin"
    CLIENT = "client"


class SwitchStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    DISABLED = "disabled"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    deadman_switches = relationship("DeadmanSwitch", back_populates="user", cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="user", cascade="all, delete-orphan")


class DeadmanSwitch(Base):
    __tablename__ = "deadman_switches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    check_in_interval = Column(Interval, default=timedelta(hours=24))  # How often user must check in
    grace_period = Column(Interval, default=timedelta(hours=2))  # Extra time before triggering
    status = Column(String(20), default=SwitchStatus.ACTIVE)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_check_in = Column(DateTime(timezone=True))
    next_check_in_due = Column(DateTime(timezone=True))
    triggered_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="deadman_switches")
    check_ins = relationship("CheckIn", back_populates="deadman_switch", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="deadman_switch", cascade="all, delete-orphan")
    emergency_contacts = relationship("EmergencyContact", back_populates="deadman_switch", cascade="all, delete-orphan")


class CheckIn(Base):
    __tablename__ = "check_ins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    deadman_switch_id = Column(Integer, ForeignKey("deadman_switches.id"), nullable=False)
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    location = Column(String(255))  # Optional location info
    notes = Column(Text)  # Optional user notes
    
    # Relationships
    user = relationship("User", back_populates="check_ins")
    deadman_switch = relationship("DeadmanSwitch", back_populates="check_ins")


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    deadman_switch_id = Column(Integer, ForeignKey("deadman_switches.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    contact_relationship = Column(String(100))  # e.g., "spouse", "friend", "lawyer"
    priority = Column(Integer, default=1)  # 1 = highest priority
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deadman_switch = relationship("DeadmanSwitch", back_populates="emergency_contacts")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    deadman_switch_id = Column(Integer, ForeignKey("deadman_switches.id"), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_phone = Column(String(20))
    subject = Column(String(500))
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))  # "warning", "trigger", "test"
    status = Column(String(20), default=NotificationStatus.PENDING)
    scheduled_for = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    error_message = Column(Text)
    
    # Relationships
    deadman_switch = relationship("DeadmanSwitch", back_populates="notifications")


class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
