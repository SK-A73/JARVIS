"""
Decision Engine and Safety Guard
Enforces safety constraints, detects conflicts with prior decisions, and checks operating modes.
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.agent.modes import OperatingMode, ModePolicy
from backend.app.models.memory import MemoryRecord, LearnedPattern

class DecisionVerdict(BaseModel):
    is_allowed: bool
    requires_user_confirmation: bool = False
    reason: str = "Action permitted."
    warnings: List[str] = []

class DecisionEngine:
    DANGEROUS_COMMAND_PATTERNS = [
        r'\brm\s+-r[fF]\s+[/~]',
        r'\bmkfs\b',
        r'\bformat\s+[a-zA-Z]:',
        r'\bdd\s+if=',
        r'\bdrop\s+database\b',
        r'\bshutdown\b',
        r'\breboot\b',
        r'del\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\',
        r'>\s*/dev/sd[a-z]'
    ]

    @classmethod
    def evaluate_tool_execution(
        cls,
        tool_name: str,
        tool_args: Dict[str, Any],
        mode: OperatingMode,
        relevant_memories: Optional[List[MemoryRecord]] = None,
        learned_patterns: Optional[List[LearnedPattern]] = None
    ) -> DecisionVerdict:
        """Evaluates whether a tool execution is safe, allowed in the mode, and consistent with past decisions."""
        warnings: List[str] = []

        # 1. Mode Enforcement
        if not ModePolicy.is_tool_allowed(mode, tool_name):
            return DecisionVerdict(
                is_allowed=False,
                requires_user_confirmation=False,
                reason=f"Tool '{tool_name}' is not permitted in {mode.value} mode. (Operating mode policy restriction)."
            )

        # 2. Terminal Dangerous Commands Check
        if tool_name == "execute_terminal_command":
            cmd = tool_args.get("command", "").strip()
            for pattern in cls.DANGEROUS_COMMAND_PATTERNS:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return DecisionVerdict(
                        is_allowed=False,
                        requires_user_confirmation=True,
                        reason=f"Command matches destructive pattern: '{cmd}'. Explicit user confirmation required.",
                        warnings=["Potentially irreversible filesystem or database alteration."]
                    )

        # 3. Conflict Detection with Prior Architectural Decisions
        if tool_name in ["write_file", "edit_file_block"]:
            file_path = tool_args.get("file_path", "")
            if relevant_memories:
                for mem in relevant_memories:
                    # Check if user explicitly asked not to use certain libraries or files
                    if "never modify" in mem.content.lower() and any(part in file_path.lower() for part in mem.content.lower().split()):
                        warnings.append(f"Notice: Prior memory indicates user preference regarding: '{mem.content}'.")

        return DecisionVerdict(
            is_allowed=True,
            requires_user_confirmation=False,
            reason="Action conforms to current mode and security policies.",
            warnings=warnings
        )
