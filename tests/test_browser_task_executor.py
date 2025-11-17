"""Tests for BrowserTaskExecutor class."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from wyn360_cli.browser_task_executor import BrowserTaskExecutor, BrowserTaskExecutorError


class TestBrowserTaskExecutorInitialization:
    """Test BrowserTaskExecutor initialization."""

    def test_initialize_with_agent(self):
        """Test initialization with agent."""
        mock_agent = Mock()
        executor = BrowserTaskExecutor(mock_agent)

        assert executor.agent == mock_agent
        assert executor.controller is not None
        assert executor.vision_engine is not None


class TestExecuteTaskSuccess:
    """Test successful task execution."""

    @pytest.mark.asyncio
    async def test_execute_task_completes_immediately(self):
        """Test task that completes on first step."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine to return complete on first step
        executor.vision_engine.analyze_and_decide = AsyncMock(return_value={
            'status': 'complete',
            'action': {'type': 'extract', 'selector': '.price'},
            'reasoning': 'Found the price',
            'confidence': 95,
            'extracted_data': {'price': '$99.99'}
        })

        # Execute task
        result = await executor.execute_task(
            task="Find the price",
            url="https://example.com",
            max_steps=10
        )

        # Verify
        assert result['status'] == 'success'
        assert result['steps_taken'] == 1
        assert result['result'] == {'price': '$99.99'}
        assert 'Found the price' in result['reasoning']
        assert 'metrics' in result

        # Verify cleanup was called
        executor.controller.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_completes_after_multiple_steps(self):
        """Test task that completes after several steps."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.execute_action = AsyncMock(return_value={'success': True})
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine to continue for 3 steps then complete
        call_count = 0

        async def mock_analyze(screenshot, goal, history, page_state):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                return {
                    'status': 'continue',
                    'action': {'type': 'click', 'selector': f'#step{call_count}'},
                    'reasoning': f'Step {call_count}',
                    'confidence': 80
                }
            else:
                return {
                    'status': 'complete',
                    'action': {'type': 'extract', 'selector': '.result'},
                    'reasoning': 'Task complete',
                    'confidence': 90,
                    'extracted_data': {'result': 'success'}
                }

        executor.vision_engine.analyze_and_decide = mock_analyze

        # Execute task
        result = await executor.execute_task(
            task="Multi-step task",
            url="https://example.com",
            max_steps=10
        )

        # Verify
        assert result['status'] == 'success'
        assert result['steps_taken'] == 3
        assert result['result'] == {'result': 'success'}
        # History only contains actions that were executed (2 clicks before completion)
        assert len(result['history']) == 2


class TestExecuteTaskPartial:
    """Test partial task execution (max steps reached)."""

    @pytest.mark.asyncio
    async def test_execute_task_reaches_max_steps(self):
        """Test task that reaches max steps without completing."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.execute_action = AsyncMock(return_value={'success': True})
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine to always continue
        executor.vision_engine.analyze_and_decide = AsyncMock(return_value={
            'status': 'continue',
            'action': {'type': 'wait', 'seconds': 1},
            'reasoning': 'Still working...',
            'confidence': 50
        })

        # Execute task with low max_steps
        result = await executor.execute_task(
            task="Never completes",
            url="https://example.com",
            max_steps=3
        )

        # Verify
        assert result['status'] == 'partial'
        assert result['steps_taken'] == 3
        assert result['result'] is None
        assert 'maximum steps' in result['reasoning'].lower()
        assert len(result['history']) == 3


class TestExecuteTaskStuck:
    """Test stuck detection."""

    @pytest.mark.asyncio
    async def test_execute_task_detects_stuck_status(self):
        """Test detection when vision engine reports stuck."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.execute_action = AsyncMock(return_value={'success': True})
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine to report stuck 3 times
        executor.vision_engine.analyze_and_decide = AsyncMock(return_value={
            'status': 'stuck',
            'action': {'type': 'wait', 'seconds': 1},
            'reasoning': 'Cannot find element',
            'confidence': 0
        })

        # Execute task
        result = await executor.execute_task(
            task="Gets stuck",
            url="https://example.com",
            max_steps=10
        )

        # Verify
        assert result['status'] == 'failed'
        assert result['steps_taken'] <= 3  # Should stop after 3 stuck attempts
        assert 'stuck' in result['reasoning'].lower()

    @pytest.mark.asyncio
    async def test_execute_task_detects_repeated_action(self):
        """Test detection when same action is repeated."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.execute_action = AsyncMock(return_value={'success': True})
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine to return same action repeatedly
        same_action = {'type': 'click', 'selector': '#same-button'}
        executor.vision_engine.analyze_and_decide = AsyncMock(return_value={
            'status': 'continue',
            'action': same_action,
            'reasoning': 'Clicking same button',
            'confidence': 50
        })

        # Execute task
        result = await executor.execute_task(
            task="Repeats action",
            url="https://example.com",
            max_steps=10
        )

        # Verify
        assert result['status'] == 'failed'
        assert 'stuck' in result['reasoning'].lower()


