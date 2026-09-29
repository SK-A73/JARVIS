"""
Multi-Device Command Router
Routes user intent and tool actions to the appropriate device node in the mesh.
"""
import re
import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.routing.device_manager import DeviceMeshManager
from backend.app.models.auth import DeviceNode

logger = logging.getLogger(__name__)

class CommandRouter:
    @staticmethod
    def resolve_target_device(
        user_request: str,
        caller_device_id: Optional[str],
        db: Session
    ) -> Tuple[Optional[str], str]:
        """
        Determines which device should execute the request.
        Returns (target_device_id, explanation_message).
        """
        mesh = DeviceMeshManager.get_instance()
        lower = user_request.lower()

        # 1. Explicit mention of laptop/PC
        if re.search(r'\b(?:on|check|to|run\s+on)?\s*my\s*(?:laptop|pc|computer)\b', lower):
            laptop = mesh.find_device_for_capability("terminal", db)
            if not laptop:
                return (None, "Your laptop is not currently connected to the JARVIS network.")
            return (laptop.id, f"Routing execution to your laptop: {laptop.name}.")

        # 2. Explicit mention of phone
        if re.search(r'\b(?:to|on|send\s+to|notify)?\s*my\s*phone\b', lower):
            phone = mesh.find_device_for_capability("notifications", db)
            if not phone:
                return (None, "Your phone is not currently connected.")
            return (phone.id, f"Routing to your phone: {phone.name}.")
            return (phone.id, f"Routing to your phone: {phone.name}.")

        # 3. Default to caller device or local server execution
        return (caller_device_id, "Executing on local JARVIS node.")
