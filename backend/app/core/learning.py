"""
Adaptive Learning Engine
Extracts learned patterns, user preferences, and corrections into persistent, reversible knowledge.
"""
import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.memory import LearnedPattern

logger = logging.getLogger(__name__)

class LearningEngine:
    def __init__(self, db: Session):
        self.db = db

    # Regex patterns for explicit user corrections
    CORRECTION_PATTERNS = [
        r"(?:don\'t|do not|never)\s+(?:use|do|write)\s+([^,.;]+)[,.;\s]+(?:always\s+)?use\s+([^,.;]+)",
        r"(?:i prefer|always use|prefer)\s+([^,.;]+)\s+(?:over|instead of)\s+([^,.;]+)",
        r"(?:from now on|in the future)[,\s]+(?:always\s+)?([^,.;]+)"
    ]

    def analyze_and_learn_from_feedback(
        self,
        user_input: str,
        scope: str = "global"
    ) -> Optional[LearnedPattern]:
        """Detects whether user is providing a rule or correction and stores it as a reversible pattern."""
        text = user_input.strip()

        # Check pattern: "Don't use X, use Y"
        match1 = re.search(self.CORRECTION_PATTERNS[0], text, re.IGNORECASE)
        if match1:
            avoid_item = match1.group(1).strip()
            prefer_item = match1.group(2).strip()
            description = f"User prefers {prefer_item} over {avoid_item}"
            return self.record_pattern(
                pattern_type="user_preference",
                description=description,
                evidence=text,
                scope=scope,
                confidence=0.85
            )

        # Check pattern: "I prefer X over Y"
        match2 = re.search(self.CORRECTION_PATTERNS[1], text, re.IGNORECASE)
        if match2:
            prefer_item = match2.group(1).strip()
            avoid_item = match2.group(2).strip()
            description = f"User prefers {prefer_item} over {avoid_item}"
            return self.record_pattern(
                pattern_type="user_preference",
                description=description,
                evidence=text,
                scope=scope,
                confidence=0.85
            )

        return None

    def record_pattern(
        self,
        pattern_type: str,
        description: str,
        evidence: Optional[str] = None,
        scope: str = "global",
        confidence: float = 0.8
    ) -> LearnedPattern:
        """Stores or updates a learned behavioral pattern."""
        existing = self.db.query(LearnedPattern).filter(
            LearnedPattern.description == description,
            LearnedPattern.scope == scope
        ).first()

        if existing:
            existing.times_applied += 1
            existing.confidence = min(0.99, existing.confidence + 0.05)
            existing.last_applied = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        pattern = LearnedPattern(
            pattern_type=pattern_type,
            description=description,
            evidence=evidence,
            confidence=confidence,
            scope=scope,
            is_active=True,
            times_applied=1,
            last_applied=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        return pattern

    def get_active_patterns(self, scope: Optional[str] = None) -> List[LearnedPattern]:
        """Retrieves active learned patterns for prompt context."""
        q = self.db.query(LearnedPattern).filter(LearnedPattern.is_active == True)
        if scope:
            q = q.filter(LearnedPattern.scope.in_(["global", scope]))
        return q.order_by(LearnedPattern.confidence.desc()).all()

    def deactivate_pattern(self, pattern_id: str) -> bool:
        """Reversibly deactivates a learned pattern."""
        p = self.db.query(LearnedPattern).filter(LearnedPattern.id == pattern_id).first()
        if p:
            p.is_active = False
            self.db.commit()
            return True
        return False