class TestErrorHandling:
    """Test error handling during execution."""

    @pytest.mark.asyncio
    async def test_execute_task_handles_vision_error(self):
        """Test handling of vision engine errors."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine to raise error on first call, then complete
        call_count = 0

        async def mock_analyze_with_error(screenshot, goal, history, page_state):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                from wyn360_cli.vision_engine import VisionDecisionError
                raise VisionDecisionError("API error")
            else:
                return {
                    'status': 'complete',
                    'action': {'type': 'extract'},
                    'reasoning': 'Recovered',
                    'confidence': 90,
                    'extracted_data': {'result': 'ok'}
                }

        executor.vision_engine.analyze_and_decide = mock_analyze_with_error

        # Execute task
        result = await executor.execute_task(
            task="Handles error",
            url="https://example.com",
            max_steps=5
        )

        # Verify task completed despite error
        assert result['status'] == 'success'
        assert result['metrics']['errors_encountered'] >= 1

    @pytest.mark.asyncio
    async def test_execute_task_handles_browser_error(self):
        """Test handling of browser controller errors."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.cleanup = AsyncMock()

        # Mock execute_action to fail once then succeed
        call_count = 0

        async def mock_execute_with_error(action):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                from wyn360_cli.browser_controller import BrowserControllerError
                raise BrowserControllerError("Click failed")
            else:
                return {'success': True}

        executor.controller.execute_action = mock_execute_with_error

        # Mock vision engine
        executor.vision_engine.analyze_and_decide = AsyncMock(side_effect=[
            {
                'status': 'continue',
                'action': {'type': 'click', 'selector': '#btn'},
                'reasoning': 'Click button',
                'confidence': 80
            },
            {
                'status': 'complete',
                'action': {'type': 'extract'},
                'reasoning': 'Done',
                'confidence': 90,
                'extracted_data': {'result': 'success'}
            }
        ])

        # Execute task
        result = await executor.execute_task(
            task="Handles browser error",
            url="https://example.com",
            max_steps=5
        )

        # Verify
        assert result['status'] == 'success'
        assert result['metrics']['errors_encountered'] >= 1


class TestContextManager:
    """Test async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that context manager cleans up browser."""
        mock_agent = AsyncMock()

        executor = BrowserTaskExecutor(mock_agent)
        executor.controller.cleanup = AsyncMock()

        async with executor as exec_ctx:
            assert exec_ctx == executor

        # Verify cleanup was called
        executor.controller.cleanup.assert_called_once()


class TestSummaryGeneration:
    """Test summary generation."""

    def test_get_summary_success(self):
        """Test summary for successful task."""
        mock_agent = Mock()
        executor = BrowserTaskExecutor(mock_agent)

        result = {
            'status': 'success',
            'result': {'price': '$99.99'},
            'steps_taken': 5,
            'reasoning': 'Found the price successfully',
            'metrics': {
                'total_duration': 12.5,
                'screenshots_taken': 5,
                'actions_executed': 4,
                'errors_encountered': 0
            }
        }

        summary = executor.get_summary(result)

        assert '✅' in summary
        assert 'SUCCESS' in summary
        assert '5' in summary  # steps
        assert '12.5s' in summary  # duration
        assert 'price' in summary or '$99.99' in summary

    def test_get_summary_partial(self):
        """Test summary for partial completion."""
        mock_agent = Mock()
        executor = BrowserTaskExecutor(mock_agent)

        result = {
            'status': 'partial',
            'result': None,
            'steps_taken': 20,
            'reasoning': 'Reached maximum steps',
            'metrics': {
                'total_duration': 45.2,
                'screenshots_taken': 20,
                'actions_executed': 19,
                'errors_encountered': 2
            }
        }

        summary = executor.get_summary(result)

        assert '⚠️' in summary
        assert 'PARTIAL' in summary
        assert '20' in summary

    def test_get_summary_failed(self):
        """Test summary for failed task."""
        mock_agent = Mock()
        executor = BrowserTaskExecutor(mock_agent)

        result = {
            'status': 'failed',
            'result': None,
            'steps_taken': 3,
            'reasoning': 'Agent appears stuck',
            'metrics': {
                'total_duration': 8.1,
                'screenshots_taken': 3,
                'actions_executed': 2,
                'errors_encountered': 1
            }
        }

        summary = executor.get_summary(result)

        assert '❌' in summary
        assert 'FAILED' in summary
        assert 'stuck' in summary.lower()


class TestMetricsTracking:
    """Test metrics tracking."""

    @pytest.mark.asyncio
    async def test_metrics_are_tracked(self):
        """Test that execution metrics are properly tracked."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Example',
            'loaded': True
        })
        executor.controller.execute_action = AsyncMock(return_value={'success': True})
        executor.controller.cleanup = AsyncMock()

        # Mock vision engine for 3 steps
        call_count = 0

        async def mock_analyze(screenshot, goal, history, page_state):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                return {
                    'status': 'continue',
                    'action': {'type': 'click', 'selector': '#btn'},
                    'reasoning': 'Continuing',
                    'confidence': 80
                }
            else:
                return {
                    'status': 'complete',
                    'action': {'type': 'extract'},
                    'reasoning': 'Done',
                    'confidence': 90,
                    'extracted_data': {}
                }

        executor.vision_engine.analyze_and_decide = mock_analyze

        # Execute task
        result = await executor.execute_task(
            task="Test metrics",
            url="https://example.com",
            max_steps=10
        )

        # Verify metrics
        assert 'metrics' in result
        metrics = result['metrics']

        assert metrics['screenshots_taken'] == 3
        assert metrics['actions_executed'] == 2  # 2 clicks before extract
        assert metrics['vision_api_calls'] == 3
        assert metrics['errors_encountered'] == 0
        assert 'total_duration' in metrics
        assert metrics['total_duration'] > 0
