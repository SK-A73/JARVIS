# JARVIS Automated Testing & Verification Suite

Testing is mandatory across all JARVIS subsystems. The test suite verifies functionality, edge cases, failure scenarios, and automatic rectification loops.

---

## 1. Running the Test Suite
To execute the complete automated test suite:
```bash
python -m pytest tests/ -v
```

To run a specific test module:
```bash
# Run Authentication and Device Registry tests
python -m pytest tests/test_auth.py -v

# Run Memory and Hybrid Semantic Retrieval tests
python -m pytest tests/test_memory.py -v

# Run Emotion and Decision Safety Engine tests
python -m pytest tests/test_emotion_decision.py -v

# Run Sandboxed Tools and Registry tests
python -m pytest tests/test_tools.py -v

# Run Failure Analysis and Coding Rectifier tests
python -m pytest tests/test_coding_rectifier.py -v

# Run 24/7 Task Queue and Interruption tests
python -m pytest tests/test_task_queue.py -v

# Run Multi-Device Mesh and Laptop Node tests
python -m pytest tests/test_multi_device.py -v

# Run End-to-End API and WebSocket tests
python -m pytest tests/test_api_e2e.py -v
```

---

## 2. Test Coverage Overview
The test harness covers 34 comprehensive tests across 8 modules:
- `test_auth.py` (5 tests): Password hashing, JWT token generation & verification, secret sanitization, user registration, device registration, and revocation.
- `test_llm_providers.py` (5 tests): Provider contracts, streaming, tool call execution, deterministic embedding vectors, and fallback factory.
- `test_memory.py` (5 tests): Vector cosine similarity, keyword overlap, memory CRUD, project context isolation, and natural language memory commands.
- `test_emotion_decision.py` (4 tests): Probabilistic tone classification, adaptive learning from user corrections, operating mode tool permission enforcement, and dangerous command safety blocks.
- `test_tools.py` (4 tests): Sandboxed file write/read/edit, directory listing, regex search, terminal execution, timeout enforcement, and audit logging.
- `test_coding_rectifier.py` (3 tests): Traceback parsing, AssertionError handling, and autonomous coding loop.
- `test_task_queue.py` (2 tests): Task interruption, cancellation state persistence, and reconnect briefing generation.
- `test_multi_device.py` (3 tests): Hardware metrics telemetry, shell execution on laptop node, and multi-device command routing.
- `test_api_e2e.py` (3 tests): System health endpoint, full user-to-task lifecycle, and bi-directional WebSocket client streaming.
