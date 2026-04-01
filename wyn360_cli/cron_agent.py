"""
WYN360 Cron Agent - Schedule agents to run on recurring intervals.

Supports scheduling background tasks that execute on a cron-like schedule,
such as monitoring CI, checking for updates, or running periodic checks.
"""

import asyncio
import time
import uuid
import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CronJob:
    """A scheduled recurring task."""
    id: str
    name: str
    prompt: str
    interval_seconds: int
    enabled: bool = True
    last_run_at: float = 0.0
    run_count: int = 0
    last_result: Optional[str] = None
    last_error: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    @property
    def next_run_at(self) -> float:
        """When this job should next run."""
        if self.last_run_at == 0:
            return self.created_at
        return self.last_run_at + self.interval_seconds

    @property
    def is_due(self) -> bool:
        """Whether this job should run now."""
        return self.enabled and time.time() >= self.next_run_at

    @property
    def interval_display(self) -> str:
        """Human-readable interval."""
        s = self.interval_seconds
        if s < 60:
            return f"{s}s"
        elif s < 3600:
            return f"{s // 60}m"
        else:
            return f"{s // 3600}h{(s % 3600) // 60}m"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "interval": self.interval_display,
            "enabled": self.enabled,
            "run_count": self.run_count,
            "last_run_at": self.last_run_at,
        }


def parse_interval(interval_str: str) -> int:
    """
    Parse an interval string like '5m', '1h', '30s', '2h30m' into seconds.

    Supported units: s (seconds), m (minutes), h (hours)
    """
    import re
    total = 0
    parts = re.findall(r'(\d+)\s*([smh])', interval_str.lower())
    if not parts:
        # Try as plain integer (assume minutes)
        try:
            return int(interval_str) * 60
        except ValueError:
            raise ValueError(f"Invalid interval: {interval_str}. Use format like '5m', '1h', '30s'")

    for value, unit in parts:
        v = int(value)
        if unit == 's':
            total += v
        elif unit == 'm':
            total += v * 60
        elif unit == 'h':
            total += v * 3600

    if total <= 0:
        raise ValueError("Interval must be positive")
    return total


class CronManager:
    """Manages scheduled recurring agents."""

    def __init__(self):
        self.jobs: Dict[str, CronJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def create_job(self, name: str, prompt: str, interval: str) -> CronJob:
        """
        Create a new cron job.

        Args:
            name: Human-readable job name
            prompt: Prompt to send to the agent
            interval: Interval string (e.g., '5m', '1h', '30s')
        """
        interval_seconds = parse_interval(interval)
        job_id = f"cron-{uuid.uuid4().hex[:6]}"
        job = CronJob(
            id=job_id,
            name=name,
            prompt=prompt,
            interval_seconds=interval_seconds,
        )
        self.jobs[job_id] = job
        logger.info(f"Created cron job '{name}' (every {job.interval_display})")
        return job

    def delete_job(self, job_id: str) -> bool:
        """Delete a cron job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        """Pause a cron job."""
        job = self.jobs.get(job_id)
        if job:
            job.enabled = False
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused cron job."""
        job = self.jobs.get(job_id)
        if job:
            job.enabled = True
            return True
        return False

    def list_jobs(self) -> List[CronJob]:
        """List all cron jobs."""
        return list(self.jobs.values())

    def get_due_jobs(self) -> List[CronJob]:
        """Get all jobs that are due to run."""
        return [j for j in self.jobs.values() if j.is_due]

    async def run_job(self, job: CronJob, model, system_prompt: str = "") -> str:
        """Run a single cron job."""
        try:
            from pydantic_ai import Agent
            agent = Agent(
                model=model,
                system_prompt=system_prompt or "You are a background monitoring agent. Be concise.",
                retries=0,
            )
            result = await agent.run(job.prompt)
            response = getattr(result, 'data', None) or getattr(result, 'output', str(result))
            if not isinstance(response, str):
                response = str(response)

            job.last_result = response
            job.last_error = None
            job.last_run_at = time.time()
            job.run_count += 1
            return response

        except Exception as e:
            job.last_error = str(e)
            job.last_run_at = time.time()
            job.run_count += 1
            logger.error(f"Cron job '{job.name}' failed: {e}")
            return f"Error: {e}"

    async def tick(self, model, system_prompt: str = "") -> List[Dict[str, Any]]:
        """
        Check for and run any due jobs. Call this periodically.

        Returns list of results from jobs that ran.
        """
        results = []
        for job in self.get_due_jobs():
            logger.info(f"Running cron job '{job.name}'")
            output = await self.run_job(job, model, system_prompt)
            results.append({
                "job_id": job.id,
                "name": job.name,
                "result": output,
                "error": job.last_error,
            })
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get cron manager statistics."""
        total_runs = sum(j.run_count for j in self.jobs.values())
        return {
            "total_jobs": len(self.jobs),
            "active_jobs": sum(1 for j in self.jobs.values() if j.enabled),
            "total_runs": total_runs,
            "due_now": len(self.get_due_jobs()),
        }
