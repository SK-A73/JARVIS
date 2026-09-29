# JARVIS System Architecture & Design Specification

## 1. Architectural Philosophy
JARVIS is architected as an **autonomous, distributed personal AI operating mesh**, rather than a static chatbot. heavy AI inference, background tasks, and persistent memory reside on the 24/7 Gateway core (local PC or server), while client nodes (Android phone, Windows/Linux/macOS laptop) handle lightweight input/output, local execution, and device telemetry.

```
                    +-------------------------------------------------+
                    |              JARVIS 24/7 GATEWAY                |
                    | (FastAPI + Async Worker + SQLite/Postgres DB)   |
                    +-----------------------+-------------------------+
                                            |
                       +--------------------+--------------------+
                       |                                         |
                       v                                         v
         +----------------------------+            +----------------------------+
         |    Android Phone Client    |            |    Windows Laptop Node     |
         | (Kotlin + Jetpack Compose) |            |   (Python Background Node) |
         |                            |            |                            |
         | • 1-Tap Home Screen Widget |            | • Terminal Executor        |
         | • Foreground Voice Service |            | • Filesystem Workspace     |
         | • Speech-to-Text (STT)     |            | • Process Monitoring       |
         | • Text-to-Speech (TTS)     |            | • Remote Workstation Lock  |
         | • Barge-In Audio Interrupt |            | • Hardware Telemetry       |
         +----------------------------+            +----------------------------+
```

---

## 2. Core Subsystems

### 2.1 Modular LLM Brain (`backend/app/llm/`)
Provides a unified abstraction layer (`LLMProvider`) supporting:
- **Local Ollama** (offline, zero-cost, private AI inference, e.g. `llama3.2`, `qwen2.5-coder`).
- **OpenAI / OpenAI-Compatible** gateways (`gpt-4o`, `gpt-4o-mini`, Groq, vLLM, OpenRouter).
- **Anthropic Claude** (`claude-3-5-sonnet`, `claude-3-5-haiku`).
- **Deterministic Mock Provider** for continuous integration and headless verification.
- Dynamic fallback: if a provider returns HTTP 429/500 or network timeout, the factory falls back gracefully.

### 2.2 Multilayer Memory System (`backend/app/memory/`)
1. **Short-Term Memory**: In-memory working buffer tracking ongoing conversational topics, active tool runs, and uncommitted steps.
2. **Long-Term Memory**: Persistent storage for user preferences, habits, instructions, and historical facts.
3. **Project Memory**: Dedicated, isolated context per project (tech stack, architectural rules, constraints, bug history).
4. **Episodic Memory**: Event log tracking cause, action, outcome, and post-execution evaluations.
5. **Hybrid Semantic Retriever**: Combines vector cosine similarity with query term coverage and Jaccard keyword overlap, weighted by importance factors.
6. **Natural Language Memory Controls**: Parses commands like *"JARVIS, remember that..."*, *"JARVIS, forget..."*, *"What do you remember about..."*.

### 2.3 Operating Modes State Machine (`backend/app/agent/modes.py`)
- **PLAN MODE**: Analyzes requirements, inspects directory structures, reads files, and formulates step plans. Writing files and terminal command execution are strictly disabled.
- **IMPLEMENT MODE**: Implements approved steps, creates/edits files, checks builds, and commits checkpoints.
- **TEST MODE**: Executes test runners, collects logs, and isolates root causes without modifying production code.
- **RECTIFY MODE**: Analyzes stack traces, identifies root cause, creates targeted fix, applies fix, and verifies regression tests.
- **AUTONOMOUS MODE**: Full lifecycle across tasks with safety checkpoints for dangerous commands.

### 2.4 Autonomous Coding Agent & Auto-Rectifier (`backend/app/agent/`)
Executes the software development loop:
$$\text{Task} \to \text{Inspect} \to \text{Plan} \to \text{Git Checkpoint} \to \text{Implement} \to \text{Test} \to (\text{Failure} \to \text{Analyze Root Cause} \to \text{Apply Fix} \to \text{Retest}) \to \text{Commit}$$

### 2.5 Multi-Device Mesh & Command Router (`backend/app/routing/`)
- Maintains an in-memory index of connected device nodes (`DeviceMeshManager`).
- Inspects device capabilities (`terminal`, `filesystem`, `microphone`, `speaker`, `notifications`).
- Intelligently routes tasks to the appropriate device (e.g. running code on the laptop while speaking status through the phone).

### 2.6 Android Client & Home Screen Widget (`android/`)
- **Jetpack Compose HUD**: Dark obsidian palette (`#0A0E17`), glowing cyan (`#00E5FF`), animated `OrbVisualizer`.
- **JarvisVoiceService**: Android Foreground Service with sticky notification, barge-in speech interruption, and persistent WebSocket connection.
- **Home Screen Widget (`JarvisAppWidget`)**: 1-tap activation to launch voice commands instantly.
