# JARVIS — Autonomous Personal AI Assistant

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-34%2F34%20passed-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Android](https://img.shields.io/badge/android-SDK%2035-green.svg)]()
[![Jetpack Compose](https://img.shields.io/badge/UI-Jetpack%20Compose%20%7C%20HUD-cyan.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

> *"The ultimate objective is a working, tested, usable JARVIS, not a demonstration or mockup."*

**JARVIS** is an autonomous personal AI assistant operating across a distributed mesh: **Android Phone** (first client with voice and home widget), **Windows/Linux/macOS Laptop Node** (terminal, filesystem, app control), and a **24/7 Gateway Server Core** (modular LLM brain, multilayer memory, background task queue, and auto-rectifying coding agent).

---

## 🏛️ System Architecture

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

## ⚡ Key Capabilities

- **Natural Voice & Barge-In Audio**: Full Speech-to-Text and Text-to-Speech with immediate audio interruption when the user speaks.
- **Android Home Screen Widget**: Dedicated 1-tap activation widget for quick microphone listening and live status.
- **Persistent Session**: Android Foreground Service keeps JARVIS active in standby with a sticky notification and instant STOP mechanism.
- **Modular LLM Brain**: Pluggable provider abstraction supporting local offline **Ollama** (`llama3.2`, `qwen2.5-coder`), cloud **OpenAI** (`gpt-4o`), and **Anthropic** (`claude-3-5-sonnet`) with automatic fallback.
- **Multilayer Memory System**: Short-term session buffer, long-term user facts, project-specific context, and episodic task outcomes with hybrid vector + keyword semantic search.
- **Natural Language Memory Controls**: Understands *"Remember that..."*, *"Forget..."*, *"What do you remember about...?"*, and provides decision rationale.
- **Autonomous Coding Agent & Rectification Loop**: Self-governing developer loop: `Inspect -> Plan -> Checkpoint -> Implement -> Test -> Rectify -> Retest -> Commit`.
- **Probabilistic Emotion Awareness**: Infers user emotional tone (Calm, Urgent, Frustrated, Confused) to modulate urgency and communication brevity without claiming psychological certainty.
- **Multi-Device Routing Mesh**: Routes tasks to the appropriate device (e.g. executing heavy Python scripts on the laptop while speaking status through the phone).
- **Security & Safety Guardrails**: JWT device tokens, SHA-256 secret hashing, automatic API key masking in logs, and mandatory user confirmation for dangerous commands (`rm -rf`, disk formatting, database drops).

---

## 🚀 Quick Start

### 1. Configure Environment
```bash
# Clone and enter directory
cd d:/JARVIS

# Copy environment template
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch 24/7 Gateway Server
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Holographic Web HUD**: Open `http://127.0.0.1:8000/` in your browser.
- **Interactive API Documentation**: Open `http://127.0.0.1:8000/docs`.

### 4. Connect Laptop Agent Node
In a separate terminal:
```bash
python laptop_node/jarvis_node.py
```

### 5. Launch Android App
Open the `android/` directory in Android Studio and run on your Android device or emulator. Add the **JARVIS Widget** to your home screen for 1-tap voice interaction.

---

## 🧪 Automated Test Verification

JARVIS includes a rigorous test suite of **34 unit, integration, API, and WebSocket tests**:

```bash
python -m pytest tests/ -v
```

```
tests/test_api_e2e.py::test_health_check_endpoint PASSED
tests/test_api_e2e.py::test_full_user_and_task_e2e_flow PASSED
tests/test_api_e2e.py::test_websocket_client_interaction PASSED
tests/test_auth.py::test_password_hashing PASSED
tests/test_auth.py::test_jwt_token_lifecycle PASSED
tests/test_auth.py::test_secret_sanitization PASSED
tests/test_auth.py::test_user_registration_and_login PASSED
tests/test_auth.py::test_device_enrollment_and_revocation PASSED
tests/test_coding_rectifier.py::test_rectifier_traceback_parsing PASSED
tests/test_coding_rectifier.py::test_rectifier_assertion_parsing PASSED
tests/test_coding_rectifier.py::test_coding_agent_successful_lifecycle PASSED
tests/test_emotion_decision.py::test_probabilistic_emotion_inference PASSED
tests/test_emotion_decision.py::test_adaptive_learning_from_feedback PASSED
tests/test_emotion_decision.py::test_operating_mode_tool_permissions PASSED
tests/test_emotion_decision.py::test_decision_engine_dangerous_commands_guard PASSED
tests/test_llm_providers.py::test_mock_provider_basic_response PASSED
tests/test_llm_providers.py::test_mock_provider_canned_tool_call PASSED
tests/test_llm_providers.py::test_mock_provider_streaming PASSED
tests/test_llm_providers.py::test_mock_provider_embeddings PASSED
tests/test_llm_providers.py::test_provider_factory PASSED
tests/test_memory.py::test_cosine_similarity PASSED
tests/test_memory.py::test_keyword_overlap_score PASSED
tests/test_memory.py::test_memory_manager_add_and_retrieve PASSED
tests/test_memory.py::test_natural_memory_commands PASSED
tests/test_memory.py::test_project_memory_purge PASSED
tests/test_multi_device.py::test_system_executor_metrics PASSED
tests/test_multi_device.py::test_system_executor_shell PASSED
tests/test_multi_device.py::test_device_capability_discovery_and_routing PASSED
tests/test_task_queue.py::test_task_queue_interruption_and_cancel PASSED
tests/test_task_queue.py::test_reconnect_briefing_generation PASSED
tests/test_tools.py::test_file_tools_crud PASSED
tests/test_tools.py::test_terminal_tool_execution PASSED
tests/test_tools.py::test_terminal_tool_timeout PASSED
tests/test_tools.py::test_tool_registry_with_audit PASSED

======================= 34 passed in 7.30s =======================
```

---

## 📚 Master Documentation Suite

Comprehensive technical manuals are located in the [`docs/`](file:///d:/JARVIS/docs/) directory:

- [ARCHITECTURE.md](file:///d:/JARVIS/docs/ARCHITECTURE.md): Distributed architecture, data flows, and subsystem blueprints.
- [SETUP.md](file:///d:/JARVIS/docs/SETUP.md): Step-by-step setup for backend, laptop node, and Android.
- [ANDROID.md](file:///d:/JARVIS/docs/ANDROID.md): Android client, Foreground service, barge-in audio, and App Widget.
- [BACKEND.md](file:///d:/JARVIS/docs/BACKEND.md): REST endpoints, WebSocket protocols, and database schema.
- [AGENT.md](file:///d:/JARVIS/docs/AGENT.md): Operating modes (`PLAN`, `IMPLEMENT`, `TEST`, `RECTIFY`, `AUTONOMOUS`) and tools.
- [MEMORY.md](file:///d:/JARVIS/docs/MEMORY.md): Multilayer memory, hybrid ranking math, and natural memory commands.
- [SECURITY.md](file:///d:/JARVIS/docs/SECURITY.md): JWT tokens, device authorization, dangerous command guardrails, secret masking.
- [TESTING.md](file:///d:/JARVIS/docs/TESTING.md): Test execution guide and coverage report.
- [DEPLOYMENT.md](file:///d:/JARVIS/docs/DEPLOYMENT.md): Docker, systemd, and Windows service deployment.
- [TROUBLESHOOTING.md](file:///d:/JARVIS/docs/TROUBLESHOOTING.md): Diagnostic steps and resolutions for common issues.
