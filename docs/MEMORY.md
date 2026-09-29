# JARVIS Multilayer Memory System

JARVIS implements persistent, multi-tiered memory with hybrid semantic retrieval and full user privacy controls.

---

## 1. Memory Tiers

| Tier | Scope | Persistence | Purpose |
|------|-------|-------------|---------|
| **Short-Term** | Session / Thread | In-Memory / Transient | Current conversation topic, active tool context, immediate user clarifications. |
| **Long-Term** | Global User | Persistent Database | User habits, recurring preferences, identity facts, enduring instructions. |
| **Project** | Per-Project | Persistent Database | Tech stack, architecture rules, dependency constraints, bug history. |
| **Episodic** | Historical | Persistent Database | Cause-action-outcome records of completed autonomous tasks. |

---

## 2. Hybrid Retrieval Math
When a user query arrives, relevant memories are retrieved using a weighted multi-signal scoring model:

$$\text{Total Score} = w_{\text{vec}} \cdot \text{Sim}_{\text{cos}}(V_q, V_m) + w_{\text{text}} \cdot \text{Score}_{\text{text}}(Q, M) + w_{\text{imp}} \cdot \frac{\text{Importance}}{10}$$

Where:
- $\text{Sim}_{\text{cos}}(V_q, V_m) = \frac{V_q \cdot V_m}{\|V_q\| \|V_m\|}$ computes cosine similarity between normalized vector embeddings.
- $\text{Score}_{\text{text}}(Q, M) = 0.7 \cdot \text{Coverage} + 0.3 \cdot \text{Jaccard}$ evaluates query keyword precision and document overlap.
- $\text{Importance}$ scales from $1.0$ (trivial fact) to $10.0$ (critical invariant).

---

## 3. Natural Language Memory Commands
JARVIS automatically recognizes natural commands without rigid syntax:

- **Storing Memories**:
  - *"JARVIS, remember that we use PostgreSQL for this project."*
  - *"Remember that my preferred Python version is 3.11."*
- **Querying Memories**:
  - *"JARVIS, what do you remember about our database?"*
  - *"What do you remember about my coding style?"*
- **Deleting / Forgetting**:
  - *"JARVIS, forget the database decision."*
  - *"Delete memory #14."*
  - *"Delete this project's memory."*
- **Rationale Inspection**:
  - *"Why did you make that decision?"* $\to$ JARVIS cites the learned pattern or stored memory evidence.
