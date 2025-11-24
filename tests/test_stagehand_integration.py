"""
Unit tests for Stagehand Integration Pipeline

Tests the StagehandIntegration class and dynamic execution pipeline functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.stagehand_integration import (
    StagehandIntegration,
    StagehandExecutionPipeline
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationOrchestrator,
    AutomationApproach,
    ActionRequest,
    ActionResult
)
from src.wyn360.tools.browser.stagehand_generator import (
    StagehandExecutionResult,
    StagehandPattern
)


class TestStagehandExecutionPipeline:
    """Test StagehandExecutionPipeline configuration"""

    def test_pipeline_default_config(self):
        """Test default pipeline configuration"""
        pipeline = StagehandExecutionPipeline()

        assert pipeline.max_retries == 2
        assert pipeline.timeout_seconds == 30.0
        assert pipeline.enable_pattern_learning is True
        assert pipeline.confidence_threshold == 0.6
        assert pipeline.show_browser is False

    def test_pipeline_custom_config(self):
        """Test custom pipeline configuration"""
        pipeline = StagehandExecutionPipeline(
            max_retries=5,
            timeout_seconds=60.0,
            enable_pattern_learning=False,
            confidence_threshold=0.8,
            show_browser=True
        )

        assert pipeline.max_retries == 5
        assert pipeline.timeout_seconds == 60.0
        assert pipeline.enable_pattern_learning is False
        assert pipeline.confidence_threshold == 0.8
        assert pipeline.show_browser is True


class TestStagehandIntegration:
    """Test StagehandIntegration class functionality"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator"""
        return Mock(spec=AutomationOrchestrator)

    @pytest.fixture
    def mock_stagehand_generator(self):
        """Create mock stagehand generator"""
        generator = Mock()
        generator.is_available.return_value = True
        generator.generate_stagehand_code = AsyncMock()
        generator.execute_stagehand_actions = AsyncMock()
        generator.update_pattern_success = Mock()
        generator.get_pattern_statistics.return_value = {"total_patterns": 0}
        return generator

    @pytest.fixture
    def integration(self, mock_orchestrator):
        """Create StagehandIntegration instance"""
        with patch('src.wyn360.tools.browser.stagehand_integration.stagehand_generator') as mock_gen:
            mock_gen.is_available.return_value = True
            integration = StagehandIntegration(mock_orchestrator)
            integration.stagehand_generator = Mock()
            integration.stagehand_generator.is_available.return_value = True
            return integration

    @pytest.fixture
    def sample_action_request(self):
        """Create sample action request"""
        return ActionRequest(
            url="https://example.com",
            task_description="Click the login button",
            action_type="click",
            target_description="login button",
            confidence_threshold=0.7
        )

    @pytest.fixture
    def sample_dom_analysis(self):
        """Create sample DOM analysis result"""
        return {
            'success': True,
            'confidence': 0.85,
            'interactive_elements_count': 8,
            'forms_count': 1,
            'dom_analysis_text': '<button id="login">Login</button>'
        }

    def test_integration_initialization_default_orchestrator(self):
        """Test integration initialization with default orchestrator"""
        with patch('src.wyn360.tools.browser.stagehand_integration.stagehand_generator'):
            integration = StagehandIntegration()
            assert integration.orchestrator is not None
            assert isinstance(integration.orchestrator, AutomationOrchestrator)
            assert integration.execution_history == []

    def test_integration_initialization_custom_orchestrator(self, mock_orchestrator):
        """Test integration initialization with custom orchestrator"""
        with patch('src.wyn360.tools.browser.stagehand_integration.stagehand_generator'):
            integration = StagehandIntegration(mock_orchestrator)
            assert integration.orchestrator == mock_orchestrator

    @pytest.mark.asyncio
    async def test_execute_stagehand_unavailable(self, integration, sample_action_request, sample_dom_analysis):
        """Test execution when Stagehand is unavailable"""
        integration.stagehand_generator.is_available.return_value = False

        result = await integration.execute_stagehand_automation(
            sample_action_request, sample_dom_analysis
        )

        assert result.success is False
        assert result.approach_used == AutomationApproach.STAGEHAND
        assert result.confidence == 0.0
        assert "not available" in result.error_message.lower()
        assert result.recommendation == "Use DOM analysis or vision fallback"

    @pytest.mark.asyncio
    async def test_execute_code_generation_failure(self, integration, sample_action_request, sample_dom_analysis):
        """Test execution when code generation fails"""
        integration.stagehand_generator.generate_stagehand_code = AsyncMock(
            return_value=(False, "Generation failed")
        )

        result = await integration.execute_stagehand_automation(
            sample_action_request, sample_dom_analysis
        )

        assert result.success is False
        assert result.approach_used == AutomationApproach.STAGEHAND
        assert "Code generation failed" in result.error_message
        assert result.recommendation == "Try DOM analysis approach"

    @pytest.mark.asyncio
    async def test_execute_successful_automation(self, integration, sample_action_request, sample_dom_analysis):
        """Test successful automation execution"""
        # Mock successful code generation
        test_actions = [
            {"type": "observe", "description": "Find login button"},
            {"type": "act", "description": "Click login button"}
        ]
        integration.stagehand_generator.generate_stagehand_code = AsyncMock(
            return_value=(True, test_actions)
        )

        # Mock successful execution
        execution_result = StagehandExecutionResult(
            success=True,
            pattern_used=None,
            actions_performed=test_actions,
            execution_time=2.5,
            result_data={"status": "completed", "button_clicked": True}
        )
        integration.stagehand_generator.execute_stagehand_actions = AsyncMock(
            return_value=execution_result
        )

        result = await integration.execute_stagehand_automation(
            sample_action_request, sample_dom_analysis
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.STAGEHAND
        assert result.confidence > 0.7  # Should be high confidence for successful execution
        assert result.result_data["status"] == "completed"
        assert result.error_message is None
        assert result.recommendation is None

    @pytest.mark.asyncio
    async def test_execute_with_pattern_used(self, integration, sample_action_request, sample_dom_analysis):
        """Test execution with a cached pattern"""
        # Create a test pattern
        test_pattern = StagehandPattern(
            pattern_id="test_pattern",
            description="Test pattern",
            stagehand_actions=[{"type": "act", "description": "click"}],
            success_count=5,
            failure_count=1
        )
        test_pattern.confidence_score = test_pattern.success_rate

        # Mock successful execution with pattern
        execution_result = StagehandExecutionResult(
            success=True,
            pattern_used=test_pattern,
            actions_performed=test_pattern.stagehand_actions,
            execution_time=1.8,
            result_data={"status": "completed"}
        )

        integration.stagehand_generator.generate_stagehand_code = AsyncMock(
            return_value=(True, test_pattern.stagehand_actions)
        )
        integration.stagehand_generator.execute_stagehand_actions = AsyncMock(
            return_value=execution_result
        )

        result = await integration.execute_stagehand_automation(
            sample_action_request, sample_dom_analysis
        )

        assert result.success is True
        assert result.confidence > 0.8  # Should be high due to pattern success rate
        # Verify pattern success was updated
        integration.stagehand_generator.update_pattern_success.assert_called_once_with(
            "test_pattern", True
        )

    @pytest.mark.asyncio
    async def test_execute_with_retries_eventual_success(self, integration, sample_action_request, sample_dom_analysis):
        """Test execution with retries that eventually succeeds"""
        test_actions = [{"type": "act", "description": "click"}]
        integration.stagehand_generator.generate_stagehand_code = AsyncMock(
            return_value=(True, test_actions)
        )

        # First two attempts fail, third succeeds
        failed_result = StagehandExecutionResult(
            success=False,
            pattern_used=None,
            actions_performed=[],
            execution_time=1.0,
            result_data={},
            error_message="Temporary failure"
        )

        successful_result = StagehandExecutionResult(
            success=True,
            pattern_used=None,
            actions_performed=test_actions,
            execution_time=2.0,
            result_data={"status": "completed"}
        )

        integration.stagehand_generator.execute_stagehand_actions = AsyncMock(
            side_effect=[failed_result, failed_result, successful_result]
        )

        # Use minimal retry config for faster testing
        config = StagehandExecutionPipeline(max_retries=2, timeout_seconds=10.0)

        with patch('asyncio.sleep'):  # Mock sleep to speed up test
            result = await integration.execute_stagehand_automation(
                sample_action_request, sample_dom_analysis, config
            )

        assert result.success is True
        assert integration.stagehand_generator.execute_stagehand_actions.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_all_retries_fail(self, integration, sample_action_request, sample_dom_analysis):
        """Test execution when all retries fail"""
        test_actions = [{"type": "act", "description": "click"}]
        integration.stagehand_generator.generate_stagehand_code = AsyncMock(
            return_value=(True, test_actions)
        )

        # All attempts fail
        failed_result = StagehandExecutionResult(
            success=False,
            pattern_used=None,
            actions_performed=[],
            execution_time=1.0,
            result_data={},
            error_message="Persistent failure"
        )

        integration.stagehand_generator.execute_stagehand_actions = AsyncMock(
            return_value=failed_result
        )

        config = StagehandExecutionPipeline(max_retries=1, timeout_seconds=5.0)

        with patch('asyncio.sleep'):  # Mock sleep to speed up test
            result = await integration.execute_stagehand_automation(
                sample_action_request, sample_dom_analysis, config
            )

        assert result.success is False
        assert "attempts failed" in result.error_message
        assert integration.stagehand_generator.execute_stagehand_actions.call_count == 2  # 1 retry + 1 original

    @pytest.mark.asyncio
    async def test_execute_timeout_error(self, integration, sample_action_request, sample_dom_analysis):
        """Test execution timeout handling"""
        test_actions = [{"type": "act", "description": "slow_action"}]
        integration.stagehand_generator.generate_stagehand_code = AsyncMock(
            return_value=(True, test_actions)
        )

        # Mock a slow execution that times out
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(10)  # Longer than timeout
            return StagehandExecutionResult(success=True, pattern_used=None, actions_performed=[], execution_time=10.0, result_data={})

        integration.stagehand_generator.execute_stagehand_actions = slow_execution

        config = StagehandExecutionPipeline(max_retries=0, timeout_seconds=0.1)

        result = await integration.execute_stagehand_automation(
            sample_action_request, sample_dom_analysis, config
        )

        assert result.success is False
        assert "timeout" in result.error_message.lower()

    def test_calculate_execution_confidence_success(self, integration):
        """Test confidence calculation for successful execution"""
        action_request = ActionRequest("http://test.com", "test", "click", "button")
        execution_result = StagehandExecutionResult(
            success=True,
            pattern_used=None,
            actions_performed=[{"type": "act"}],
            execution_time=3.0,
            result_data={}
        )
        actions = [{"type": "act"}]

        confidence = integration._calculate_execution_confidence(
            action_request, execution_result, actions
        )

        assert 0.7 <= confidence <= 1.0  # Base 0.7 + adjustments

    def test_calculate_execution_confidence_failure(self, integration):
        """Test confidence calculation for failed execution"""
        action_request = ActionRequest("http://test.com", "test", "click", "button")
        execution_result = StagehandExecutionResult(
            success=False,
            pattern_used=None,
            actions_performed=[],
            execution_time=0.0,
            result_data={},
            error_message="Failed"
        )
        actions = []

        confidence = integration._calculate_execution_confidence(
            action_request, execution_result, actions
        )

        assert confidence == 0.0

    def test_calculate_confidence_with_pattern(self, integration):
        """Test confidence calculation with pattern history"""
        pattern = StagehandPattern(
            pattern_id="test",
            description="Test",
            stagehand_actions=[],
            success_count=8,
            failure_count=2
        )
        pattern.confidence_score = pattern.success_rate  # 0.8

        action_request = ActionRequest("http://test.com", "test", "click", "button")
        execution_result = StagehandExecutionResult(
            success=True,
            pattern_used=pattern,
            actions_performed=[{"type": "act"}],
            execution_time=2.0,
            result_data={}
        )
        actions = [{"type": "act"}]

        confidence = integration._calculate_execution_confidence(
            action_request, execution_result, actions
        )

        # Should be average of base confidence and pattern confidence
        expected = (0.8 + 0.8) / 2  # Base ~0.8 + pattern 0.8
        assert abs(confidence - expected) < 0.1

    def test_generate_recommendation_success(self, integration):
        """Test recommendation generation for successful execution"""
        execution_result = StagehandExecutionResult(
            success=True, pattern_used=None, actions_performed=[], execution_time=1.0, result_data={}
        )

        recommendation = integration._generate_recommendation(execution_result)
        assert recommendation is None

    def test_generate_recommendation_timeout(self, integration):
        """Test recommendation generation for timeout error"""
        execution_result = StagehandExecutionResult(
            success=False, pattern_used=None, actions_performed=[], execution_time=0.0,
            result_data={}, error_message="Execution timeout after 30s"
        )

        recommendation = integration._generate_recommendation(execution_result)
        assert "timeout" in recommendation.lower()

    def test_generate_recommendation_not_found(self, integration):
        """Test recommendation generation for element not found"""
        execution_result = StagehandExecutionResult(
            success=False, pattern_used=None, actions_performed=[], execution_time=0.0,
            result_data={}, error_message="Element not found on page"
        )

        recommendation = integration._generate_recommendation(execution_result)
        assert "vision fallback" in recommendation.lower()

    @pytest.mark.asyncio
    async def test_record_execution_for_learning(self, integration, sample_action_request):
        """Test recording execution results for learning"""
        test_pattern = StagehandPattern("test_id", "Test", [])
        execution_result = StagehandExecutionResult(
            success=True,
            pattern_used=test_pattern,
            actions_performed=[],
            execution_time=2.0,
            result_data={}
        )
        final_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.8,
            execution_time=2.5,
            result_data={}
        )

        initial_history_length = len(integration.execution_history)

        await integration._record_execution_for_learning(
            sample_action_request, [], execution_result, final_result
        )

        # Verify pattern success was updated
        integration.stagehand_generator.update_pattern_success.assert_called_once_with("test_id", True)

        # Verify orchestrator was called
        integration.orchestrator.record_execution_result.assert_called_once_with(
            sample_action_request, AutomationApproach.STAGEHAND, final_result
        )

        # Verify execution history was updated
        assert len(integration.execution_history) == initial_history_length + 1
        latest_record = integration.execution_history[-1]
        assert latest_record['url'] == sample_action_request.url
        assert latest_record['success'] is True

    def test_get_execution_analytics_empty(self, integration):
        """Test analytics when no executions recorded"""
        analytics = integration.get_execution_analytics()
        assert analytics["total_executions"] == 0

    def test_get_execution_analytics_with_data(self, integration):
        """Test analytics with execution data"""
        # Add test execution records
        integration.execution_history = [
            {
                'timestamp': time.time(),
                'url': 'http://test1.com',
                'task': 'Login',
                'action_type': 'click',
                'success': True,
                'execution_time': 2.0,
                'actions_count': 2,
                'pattern_used': 'pattern1',
                'error': None
            },
            {
                'timestamp': time.time(),
                'url': 'http://test2.com',
                'task': 'Submit',
                'action_type': 'click',
                'success': False,
                'execution_time': 3.0,
                'actions_count': 3,
                'pattern_used': None,
                'error': 'Failed'
            },
            {
                'timestamp': time.time(),
                'url': 'http://test3.com',
                'task': 'Type',
                'action_type': 'type',
                'success': True,
                'execution_time': 1.5,
                'actions_count': 1,
                'pattern_used': 'pattern2',
                'error': None
            }
        ]

        analytics = integration.get_execution_analytics()

        assert analytics["total_executions"] == 3
        assert analytics["success_rate"] == 2/3  # 2 successes out of 3
        assert analytics["average_execution_time"] == (2.0 + 3.0 + 1.5) / 3

        # Check action type breakdown
        assert "click" in analytics["action_types"]
        assert "type" in analytics["action_types"]
        assert analytics["action_types"]["click"]["total"] == 2
        assert analytics["action_types"]["click"]["successful"] == 1
        assert analytics["action_types"]["click"]["success_rate"] == 0.5
        assert analytics["action_types"]["type"]["total"] == 1
        assert analytics["action_types"]["type"]["successful"] == 1
        assert analytics["action_types"]["type"]["success_rate"] == 1.0

    def test_clear_execution_history(self, integration):
        """Test clearing execution history"""
        # Add some test records
        integration.execution_history = [{'test': 'data1'}, {'test': 'data2'}]

        count = integration.clear_execution_history()

        assert count == 2
        assert len(integration.execution_history) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])