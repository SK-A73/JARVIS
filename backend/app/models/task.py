"""
Task Management and Audit Logging Models
Supports 24/7 persistent background tasks, step tracking, and security audit.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, JSON, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from backend.app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    project_id = Column(String(36), ForeignKey("project_contexts.id"), nullable=True)
    target_device_id = Column(String(64), ForeignKey("device_nodes.id"), nullable=True)
    title = Column(String(256), nullable=False)
    user_request = Column(Text, nullable=False)
    mode = Column(String(32), default="AUTONOMOUS")  # PLAN | IMPLEMENT | TEST | RECTIFY | AUTONOMOUS
    status = Column(String(32), default="QUEUED", index=True)
    # Statuses: QUEUED | PLANNING | IMPLEMENTING | TESTING | RECTIFYING | WAITING_FOR_USER | COMPLETED | FAILED | CANCELLED
    priority = Column(Integer, default=5)  # 1 (lowest) to 10 (highest)
    current_step = Column(String(256), nullable=True)
    plan_data = Column(JSON, default=dict)
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=5)
    created_at = Column(DateTime, default=utc_now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="tasks")
    project = relationship("ProjectContext", back_populates="tasks")
    target_device = relationship("DeviceNode", back_populates="tasks")
    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan", order_by="TaskStep.step_number")
    audit_logs = relationship("AuditLog", back_populates="task", cascade="all, delete-orphan")

class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    name = Column(String(128), nullable=False)
    status = Column(String(32), default="PENDING")  # PENDING | RUNNING | SUCCESS | FAILED | SKIPPED
    tool_name = Column(String(64), nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    task = relationship("Task", back_populates="steps")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(String(64), nullable=True)
    action = Column(String(128), nullable=False, index=True)
    target = Column(String(512), nullable=True)
    command = Column(Text, nullable=True)
    status = Column(String(32), default="SUCCESS")
    risk_level = Column(String(32), default="LOW")  # LOW | MEDIUM | HIGH | CRITICAL
    requires_approval = Column(Boolean, default=False)
    user_approved = Column(Boolean, nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now, index=True)

    task = relationship("Task", back_populates="audit_logs")
