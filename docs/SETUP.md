# JARVIS Setup & Quick Start Guide

This guide describes how to set up and run JARVIS across the backend gateway, laptop node, and Android client.

---

## 1. Prerequisites
- **Python**: Version 3.11+
- **Node.js**: Version 18+ (for companion tools / dashboard)
- **Git**: Installed and in PATH
- **Ollama (Optional for offline AI)**: Pre-installed or download from https://ollama.ai
- **Android Studio (Optional for building APK)**: Hedgehog or later with Android SDK 35

---

## 2. Environment Configuration
Clone or navigate to the repository directory:
```bash
cd d:/JARVIS
```

Copy the environment template:
```bash
cp .env.example .env
```

Edit `.env` to configure your preferred LLM provider:
```ini
# To use local Ollama (offline, zero-cost, private)
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2

# Or to use Cloud OpenAI
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Or for headless testing / CI
DEFAULT_LLM_PROVIDER=mock
```

---

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 4. Run the JARVIS 24/7 Gateway
Start the asynchronous server:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started:
- **Holographic Web HUD**: Navigate to `http://127.0.0.1:8000/` in your browser.
- **Interactive Swagger API Docs**: Navigate to `http://127.0.0.1:8000/docs`.
- **System Health**: Navigate to `http://127.0.0.1:8000/health`.

---

## 5. Connect the Laptop Agent Node
Open a separate terminal and start the background laptop node daemon:
```bash
python laptop_node/jarvis_node.py
```
The node will automatically connect to the gateway WebSocket, register its terminal, filesystem, and telemetry capabilities, and begin streaming heartbeats.

---

## 6. Build & Run the Android Client
Open the `android/` directory in Android Studio:
1. Allow Gradle to sync dependencies.
2. Select your connected Android device or Android Virtual Device (AVD).
3. Run the project (`Shift + F10`).
4. Grant Audio & Notification permissions upon first launch.
5. Add the **JARVIS Widget** to your home screen for 1-tap voice activation.
