"""
Laptop Node System Executor
Handles local terminal execution, process monitoring, hardware statistics, and system commands.
"""
import os
import sys
import platform
import subprocess
import psutil
from typing import Dict, Any, Optional

class SystemExecutor:
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Collects current hardware metrics (CPU, Memory, Disk, Platform)."""
        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/") if platform.system() != "Windows" else psutil.disk_usage("C:\\")

        battery_info = "N/A"
        if hasattr(psutil, "sensors_battery"):
            bat = psutil.sensors_battery()
            if bat:
                battery_info = f"{bat.percent}% ({'Charging' if bat.power_plugged else 'Discharging'})"

        return {
            "platform": platform.platform(),
            "cpu_percent": cpu_pct,
            "memory_percent": mem.percent,
            "memory_available_mb": int(mem.available / (1024 * 1024)),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "battery": battery_info
        }

    @staticmethod
    def execute_shell(command: str, cwd: Optional[str] = None, timeout: int = 60) -> Dict[str, Any]:
        """Executes a shell command locally on the laptop."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds."
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e)
            }

    @staticmethod
    def lock_workstation() -> Dict[str, Any]:
        """Locks the laptop screen."""
        os_name = platform.system()
        if os_name == "Windows":
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            return {"success": True, "message": "Windows workstation locked."}
        elif os_name == "Darwin":
            subprocess.run("pmset displaysleepnow", shell=True)
            return {"success": True, "message": "macOS display put to sleep."}
        else:
            subprocess.run("xdg-screensaver lock", shell=True)
            return {"success": True, "message": "Linux screensaver locked."}
