"""
Memory API Router
Endpoints for querying, creating, and managing JARVIS memory records.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.memory import MemoryRecord
from backend.app.memory.manager import MemoryManager
from backend.app.llm.factory import LLMProviderFactory
from backend.app.core.security import get_current_user_or_device

router = APIRouter(prefix="/api/v1/memory", tags=["Memory Management"])

class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    category: str = Field("long_term", description="short_term | long_term | project | episodic")
    project_id: Optional[str] = None
    importance: float = Field(5.0, ge=1.0, le=10.0)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    summary: Optional[str] = None

class MemorySearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    category: Optional[str] = None
    limit: int = Field(5, ge=1, le=20)

class MemoryRecordResponse(BaseModel):
    id: str
    content: str
    category: str
    summary: Optional[str]
    project_id: Optional[str]
    source: str
    importance: float
    confidence: float
    created_at: Any

@router.post("", response_model=MemoryRecordResponse)
async def create_memory(
    req: MemoryCreateRequest,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    provider = LLMProviderFactory.get_provider()
    manager = MemoryManager(db, provider)
    record = await manager.add_memory(
        content=req.content,
        category=req.category,
        project_id=req.project_id,
        importance=req.importance,
        confidence=req.confidence,
        summary=req.summary
    )
    return MemoryRecordResponse(
        id=record.id,
        content=record.content,
        category=record.category,
        summary=record.summary,
        project_id=record.project_id,
        source=record.source,
        importance=record.importance,
        confidence=record.confidence,
        created_at=record.created_at
    )

@router.get("", response_model=List[MemoryRecordResponse])
def list_memories(
    category: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    q = db.query(MemoryRecord)
    if category:
        q = q.filter(MemoryRecord.category == category)
    if project_id:
        q = q.filter(MemoryRecord.project_id == project_id)
    records = q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
    return [
        MemoryRecordResponse(
            id=r.id,
            content=r.content,
            category=r.category,
            summary=r.summary,
            project_id=r.project_id,
            source=r.source,
            importance=r.importance,
            confidence=r.confidence,
            created_at=r.created_at
        )
        for r in records
    ]

@router.post("/search")
async def search_memories(
    req: MemorySearchRequest,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    provider = LLMProviderFactory.get_provider()
    manager = MemoryManager(db, provider)
    results = await manager.retrieve_relevant(
        query=req.query,
        project_id=req.project_id,
        category=req.category,
        limit=req.limit
    )
    return [
        {
            "id": r.id,
            "content": r.content,
            "category": r.category,
            "project_id": r.project_id,
            "importance": r.importance,
            "score": round(score, 4)
        }
        for r, score in results
    ]

@router.delete("/{memory_id}")
def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    manager = MemoryManager(db)
    if not manager.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success", "message": f"Memory {memory_id} deleted"}

@router.delete("/project/{project_id}")
def purge_project_memories(
    project_id: str,
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    manager = MemoryManager(db)
    count = manager.purge_project_memories(project_id)
    return {"status": "success", "purged_count": count}

@router.get("/stats")
def get_memory_stats(
    db: Session = Depends(get_db),
    auth_data: dict = Depends(get_current_user_or_device)
):
    stats = db.query(MemoryRecord.category, func.count(MemoryRecord.id)).group_by(MemoryRecord.category).all()
    return {"counts_by_category": {cat: count for cat, count in stats}, "total": sum(c for _, c in stats)}
