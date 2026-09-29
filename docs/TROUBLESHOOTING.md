# JARVIS Troubleshooting & Diagnosis Guide

This guide covers common issues, diagnostic procedures, and resolution steps.

---

## 1. Gateway & Connection Issues

### Issue: "Core Offline - Reconnecting..." in Android / Web HUD
- **Probable Cause**: The backend FastAPI server is not running or the port is blocked.
- **Diagnostic Step**: Test health endpoint:
  ```bash
  curl http://127.0.0.1:8000/health
  ```
- **Resolution**:
  - Start the backend gateway: `python -m uvicorn backend.app.main:app --port 8000`.
  - For Android Emulator, verify endpoint uses `10.0.2.2:8000` (the host alias for localhost).
  - For a physical Android phone on the same Wi-Fi, set your laptop's local IP address (e.g. `192.168.1.X:8000`) in `.env` and `JarvisVoiceService.kt`.

---

## 2. LLM Provider Errors

### Issue: "Ollama connection failed" / "Connection refused on port 11434"
- **Probable Cause**: The local Ollama service is not running.
- **Diagnostic Step**: Check Ollama service:
  ```bash
  ollama list
  ```
- **Resolution**:
  - Start Ollama: run `ollama serve` in a terminal or launch the Ollama desktop app.
  - Pull your desired model: `ollama pull llama3.2` or `ollama pull qwen2.5-coder`.
  - Alternatively, switch `DEFAULT_LLM_PROVIDER=mock` or `DEFAULT_LLM_PROVIDER=openai` in `.env`.

### Issue: "OpenAI API key is missing"
- **Resolution**: Ensure `OPENAI_API_KEY=sk-...` is defined in `.env` or set `DEFAULT_LLM_PROVIDER=ollama` / `mock`.

---

## 3. Android Voice & Microphone

### Issue: Microphone error code 7 / 9
- **Probable Cause**: Missing runtime permissions or audio device is locked by another application.
- **Resolution**:
  - Ensure `Manifest.permission.RECORD_AUDIO` is granted in Settings $\to$ Apps $\to$ JARVIS $\to$ Permissions $\to$ Microphone $\to$ "Allow only while using the app" or "Allow all the time".
  - Verify Google Speech Services are enabled on the phone/emulator.

---

## 4. Laptop Node Execution

### Issue: "Target device is not connected" when routing commands from phone
- **Probable Cause**: The laptop node daemon is not active.
- **Resolution**:
  - Run the laptop node daemon: `python laptop_node/jarvis_node.py`.
  - Check the device list via `GET /api/v1/auth/devices` to verify the laptop node is registered and marked online.

---

## 5. Database Operational Errors

### Issue: "database is locked" (SQLite)
- **Probable Cause**: Multiple simultaneous write connections exceeding SQLite timeout.
- **Resolution**:
  - SQLite pragma foreign keys are automatically managed with `check_same_thread: False`.
  - For high-concurrency production deployments, migrate to PostgreSQL by setting `DATABASE_URL=postgresql://user:password@localhost:5432/jarvis` in `.env`.
