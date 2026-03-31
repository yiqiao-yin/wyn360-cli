"""Unit tests for the sub-agent system."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from wyn360_cli.subagent import SubAgentManager, SubAgentTask, TaskStatus, TaskType


class TestSubAgentTask:
    """Tests for SubAgentTask dataclass."""

    def test_task_creation(self):
        task = SubAgentTask(
            id="agent-abc123",
            description="Test task",
            prompt="Do something",
        )
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert not task.is_terminal

    def test_terminal_states(self):
        task = SubAgentTask(id="t1", description="", prompt="")
        task.status = TaskStatus.COMPLETED
        assert task.is_terminal
        task.status = TaskStatus.FAILED
        assert task.is_terminal
        task.status = TaskStatus.KILLED
        assert task.is_terminal
        task.status = TaskStatus.RUNNING
        assert not task.is_terminal

    def test_duration(self):
        task = SubAgentTask(id="t1", description="", prompt="")
        assert task.duration_ms is None
        task.start_time = 1000.0
        task.end_time = 1002.5
        assert task.duration_ms == 2500.0


class TestSubAgentManager:
    """Tests for SubAgentManager class."""

    def setup_method(self):
        self.model = MagicMock()
        self.manager = SubAgentManager(
            model=self.model,
            system_prompt="Test prompt",
            max_concurrent=2,
        )

    def test_create_task(self):
        task = self.manager.create_task("Research auth", "Find auth bugs")
        assert task.id.startswith("agent-")
        assert task.description == "Research auth"
        assert task.status == TaskStatus.PENDING
        assert task.id in self.manager.tasks

    def test_create_task_with_type(self):
        task = self.manager.create_task("Verify", "Run tests", TaskType.VERIFY)
        assert task.task_type == TaskType.VERIFY

    def test_kill_task(self):
        task = self.manager.create_task("Test", "prompt")
        task.status = TaskStatus.RUNNING
        assert self.manager.kill_task(task.id)
        assert task.status == TaskStatus.KILLED
        assert task.end_time is not None

    def test_kill_terminal_task_fails(self):
        task = self.manager.create_task("Test", "prompt")
        task.status = TaskStatus.COMPLETED
        assert not self.manager.kill_task(task.id)

    def test_kill_nonexistent_fails(self):
        assert not self.manager.kill_task("nonexistent")

    def test_get_task(self):
        task = self.manager.create_task("Test", "prompt")
        found = self.manager.get_task(task.id)
        assert found is task

    def test_get_nonexistent(self):
        assert self.manager.get_task("nope") is None

    def test_list_tasks(self):
        t1 = self.manager.create_task("A", "p1")
        t2 = self.manager.create_task("B", "p2")
        t2.status = TaskStatus.COMPLETED
        assert len(self.manager.list_tasks()) == 2
        assert len(self.manager.list_tasks(TaskStatus.COMPLETED)) == 1

    def test_running_count(self):
        t1 = self.manager.create_task("A", "p1")
        t1.status = TaskStatus.RUNNING
        t2 = self.manager.create_task("B", "p2")
        assert self.manager.get_running_count() == 1

    def test_synthesize_results(self):
        t1 = SubAgentTask(id="a1", description="Research auth", prompt="", status=TaskStatus.COMPLETED, result="Found bug in auth.py")
        t2 = SubAgentTask(id="a2", description="Research tests", prompt="", status=TaskStatus.FAILED, error="Timeout")

        summary = self.manager.synthesize_results([t1, t2])
        assert "Research auth" in summary
        assert "Found bug" in summary
        assert "FAILED" in summary
        assert "Timeout" in summary

    @pytest.mark.asyncio
    async def test_run_task(self):
        """Test running a task with mocked agent."""
        with patch('pydantic_ai.Agent') as MockAgent:
            mock_result = MagicMock()
            mock_result.data = "Found the bug in line 42"
            mock_instance = MockAgent.return_value
            mock_instance.run = AsyncMock(return_value=mock_result)

            task = self.manager.create_task("Find bug", "Look for null pointers")
            result = await self.manager.run_task(task)

            assert result.status == TaskStatus.COMPLETED
            assert "Found the bug" in result.result

    @pytest.mark.asyncio
    async def test_run_task_failure(self):
        """Test task failure handling."""
        with patch('pydantic_ai.Agent') as MockAgent:
            mock_instance = MockAgent.return_value
            mock_instance.run = AsyncMock(side_effect=RuntimeError("API error"))

            task = self.manager.create_task("Fail", "This will fail")
            result = await self.manager.run_task(task)

            assert result.status == TaskStatus.FAILED
            assert "API error" in result.error

    @pytest.mark.asyncio
    async def test_run_parallel(self):
        """Test parallel task execution."""
        with patch('pydantic_ai.Agent') as MockAgent:
            mock_result = MagicMock()
            mock_result.data = "Done"
            mock_instance = MockAgent.return_value
            mock_instance.run = AsyncMock(return_value=mock_result)

            tasks = [
                self.manager.create_task("Task1", "Do thing 1"),
                self.manager.create_task("Task2", "Do thing 2"),
            ]
            results = await self.manager.run_parallel(tasks)

            assert len(results) == 2
            assert all(t.status == TaskStatus.COMPLETED for t in results)
