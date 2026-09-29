"""
Autonomous Coding Agent
Implements the software development loop: Inspect -> Plan -> Checkpoint -> Implement -> Test -> Rectify -> Commit.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.llm.base import LLMProvider, LLMMessage
from backend.app.agent.modes import OperatingMode
from backend.app.agent.rectifier import Rectifier, FailureAnalysis
from backend.app.tools.registry import ToolRegistry
from backend.app.models.task import Task, TaskStep

logger = logging.getLogger(__name__)

class CodingAgent:
    def __init__(self, db: Session, llm_provider: LLMProvider, task: Task):
        self.db = db
        self.llm_provider = llm_provider
        self.task = task
        self.rectifier = Rectifier(llm_provider)
        self.step_counter = 0

    def _record_step(
        self,
        name: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[str] = None,
        status: str = "SUCCESS",
        error: Optional[str] = None
    ) -> TaskStep:
        self.step_counter += 1
        step = TaskStep(
            task_id=self.task.id,
            step_number=self.step_counter,
            name=name,
            status=status,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            error=error,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(step)
        self.task.current_step = name
        self.db.commit()
        self.db.refresh(step)
        return step

    async def run_development_cycle(
        self,
        test_command: str = "python -m pytest",
        max_rectification_attempts: int = 5
    ) -> Dict[str, Any]:
        """Runs the complete autonomous development and rectification loop."""
        self.task.status = "PLANNING"
        self.task.started_at = datetime.now(timezone.utc)
        self.db.commit()

        # Step 1: Planning
        self._record_step("Analyze requirements and plan implementation")
        plan_prompt = (
            f"User request: {self.task.user_request}\n"
            f"Formulate a step-by-step implementation plan for this coding task."
        )
        plan_resp = await self.llm_provider.generate_response([
            LLMMessage(role="system", content="You are the lead JARVIS software architect."),
            LLMMessage(role="user", content=plan_prompt)
        ])
        self.task.plan_data = {"plan": plan_resp.content}
        self.task.status = "IMPLEMENTING"
        self.db.commit()

        # Step 2: Create safety checkpoint
        self._record_step("Create safety Git checkpoint", tool_name="git_create_checkpoint")
        await ToolRegistry.execute_tool(
            "git_create_checkpoint",
            {"checkpoint_name": f"task_{self.task.id[:8]}"},
            mode=OperatingMode.AUTONOMOUS,
            db=self.db,
            task_id=self.task.id
        )

        # Step 3: Initial Test & Verification
        self.task.status = "TESTING"
        self.db.commit()
        test_res = await ToolRegistry.execute_tool(
            "execute_terminal_command",
            {"command": test_command},
            mode=OperatingMode.TEST,
            db=self.db,
            task_id=self.task.id
        )

        # Step 4: Rectification Loop if failing
        attempt = 0
        while not test_res.get("success") and attempt < max_rectification_attempts:
            attempt += 1
            self.task.status = "RECTIFYING"
            self.task.retry_count = attempt
            self.db.commit()

            err_text = test_res.get("stderr") or test_res.get("stdout") or "Unknown failure"
            analysis = self.rectifier.parse_traceback(err_text)

            self._record_step(
                f"Rectification Attempt {attempt}: {analysis.error_type}",
                tool_name="rectifier",
                tool_output=f"Root cause: {analysis.root_cause}. Suggestion: {analysis.suggested_fix}"
            )

            # Generate fix
            fix_result = await self.rectifier.generate_and_apply_fix(
                analysis,
                err_text,
                test_command
            )

            # Re-test
            self._record_step(f"Re-running test suite (Attempt {attempt})", tool_name="execute_terminal_command")
            test_res = await ToolRegistry.execute_tool(
                "execute_terminal_command",
                {"command": test_command},
                mode=OperatingMode.TEST,
                db=self.db,
                task_id=self.task.id
            )

        # Step 5: Final Evaluation
        if test_res.get("success"):
            self.task.status = "COMPLETED"
            self.task.completed_at = datetime.now(timezone.utc)
            self.task.result_summary = f"All tests passed successfully after {attempt} rectification iteration(s)."
            self._record_step("Task successfully completed", status="SUCCESS")
        else:
            self.task.status = "FAILED"
            self.task.completed_at = datetime.now(timezone.utc)
            self.task.error_message = f"Failed to resolve errors after {attempt} rectification attempts."
            self._record_step("Task failed after maximum retries", status="FAILED", error=self.task.error_message)

        self.db.commit()
        return {
            "task_id": self.task.id,
            "status": self.task.status,
            "attempts": attempt,
            "summary": self.task.result_summary or self.task.error_message
        }
