"""
Authentication and Device Registration Models
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    devices = relationship("DeviceNode", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class DeviceNode(Base):
    __tablename__ = "device_nodes"

    id = Column(String(64), primary_key=True)  # Unique hardware / client device ID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    name = Column(String(128), nullable=False)
    device_type = Column(String(32), nullable=False)  # phone | laptop | desktop | server | smart_device
    api_token_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=utc_now)
    ip_address = Column(String(64), nullable=True)
    platform = Column(String(64), nullable=True)  # Android 14, Windows 11, Linux, etc.
    capabilities = Column(JSON, default=list)  # ["microphone", "speaker", "terminal", "filesystem"]
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="devices")
    tasks = relationship("Task", back_populates="target_device")
