"""
Hybrid Semantic and Keyword Memory Retriever
Combines cosine embedding similarity, keyword matching, and importance weighting.
"""
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from backend.app.models.memory import MemoryRecord

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two numerical vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

def keyword_overlap_score(query: str, text: str) -> float:
    """Calculates query coverage and Jaccard overlap between query and target text."""
    def tokenize(s: str) -> set:
        words = re.findall(r'\b[a-zA-Z0-9_-]{2,}\b', s.lower())
        return set(words)

    q_tokens = tokenize(query)
    t_tokens = tokenize(text)
    if not q_tokens or not t_tokens:
        return 0.0

    intersection = q_tokens.intersection(t_tokens)
    if not intersection:
        return 0.0

    # Query coverage: fraction of query words found in text
    coverage = len(intersection) / len(q_tokens)
    # Jaccard: intersection over union
    jaccard = len(intersection) / len(q_tokens.union(t_tokens))

    return (0.7 * coverage) + (0.3 * jaccard)

class HybridRetriever:
    @staticmethod
    def rank_memories(
        query: str,
        query_embedding: Optional[List[float]],
        candidates: List[MemoryRecord],
        vector_weight: float = 0.6,
        text_weight: float = 0.3,
        importance_weight: float = 0.1,
        min_threshold: float = 0.05
    ) -> List[Tuple[MemoryRecord, float]]:
        """
        Ranks candidate memory records using weighted hybrid score:
        Score = w_vec * sim(vec) + w_txt * overlap(txt) + w_imp * (importance / 10)
        """
        scored_records: List[Tuple[MemoryRecord, float]] = []

        for record in candidates:
            # 1. Vector similarity
            vec_sim = 0.0
            if query_embedding and record.embedding:
                vec_sim = max(0.0, cosine_similarity(query_embedding, record.embedding))

            # 2. Text keyword overlap
            text_sim = keyword_overlap_score(query, record.content)

            # 3. Importance factor (normalized 0 to 1)
            imp_norm = min(1.0, max(0.0, (record.importance or 1.0) / 10.0))

            # If embedding is unavailable, distribute vector weight to text
            if not query_embedding or not record.embedding:
                current_v_weight = 0.0
                current_t_weight = vector_weight + text_weight
            else:
                current_v_weight = vector_weight
                current_t_weight = text_weight

            total_score = (current_v_weight * vec_sim) + (current_t_weight * text_sim) + (importance_weight * imp_norm)

            if total_score >= min_threshold:
                scored_records.append((record, total_score))

        # Sort descending by total score
        scored_records.sort(key=lambda x: x[1], reverse=True)
        return scored_records
