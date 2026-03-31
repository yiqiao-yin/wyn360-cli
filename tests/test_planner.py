"""Unit tests for the plan mode system."""

import pytest
from wyn360_cli.planner import Planner, Plan, PlanStep, PlanStepStatus


class TestPlanStep:
    def test_default_status(self):
        step = PlanStep(index=1, description="Do something")
        assert step.status == PlanStepStatus.PENDING
        assert step.files_involved == []
        assert step.notes == ""


class TestPlan:
    def test_current_step(self):
        plan = Plan(
            goal="Fix bug",
            steps=[
                PlanStep(index=1, description="Investigate"),
                PlanStep(index=2, description="Fix"),
            ]
        )
        current = plan.current_step
        assert current is not None
        assert current.index == 1

    def test_current_step_skips_completed(self):
        plan = Plan(
            goal="Fix bug",
            steps=[
                PlanStep(index=1, description="Done", status=PlanStepStatus.COMPLETED),
                PlanStep(index=2, description="Next"),
            ]
        )
        assert plan.current_step.index == 2

    def test_current_step_none_when_all_done(self):
        plan = Plan(
            goal="Fix bug",
            steps=[
                PlanStep(index=1, description="Done", status=PlanStepStatus.COMPLETED),
            ]
        )
        assert plan.current_step is None

    def test_progress(self):
        plan = Plan(
            goal="Fix",
            steps=[
                PlanStep(index=1, description="A", status=PlanStepStatus.COMPLETED),
                PlanStep(index=2, description="B", status=PlanStepStatus.SKIPPED),
                PlanStep(index=3, description="C"),
            ]
        )
        assert plan.progress == "2/3 steps completed"

    def test_to_markdown(self):
        plan = Plan(
            goal="Add feature",
            steps=[
                PlanStep(index=1, description="Create file", files_involved=["src/new.py"]),
                PlanStep(index=2, description="Write tests"),
            ]
        )
        md = plan.to_markdown()
        assert "Add feature" in md
        assert "Create file" in md
        assert "`src/new.py`" in md

    def test_advance(self):
        plan = Plan(
            goal="Fix",
            steps=[
                PlanStep(index=1, description="A"),
                PlanStep(index=2, description="B"),
            ]
        )
        plan.steps[0].status = PlanStepStatus.IN_PROGRESS
        next_step = plan.advance()
        assert plan.steps[0].status == PlanStepStatus.COMPLETED
        assert next_step.index == 2
        assert next_step.status == PlanStepStatus.IN_PROGRESS

    def test_advance_completes_plan(self):
        plan = Plan(
            goal="Fix",
            steps=[PlanStep(index=1, description="A", status=PlanStepStatus.IN_PROGRESS)]
        )
        next_step = plan.advance()
        assert next_step is None
        assert plan.completed


class TestPlanner:
    def setup_method(self):
        self.planner = Planner()

    def test_create_plan(self):
        plan = self.planner.create_plan("Fix auth", [
            {"description": "Find the bug", "files": ["auth.py"]},
            {"description": "Write fix"},
        ])
        assert plan.goal == "Fix auth"
        assert len(plan.steps) == 2
        assert plan.steps[0].files_involved == ["auth.py"]
        assert self.planner.is_planning

    def test_create_plan_from_strings(self):
        plan = self.planner.create_plan("Task", ["Step 1", "Step 2"])
        assert len(plan.steps) == 2
        assert plan.steps[0].description == "Step 1"

    def test_approve_plan(self):
        self.planner.create_plan("Task", ["Step 1"])
        assert self.planner.approve_plan()
        assert not self.planner.is_planning
        assert self.planner.is_executing
        assert self.planner.current_plan.steps[0].status == PlanStepStatus.IN_PROGRESS

    def test_approve_without_plan(self):
        assert not self.planner.approve_plan()

    def test_reject_plan(self):
        self.planner.create_plan("Task", ["Step 1"])
        assert self.planner.reject_plan()
        assert self.planner.current_plan is None
        assert len(self.planner.plan_history) == 1

    def test_advance_plan(self):
        self.planner.create_plan("Task", ["Step 1", "Step 2"])
        self.planner.approve_plan()
        next_step = self.planner.advance_plan()
        assert next_step.index == 2

    def test_skip_step(self):
        self.planner.create_plan("Task", ["Step 1", "Step 2"])
        self.planner.approve_plan()
        self.planner.skip_step()
        assert self.planner.current_plan.steps[0].status == PlanStepStatus.SKIPPED

    def test_get_plan_context_empty(self):
        assert self.planner.get_plan_context() == ""

    def test_get_plan_context_planning(self):
        self.planner.create_plan("Task", ["Step 1"])
        ctx = self.planner.get_plan_context()
        assert "awaiting approval" in ctx

    def test_get_plan_context_executing(self):
        self.planner.create_plan("Task", ["Step 1"])
        self.planner.approve_plan()
        ctx = self.planner.get_plan_context()
        assert "executing" in ctx
