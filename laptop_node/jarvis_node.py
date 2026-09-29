import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import asyncio
import logging
import platform
import websockets
from typing import Optional

from laptop_node.system_executor import SystemExecutor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JarvisLaptopNode")

class JarvisLaptopNode:
    def __init__(
        self,
        server_ws_url: str = "ws://127.0.0.1:8000/ws/node",
        device_id: str = "laptop-node-main",
        token: Optional[str] = None
    ):
        self.server_ws_url = server_ws_url
        self.device_id = device_id
        self.token = token or os.getenv("JARVIS_DEVICE_TOKEN", "mock_device_token")
        self.running = True
        self.capabilities = [
            "terminal",
            "filesystem",
            "build_tools",
            "screen",
            "system_monitor"
        ]

    async def run(self):
        """Main connection and message processing loop."""
        url = f"{self.server_ws_url}/{self.device_id}?token={self.token}"
        logger.info(f"Starting JARVIS Laptop Node for device: {self.device_id}")

        while self.running:
            try:
                logger.info(f"Connecting to JARVIS Gateway at {self.server_ws_url}...")
                async with websockets.connect(url) as ws:
                    logger.info("Connected to JARVIS Gateway successfully!")

                    # 1. Send Handshake with capabilities
                    handshake = {
                        "type": "node_handshake",
                        "device_id": self.device_id,
                        "device_type": "laptop",
                        "platform": f"{platform.system()} {platform.release()}",
                        "capabilities": self.capabilities
                    }
                    await ws.send(json.dumps(handshake))

                    # 2. Start heartbeat & message listener
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
                    try:
                        async for message in ws:
                            await self._handle_server_message(ws, message)
                    finally:
                        heartbeat_task.cancel()

            except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                logger.warning(f"Connection lost ({e}). Reconnecting in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def _heartbeat_loop(self, ws):
        """Sends periodic heartbeats with live system metrics."""
        while True:
            try:
                await asyncio.sleep(30)
                metrics = SystemExecutor.get_system_metrics()
                ping_msg = {
                    "type": "heartbeat",
                    "device_id": self.device_id,
                    "metrics": metrics
                }
                await ws.send(json.dumps(ping_msg))
            except asyncio.CancelledError:
                break
            except Exception:
                break

    async def _handle_server_message(self, ws, raw_message: str):
        """Dispatches RPC requests from JARVIS backend."""
        try:
            data = json.loads(raw_message)
            msg_type = data.get("type")

            if msg_type == "rpc_request":
                correlation_id = data.get("correlation_id")
                action = data.get("action")
                params = data.get("params", {})

                logger.info(f"Received RPC action: {action} (ID: {correlation_id})")
                result = {}

                if action == "execute_shell":
                    result = SystemExecutor.execute_shell(
                        command=params.get("command", ""),
                        cwd=params.get("cwd"),
                        timeout=params.get("timeout", 60)
                    )
                elif action == "get_system_metrics":
                    result = SystemExecutor.get_system_metrics()
                elif action == "lock_workstation":
                    result = SystemExecutor.lock_workstation()
                else:
                    result = {"error": f"Unsupported action: {action}"}

                response_msg = {
                    "type": "rpc_response",
                    "correlation_id": correlation_id,
                    "result": result
                }
                await ws.send(json.dumps(response_msg))

        except Exception as e:
            logger.error(f"Failed to process incoming message: {e}")

if __name__ == "__main__":
    node = JarvisLaptopNode()
    try:
        asyncio.run(node.run())
    except KeyboardInterrupt:
        logger.info("Laptop Node daemon stopped by user.")
