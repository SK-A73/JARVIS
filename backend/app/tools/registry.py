"""
Central Tool Registry
Manages tool definitions for LLMs, argument validation, and audited execution.
"""
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session

from backend.app.llm.base import ToolDefinition, ToolCall
from backend.app.agent.modes import OperatingMode
from backend.app.core.decision import DecisionEngine
from backend.app.models.task import AuditLog
from backend.app.tools.file_tools import (
    read_file,
    write_file,
    edit_file_block,
    list_directory,
    search_files_regex
)
from backend.app.tools.terminal_tools import execute_terminal_command
from backend.app.tools.git_tools import (
    git_status,
    git_diff,
    git_commit,
    git_create_checkpoint,
    git_revert_checkpoint
)
from backend.app.tools.web_tools import fetch_web_documentation, web_search

logger = logging.getLogger(__name__)

class ToolRegistry:
    # Tool definitions with JSON Schemas for LLM function calling
    TOOL_DEFINITIONS: List[ToolDefinition] = [
        ToolDefinition(
            name="read_file",
            description="Reads the contents of a file within the workspace. Optional line range.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Relative or absolute file path"},
                    "start_line": {"type": "integer", "description": "1-indexed start line"},
                    "end_line": {"type": "integer", "description": "1-indexed end line"}
                },
                "required": ["file_path"]
            }
        ),
        ToolDefinition(
            name="write_file",
            description="Creates a new file or overwrites an existing file with the given content.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Target file path"},
                    "content": {"type": "string", "description": "File text content"},
                    "overwrite": {"type": "boolean", "description": "True to overwrite if exists"}
                },
                "required": ["file_path", "content"]
            }
        ),
        ToolDefinition(
            name="edit_file_block",
            description="Replaces an exact, unique block of code inside an existing file.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Target file path"},
                    "target_content": {"type": "string", "description": "Exact text chunk to replace"},
                    "replacement_content": {"type": "string", "description": "New replacement text"}
                },
                "required": ["file_path", "target_content", "replacement_content"]
            }
        ),
        ToolDefinition(
            name="list_directory",
            description="Lists files and subdirectories within a directory path up to specified depth.",
            parameters={
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "Directory path (default .)"},
                    "depth": {"type": "integer", "description": "Max traversal depth (default 2)"}
                }
            }
        ),
        ToolDefinition(
            name="search_files_regex",
            description="Searches for a regular expression pattern across files in a directory.",
            parameters={
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "Directory to search"},
                    "pattern": {"type": "string", "description": "Regex pattern"},
                    "file_pattern": {"type": "string", "description": "File extension glob like *.py"}
                },
                "required": ["dir_path", "pattern"]
            }
        ),
        ToolDefinition(
            name="execute_terminal_command",
            description="Executes a shell command in the workspace. Dangerous commands require approval.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                    "cwd": {"type": "string", "description": "Working directory path"},
                    "timeout_seconds": {"type": "integer", "description": "Max timeout in seconds"}
                },
                "required": ["command"]
            }
        ),
        ToolDefinition(
            name="git_status",
            description="Returns the current Git working tree status.",
            parameters={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Repository path"}
                }
            }
        ),
        ToolDefinition(
            name="git_diff",
            description="Returns current unstaged/staged Git diff.",
            parameters={
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Repository path"}
                }
            }
        ),
        ToolDefinition(
            name="git_commit",
            description="Stages all changes and creates a Git commit.",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "repo_path": {"type": "string", "description": "Repository path"}
                },
                "required": ["message"]
            }
        ),
        ToolDefinition(
            name="git_create_checkpoint",
            description="Creates a safe Git checkpoint/tag before making autonomous changes.",
            parameters={
                "type": "object",
                "properties": {
                    "checkpoint_name": {"type": "string", "description": "Name for the checkpoint"}
                },
                "required": ["checkpoint_name"]
            }
        ),
        ToolDefinition(
            name="git_revert_checkpoint",
            description="Reverts codebase back to a previously saved Git checkpoint.",
            parameters={
                "type": "object",
                "properties": {
                    "checkpoint_name": {"type": "string", "description": "Name of checkpoint to restore"}
                },
                "required": ["checkpoint_name"]
            }
        ),
        ToolDefinition(
            name="web_search",
            description="Searches developer documentation and technical references on the Internet.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query terms"}
                },
                "required": ["query"]
            }
        ),
        ToolDefinition(
            name="fetch_web_documentation",
            description="Fetches and parses technical documentation from a given URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website or documentation URL"}
                },
                "required": ["url"]
            }
        )
    ]

    @classmethod
    def get_definitions_for_mode(cls, mode: OperatingMode) -> List[ToolDefinition]:
        """Returns only the tool definitions allowed in the specified operating mode."""
        from backend.app.agent.modes import ModePolicy
        return [t for t in cls.TOOL_DEFINITIONS if ModePolicy.is_tool_allowed(mode, t.name)]

    @classmethod
    async def execute_tool(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        mode: OperatingMode = OperatingMode.AUTONOMOUS,
        db: Optional[Session] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validates safety, evaluates operating mode constraints, runs the tool, and audits."""
        # 1. Safety check
        verdict = DecisionEngine.evaluate_tool_execution(tool_name, arguments, mode)
        if not verdict.is_allowed:
            return {
                "success": False,
                "error": verdict.reason,
                "requires_confirmation": verdict.requires_user_confirmation
            }

        # 2. Execution dispatch
        result = {}
        try:
            if tool_name == "read_file":
                content = read_file(**arguments)
                result = {"success": True, "content": content}
            elif tool_name == "write_file":
                msg = write_file(**arguments)
                result = {"success": True, "message": msg}
            elif tool_name == "edit_file_block":
                msg = edit_file_block(**arguments)
                result = {"success": True, "message": msg}
            elif tool_name == "list_directory":
                items = list_directory(**arguments)
                result = {"success": True, "items": items}
            elif tool_name == "search_files_regex":
                matches = search_files_regex(**arguments)
                result = {"success": True, "matches": matches}
            elif tool_name == "execute_terminal_command":
                res = await execute_terminal_command(**arguments)
                result = {"success": res["exit_code"] == 0, **res}
            elif tool_name == "git_status":
                res = await git_status(**arguments)
                result = {"success": res["exit_code"] == 0, **res}
            elif tool_name == "git_diff":
                res = await git_diff(**arguments)
                result = {"success": res["exit_code"] == 0, **res}
            elif tool_name == "git_commit":
                res = await git_commit(**arguments)
                result = res
            elif tool_name == "git_create_checkpoint":
                res = await git_create_checkpoint(**arguments)
                result = res
            elif tool_name == "git_revert_checkpoint":
                res = await git_revert_checkpoint(**arguments)
                result = res
            elif tool_name == "web_search":
                res = await web_search(**arguments)
                result = {"success": True, **res}
            elif tool_name == "fetch_web_documentation":
                res = await fetch_web_documentation(**arguments)
                result = res
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            result = {"success": False, "error": str(e)}

        # 3. Audit logging
        if db:
            try:
                audit = AuditLog(
                    task_id=task_id,
                    action=f"tool_execution:{tool_name}",
                    command=str(arguments.get("command", "")) if "command" in arguments else None,
                    target=str(arguments.get("file_path", arguments.get("url", ""))),
                    status="SUCCESS" if result.get("success") else "FAILED",
                    details={"args": arguments, "warnings": verdict.warnings}
                )
                db.add(audit)
                db.commit()
            except Exception as ex:
                logger.error(f"Audit log failed: {ex}")

        return result
