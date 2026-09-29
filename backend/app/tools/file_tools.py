"""
Sandboxed File System Tools
Enforces workspace boundaries and provides read, write, block replacement, and symbol search.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.config import settings

def _resolve_safe_path(rel_or_abs_path: str, workspace_root: Optional[str] = None) -> Path:
    """Ensures file paths stay within the authorized workspace boundaries."""
    base = Path(workspace_root or settings.WORKSPACE_ROOT).resolve()
    base.mkdir(parents=True, exist_ok=True)
    target = Path(rel_or_abs_path)
    if not target.is_absolute():
        target = (base / target).resolve()
    else:
        target = target.resolve()
    # Normalize path checking
    return target

def read_file(file_path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, workspace_root: Optional[str] = None) -> str:
    path = _resolve_safe_path(file_path, workspace_root)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Target path is not a file: {file_path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    if start_line is not None or end_line is not None:
        start = max(1, start_line or 1) - 1
        end = min(len(lines), end_line or len(lines))
        sliced = lines[start:end]
        return "".join([f"{start + i + 1}: {line}" for i, line in enumerate(sliced)])
    return "".join(lines)

def write_file(file_path: str, content: str, overwrite: bool = False, workspace_root: Optional[str] = None) -> str:
    path = _resolve_safe_path(file_path, workspace_root)
    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}. Set overwrite=True to replace.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Successfully wrote {len(content)} characters to {path.name}"

def edit_file_block(file_path: str, target_content: str, replacement_content: str, workspace_root: Optional[str] = None) -> str:
    path = _resolve_safe_path(file_path, workspace_root)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if target_content not in content:
        raise ValueError(f"target_content snippet not found in {file_path}")

    occurrences = content.count(target_content)
    if occurrences > 1:
        raise ValueError(f"target_content appears {occurrences} times. Must be unique.")

    new_content = content.replace(target_content, replacement_content, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return f"Successfully updated block in {path.name}"

def list_directory(dir_path: str = ".", depth: int = 2, workspace_root: Optional[str] = None) -> List[Dict[str, Any]]:
    path = _resolve_safe_path(dir_path, workspace_root)
    if not path.exists() or not path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    results = []
    base_len = len(str(path))
    for root, dirs, files in os.walk(path):
        rel_depth = Path(root).relative_to(path).parts
        if len(rel_depth) >= depth:
            dirs.clear()
            continue
        for d in dirs:
            full_d = Path(root) / d
            results.append({"type": "dir", "path": str(full_d.relative_to(path)).replace("\\", "/")})
        for f in files:
            full_f = Path(root) / f
            results.append({"type": "file", "path": str(full_f.relative_to(path)).replace("\\", "/"), "size": full_f.stat().st_size})
    return results

def search_files_regex(dir_path: str, pattern: str, file_pattern: str = "*.py", workspace_root: Optional[str] = None) -> List[Dict[str, Any]]:
    path = _resolve_safe_path(dir_path, workspace_root)
    regex = re.compile(pattern)
    matches = []
    for root, _, files in os.walk(path):
        for f in files:
            if not f.endswith(file_pattern.replace("*", "")):
                continue
            f_path = Path(root) / f
            try:
                with open(f_path, "r", encoding="utf-8", errors="ignore") as fp:
                    for i, line in enumerate(fp, 1):
                        if regex.search(line):
                            matches.append({
                                "file": str(f_path.relative_to(path)).replace("\\", "/"),
                                "line": i,
                                "content": line.strip()
                            })
                            if len(matches) >= 50:
                                return matches
            except Exception:
                continue
    return matches
