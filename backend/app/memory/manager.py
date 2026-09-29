"""
Multilayer Memory Manager
Coordinates short-term working memory, persistent long-term memory,
project memory, episodic events, and natural memory commands.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from backend.app.models.memory import MemoryRecord, ProjectContext, LearnedPattern
from backend.app.memory.retriever import HybridRetriever
from backend.app.llm.base import LLMProvider
from backend.app.config import settings

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, db: Session, llm_provider: Optional[LLMProvider] = None):
        self.db = db
        self.llm_provider = llm_provider

    async def add_memory(
        self,
        content: str,
        category: str = "long_term",  # short_term | long_term | project | episodic
        project_id: Optional[str] = None,
        source: str = "user_conversation",
        importance: float = 5.0,
        confidence: float = 1.0,
        summary: Optional[str] = None,
        metadata_info: Optional[Dict[str, Any]] = None
    ) -> MemoryRecord:
        """Stores a new memory record with vector embeddings."""
        embedding = None
        if self.llm_provider:
            try:
                embeddings = await self.llm_provider.generate_embeddings([content])
                if embeddings and embeddings[0]:
                    embedding = embeddings[0]
            except Exception as e:
                logger.warning(f"Failed to generate embedding for memory: {e}")

        clean_summary = summary or (content[:97] + "..." if len(content) > 100 else content)

        record = MemoryRecord(
            content=content,
            category=category,
            project_id=project_id,
            source=source,
            importance=min(10.0, max(1.0, importance)),
            confidence=min(1.0, max(0.0, confidence)),
            summary=clean_summary,
            embedding=embedding,
            metadata_info=metadata_info or {},
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    async def retrieve_relevant(
        self,
        query: str,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 5,
        min_threshold: float = 0.05
    ) -> List[Tuple[MemoryRecord, float]]:
        """Retrieves and ranks relevant memories using hybrid vector + keyword matching."""
        # Query candidates from DB
        filters = []
        if category:
            filters.append(MemoryRecord.category == category)
        if project_id:
            # Match project specific memories OR general long-term memories
            filters.append(or_(MemoryRecord.project_id == project_id, MemoryRecord.project_id.is_(None)))

        q = self.db.query(MemoryRecord)
        if filters:
            q = q.filter(and_(*filters))

        candidates = q.all()
        if not candidates:
            return []

        # Generate query embedding if provider available
        query_embedding = None
        if self.llm_provider:
            try:
                embs = await self.llm_provider.generate_embeddings([query])
                if embs and embs[0]:
                    query_embedding = embs[0]
            except Exception as e:
                logger.warning(f"Query embedding generation failed: {e}")

        ranked = HybridRetriever.rank_memories(
            query=query,
            query_embedding=query_embedding,
            candidates=candidates,
            min_threshold=min_threshold
        )
        return ranked[:limit]

    def delete_memory(self, memory_id: str) -> bool:
        """Deletes a single memory record by ID."""
        record = self.db.query(MemoryRecord).filter(MemoryRecord.id == memory_id).first()
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False

    def purge_project_memories(self, project_id: str) -> int:
        """Purges all memories associated with a given project ID."""
        count = self.db.query(MemoryRecord).filter(MemoryRecord.project_id == project_id).delete()
        self.db.commit()
        return count

    async def handle_natural_memory_command(
        self,
        user_input: str,
        project_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Parses and handles natural user memory commands:
        'Remember this/that...', 'Forget this/that...', 'What do you remember about...?'
        Returns a dict if handled, or None if it's a regular conversation turn.
        """
        text = user_input.strip()
        lower = text.lower()

        # 1. "Remember that / Remember this"
        rem_match = re.match(r'^(?:jarvis,?\s*)?remember\s+(?:that|this)?\s*[:,-]?\s*(.+)$', lower, re.IGNORECASE)
        if rem_match:
            mem_content = rem_match.group(1).strip()
            cat = "project" if project_id else "long_term"
            rec = await self.add_memory(
                content=mem_content,
                category=cat,
                project_id=project_id,
                importance=8.0,
                source="user_explicit_command"
            )
            return {
                "handled": True,
                "action": "remembered",
                "message": f"I have stored that in my {'project' if project_id else 'long-term'} memory: \"{mem_content}\"",
                "memory_id": rec.id
            }

        # 2. "Forget that / Forget this / Forget [topic]"
        forget_match = re.match(r'^(?:jarvis,?\s*)?forget\s+(?:that|this)?\s*[:,-]?\s*(.+)$', lower, re.IGNORECASE)
        if forget_match:
            topic = forget_match.group(1).strip()
            relevant = await self.retrieve_relevant(query=topic, project_id=project_id, limit=3)
            if relevant:
                target_mem, score = relevant[0]
                self.delete_memory(target_mem.id)
                return {
                    "handled": True,
                    "action": "forgot",
                    "message": f"I have removed the following memory: \"{target_mem.content}\"",
                    "memory_id": target_mem.id
                }
            else:
                return {
                    "handled": True,
                    "action": "not_found",
                    "message": f"I couldn't find any relevant memory matching \"{topic}\" to forget."
                }

        # 3. "What do you remember about me / this project / [topic]?"
        query_match = re.match(r'^(?:jarvis,?\s*)?what\s+do\s+you\s+remember\s+about\s+(.+)\??$', lower, re.IGNORECASE)
        if query_match:
            topic = query_match.group(1).strip()
            relevant = await self.retrieve_relevant(query=topic, project_id=project_id, limit=5)
            if relevant:
                items_str = "\n".join([f"• [{m.category}] {m.content}" for m, s in relevant])
                return {
                    "handled": True,
                    "action": "retrieved",
                    "message": f"Here is what I remember about '{topic}':\n{items_str}",
                    "memories": [{"id": m.id, "content": m.content, "category": m.category} for m, s in relevant]
                }
            else:
                return {
                    "handled": True,
                    "action": "empty",
                    "message": f"I have no stored memories regarding '{topic}'."
                }

        return None
