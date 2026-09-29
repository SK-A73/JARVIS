"""
Secure Terminal Execution Layer
Executes shell commands with timeout enforcement, secret masking, and cancellation tokens.
"""
import asyncio
import os
import time
import logging
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.core.security import sanitize_secrets

logger = logging.getLogger(__name__)

async def execute_terminal_command(
    command: str,
    cwd: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
    cancel_event: Optional[asyncio.Event] = None
) -> Dict[str, Any]:
    """
    Executes a shell command asynchronously with strict safety guards.
    """
    timeout = timeout_seconds or settings.MAX_COMMAND_TIMEOUT_SECONDS
    work_dir = cwd or settings.WORKSPACE_ROOT
    os.makedirs(work_dir, exist_ok=True)

    start_time = time.time()
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def monitor_cancellation():
            if cancel_event:
                await cancel_event.wait()
                try:
                    proc.kill()
                except Exception:
                    pass

        cancel_task = asyncio.create_task(monitor_cancellation()) if cancel_event else None

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(timeout)
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds.",
                "duration_ms": int((time.time() - start_time) * 1000),
                "is_cancelled": False,
                "is_timeout": True
            }
        finally:
            if cancel_task:
                cancel_task.cancel()

        duration = int((time.time() - start_time) * 1000)
        stdout_str = stdout_data.decode("utf-8", errors="replace")
        stderr_str = stderr_data.decode("utf-8", errors="replace")

        # Truncate overly long outputs (limit 15KB per execution to protect context)
        max_bytes = 15000
        if len(stdout_str) > max_bytes:
            stdout_str = stdout_str[:max_bytes] + "\n...[stdout truncated for brevity]..."
        if len(stderr_str) > max_bytes:
            stderr_str = stderr_str[:max_bytes] + "\n...[stderr truncated for brevity]..."

        return {
            "exit_code": proc.returncode,
            "stdout": sanitize_secrets(stdout_str),
            "stderr": sanitize_secrets(stderr_str),
            "duration_ms": duration,
            "is_cancelled": cancel_event.is_set() if cancel_event else False,
            "is_timeout": False
        }

    except Exception as e:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": sanitize_secrets(f"Execution failed: {str(e)}"),
            "duration_ms": int((time.time() - start_time) * 1000),
            "is_cancelled": False,
            "is_timeout": False
        }
