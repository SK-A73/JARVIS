"""
Git Versioning and Checkpoint Management Tools
Allows creating checkpoints before autonomous modifications and reverting if necessary.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from backend.app.tools.terminal_tools import execute_terminal_command
from backend.app.config import settings

def _get_repo_path(repo_path: Optional[str] = None) -> str:
    return repo_path or settings.WORKSPACE_ROOT

async def git_status(repo_path: Optional[str] = None) -> Dict[str, Any]:
    path = _get_repo_path(repo_path)
    res = await execute_terminal_command("git status --short", cwd=path)
    return {"status": res["stdout"], "exit_code": res["exit_code"]}

async def git_diff(repo_path: Optional[str] = None) -> Dict[str, Any]:
    path = _get_repo_path(repo_path)
    res = await execute_terminal_command("git diff", cwd=path)
    return {"diff": res["stdout"], "exit_code": res["exit_code"]}

async def git_commit(message: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    path = _get_repo_path(repo_path)
    add_res = await execute_terminal_command("git add -A", cwd=path)
    if add_res["exit_code"] != 0:
        return {"success": False, "error": add_res["stderr"]}
    clean_msg = message.replace('"', '\\"')
    commit_res = await execute_terminal_command(f'git commit -m "{clean_msg}"', cwd=path)
    return {
        "success": commit_res["exit_code"] == 0,
        "output": commit_res["stdout"],
        "error": commit_res["stderr"]
    }

async def git_create_checkpoint(checkpoint_name: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Creates a local Git tag/checkpoint before risky modifications."""
    path = _get_repo_path(repo_path)
    tag_name = f"checkpoint_{checkpoint_name.replace(' ', '_')}"
    # Commit changes if dirty first
    await git_commit(f"chore(checkpoint): save state before {checkpoint_name}", repo_path=path)
    tag_res = await execute_terminal_command(f"git tag -f {tag_name}", cwd=path)
    return {
        "success": tag_res["exit_code"] == 0,
        "checkpoint": tag_name,
        "output": tag_res["stdout"]
    }

async def git_revert_checkpoint(checkpoint_name: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """Reverts codebase to a previously saved checkpoint."""
    path = _get_repo_path(repo_path)
    tag_name = f"checkpoint_{checkpoint_name.replace(' ', '_')}"
    reset_res = await execute_terminal_command(f"git reset --hard {tag_name}", cwd=path)
    return {
        "success": reset_res["exit_code"] == 0,
        "message": f"Reverted codebase to checkpoint: {tag_name}",
        "output": reset_res["stdout"],
        "error": reset_res["stderr"]
    }
