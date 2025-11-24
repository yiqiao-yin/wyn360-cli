"""
Unit tests for Stagehand code generation system

Tests the StagehandCodeGenerator class functionality including pattern caching,
action generation, and integration with the DOM automation system.
"""

import pytest
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.stagehand_generator import (
    StagehandCodeGenerator,
    StagehandAvailability,
    StagehandPattern,
    StagehandExecutionResult
)


class TestStagehandPattern:
    """Test StagehandPattern dataclass functionality"""

    def test_pattern_initialization(self):
        """Test StagehandPattern initialization with default values"""
        pattern = StagehandPattern(
            pattern_id="test_pattern",
            description="Test pattern",
            stagehand_actions=[{"type": "act", "description": "test"}]
        )

        assert pattern.pattern_id == "test_pattern"
        assert pattern.description == "Test pattern"
        assert len(pattern.stagehand_actions) == 1
        assert pattern.success_count == 0
        assert pattern.failure_count == 0
        assert pattern.confidence_score == 0.0
        assert pattern.last_used is None
        assert pattern.created_at > 0  # Should have a timestamp

    def test_success_rate_calculation(self):
        """Test success rate calculation for patterns"""
        pattern = StagehandPattern(
            pattern_id="test",
            description="Test",
            stagehand_actions=[],
            success_count=7,
            failure_count=3
        )

        assert pattern.success_rate == 0.7  # 7/(7+3) = 0.7

    def test_success_rate_no_attempts(self):
        """Test success rate when no attempts have been made"""
        pattern = StagehandPattern(
            pattern_id="test",
            description="Test",
            stagehand_actions=[]
        )

        assert pattern.success_rate == 0.0


class TestStagehandExecutionResult:
    """Test StagehandExecutionResult dataclass functionality"""

    def test_execution_result_initialization(self):
        """Test execution result initialization"""
        result = StagehandExecutionResult(
            success=True,
            pattern_used=None,
            actions_performed=[{"type": "act"}],
            execution_time=1.5,
            result_data={"status": "complete"}
        )

        assert result.success is True
        assert result.pattern_used is None
        assert len(result.actions_performed) == 1
        assert result.execution_time == 1.5
        assert result.result_data["status"] == "complete"
        assert result.error_message is None
        assert result.token_usage is None


