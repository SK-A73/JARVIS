"""
Probabilistic Emotion and Context Awareness Engine
Infers user tone and emotional context to modulate communication style and urgency.
"""
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel

class EmotionContext(BaseModel):
    state: str  # Calm | Urgent | Frustrated | Confused | Stressed | Happy | Neutral
    confidence: float  # 0.0 to 1.0
    empathetic_phrase: Optional[str] = None
    brevity_level: str = "normal"  # concise | normal | detailed
    should_pause_for_confirmation: bool = False

class EmotionEngine:
    # Heuristic cue patterns for fast, deterministic context inference
    URGENT_PATTERNS = [
        r'\basap\b', r'\burgent\b', r'\bimmediately\b', r'\bquick\b', r'\bright now\b',
        r'\bcritical\b', r'\bproduction down\b', r'\bemergency\b', r'!{2,}'
    ]
    FRUSTRATED_PATTERNS = [
        r'\bwhy is this failing\b', r'\bthis is broken\b', r'\bstill not working\b',
        r'\bwhat is wrong with\b', r'\bstop failing\b', r'\bannoying\b', r'\bterrible\b',
        r'\bwtf\b', r'\bdammit\b', r'\bhorrible\b'
    ]
    CONFUSED_PATTERNS = [
        r'\bi don\'t understand\b', r'\bwhat does this mean\b', r'\bhow come\b',
        r'\bconfused\b', r'\bwhat happened\b', r'\bwhy did it\b', r'\bexplain\b'
    ]
    HAPPY_PATTERNS = [
        r'\bgreat job\b', r'\bawesome\b', r'\bperfect\b', r'\bthank you\b',
        r'\bthanks\b', r'\bbrilliant\b', r'\bexcellent\b', r'\bamazing\b'
    ]

    @classmethod
    def infer_emotion(cls, text: str) -> EmotionContext:
        """
        Infers emotional context probabilistically from message text.
        Never asserts absolute certainty about user psychological state.
        """
        clean = text.lower().strip()
        if not clean:
            return EmotionContext(state="Neutral", confidence=1.0)

        # 1. Frustrated check
        for pat in cls.FRUSTRATED_PATTERNS:
            if re.search(pat, clean):
                return EmotionContext(
                    state="Frustrated",
                    confidence=0.85,
                    empathetic_phrase="You seem frustrated. I'll focus directly on diagnosing and resolving the issue.",
                    brevity_level="concise",
                    should_pause_for_confirmation=False
                )

        # 2. Urgent check
        for pat in cls.URGENT_PATTERNS:
            if re.search(pat, clean):
                return EmotionContext(
                    state="Urgent",
                    confidence=0.90,
                    empathetic_phrase="Understood, treating this with high priority.",
                    brevity_level="concise",
                    should_pause_for_confirmation=False
                )

        # 3. Confused check
        for pat in cls.CONFUSED_PATTERNS:
            if re.search(pat, clean):
                return EmotionContext(
                    state="Confused",
                    confidence=0.80,
                    empathetic_phrase="Let me break this down step-by-step to clarify.",
                    brevity_level="detailed",
                    should_pause_for_confirmation=False
                )

        # 4. Happy / Satisfied check
        for pat in cls.HAPPY_PATTERNS:
            if re.search(pat, clean):
                return EmotionContext(
                    state="Happy",
                    confidence=0.85,
                    empathetic_phrase="Glad to hear that!",
                    brevity_level="normal"
                )

        # Default Calm
        return EmotionContext(state="Calm", confidence=0.75, brevity_level="normal")
