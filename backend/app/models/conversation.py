"""
Conversation and Messaging Models
Supports multi-turn dialogs, audio interactions, and emotion tracking.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    device_id = Column(String(64), nullable=True)
    title = Column(String(256), default="New Conversation")
    mode = Column(String(32), default="AUTONOMOUS")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user | assistant | system | tool
    content = Column(Text, nullable=False)
    audio_path = Column(String(512), nullable=True)  # Path to recorded or synthesized audio
    inferred_emotion = Column(String(32), nullable=True)  # Calm | Urgent | Frustrated | etc.
    emotion_confidence = Column(Float, nullable=True)
    tool_calls = Column(JSON, nullable=True)
    tool_results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, index=True)

    conversation = relationship("Conversation", back_populates="messages")
