# JARVIS Production Deployment & DevOps Guide

JARVIS can be deployed locally, as a system service, or in containerized production environments.

---

## 1. Docker Deployment
A containerized deployment encapsulates the 24/7 gateway and background worker:

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  jarvis-gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - JARVIS_ENV=production
      - JARVIS_SECRET_KEY=generate_a_secure_production_secret_here
      - DATABASE_URL=sqlite:///./jarvis.db
      - DEFAULT_LLM_PROVIDER=ollama
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - jarvis-data:/app/workspace_storage
    restart: unless-stopped

volumes:
  jarvis-data:
```

---

## 2. Linux Systemd Service
To run JARVIS 24/7 as a background Linux daemon:
```ini
[Unit]
Description=JARVIS 24/7 Assistant Gateway
After=network.target

[Service]
Type=simple
User=jarvis
WorkingDirectory=/opt/jarvis
ExecStart=/opt/jarvis/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/opt/jarvis/.env

[Install]
WantedBy=multi-user.target
```

---

## 3. Windows Service Setup
On Windows, run the server using NSSM (Non-Sucking Service Manager) or PowerShell background jobs:
```powershell
# In PowerShell as Administrator:
nssm install JarvisGateway "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe" "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
nssm set JarvisGateway AppDirectory "D:\JARVIS"
nssm start JarvisGateway
```
