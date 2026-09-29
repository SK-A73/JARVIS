"""
Task Management API Router
Endpoints for submitting, monitoring, interrupting, and resuming autonomous background tasks.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.task import Task, TaskStep
from backend.app.agent.task_queue import TaskQueue
from backend.app.agent.modes import ModePolicy, OperatingMode
from backend.app.core.security import get_current_user_or_device

router = APIRouter(prefix="/api/v1/tasks", tags=["Task Management"])

class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=256)
    user_request: str = Field(..., min_length=3)
    mode: Optional[str] = None  # If omitted, auto-detected from prompt
    project_id: Optional[str] = None
    target_device_id: Optional[str] = None
    priority: int = Field(5, ge=1, le=10)

class TaskStepResponse(BaseModel):
    step_number: int
    name: str
    status: str
    tool_name: Optional[str]
    tool_output: Optional[str]
    error: Optional[str]
    created_at: Any

class TaskDetailResponse(BaseModel):
    id: str
    title: str
    user_request: str
    mode: str
    status: str
    current_step: Optional[str]
    retry_count: int
    result_summary: Optional[str]
    error_message: Optional[str]
    created_at: Any
    started_at: Optional[Any]
    completed_at: Optional[Any]
    steps: List[TaskStepResponse]

@router.post("", response_model=TaskDetailResponse)
async def create_and_enqueue_task(
    req: TaskCreateRequest,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    # Detect mode if not provided
    detected_mode = req.mode or ModePolicy.detect_mode_from_prompt(req.user_request).value

    user_id = auth_data.get("user_id") if auth_data.get("type") == "user" else None

    task = Task(
        title=req.title,
        user_request=req.user_request,
        mode=detected_mode,
        status="QUEUED",
        priority=req.priority,
        project_id=req.project_id,
        target_device_id=req.target_device_id,
        user_id=user_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Submit to 24/7 background worker queue
    queue = TaskQueue.get_instance()
    await queue.enqueue_task(task.id)

    return TaskDetailResponse(
        id=task.id,
        title=task.title,
        user_request=task.user_request,
        mode=task.mode,
        status=task.status,
        current_step=task.current_step,
        retry_count=task.retry_count,
        result_summary=task.result_summary,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        steps=[]
    )

@router.get("", response_model=List[TaskDetailResponse])
def list_tasks(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    if project_id:
        q = q.filter(Task.project_id == project_id)
    tasks = q.order_by(Task.created_at.desc()).limit(limit).all()

    return [
        TaskDetailResponse(
            id=t.id,
            title=t.title,
            user_request=t.user_request,
            mode=t.mode,
            status=t.status,
            current_step=t.current_step,
            retry_count=t.retry_count,
            result_summary=t.result_summary,
            error_message=t.error_message,
            created_at=t.created_at,
            started_at=t.started_at,
            completed_at=t.completed_at,
            steps=[
                TaskStepResponse(
                    step_number=s.step_number,
                    name=s.name,
                    status=s.status,
                    tool_name=s.tool_name,
                    tool_output=s.tool_output,
                    error=s.error,
                    created_at=s.created_at
                ) for s in t.steps
            ]
        ) for t in tasks
    ]

@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: str, db: Session = Depends(get_db), auth_data: dict = Depends(get_current_user_or_device)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskDetailResponse(
        id=task.id,
        title=task.title,
        user_request=task.user_request,
        mode=task.mode,
        status=task.status,
        current_step=task.current_step,
        retry_count=task.retry_count,
        result_summary=task.result_summary,
        error_message=task.error_message,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        steps=[
            TaskStepResponse(
                step_number=s.step_number,
                name=s.name,
                status=s.status,
                tool_name=s.tool_name,
                tool_output=s.tool_output,
                error=s.error,
                created_at=s.created_at
            ) for s in task.steps
        ]
    )

@router.post("/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db), auth_data: dict = Depends(get_current_user_or_device)):
    """User interruption: stops or cancels an active task."""
    queue = TaskQueue.get_instance()
    success = queue.cancel_task(task_id, db)
    if not success:
        raise HTTPException(status_code=400, detail="Task could not be cancelled or is already finished")
    return {"status": "success", "message": f"Task {task_id} successfully cancelled"}

@router.get("/{task_id}/timeline")
def get_task_timeline(task_id: str, db: Session = Depends(get_db), auth_data: dict = Depends(get_current_user_or_device)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    timeline = []
    timeline.append({
        "time": task.created_at,
        "event": f"Task Created: {task.title}",
        "mode": task.mode
    })
    for s in task.steps:
        timeline.append({
            "time": s.created_at,
            "event": s.name,
            "status": s.status,
            "tool": s.tool_name
        })
    if task.completed_at:
        timeline.append({
            "time": task.completed_at,
            "event": f"Task Completed with status: {task.status}",
            "summary": task.result_summary or task.error_message
        })
    return {"task_id": task.id, "timeline": timeline}

@router.get("/briefing/reconnect")
def get_reconnect_briefing(db: Session = Depends(get_db), auth_data: dict = Depends(get_current_user_or_device)):
    """Returns a natural language briefing of tasks completed while client was away."""
    briefing = TaskQueue.get_reconnect_briefing(db)
    return {"briefing": briefing}
