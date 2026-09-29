"""
Real-time WebSocket Hub Router
Handles live chat streaming, multi-device node RPC, and active task progress broadcasts.
"""
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db, SessionLocal
from backend.app.routing.device_manager import DeviceMeshManager
from backend.app.routing.command_router import CommandRouter
from backend.app.models.auth import DeviceNode
from backend.app.llm.factory import LLMProviderFactory
from backend.app.llm.base import LLMMessage
from backend.app.memory.manager import MemoryManager
from backend.app.core.emotion import EmotionEngine
from backend.app.agent.modes import ModePolicy

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Realtime WebSockets"])

@router.websocket("/ws/node/{device_id}")
async def websocket_node_endpoint(websocket: WebSocket, device_id: str, db: Session = Depends(get_db)):
    """Channel for background device nodes (e.g. Windows Laptop node)."""
    await websocket.accept()
    mesh = DeviceMeshManager.get_instance()

    try:
        await mesh.register_connection(device_id, websocket, db)

        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            msg_type = data.get("type")

            if msg_type == "node_handshake":
                device = db.query(DeviceNode).filter(DeviceNode.id == device_id).first()
                if device:
                    device.capabilities = data.get("capabilities", [])
                    device.platform = data.get("platform")
                    db.commit()
                await websocket.send_text(json.dumps({"type": "handshake_ack", "status": "registered"}))

            elif msg_type == "heartbeat":
                device = db.query(DeviceNode).filter(DeviceNode.id == device_id).first()
                if device:
                    device.last_seen = json.dumps(data.get("metrics", {}))
                    db.commit()

            elif msg_type == "rpc_response":
                correlation_id = data.get("correlation_id")
                mesh.handle_rpc_response(correlation_id, data.get("result", {}))

    except WebSocketDisconnect:
        await mesh.disconnect(device_id, db)
    except Exception as e:
        logger.error(f"Error on node websocket {device_id}: {e}")
        await mesh.disconnect(device_id, db)

@router.websocket("/ws/client/{client_id}")
async def websocket_client_endpoint(websocket: WebSocket, client_id: str, db: Session = Depends(get_db)):
    """Channel for user clients (Android phone, Desktop HUD, Web)."""
    await websocket.accept()
    provider = LLMProviderFactory.get_provider()
    memory_manager = MemoryManager(db, provider)

    try:
        # Send initial status
        await websocket.send_text(json.dumps({
            "type": "jarvis_status",
            "state": "online",
            "message": "JARVIS core online and listening."
        }))

        while True:
            raw_text = await websocket.receive_text()
            payload = json.loads(raw_text)
            user_text = payload.get("message", "").strip()
            if not user_text:
                continue

            # 1. Infer Emotion & Urgency
            emotion = EmotionEngine.infer_emotion(user_text)

            # 2. Check Natural Memory Command (Remember/Forget/Query)
            mem_cmd_res = await memory_manager.handle_natural_memory_command(user_text)
            if mem_cmd_res:
                await websocket.send_text(json.dumps({
                    "type": "chat_response",
                    "content": mem_cmd_res["message"],
                    "emotion": emotion.model_dump()
                }))
                continue

            # 3. Check Multi-Device Routing
            target_device, explanation = CommandRouter.resolve_target_device(user_text, client_id, db)

            # 4. Stream response from LLM
            await websocket.send_text(json.dumps({
                "type": "stream_start",
                "inferred_emotion": emotion.state,
                "confidence": emotion.confidence
            }))

            # Retrieve relevant memory context
            relevant_mems = await memory_manager.retrieve_relevant(user_text, limit=3)
            mem_context = ""
            if relevant_mems:
                mem_context = "Relevant Persistent Memory:\n" + "\n".join([f"- {m.content}" for m, s in relevant_mems]) + "\n\n"

            messages = [
                LLMMessage(role="system", content=f"You are JARVIS, an autonomous personal AI assistant. {mem_context}"),
                LLMMessage(role="user", content=user_text)
            ]

            full_reply = []
            async for token in provider.stream_response(messages):
                full_reply.append(token)
                await websocket.send_text(json.dumps({"type": "stream_chunk", "chunk": token}))

            await websocket.send_text(json.dumps({
                "type": "stream_end",
                "full_text": "".join(full_reply),
                "emotion": emotion.model_dump()
            }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Client websocket error: {e}")
