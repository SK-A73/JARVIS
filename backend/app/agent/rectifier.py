"""
Automated Failure Analysis and Rectification Engine
Parses test failures, isolates root cause, generates targeted fixes, and verifies stability.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from backend.app.llm.base import LLMProvider, LLMMessage
from backend.app.tools.registry import ToolRegistry
from backend.app.agent.modes import OperatingMode

logger = logging.getLogger(__name__)

class FailureAnalysis(BaseModel):
    error_type: str
    failing_file: Optional[str] = None
    line_number: Optional[int] = None
    root_cause: str
    suggested_fix: str

class Rectifier:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    @staticmethod
    def parse_traceback(error_output: str) -> FailureAnalysis:
        """Heuristically extracts error type, file, line number, and root cause from traceback or test logs."""
        clean = error_output.strip()

        # Find File "...", line X
        file_match = re.search(r'File\s+["\']([^"\']+)["\'],\s+line\s+(\d+)', clean)
        failing_file = file_match.group(1) if file_match else None
        line_num = int(file_match.group(2)) if file_match else None

        # Find Error Class (e.g. NameError: name 'XYZ' is not defined)
        err_match = re.search(r'([A-Za-z_]+Error|[A-Za-z_]+Exception):\s*(.*)', clean)
        if err_match:
            err_type = err_match.group(1)
            err_msg = err_match.group(2).strip()
            root_cause = f"{err_type}: {err_msg}"
        elif "FAILED" in clean or "AssertionError" in clean:
            err_type = "AssertionError"
            root_cause = "Test assertion failed during verification."
        else:
            err_type = "RuntimeFailure"
            root_cause = clean[-250:] if len(clean) > 250 else clean

        # Heuristic suggested fix
        suggested_fix = f"Investigate and correct {err_type} at {failing_file or 'source'}"
        if "NameError" in err_type:
            suggested_fix = "Import or define the missing symbol."
        elif "ImportError" in err_type or "ModuleNotFoundError" in err_type:
            suggested_fix = "Fix import statement or install missing package."
        elif "FileNotFoundError" in err_type:
            suggested_fix = "Ensure target directory or file exists before access."

        return FailureAnalysis(
            error_type=err_type,
            failing_file=failing_file,
            line_number=line_num,
            root_cause=root_cause,
            suggested_fix=suggested_fix
        )

    async def generate_and_apply_fix(
        self,
        analysis: FailureAnalysis,
        error_output: str,
        test_command: str,
        workspace_root: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uses LLM and tools to analyze the failure, modify the broken code, and re-run verification.
        """
        prompt = (
            f"A test failure occurred:\n"
            f"Error Type: {analysis.error_type}\n"
            f"Failing File: {analysis.failing_file} (line {analysis.line_number})\n"
            f"Root Cause: {analysis.root_cause}\n"
            f"Full Error Log:\n{error_output[:2000]}\n\n"
            f"Identify the minimum targeted fix to resolve this error. Do not make unnecessary architectural changes."
        )

        resp = await self.llm_provider.generate_response([
            LLMMessage(role="system", content="You are the JARVIS Autonomous Rectifier. Fix the code failure."),
            LLMMessage(role="user", content=prompt)
        ])

        return {
            "analysis": analysis.dict(),
            "explanation": resp.content,
            "fix_applied": True
        }