class TestStagehandCodeGenerator:
    """Test StagehandCodeGenerator class functionality"""

    @pytest.fixture
    def mock_stagehand_available(self):
        """Mock Stagehand as available"""
        with patch.dict(os.environ, {
            'STAGEHAND_API_URL': 'http://test.url',
            'BROWSERBASE_API_KEY': 'test_key'
        }):
            with patch('src.wyn360.tools.browser.stagehand_generator.HAS_STAGEHAND', True):
                yield

    @pytest.fixture
    def mock_stagehand_unavailable(self):
        """Mock Stagehand as unavailable"""
        with patch('src.wyn360.tools.browser.stagehand_generator.HAS_STAGEHAND', False):
            yield

    @pytest.fixture
    def mock_stagehand_not_configured(self):
        """Mock Stagehand package available but not configured"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.wyn360.tools.browser.stagehand_generator.HAS_STAGEHAND', True):
                yield

    def test_availability_check_not_installed(self, mock_stagehand_unavailable):
        """Test availability check when Stagehand package not installed"""
        generator = StagehandCodeGenerator()
        assert generator.availability_status == StagehandAvailability.NOT_INSTALLED
        assert not generator.is_available()

    def test_availability_check_not_configured(self, mock_stagehand_not_configured):
        """Test availability check when Stagehand not configured"""
        generator = StagehandCodeGenerator()
        assert generator.availability_status == StagehandAvailability.NOT_CONFIGURED
        assert not generator.is_available()

    def test_availability_check_available(self, mock_stagehand_available):
        """Test availability check when Stagehand is available"""
        generator = StagehandCodeGenerator()
        assert generator.availability_status == StagehandAvailability.AVAILABLE
        assert generator.is_available()

    def test_initialization_with_stagehand_available(self, mock_stagehand_available):
        """Test initialization when Stagehand is available"""
        with patch.object(StagehandCodeGenerator, '_initialize_stagehand') as mock_init:
            generator = StagehandCodeGenerator()
            mock_init.assert_called_once()
            assert generator.availability_status == StagehandAvailability.AVAILABLE

    def test_initialization_without_stagehand(self, mock_stagehand_unavailable):
        """Test initialization when Stagehand is not available"""
        with patch.object(StagehandCodeGenerator, '_initialize_stagehand') as mock_init:
            generator = StagehandCodeGenerator()
            # _initialize_stagehand should not be called when Stagehand is unavailable
            mock_init.assert_not_called()
            assert generator.availability_status == StagehandAvailability.NOT_INSTALLED

    def test_get_status_info(self, mock_stagehand_available):
        """Test getting detailed status information"""
        generator = StagehandCodeGenerator()
        status = generator.get_status_info()

        assert status["status"] == "available"
        assert status["is_configured"] is True
        assert status["has_package"] is True
        assert status["pattern_cache_size"] == 0
        assert "required_env_vars" in status
        assert status["required_env_vars"]["STAGEHAND_API_URL"] is True
        assert status["required_env_vars"]["BROWSERBASE_API_KEY"] is True

    @pytest.mark.asyncio
    async def test_generate_stagehand_code_unavailable(self, mock_stagehand_unavailable):
        """Test code generation when Stagehand is unavailable"""
        generator = StagehandCodeGenerator()
        success, result = await generator.generate_stagehand_code(
            url="https://example.com",
            task_description="Test task",
            dom_context="<div>Test</div>",
            target_description="button",
            action_type="click"
        )

        assert success is False
        assert "not available" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_stagehand_code_click_action(self, mock_stagehand_available):
        """Test generating Stagehand code for click action"""
        generator = StagehandCodeGenerator()
        success, actions = await generator.generate_stagehand_code(
            url="https://example.com",
            task_description="Click the submit button",
            dom_context="<button>Submit</button>",
            target_description="submit button",
            action_type="click"
        )

        assert success is True
        assert isinstance(actions, list)
        assert len(actions) == 3  # observe, act, observe

        # Check action sequence
        assert actions[0]["type"] == "observe"
        assert actions[1]["type"] == "act"
        assert "click" in actions[1]["options"]["action"]
        assert actions[2]["type"] == "observe"

    @pytest.mark.asyncio
    async def test_generate_stagehand_code_type_action(self, mock_stagehand_available):
        """Test generating Stagehand code for type action"""
        generator = StagehandCodeGenerator()
        success, actions = await generator.generate_stagehand_code(
            url="https://example.com",
            task_description="Fill in the email field",
            dom_context="<input type='email' />",
            target_description="email field",
            action_type="type",
            action_data={"text": "test@example.com"}
        )

        assert success is True
        assert isinstance(actions, list)
        assert len(actions) == 3

        # Check type action
        act_action = actions[1]
        assert act_action["type"] == "act"
        assert "test@example.com" in act_action["options"]["action"]

    @pytest.mark.asyncio
    async def test_generate_stagehand_code_extract_action(self, mock_stagehand_available):
        """Test generating Stagehand code for extract action"""
        generator = StagehandCodeGenerator()
        success, actions = await generator.generate_stagehand_code(
            url="https://example.com",
            task_description="Extract product information",
            dom_context="<div class='product'></div>",
            target_description="product details",
            action_type="extract",
            action_data={"schema": {"name": "string", "price": "number"}}
        )

        assert success is True
        assert isinstance(actions, list)
        assert len(actions) == 3

        # Check extract action
        extract_action = actions[1]
        assert extract_action["type"] == "extract"
        assert "schema" in extract_action["options"]

    @pytest.mark.asyncio
    async def test_pattern_caching(self, mock_stagehand_available):
        """Test that patterns are cached and reused"""
        generator = StagehandCodeGenerator()

        # Generate first time
        success1, actions1 = await generator.generate_stagehand_code(
            url="https://example.com",
            task_description="Click button",
            dom_context="<button>Test</button>",
            target_description="test button",
            action_type="click"
        )

        assert success1 is True
        assert len(generator.pattern_cache) == 1

        # Generate same pattern again
        success2, actions2 = await generator.generate_stagehand_code(
            url="https://example.com",
            task_description="Click button",
            dom_context="<button>Test</button>",
            target_description="test button",
            action_type="click"
        )

        assert success2 is True
        assert actions1 == actions2  # Should be same cached pattern
        assert len(generator.pattern_cache) == 1  # No new pattern created

    def test_generate_pattern_key(self, mock_stagehand_available):
        """Test pattern key generation"""
        generator = StagehandCodeGenerator()

        key1 = generator._generate_pattern_key("Task 1", "click", "button")
        key2 = generator._generate_pattern_key("task 1", "CLICK", "BUTTON")  # Case insensitive
        key3 = generator._generate_pattern_key("Task 2", "click", "button")  # Different task

        assert key1 == key2  # Should be case insensitive
        assert key1 != key3  # Different tasks should have different keys
        assert len(key1) == 16  # MD5 hash truncated to 16 chars

    def test_update_pattern_success(self, mock_stagehand_available):
        """Test updating pattern success statistics"""
        generator = StagehandCodeGenerator()

        # Create a pattern manually
        pattern = StagehandPattern(
            pattern_id="test_pattern",
            description="Test",
            stagehand_actions=[]
        )
        generator.pattern_cache["test_pattern"] = pattern

        # Update with successes and failures
        generator.update_pattern_success("test_pattern", True)
        generator.update_pattern_success("test_pattern", True)
        generator.update_pattern_success("test_pattern", False)

        pattern = generator.pattern_cache["test_pattern"]
        assert pattern.success_count == 2
        assert pattern.failure_count == 1
        assert pattern.success_rate == 2/3
        assert pattern.confidence_score == 2/3

    def test_update_pattern_success_nonexistent(self, mock_stagehand_available):
        """Test updating success for nonexistent pattern"""
        generator = StagehandCodeGenerator()

        # Should not raise error for nonexistent pattern
        generator.update_pattern_success("nonexistent", True)
        assert len(generator.pattern_cache) == 0

    def test_get_pattern_statistics_empty(self, mock_stagehand_available):
        """Test getting pattern statistics when cache is empty"""
        generator = StagehandCodeGenerator()
        stats = generator.get_pattern_statistics()

        assert stats["total_patterns"] == 0
        assert stats["patterns"] == []

    def test_get_pattern_statistics_with_patterns(self, mock_stagehand_available):
        """Test getting pattern statistics with cached patterns"""
        generator = StagehandCodeGenerator()

        # Add some test patterns
        pattern1 = StagehandPattern(
            pattern_id="pattern1",
            description="Pattern 1",
            stagehand_actions=[],
            success_count=8,
            failure_count=2
        )
        pattern1.confidence_score = pattern1.success_rate

        pattern2 = StagehandPattern(
            pattern_id="pattern2",
            description="Pattern 2",
            stagehand_actions=[],
            success_count=3,
            failure_count=7
        )
        pattern2.confidence_score = pattern2.success_rate

        generator.pattern_cache["pattern1"] = pattern1
        generator.pattern_cache["pattern2"] = pattern2

        stats = generator.get_pattern_statistics()

        assert stats["total_patterns"] == 2
        assert len(stats["patterns"]) == 2

        # Should be sorted by success rate (highest first)
        assert stats["patterns"][0]["pattern_id"] == "pattern1"  # 0.8 success rate
        assert stats["patterns"][1]["pattern_id"] == "pattern2"  # 0.3 success rate

    def test_clear_pattern_cache(self, mock_stagehand_available):
        """Test clearing the pattern cache"""
        generator = StagehandCodeGenerator()

        # Add some patterns
        pattern = StagehandPattern("test", "Test", [])
        generator.pattern_cache["test1"] = pattern
        generator.pattern_cache["test2"] = pattern

        assert len(generator.pattern_cache) == 2

        count = generator.clear_pattern_cache()

        assert count == 2
        assert len(generator.pattern_cache) == 0

    @pytest.mark.asyncio
    async def test_execute_stagehand_actions_unavailable(self, mock_stagehand_unavailable):
        """Test executing actions when Stagehand is unavailable"""
        generator = StagehandCodeGenerator()
        result = await generator.execute_stagehand_actions(
            url="https://example.com",
            actions=[{"type": "act"}]
        )

        assert result.success is False
        assert "not available" in result.error_message.lower()
        assert result.execution_time == 0.0
        assert len(result.actions_performed) == 0

    @pytest.mark.asyncio
    async def test_execute_stagehand_actions_simulation(self, mock_stagehand_available):
        """Test executing actions in simulation mode"""
        generator = StagehandCodeGenerator()
        actions = [
            {"type": "observe", "description": "Find button"},
            {"type": "act", "description": "Click button"}
        ]

        result = await generator.execute_stagehand_actions(
            url="https://example.com",
            actions=actions,
            show_browser=False
        )

        assert result.success is True
        assert result.pattern_used is None
        assert result.actions_performed == actions
        assert result.execution_time > 0
        assert result.result_data["status"] == "completed"
        assert result.result_data["simulated"] is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_execute_stagehand_actions_with_exception(self, mock_stagehand_available):
        """Test executing actions when an exception occurs"""
        generator = StagehandCodeGenerator()

        # Mock asyncio.sleep to raise an exception
        with patch('asyncio.sleep', side_effect=Exception("Test error")):
            result = await generator.execute_stagehand_actions(
                url="https://example.com",
                actions=[{"type": "act"}]
            )

            assert result.success is False
            assert "Test error" in result.error_message
            assert result.execution_time > 0
            assert len(result.actions_performed) == 0

    @pytest.mark.asyncio
    async def test_close_cleanup(self, mock_stagehand_available):
        """Test cleanup when closing Stagehand resources"""
        generator = StagehandCodeGenerator()

        # Mock some resources
        generator.current_page = Mock()
        generator.stagehand_instance = Mock()

        await generator.close()

        assert generator.current_page is None
        assert generator.stagehand_instance is None

    @pytest.mark.asyncio
    async def test_close_with_exception(self, mock_stagehand_available):
        """Test cleanup when an exception occurs during close"""
        generator = StagehandCodeGenerator()

        # Mock resources that will cause an exception
        mock_page = Mock()
        mock_page.close.side_effect = Exception("Close error")
        generator.current_page = mock_page

        # Should not raise exception
        await generator.close()

        # Resources should still be cleaned up
        assert generator.current_page is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])