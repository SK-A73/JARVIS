# JARVIS 24/7 Backend & Gateway API Guide

The backend is built with **FastAPI**, **SQLAlchemy ORM**, **WebSockets**, and **Asyncio Background Workers**.

---

## 1. Core Architecture
- **WebSockets Hub (`backend/app/api/ws_router.py`)**:
  - `/ws/client/{client_id}`: Real-time user streaming channel with token generation, sentiment indicators, and memory augmentation.
  - `/ws/node/{device_id}`: Remote Procedure Call (RPC) and heartbeat channel for background nodes (Windows Laptop).
- **24/7 Background Task Queue (`backend/app/agent/task_queue.py`)**:
  - Independent task runner that survives client disconnects.
  - Maintains task state machine: `QUEUED -> PLANNING -> IMPLEMENTING -> TESTING -> RECTIFYING -> COMPLETED / FAILED / CANCELLED`.
  - Automatic reconnect briefing: when clients reconnect, a natural language briefing summarizing actions taken while away is generated.

---

## 2. API Endpoints Reference

### 2.1 Authentication & Devices (`/api/v1/auth`)
- `POST /api/v1/auth/register`: Register user or root admin account.
- `POST /api/v1/auth/login`: Authenticate and receive JWT bearer token.
- `POST /api/v1/auth/devices/register`: Enroll client device (Phone or Laptop) and receive unique device secret.
- `GET /api/v1/auth/devices`: List all registered devices.
- `DELETE /api/v1/auth/devices/{device_id}`: Revoke device access.
- `GET /api/v1/auth/me`: Inspect current caller identity.

### 2.2 Multilayer Memory (`/api/v1/memory`)
- `GET /api/v1/memory`: Filter memories by category (`short_term`, `long_term`, `project`, `episodic`) or project ID.
- `POST /api/v1/memory`: Add explicit memory record with importance and confidence score.
- `POST /api/v1/memory/search`: Semantic + keyword hybrid search.
- `DELETE /api/v1/memory/{id}`: Delete specific memory item.
- `DELETE /api/v1/memory/project/{project_id}`: Purge all memories for a project.
- `GET /api/v1/memory/stats`: Memory statistics count by category.

### 2.3 Task Operations (`/api/v1/tasks`)
- `POST /api/v1/tasks`: Submit autonomous task into the 24/7 background queue.
- `GET /api/v1/tasks`: List tasks with status filtering.
- `GET /api/v1/tasks/{id}`: Inspect task details and step-by-step audit logs.
- `POST /api/v1/tasks/{id}/cancel`: User interruption to immediately stop an active task.
- `GET /api/v1/tasks/{id}/timeline`: Human-readable activity timeline.
- `GET /api/v1/tasks/briefing/reconnect`: Executive catch-up briefing.

---

## 3. Database Schema
Models reside in `backend/app/models/`:
- `User`: Users with hashed passwords and admin flags.
- `DeviceNode`: Hardware identifier, device type, platform, capabilities, and token hash.
- `MemoryRecord`: Content, category, importance ($1.0-10.0$), confidence ($0.0-1.0$), embedding vector, project association.
- `LearnedPattern`: Reversible learned behavioral and architectural patterns.
- `Task`: 24/7 background task with full lifecycle status and retry counts.
- `TaskStep`: Step log with tool names, input arguments, output observations, and timing.
- `AuditLog`: Security audit trail for all executed commands.
