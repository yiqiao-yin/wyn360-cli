"""
WYN360 Sub-Agent System - Parallel worker agents for research and implementation.

Supports spawning multiple pydantic-ai agents that run concurrently,
with task lifecycle management and result synthesis.
"""

import asyncio
import time
import uuid
import logging
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


class TaskType(Enum):
    RESEARCH = "research"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    GENERAL = "general"


@dataclass
class SubAgentTask:
    """A task assigned to a sub-agent."""
    id: str
    description: str
    prompt: str
    task_type: TaskType = TaskType.GENERAL
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def duration_ms(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED)


class SubAgentManager:
    """Manages spawning and tracking of sub-agent workers."""

    def __init__(self, model, system_prompt: str = "", max_concurrent: int = 3):
        """
        Args:
            model: The pydantic-ai model to use for sub-agents
            system_prompt: Base system prompt for workers
            max_concurrent: Max number of concurrent workers
        """
        self.model = model
        self.system_prompt = system_prompt
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, SubAgentTask] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def create_task(self, description: str, prompt: str,
                    task_type: TaskType = TaskType.GENERAL) -> SubAgentTask:
        """Create a new task (does not start it)."""
        task_id = f"agent-{uuid.uuid4().hex[:6]}"
        task = SubAgentTask(
            id=task_id,
            description=description,
            prompt=prompt,
            task_type=task_type,
        )
        self.tasks[task_id] = task
        return task

    async def run_task(self, task: SubAgentTask,
                       message_history: Optional[List] = None) -> SubAgentTask:
        """Run a single task with the sub-agent."""
        from pydantic_ai import Agent

        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.start_time = time.time()

            try:
                # Build worker system prompt
                worker_prompt = self.system_prompt
                if task.task_type == TaskType.RESEARCH:
                    worker_prompt += "\n\nYou are a research worker. Investigate and report findings. Do NOT modify files."
                elif task.task_type == TaskType.VERIFY:
                    worker_prompt += "\n\nYou are a verification worker. Prove the code works, don't just confirm it exists."

                worker = Agent(
                    model=self.model,
                    system_prompt=worker_prompt,
                    retries=0,
                )

                result = await worker.run(
                    task.prompt,
                    message_history=message_history or [],
                )

                response = getattr(result, 'data', None) or getattr(result, 'output', str(result))
                if not isinstance(response, str):
                    response = str(response)

                task.result = response
                task.status = TaskStatus.COMPLETED

            except asyncio.CancelledError:
                task.status = TaskStatus.KILLED
                task.error = "Task was cancelled"
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.error(f"Sub-agent task {task.id} failed: {e}")

            task.end_time = time.time()
            return task

    async def run_parallel(self, tasks: List[SubAgentTask]) -> List[SubAgentTask]:
        """Run multiple tasks in parallel, respecting concurrency limits."""
        coros = [self.run_task(task) for task in tasks]
        await asyncio.gather(*coros, return_exceptions=True)
        return tasks

    async def spawn_research(self, prompts: List[Dict[str, str]]) -> List[SubAgentTask]:
        """
        Convenience method to spawn parallel research tasks.

        Args:
            prompts: List of dicts with 'description' and 'prompt' keys

        Returns:
            List of completed tasks
        """
        tasks = []
        for p in prompts:
            task = self.create_task(
                description=p["description"],
                prompt=p["prompt"],
                task_type=TaskType.RESEARCH,
            )
            tasks.append(task)

        return await self.run_parallel(tasks)

    def kill_task(self, task_id: str) -> bool:
        """Mark a task as killed (cancellation is best-effort)."""
        task = self.tasks.get(task_id)
        if task and not task.is_terminal:
            task.status = TaskStatus.KILLED
            task.end_time = time.time()
            return True
        return False

    def get_task(self, task_id: str) -> Optional[SubAgentTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[SubAgentTask]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def get_running_count(self) -> int:
        """Get number of currently running tasks."""
        return sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)

    def synthesize_results(self, tasks: List[SubAgentTask]) -> str:
        """
        Combine results from multiple completed tasks into a summary.

        Returns formatted text with each task's result.
        """
        parts = []
        for task in tasks:
            header = f"### {task.description}"
            if task.status == TaskStatus.COMPLETED:
                parts.append(f"{header}\n{task.result}")
            elif task.status == TaskStatus.FAILED:
                parts.append(f"{header}\n**FAILED**: {task.error}")
            elif task.status == TaskStatus.KILLED:
                parts.append(f"{header}\n**KILLED**: Task was stopped")
            else:
                parts.append(f"{header}\n**{task.status.value}**: Still running")

        stats = self._task_stats(tasks)
        summary = f"**Workers**: {stats['total']} total, {stats['completed']} completed, {stats['failed']} failed"
        if stats['total_duration_ms']:
            summary += f" | Duration: {stats['total_duration_ms']:.0f}ms"

        return f"{summary}\n\n" + "\n\n".join(parts)

    def _task_stats(self, tasks: List[SubAgentTask]) -> Dict[str, Any]:
        """Compute aggregate statistics for a set of tasks."""
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        durations = [t.duration_ms for t in tasks if t.duration_ms is not None]

        return {
            "total": len(tasks),
            "completed": len(completed),
            "failed": len(failed),
            "total_duration_ms": sum(durations) if durations else None,
        }
