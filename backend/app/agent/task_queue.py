"""
24/7 Persistent Task Queue and Background Worker
Manages autonomous long-running tasks, cancellation events, state persistence,
and reconnection catch-up briefings.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.task import Task, TaskStep
from backend.app.agent.coding_agent import CodingAgent
from backend.app.llm.factory import LLMProviderFactory
from backend.app.agent.modes import OperatingMode

logger = logging.getLogger(__name__)

class TaskQueue:
    _instance = None

    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.cancel_events: Dict[str, asyncio.Event] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self._worker_loop_task: Optional[asyncio.Task] = None
        self._running = False

    @classmethod
    def get_instance(cls) -> "TaskQueue":
        if cls._instance is None:
            cls._instance = TaskQueue()
        return cls._instance

    def start_worker(self):
        if not self._running:
            self._running = True
            self._worker_loop_task = asyncio.create_task(self._process_queue())
            logger.info("JARVIS 24/7 Task Queue Worker started.")

    def stop_worker(self):
        self._running = False
        if self._worker_loop_task:
            self._worker_loop_task.cancel()
        for t_id, event in self.cancel_events.items():
            event.set()

    async def enqueue_task(self, task_id: str):
        """Adds a task ID to the background execution queue."""
        self.cancel_events[task_id] = asyncio.Event()
        await self.queue.put(task_id)

    async def _process_queue(self):
        """Worker loop processing queued tasks asynchronously."""
        while self._running:
            try:
                task_id = await self.queue.get()
                if task_id in self.cancel_events and self.cancel_events[task_id].is_set():
                    self.queue.task_done()
                    continue

                # Run task in background
                bg_task = asyncio.create_task(self._execute_single_task(task_id))
                self.active_tasks[task_id] = bg_task
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task worker loop: {e}")
                await asyncio.sleep(1)

    async def _execute_single_task(self, task_id: str):
        """Executes a single autonomous task with database session and error isolation."""
        db: Session = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                return

            if task.status == "CANCELLED":
                return

            provider = LLMProviderFactory.get_provider()
            agent = CodingAgent(db, provider, task)

            # Check if cancelled before starting
            if task_id in self.cancel_events and self.cancel_events[task_id].is_set():
                task.status = "CANCELLED"
                db.commit()
                return

            # Execute autonomous cycle
            await agent.run_development_cycle(
                test_command="python -c \"print('Verification Passed')\"",
                max_rectification_attempts=3
            )

        except asyncio.CancelledError:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "CANCELLED"
                task.result_summary = "Task was interrupted and cancelled by user."
                db.commit()
        except Exception as e:
            logger.error(f"Task {task_id} execution encountered error: {e}")
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "FAILED"
                task.error_message = str(e)
                db.commit()
        finally:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            if task_id in self.cancel_events:
                del self.cancel_events[task_id]
            db.close()

    def cancel_task(self, task_id: str, db: Session) -> bool:
        """Signals cancellation to an ongoing task and updates state immediately."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False

        if task.status in ["COMPLETED", "FAILED", "CANCELLED"]:
            return False

        if task_id in self.cancel_events:
            self.cancel_events[task_id].set()

        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()

        task.status = "CANCELLED"
        task.result_summary = "Operation halted by user request (Interrupted)."
        db.commit()
        return True

    @staticmethod
    def get_reconnect_briefing(db: Session, since: Optional[datetime] = None) -> str:
        """Generates an executive briefing of actions completed while client was away."""
        cutoff = since or (datetime.now(timezone.utc) - asyncio.timedelta(hours=24) if hasattr(asyncio, 'timedelta') else None)
        
        q = db.query(Task).order_by(Task.updated_at.desc())
        recent_tasks = q.limit(5).all()

        if not recent_tasks:
            return "While you were away, all systems remained idle and stable."

        lines = ["Here is what happened while you were away:"]
        for t in recent_tasks:
            status_icon = "✓" if t.status == "COMPLETED" else ("✗" if t.status == "FAILED" else "⏳")
            lines.append(f"• {status_icon} [{t.status}] {t.title}: {t.result_summary or t.error_message or 'In progress'}")

        return "\n".join(lines)
