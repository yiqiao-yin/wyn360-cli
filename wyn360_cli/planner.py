"""
WYN360 Plan Mode - Structured planning before execution.

The planner produces a step-by-step plan for user approval before
the agent begins making changes. This prevents the agent from
jumping into code modifications without thinking through the approach.
"""

import time
import logging
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class PlanStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in an execution plan."""
    index: int
    description: str
    files_involved: List[str] = field(default_factory=list)
    status: PlanStepStatus = PlanStepStatus.PENDING
    notes: str = ""


@dataclass
class Plan:
    """A structured execution plan."""
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    approved: bool = False
    completed: bool = False

    @property
    def current_step(self) -> Optional[PlanStep]:
        """Get the next pending or in-progress step."""
        for step in self.steps:
            if step.status in (PlanStepStatus.PENDING, PlanStepStatus.IN_PROGRESS):
                return step
        return None

    @property
    def progress(self) -> str:
        """Get progress string like '2/5 steps completed'."""
        done = sum(1 for s in self.steps if s.status in (PlanStepStatus.COMPLETED, PlanStepStatus.SKIPPED))
        return f"{done}/{len(self.steps)} steps completed"

    def to_markdown(self) -> str:
        """Render the plan as markdown for display."""
        lines = [f"## Plan: {self.goal}\n"]

        status_icons = {
            PlanStepStatus.PENDING: "[ ]",
            PlanStepStatus.IN_PROGRESS: "[>]",
            PlanStepStatus.COMPLETED: "[x]",
            PlanStepStatus.SKIPPED: "[-]",
        }

        for step in self.steps:
            icon = status_icons[step.status]
            lines.append(f"{icon} **Step {step.index}**: {step.description}")
            if step.files_involved:
                files = ", ".join(f"`{f}`" for f in step.files_involved)
                lines.append(f"    Files: {files}")
            if step.notes:
                lines.append(f"    Note: {step.notes}")

        if self.approved:
            lines.append(f"\nProgress: {self.progress}")

        return "\n".join(lines)

    def advance(self) -> Optional[PlanStep]:
        """Mark current step as completed and return the next one."""
        current = self.current_step
        if current:
            current.status = PlanStepStatus.COMPLETED
        next_step = self.current_step
        if next_step:
            next_step.status = PlanStepStatus.IN_PROGRESS
        else:
            self.completed = True
        return next_step


class Planner:
    """Manages plan creation and execution tracking."""

    def __init__(self):
        self.current_plan: Optional[Plan] = None
        self.plan_history: List[Plan] = []

    @property
    def is_planning(self) -> bool:
        """True if there's an active unapproved plan."""
        return self.current_plan is not None and not self.current_plan.approved

    @property
    def is_executing(self) -> bool:
        """True if there's an approved plan being executed."""
        return (self.current_plan is not None
                and self.current_plan.approved
                and not self.current_plan.completed)

    def create_plan(self, goal: str, steps: List[dict]) -> Plan:
        """
        Create a new plan from a goal and list of step descriptions.

        Args:
            goal: What the plan aims to accomplish
            steps: List of dicts with 'description' and optional 'files' keys
        """
        plan_steps = []
        for i, step_data in enumerate(steps, 1):
            if isinstance(step_data, str):
                step_data = {"description": step_data}
            plan_steps.append(PlanStep(
                index=i,
                description=step_data.get("description", step_data.get("desc", "")),
                files_involved=step_data.get("files", []),
            ))

        plan = Plan(goal=goal, steps=plan_steps)
        self.current_plan = plan
        return plan

    def approve_plan(self) -> bool:
        """Approve the current plan for execution."""
        if self.current_plan and not self.current_plan.approved:
            self.current_plan.approved = True
            # Start first step
            if self.current_plan.steps:
                self.current_plan.steps[0].status = PlanStepStatus.IN_PROGRESS
            return True
        return False

    def reject_plan(self) -> bool:
        """Reject and discard the current plan."""
        if self.current_plan and not self.current_plan.approved:
            self.plan_history.append(self.current_plan)
            self.current_plan = None
            return True
        return False

    def advance_plan(self) -> Optional[PlanStep]:
        """Advance to the next step in the current plan."""
        if self.current_plan and self.current_plan.approved:
            next_step = self.current_plan.advance()
            if self.current_plan.completed:
                self.plan_history.append(self.current_plan)
            return next_step
        return None

    def skip_step(self) -> Optional[PlanStep]:
        """Skip the current step and move to the next."""
        if not self.current_plan or not self.current_plan.approved:
            return None
        current = self.current_plan.current_step
        if current:
            current.status = PlanStepStatus.SKIPPED
        return self.current_plan.current_step

    def get_plan_context(self) -> str:
        """Get current plan context for the system prompt."""
        if not self.current_plan:
            return ""

        plan_md = self.current_plan.to_markdown()

        if self.is_planning:
            return f"\n## Active Plan (awaiting approval)\n\n{plan_md}\n\nThe user needs to approve this plan before execution begins."
        elif self.is_executing:
            current = self.current_plan.current_step
            step_info = f"\n\nCurrently executing: Step {current.index} - {current.description}" if current else ""
            return f"\n## Active Plan (executing)\n\n{plan_md}{step_info}"

        return ""

    def get_planning_prompt(self) -> str:
        """Get the system prompt addition for plan mode."""
        return """
When the user asks you to plan or when a task is complex (involves multiple files or steps),
enter plan mode:

1. Analyze the task and break it into concrete steps
2. Present the plan as a numbered list with files involved
3. Wait for user approval before executing
4. Execute one step at a time, reporting progress

Use /plan to enter plan mode. The plan should be specific:
- Each step should be a single, actionable change
- List the files that will be modified
- Order steps by dependency (do prerequisites first)
"""
