"""
Operating Modes State Machine and Rule Engine
Strictly manages PLAN, IMPLEMENT, TEST, RECTIFY, and AUTONOMOUS modes.
"""
from enum import Enum
from typing import Set, Dict, Any, Optional
from pydantic import BaseModel

class OperatingMode(str, Enum):
    PLAN = "PLAN"
    IMPLEMENT = "IMPLEMENT"
    TEST = "TEST"
    RECTIFY = "RECTIFY"
    AUTONOMOUS = "AUTONOMOUS"

class ModePolicy:
    ALLOWED_TOOLS: Dict[OperatingMode, Set[str]] = {
        OperatingMode.PLAN: {
            "read_file", "list_directory", "search_files_regex", "search_symbols",
            "web_search", "fetch_web_documentation", "git_status", "git_diff"
        },
        OperatingMode.IMPLEMENT: {
            "read_file", "write_file", "edit_file_block", "list_directory",
            "search_files_regex", "search_symbols", "execute_terminal_command",
            "git_status", "git_diff", "git_commit", "git_checkout_branch"
        },
        OperatingMode.TEST: {
            "read_file", "list_directory", "search_files_regex", "search_symbols",
            "execute_terminal_command", "git_status", "git_diff"
        },
        OperatingMode.RECTIFY: {
            "read_file", "write_file", "edit_file_block", "list_directory",
            "search_files_regex", "search_symbols", "execute_terminal_command",
            "git_status", "git_diff", "git_commit", "git_revert_checkpoint"
        },
        OperatingMode.AUTONOMOUS: {
            "read_file", "write_file", "edit_file_block", "list_directory",
            "search_files_regex", "search_symbols", "execute_terminal_command",
            "web_search", "fetch_web_documentation",
            "git_status", "git_diff", "git_commit", "git_checkout_branch",
            "git_create_checkpoint", "git_revert_checkpoint"
        }
    }

    @classmethod
    def is_tool_allowed(cls, mode: OperatingMode, tool_name: str) -> bool:
        allowed = cls.ALLOWED_TOOLS.get(mode, set())
        return tool_name in allowed

    @classmethod
    def detect_mode_from_prompt(cls, prompt: str) -> OperatingMode:
        """Detects explicit user operating mode intent."""
        lower = prompt.lower()
        if lower.startswith("plan") or "create a plan" in lower or "plan the" in lower:
            return OperatingMode.PLAN
        elif lower.startswith("test") or "run test" in lower or "verify build" in lower:
            return OperatingMode.TEST
        elif lower.startswith("rectify") or lower.startswith("fix") or "fix the test" in lower or "debug" in lower:
            return OperatingMode.RECTIFY
        elif lower.startswith("implement") or "write code" in lower or "implement the" in lower:
            return OperatingMode.IMPLEMENT
        else:
            return OperatingMode.AUTONOMOUS
