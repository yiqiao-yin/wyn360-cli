"""Integration tests for Phase 5.4: Testing & Refinement."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.browser_controller import BrowserController, BrowserConfig, BrowserControllerError
from wyn360_cli.vision_engine import VisionDecisionEngine, VisionDecisionError
from wyn360_cli.browser_task_executor import BrowserTaskExecutor


class TestBrowserConfigurationPhase54:
    """Test Phase 5.4 browser configuration improvements."""

    def test_browser_config_timeout_values(self):
        """Test that BrowserConfig has appropriate timeout values."""
        assert BrowserConfig.DEFAULT_TIMEOUT == 30000
        assert BrowserConfig.NAVIGATION_TIMEOUT == 60000
        assert BrowserConfig.ACTION_TIMEOUT == 10000

    def test_browser_config_retry_values(self):
        """Test that BrowserConfig has retry configuration."""
        assert BrowserConfig.MAX_RETRIES == 2
        assert BrowserConfig.RETRY_DELAY == 1.0

    def test_browser_config_performance_values(self):
        """Test that BrowserConfig has performance settings."""
        assert BrowserConfig.WAIT_AFTER_NAVIGATION == 1.0
        assert BrowserConfig.WAIT_AFTER_ACTION == 0.5


class TestRetryLogicPhase54:
    """Test Phase 5.4 retry logic improvements."""

    @pytest.mark.asyncio
    async def test_execute_action_retries_on_failure(self):
        """Test that execute_action retries failed actions."""
        controller = BrowserController()
        controller._initialized = True
        controller.page = AsyncMock()

        # Mock click to fail twice then succeed
        call_count = 0

        async def mock_click(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                from playwright.async_api import TimeoutError as PlaywrightTimeoutError
                raise PlaywrightTimeoutError("Element not found")
            # Third attempt succeeds
            return

        controller.page.click = mock_click

        # Execute action with retry
        result = await controller.execute_action({
            'type': 'click',
            'selector': '#test-btn'
        }, retry=True)

        # Should succeed after retries
        assert result['success'] == True
        assert call_count == 3  # Failed 2 times, succeeded on 3rd

    @pytest.mark.asyncio
    async def test_execute_action_respects_retry_false(self):
        """Test that retry=False prevents retries."""
        controller = BrowserController()
        controller._initialized = True
        controller.page = AsyncMock()

        # Mock click to always fail
        async def mock_click(*args, **kwargs):
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError
            raise PlaywrightTimeoutError("Element not found")

        controller.page.click = mock_click

        # Execute action without retry
        result = await controller.execute_action({
            'type': 'click',
            'selector': '#test-btn'
        }, retry=False)

        # Should fail immediately without retries
        assert result['success'] == False
        assert 'attempts' in result
        assert result['attempts'] == 1

    @pytest.mark.asyncio
    async def test_execute_action_does_not_retry_unknown_action(self):
        """Test that unknown action types are not retried."""
        controller = BrowserController()
        controller._initialized = True

        # Execute unknown action type
        result = await controller.execute_action({
            'type': 'unknown_action'
        }, retry=True)

        # Should fail immediately without retries
        assert result['success'] == False
        assert 'Unknown action type' in result['error']


class TestNavigationTimeoutHandlingPhase54:
    """Test Phase 5.4 navigation timeout improvements."""

    @pytest.mark.asyncio
    async def test_navigate_fallback_on_networkidle_timeout(self):
        """Test navigation falls back to 'load' if 'networkidle' times out."""
        controller = BrowserController()
        controller._initialized = True
        controller.page = AsyncMock()

        # Mock goto to fail on networkidle but succeed on load
        call_count = 0

        async def mock_goto(url, wait_until=None, timeout=None):
            nonlocal call_count
            call_count += 1

            if call_count == 1 and wait_until == 'networkidle':
                from playwright.async_api import TimeoutError as PlaywrightTimeoutError
                raise PlaywrightTimeoutError("Navigation timeout")
            # Second call with 'load' succeeds
            return

        controller.page.goto = mock_goto

        # Navigate with networkidle (should fallback to load)
        await controller.navigate("https://example.com", wait_until='networkidle')

        # Should have called goto twice (networkidle failed, load succeeded)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_navigate_uses_navigation_timeout(self):
        """Test that navigate uses NAVIGATION_TIMEOUT config."""
        controller = BrowserController()
        controller._initialized = True
        controller.page = AsyncMock()

        called_with_timeout = None

        async def mock_goto(url, wait_until=None, timeout=None):
            nonlocal called_with_timeout
            called_with_timeout = timeout

        controller.page.goto = mock_goto

        await controller.navigate("https://example.com")

        # Verify navigation timeout was used
        assert called_with_timeout == BrowserConfig.NAVIGATION_TIMEOUT


class TestVisionPromptImprovementsPhase54:
    """Test Phase 5.4 vision prompt improvements."""

    def test_vision_prompt_includes_common_scenarios(self):
        """Test that vision prompt includes common scenario handling."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        prompt = engine._build_analysis_prompt(
            goal="Test task",
            history=[],
            page_state={'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        )

        # Verify improved prompt includes common scenarios
        assert 'Popups/Modals/Cookie Banners' in prompt
        assert 'Missing elements' in prompt
        assert 'Loading states' in prompt
        assert 'Forms and filters' in prompt
        assert 'Captchas/Authentication' in prompt

    def test_vision_prompt_includes_confidence_guidelines(self):
        """Test that vision prompt includes confidence scoring guidelines."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        prompt = engine._build_analysis_prompt(
            goal="Test task",
            history=[],
            page_state={'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        )

        # Verify confidence guidelines
        assert 'High confidence (80-100)' in prompt
        assert 'Medium confidence (50-79)' in prompt
        assert 'Low confidence (0-49)' in prompt

    def test_vision_prompt_includes_specific_selector_guidance(self):
        """Test that vision prompt encourages specific selectors."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        prompt = engine._build_analysis_prompt(
            goal="Test task",
            history=[],
            page_state={'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        )

        # Verify selector guidance
        assert 'Prefer specific selectors' in prompt
        assert 'CSS selectors' in prompt


class TestVisionIntegrationPhase54:
    """Test Phase 5.4 actual vision API integration."""

    @pytest.mark.asyncio
    async def test_analyze_with_vision_uses_binary_content(self):
        """Test that vision analysis uses BinaryContent for screenshots."""
        mock_agent = AsyncMock()

        # Mock agent.run response
        mock_result = Mock()
        mock_result.data = """
        {
            "status": "continue",
            "action": {"type": "click", "selector": "#btn"},
            "reasoning": "Clicking the button",
            "confidence": 85
        }
        """
        mock_agent.run = AsyncMock(return_value=mock_result)

        engine = VisionDecisionEngine(mock_agent)

        screenshot = b'fake_screenshot_data'
        prompt = "Test prompt"

        # Call vision analysis
        result = await engine._analyze_with_vision(screenshot, prompt)

        # Verify agent.run was called
        mock_agent.run.assert_called_once()

        # Verify call includes BinaryContent
        call_args = mock_agent.run.call_args
        user_prompt = call_args.kwargs['user_prompt']

        # Should be a list with text + BinaryContent
        assert isinstance(user_prompt, list)
        assert len(user_prompt) == 2
        assert user_prompt[0] == prompt

        # Check BinaryContent
        from pydantic_ai import BinaryContent
        assert isinstance(user_prompt[1], BinaryContent)
        assert user_prompt[1].data == screenshot
        assert user_prompt[1].media_type == 'image/png'

    @pytest.mark.asyncio
    async def test_analyze_with_vision_handles_api_error(self):
        """Test that vision analysis handles API errors gracefully."""
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(side_effect=Exception("API error"))

        engine = VisionDecisionEngine(mock_agent)

        screenshot = b'fake_screenshot_data'
        prompt = "Test prompt"

        # Should raise VisionDecisionError
        with pytest.raises(VisionDecisionError) as exc_info:
            await engine._analyze_with_vision(screenshot, prompt)

        assert "Vision analysis failed" in str(exc_info.value)
        assert "API error" in str(exc_info.value)


class TestPerformanceOptimizationsPhase54:
    """Test Phase 5.4 performance optimizations."""

    @pytest.mark.asyncio
    async def test_wait_after_action_is_applied(self):
        """Test that WAIT_AFTER_ACTION is applied after actions."""
        controller = BrowserController()
        controller._initialized = True
        controller.page = AsyncMock()

        # Mock click
        controller.page.click = AsyncMock()

        start_time = asyncio.get_event_loop().time()

        # Execute action
        await controller.execute_action({
            'type': 'click',
            'selector': '#btn'
        })

        end_time = asyncio.get_event_loop().time()

        # Should have waited at least WAIT_AFTER_ACTION
        duration = end_time - start_time
        assert duration >= BrowserConfig.WAIT_AFTER_ACTION

    @pytest.mark.asyncio
    async def test_wait_after_navigation_is_applied(self):
        """Test that WAIT_AFTER_NAVIGATION is applied after navigation."""
        controller = BrowserController()
        controller._initialized = True
        controller.page = AsyncMock()

        # Mock goto
        controller.page.goto = AsyncMock()

        start_time = asyncio.get_event_loop().time()

        # Navigate
        await controller.navigate("https://example.com")

        end_time = asyncio.get_event_loop().time()

        # Should have waited at least WAIT_AFTER_NAVIGATION
        duration = end_time - start_time
        assert duration >= BrowserConfig.WAIT_AFTER_NAVIGATION


class TestErrorResiliencePhase54:
    """Test Phase 5.4 error resilience improvements."""

    @pytest.mark.asyncio
    async def test_executor_continues_after_vision_error_with_retry(self):
        """Test that executor can recover from transient vision errors."""
        mock_agent = AsyncMock()
        executor = BrowserTaskExecutor(mock_agent)

        # Mock browser controller
        executor.controller.initialize = AsyncMock()
        executor.controller.navigate = AsyncMock()
        executor.controller.take_screenshot = AsyncMock(return_value=b'screenshot')
        executor.controller.get_page_state = AsyncMock(return_value={
            'url': 'https://example.com',
            'title': 'Test',
            'loaded': True
        })
        executor.controller.cleanup = AsyncMock()

        # Mock vision to fail once then succeed
        call_count = 0

        async def mock_analyze(screenshot, goal, history, page_state):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                from wyn360_cli.vision_engine import VisionDecisionError
                raise VisionDecisionError("Transient error")
            else:
                return {
                    'status': 'complete',
                    'action': {'type': 'extract'},
                    'reasoning': 'Recovered and completed',
                    'confidence': 90,
                    'extracted_data': {'result': 'success'}
                }

        executor.vision_engine.analyze_and_decide = mock_analyze

        # Execute task
        result = await executor.execute_task(
            task="Test task",
            url="https://example.com",
            max_steps=5
        )

        # Should succeed despite one error
        assert result['status'] == 'success'
        assert result['metrics']['errors_encountered'] >= 1
        assert call_count >= 2  # At least 2 attempts
