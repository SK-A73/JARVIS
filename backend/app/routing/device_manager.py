"""
Multi-Device Connection Manager and Routing Mesh
Maintains active node connections, capability indexing, and remote RPC dispatching.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import WebSocket
from sqlalchemy.orm import Session

from backend.app.models.auth import DeviceNode

logger = logging.getLogger(__name__)

class DeviceMeshManager:
    _instance = None

    def __init__(self):
        # Maps device_id -> active WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # Maps correlation_id -> asyncio.Future for RPC responses
        self.pending_responses: Dict[str, asyncio.Future] = {}

    @classmethod
    def get_instance(cls) -> "DeviceMeshManager":
        if cls._instance is None:
            cls._instance = DeviceMeshManager()
        return cls._instance

    async def register_connection(self, device_id: str, websocket: WebSocket, db: Session):
        """Registers a newly connected device node and marks it online."""
        self.active_connections[device_id] = websocket
        device = db.query(DeviceNode).filter(DeviceNode.id == device_id).first()
        if device:
            device.is_online = True
            device.last_seen = datetime.now(timezone.utc)
            db.commit()
        logger.info(f"Device connected and active: {device_id}")

    async def disconnect(self, device_id: str, db: Session):
        """Removes an active device node and marks it offline."""
        if device_id in self.active_connections:
            del self.active_connections[device_id]
        device = db.query(DeviceNode).filter(DeviceNode.id == device_id).first()
        if device:
            device.is_online = False
            device.last_seen = datetime.now(timezone.utc)
            db.commit()
        logger.info(f"Device disconnected: {device_id}")

    def find_device_for_capability(self, required_capability: str, db: Session) -> Optional[DeviceNode]:
        """Finds an online device that possesses the requested capability."""
        online_devices = db.query(DeviceNode).filter(
            DeviceNode.is_active == True,
            DeviceNode.is_online == True
        ).all()

        for d in online_devices:
            caps = d.capabilities or []
            if required_capability in caps:
                return d
        return None

    async def send_to_device(self, device_id: str, message: Dict[str, Any]) -> bool:
        """Sends a JSON message to an active connected device."""
        ws = self.active_connections.get(device_id)
        if not ws:
            return False
        try:
            await ws.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to device {device_id}: {e}")
            return False

    async def rpc_call(self, device_id: str, action: str, params: Dict[str, Any], timeout_seconds: float = 30.0) -> Dict[str, Any]:
        """Performs a remote procedure call to a connected device node and waits for the response."""
        ws = self.active_connections.get(device_id)
        if not ws:
            raise ConnectionError(f"Target device {device_id} is not connected.")

        import uuid
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self.pending_responses[correlation_id] = future

        message = {
            "type": "rpc_request",
            "correlation_id": correlation_id,
            "action": action,
            "params": params
        }
        await ws.send_text(json.dumps(message))

        try:
            result = await asyncio.wait_for(future, timeout=timeout_seconds)
            return result
        finally:
            if correlation_id in self.pending_responses:
                del self.pending_responses[correlation_id]

    def handle_rpc_response(self, correlation_id: str, payload: Dict[str, Any]):
        """Resolves the pending RPC future when a node replies."""
        future = self.pending_responses.get(correlation_id)
        if future and not future.done():
            future.set_result(payload)
