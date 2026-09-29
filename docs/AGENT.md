# JARVIS Autonomous Agent & Operating Modes Specification

JARVIS functions as an autonomous, self-governing software development and personal agent.

---

## 1. Operating Modes

```
                  +----------------------------------+
                  |         USER REQUEST             |
                  +-----------------+----------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
     [ PLAN MODE ]           [ TEST MODE ]          [ RECTIFY MODE ]
   Read & Plan only        Execute tests only      Fix failed tests
   (No writes/commands)    (No code edits)         (Targeted repairs)
            |                       |                       |
            +-----------------------+-----------------------+
                                    |
                                    v
                          [ AUTONOMOUS MODE ]
                 Full Cycle: Plan -> Implement -> Test
                 -> Rectify -> Checkpoint -> Complete
```

### 1.1 PLAN MODE
- Inspects directories, reads files, reviews tech stack, analyzes requirements.
- Outputs architectural breakdown, dependency risks, and implementation order.
- **Enforcement**: File modification (`write_file`, `edit_file_block`) and terminal command execution (`execute_terminal_command`) are strictly blocked.

### 1.2 IMPLEMENT MODE
- Reads existing plan and files.
- Creates or edits target code blocks.
- Preserves architectural consistency with established project memory.

### 1.3 TEST MODE
- Runs test suites and static analysis tools.
- Observes exit codes and failure logs.
- Isolates probable root causes without modifying production code.

### 1.4 RECTIFY MODE
- Analyzes error stack traces using `Rectifier.parse_traceback()`.
- Identifies error class (`NameError`, `ImportError`, `AssertionError`, etc.), file, and line number.
- Applies minimal targeted fix.
- Re-runs tests and regression suites until stable or max retries reached.

### 1.5 AUTONOMOUS MODE
- Executes the full development cycle across multiple tasks.
- Automatically creates Git safety checkpoints (`git tag checkpoint_*`) before applying changes.
- Dangerous commands (e.g. `rm -rf /`, `mkfs`, destructive database commands) require explicit confirmation.

---

## 2. Tool Registry
Tools are sandboxed and audited:
- `read_file`: Line-sliced or full file inspection.
- `write_file`: Workspace-bounded file creation.
- `edit_file_block`: Exact string replacement ensuring single uniqueness.
- `list_directory`: Directory traversal up to depth $N$.
- `search_files_regex`: Regex matching across source files.
- `execute_terminal_command`: Async subprocess execution with timeout, cancel event, and secret redaction.
- `git_create_checkpoint` / `git_revert_checkpoint`: Instant rollback mechanism.
- `web_search` / `fetch_web_documentation`: Technical research using authoritative documentation sources.
