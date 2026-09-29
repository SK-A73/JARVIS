"""
Multilayer Memory Models
Supports short-term, long-term, project, episodic, and learned patterns.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, JSON, DateTime, Index, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class ProjectContext(Base):
    __tablename__ = "project_contexts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    workspace_path = Column(String(512), nullable=True)
    tech_stack = Column(JSON, default=list)  # ["FastAPI", "PostgreSQL", "Kotlin", "Compose"]
    architectural_decisions = Column(JSON, default=list)
    constraints = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    memories = relationship("MemoryRecord", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String(32), nullable=False, index=True)  # short_term | long_term | project | episodic
    content = Column(Text, nullable=False)
    summary = Column(String(256), nullable=True)
    project_id = Column(String(36), ForeignKey("project_contexts.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(64), default="user_conversation")  # user_conversation | agent_observation | feedback
    importance = Column(Float, default=1.0)  # 1.0 to 10.0 scale
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0 scale
    embedding = Column(JSON, nullable=True)  # List of floats for cosine similarity search
    metadata_info = Column(JSON, default=dict)
    expires_at = Column(DateTime, nullable=True)  # For short-term retention expiry
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    project = relationship("ProjectContext", back_populates="memories")

    __table_args__ = (
        Index("idx_memory_category_project", "category", "project_id"),
    )

class LearnedPattern(Base):
    __tablename__ = "learned_patterns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pattern_type = Column(String(64), nullable=False)  # user_preference | coding_style | architecture | workflow
    description = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True)  # User quote or event that prompted learning
    confidence = Column(Float, default=0.7)  # Adaptive confidence score
    scope = Column(String(64), default="global")  # global | project:<name>
    is_active = Column(Boolean, default=True)
    times_applied = Column(Integer, default=1)
    last_applied = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
