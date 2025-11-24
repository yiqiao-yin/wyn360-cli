"""
Unit tests for Vision Fallback Integration

Tests the VisionFallbackIntegration class that wraps the existing vision-based
browser automation system for integration with the unified automation pipeline.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.vision_fallback_integration import (
    VisionFallbackIntegration,
    VisionFallbackConfig
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionRequest,
    ActionResult
)


class TestVisionFallbackConfig:
    """Test VisionFallbackConfig dataclass"""

    def test_config_defaults(self):
        """Test default configuration values"""
        config = VisionFallbackConfig()

        assert config.max_steps == 20
        assert config.headless is False
        assert config.enable_screenshots is True
        assert config.timeout_seconds == 120.0
        assert config.confidence_threshold == 0.5

    def test_config_custom_values(self):
        """Test custom configuration values"""
        config = VisionFallbackConfig(
            max_steps=30,
            headless=True,
            enable_screenshots=False,
            timeout_seconds=180.0,
            confidence_threshold=0.7
        )

        assert config.max_steps == 30
        assert config.headless is True
        assert config.enable_screenshots is False
        assert config.timeout_seconds == 180.0
        assert config.confidence_threshold == 0.7


class TestVisionFallbackIntegration:
    """Test VisionFallbackIntegration class"""

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent with vision capabilities"""
        agent = Mock()
        agent.use_bedrock = False
        agent.browse_and_find = AsyncMock()
        return agent

    @pytest.fixture
    def mock_bedrock_agent(self):
        """Create mock agent in Bedrock mode (no vision)"""
        agent = Mock()
        agent.use_bedrock = True
        return agent

    @pytest.fixture
    def vision_integration(self):
        """Create VisionFallbackIntegration instance"""
        return VisionFallbackIntegration()

    @pytest.fixture
    def sample_action_request(self):
        """Create sample action request"""
        return ActionRequest(
            url="https://example.com",
            task_description="Click the login button and enter credentials",
            action_type="click",
            target_description="login button",
            action_data={"username": "test@example.com", "password": "testpass"}
        )

    def test_initialization_default(self, vision_integration):
        """Test default initialization"""
        assert vision_integration.agent is None
        assert vision_integration.execution_history == []
        assert vision_integration.total_executions == 0
        assert vision_integration.successful_executions == 0

    def test_initialization_with_agent(self, mock_agent):
        """Test initialization with agent"""
        integration = VisionFallbackIntegration(mock_agent)
        assert integration.agent == mock_agent

    def test_is_available_no_agent(self, vision_integration):
        """Test availability check with no agent"""
        assert vision_integration.is_available() is False

    def test_is_available_bedrock_mode(self, vision_integration, mock_bedrock_agent):
        """Test availability check in Bedrock mode"""
        assert vision_integration.is_available(mock_bedrock_agent) is False

    def test_is_available_no_browse_method(self, vision_integration):
        """Test availability check with agent lacking browse_and_find"""
        agent = Mock()
        agent.use_bedrock = False
        # Explicitly remove browse_and_find method
        if hasattr(agent, 'browse_and_find'):
            delattr(agent, 'browse_and_find')
        assert vision_integration.is_available(agent) is False

    def test_is_available_success(self, vision_integration, mock_agent):
        """Test availability check with proper agent"""
        assert vision_integration.is_available(mock_agent) is True

    def test_convert_request_to_vision_task_basic(self, vision_integration, sample_action_request):
        """Test converting basic action request to vision task"""
        task = vision_integration._convert_request_to_vision_task(sample_action_request)

        expected = "Click the login button and enter credentials. click on login button"
        assert task == expected

    def test_convert_request_to_vision_task_with_type_action(self, vision_integration):
        """Test converting type action request to vision task"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Fill in the email field",
            action_type="type",
            target_description="email input",
            action_data={"text": "test@example.com"}
        )

        task = vision_integration._convert_request_to_vision_task(request)
        assert "Fill in the email field" in task
        assert "type on email input" in task
        assert "Type: 'test@example.com'" in task

    def test_convert_request_to_vision_task_with_select_action(self, vision_integration):
        """Test converting select action request to vision task"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Select country from dropdown",
            action_type="select",
            target_description="country dropdown",
            action_data={"value": "United States"}
        )

        task = vision_integration._convert_request_to_vision_task(request)
        assert "Select country from dropdown" in task
        assert "select on country dropdown" in task
        assert "Select: 'United States'" in task

    def test_parse_vision_result_success(self, vision_integration):
        """Test parsing successful vision result"""
        result_text = """✅ **Task Completed Successfully!**

**Task:** Click login button
**Steps Taken:** 3

**Result:**
Login successful

**Summary:**
Successfully clicked login button and entered credentials
"""

        success, confidence, data = vision_integration._parse_vision_result(result_text)

        assert success is True
        assert confidence == 0.8
        assert data['raw_result'] == result_text
        assert data['steps_taken'] == '3'

    def test_parse_vision_result_partial(self, vision_integration):
        """Test parsing partial vision result"""
        result_text = """⚠️ **Task Partially Completed**

**Task:** Complex multi-step task
**Steps Taken:** 20 (reached maximum)

**Note:** Completed login but couldn't find target element
"""

        success, confidence, data = vision_integration._parse_vision_result(result_text)

        assert success is False
        assert confidence == 0.4
        assert data['partial_success'] is True
        assert data['steps_taken'] == '20 (reached maximum)'

    def test_parse_vision_result_failure(self, vision_integration):
        """Test parsing failed vision result"""
        result_text = """❌ **Task Failed**

**Task:** Login to website
**Steps Attempted:** 5

**Issue:** Could not locate login button on page

**Suggestions:**
- Verify the URL is accessible
"""

        success, confidence, data = vision_integration._parse_vision_result(result_text)

        assert success is False
        assert confidence == 0.1
        assert data['steps_taken'] == '5'
        assert data['error'] == 'Could not locate login button on page'

    def test_parse_vision_result_bedrock_error(self, vision_integration):
        """Test parsing Bedrock mode error"""
        result_text = "❌ Autonomous browsing requires vision capabilities."

        success, confidence, data = vision_integration._parse_vision_result(result_text)

        assert success is False
        assert confidence == 0.1
        assert data['bedrock_mode'] is True
        assert data['error'] == "Vision capabilities not available in current mode"

    def test_generate_vision_recommendation_success(self, vision_integration):
        """Test recommendation generation for success"""
        recommendation = vision_integration._generate_vision_recommendation(True, {})
        assert recommendation is None

    def test_generate_vision_recommendation_bedrock(self, vision_integration):
        """Test recommendation generation for Bedrock mode"""
        recommendation = vision_integration._generate_vision_recommendation(
            False, {'bedrock_mode': True}
        )
        assert "Anthropic API mode" in recommendation

    def test_generate_vision_recommendation_partial(self, vision_integration):
        """Test recommendation generation for partial success"""
        recommendation = vision_integration._generate_vision_recommendation(
            False, {'partial_success': True}
        )
        assert "smaller steps" in recommendation

    def test_generate_vision_recommendation_timeout(self, vision_integration):
        """Test recommendation generation for timeout error"""
        recommendation = vision_integration._generate_vision_recommendation(
            False, {'error': 'Task timeout after 120 seconds'}
        )
        assert "too complex" in recommendation

    def test_generate_vision_recommendation_accessibility(self, vision_integration):
        """Test recommendation generation for accessibility error"""
        recommendation = vision_integration._generate_vision_recommendation(
            False, {'error': 'URL not accessible'}
        )
        assert "accessibility" in recommendation

    @pytest.mark.asyncio
    async def test_execute_vision_fallback_unavailable(self, vision_integration, sample_action_request):
        """Test execution when vision is unavailable"""
        # No agent set
        result = await vision_integration.execute_vision_fallback(sample_action_request)

        assert result.success is False
        assert result.approach_used == AutomationApproach.VISION_FALLBACK
        assert result.confidence == 0.0
        assert "not available" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_vision_fallback_bedrock(self, vision_integration, sample_action_request, mock_bedrock_agent):
        """Test execution in Bedrock mode"""
        result = await vision_integration.execute_vision_fallback(
            sample_action_request, agent=mock_bedrock_agent
        )

        assert result.success is False
        assert result.approach_used == AutomationApproach.VISION_FALLBACK
        assert "Bedrock mode" in result.error_message
        assert "Anthropic API mode" in result.recommendation

    @pytest.mark.asyncio
    async def test_execute_vision_fallback_success(self, vision_integration, sample_action_request, mock_agent):
        """Test successful vision execution"""
        # Mock successful browse_and_find result
        mock_agent.browse_and_find.return_value = """✅ **Task Completed Successfully!**

**Task:** Click the login button and enter credentials
**Steps Taken:** 4

**Result:**
Successfully logged into account

**Summary:**
Located login button, entered credentials, and confirmed login success
"""

        result = await vision_integration.execute_vision_fallback(
            sample_action_request, agent=mock_agent
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.VISION_FALLBACK
        assert result.confidence == 0.8
        assert result.error_message is None
        assert result.recommendation is None

        # Verify browse_and_find was called correctly
        mock_agent.browse_and_find.assert_called_once()
        call_args = mock_agent.browse_and_find.call_args
        assert call_args.kwargs['task'] == "Click the login button and enter credentials. click on login button"
        assert call_args.kwargs['url'] == sample_action_request.url
        assert call_args.kwargs['max_steps'] == 20  # Default
        assert call_args.kwargs['headless'] is False  # Default

    @pytest.mark.asyncio
    async def test_execute_vision_fallback_with_config(self, vision_integration, sample_action_request, mock_agent):
        """Test vision execution with custom config"""
        mock_agent.browse_and_find.return_value = "✅ Task completed"

        config = VisionFallbackConfig(
            max_steps=15,
            headless=True,
            timeout_seconds=60.0
        )

        await vision_integration.execute_vision_fallback(
            sample_action_request, config=config, agent=mock_agent
        )

        # Verify config was applied
        call_args = mock_agent.browse_and_find.call_args
        assert call_args.kwargs['max_steps'] == 15
        assert call_args.kwargs['headless'] is True

    @pytest.mark.asyncio
    async def test_execute_vision_fallback_failure(self, vision_integration, sample_action_request, mock_agent):
        """Test failed vision execution"""
        mock_agent.browse_and_find.return_value = """❌ **Task Failed**

**Task:** Click the login button
**Steps Attempted:** 8

**Issue:** Could not locate login button after multiple attempts
"""

        result = await vision_integration.execute_vision_fallback(
            sample_action_request, agent=mock_agent
        )

        assert result.success is False
        assert result.approach_used == AutomationApproach.VISION_FALLBACK
        assert result.confidence == 0.1
        assert "Could not locate login button" in result.result_data['error']

    @pytest.mark.asyncio
    async def test_execute_vision_fallback_exception(self, vision_integration, sample_action_request, mock_agent):
        """Test vision execution with exception"""
        mock_agent.browse_and_find.side_effect = Exception("Browser initialization failed")

        result = await vision_integration.execute_vision_fallback(
            sample_action_request, agent=mock_agent
        )

        assert result.success is False
        assert result.approach_used == AutomationApproach.VISION_FALLBACK
        assert "Browser initialization failed" in result.error_message

    def test_record_execution(self, vision_integration, sample_action_request):
        """Test execution recording for analytics"""
        # Create a test result
        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.VISION_FALLBACK,
            confidence=0.8,
            execution_time=15.5,
            result_data={'steps_taken': '5'}
        )

        initial_count = vision_integration.total_executions
        initial_success_count = vision_integration.successful_executions

        vision_integration._record_execution(sample_action_request, result, "Test vision task")

        assert vision_integration.total_executions == initial_count + 1
        assert vision_integration.successful_executions == initial_success_count + 1
        assert len(vision_integration.execution_history) == 1

        record = vision_integration.execution_history[0]
        assert record['success'] is True
        assert record['confidence'] == 0.8
        assert record['execution_time'] == 15.5
        assert record['vision_task'] == "Test vision task"

    def test_get_execution_analytics_empty(self, vision_integration, mock_agent):
        """Test analytics when no executions recorded"""
        vision_integration.agent = mock_agent
        analytics = vision_integration.get_execution_analytics()

        assert analytics['total_executions'] == 0
        assert analytics['success_rate'] == 0.0
        assert analytics['availability'] is True

    def test_get_execution_analytics_with_data(self, vision_integration, mock_agent):
        """Test analytics with execution data"""
        vision_integration.agent = mock_agent

        # Add test execution records
        vision_integration.execution_history = [
            {
                'success': True,
                'execution_time': 10.0,
                'action_type': 'click'
            },
            {
                'success': False,
                'execution_time': 20.0,
                'action_type': 'click'
            },
            {
                'success': True,
                'execution_time': 15.0,
                'action_type': 'type'
            }
        ]
        vision_integration.total_executions = 3
        vision_integration.successful_executions = 2

        analytics = vision_integration.get_execution_analytics()

        assert analytics['total_executions'] == 3
        assert analytics['successful_executions'] == 2
        assert analytics['success_rate'] == 2/3
        assert analytics['average_execution_time'] == 15.0  # (10 + 20 + 15) / 3

        # Check action type breakdown
        assert 'click' in analytics['action_types']
        assert 'type' in analytics['action_types']
        assert analytics['action_types']['click']['total'] == 2
        assert analytics['action_types']['click']['successful'] == 1
        assert analytics['action_types']['click']['success_rate'] == 0.5
        assert analytics['action_types']['type']['total'] == 1
        assert analytics['action_types']['type']['successful'] == 1
        assert analytics['action_types']['type']['success_rate'] == 1.0

    def test_clear_execution_history(self, vision_integration):
        """Test clearing execution history"""
        # Add test data
        vision_integration.execution_history = [{'test': 'data1'}, {'test': 'data2'}]
        vision_integration.total_executions = 5
        vision_integration.successful_executions = 3

        count = vision_integration.clear_execution_history()

        assert count == 2
        assert len(vision_integration.execution_history) == 0
        assert vision_integration.total_executions == 0
        assert vision_integration.successful_executions == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])