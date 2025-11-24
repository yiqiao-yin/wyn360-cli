"""
Unit tests for Unified Automation Interface

Tests the UnifiedAutomationInterface class that provides a single entry point
for all browser automation approaches with intelligent routing and fallbacks.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.unified_automation_interface import (
    UnifiedAutomationInterface,
    UnifiedAutomationConfig
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionResult
)
from src.wyn360.tools.browser.stagehand_integration import StagehandExecutionPipeline
from src.wyn360.tools.browser.vision_fallback_integration import VisionFallbackConfig


class TestUnifiedAutomationConfig:
    """Test UnifiedAutomationConfig dataclass"""

    def test_config_defaults(self):
        """Test default configuration values"""
        config = UnifiedAutomationConfig()

        assert config.preferred_approach is None
        assert config.enable_dom_analysis is True
        assert config.enable_stagehand is True
        assert config.enable_vision_fallback is True
        assert config.max_retries_per_approach == 2
        assert config.total_timeout_seconds == 300.0
        assert config.show_browser is False
        assert config.dom_confidence_threshold == 0.7
        assert config.stagehand_confidence_threshold == 0.6
        assert config.vision_confidence_threshold == 0.5
        assert config.stagehand_config is None
        assert config.vision_config is None

    def test_config_custom_values(self):
        """Test custom configuration values"""
        stagehand_config = StagehandExecutionPipeline(max_retries=5)
        vision_config = VisionFallbackConfig(max_steps=15)

        config = UnifiedAutomationConfig(
            preferred_approach=AutomationApproach.STAGEHAND,
            enable_dom_analysis=False,
            max_retries_per_approach=3,
            total_timeout_seconds=600.0,
            show_browser=True,
            dom_confidence_threshold=0.8,
            stagehand_config=stagehand_config,
            vision_config=vision_config
        )

        assert config.preferred_approach == AutomationApproach.STAGEHAND
        assert config.enable_dom_analysis is False
        assert config.max_retries_per_approach == 3
        assert config.total_timeout_seconds == 600.0
        assert config.show_browser is True
        assert config.dom_confidence_threshold == 0.8
        assert config.stagehand_config == stagehand_config
        assert config.vision_config == vision_config


class TestUnifiedAutomationInterface:
    """Test UnifiedAutomationInterface class"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock enhanced orchestrator"""
        orchestrator = Mock()
        orchestrator.execute_automation_task = AsyncMock()
        orchestrator.set_agent = Mock()
        orchestrator.get_enhanced_analytics = Mock(return_value={'test': 'analytics'})
        orchestrator.clear_execution_history = Mock(return_value=5)

        # Mock integrations
        orchestrator.stagehand_integration = Mock()
        orchestrator.stagehand_integration.stagehand_generator = Mock()
        orchestrator.stagehand_integration.stagehand_generator.is_available.return_value = True
        orchestrator.stagehand_integration.stagehand_generator.get_status_info.return_value = {'status': 'available'}

        orchestrator.vision_integration = Mock()
        orchestrator.vision_integration.is_available.return_value = True
        orchestrator.vision_integration.get_execution_analytics.return_value = {'total_executions': 0}

        return orchestrator

    @pytest.fixture
    def unified_interface(self, mock_orchestrator):
        """Create UnifiedAutomationInterface instance"""
        return UnifiedAutomationInterface(mock_orchestrator)

    def test_initialization_default(self):
        """Test default initialization"""
        with patch('src.wyn360.tools.browser.unified_automation_interface.enhanced_automation_orchestrator'):
            interface = UnifiedAutomationInterface()
            assert interface.orchestrator is not None
            assert interface.execution_history == []

    def test_initialization_with_orchestrator(self, mock_orchestrator):
        """Test initialization with custom orchestrator"""
        interface = UnifiedAutomationInterface(mock_orchestrator)
        assert interface.orchestrator == mock_orchestrator

    def test_set_agent(self, unified_interface, mock_orchestrator):
        """Test setting agent"""
        mock_agent = Mock()
        unified_interface.set_agent(mock_agent)
        mock_orchestrator.set_agent.assert_called_once_with(mock_agent)

    @pytest.mark.asyncio
    async def test_execute_automation_basic(self, unified_interface, mock_orchestrator):
        """Test basic automation execution"""
        # Mock successful execution
        mock_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.8,
            execution_time=2.5,
            result_data={'status': 'completed'}
        )
        mock_orchestrator.execute_automation_task.return_value = mock_result

        result = await unified_interface.execute_automation(
            url="https://example.com",
            task_description="Click the login button"
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.DOM_ANALYSIS
        assert result.confidence == 0.8

        # Verify orchestrator was called correctly
        mock_orchestrator.execute_automation_task.assert_called_once()
        call_args = mock_orchestrator.execute_automation_task.call_args[0][0]
        assert call_args.url == "https://example.com"
        assert call_args.task_description == "Click the login button"
        assert call_args.action_type == "automation"
        assert call_args.target_description == "target element"

    @pytest.mark.asyncio
    async def test_execute_automation_with_full_params(self, unified_interface, mock_orchestrator):
        """Test automation execution with all parameters"""
        mock_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.9,
            execution_time=5.0,
            result_data={'actions': 'completed'}
        )
        mock_orchestrator.execute_automation_task.return_value = mock_result

        config = UnifiedAutomationConfig(
            show_browser=True,
            dom_confidence_threshold=0.8
        )

        result = await unified_interface.execute_automation(
            url="https://example.com",
            task_description="Fill out the form",
            action_type="type",
            target_description="email field",
            action_data={"text": "test@example.com"},
            config=config
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.STAGEHAND

        # Verify enhanced request was created correctly
        call_args = mock_orchestrator.execute_automation_task.call_args[0][0]
        assert call_args.url == "https://example.com"
        assert call_args.task_description == "Fill out the form"
        assert call_args.action_type == "type"
        assert call_args.target_description == "email field"
        assert call_args.action_data == {"text": "test@example.com"}
        assert call_args.show_browser is True
        assert call_args.confidence_threshold == 0.8

    @pytest.mark.asyncio
    async def test_execute_automation_exception(self, unified_interface, mock_orchestrator):
        """Test automation execution with exception"""
        mock_orchestrator.execute_automation_task.side_effect = Exception("Orchestrator error")

        result = await unified_interface.execute_automation(
            url="https://example.com",
            task_description="Test task"
        )

        assert result.success is False
        assert result.approach_used == AutomationApproach.DOM_ANALYSIS  # Default
        assert "Orchestrator error" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_approach_forced(self, unified_interface, mock_orchestrator):
        """Test execution with forced approach"""
        mock_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.VISION_FALLBACK,
            confidence=0.7,
            execution_time=8.0,
            result_data={'vision_result': 'success'}
        )
        mock_orchestrator.execute_automation_task.return_value = mock_result

        result = await unified_interface.execute_with_approach(
            approach=AutomationApproach.VISION_FALLBACK,
            url="https://example.com",
            task_description="Complex visual task"
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.VISION_FALLBACK

        # Verify forced approach was set
        call_args = mock_orchestrator.execute_automation_task.call_args[0][0]
        assert call_args.force_approach == AutomationApproach.VISION_FALLBACK

    def test_create_enhanced_request(self, unified_interface):
        """Test creation of enhanced action request"""
        config = UnifiedAutomationConfig(
            show_browser=True,
            enable_stagehand=False,
            preferred_approach=AutomationApproach.DOM_ANALYSIS
        )

        request = unified_interface._create_enhanced_request(
            url="https://test.com",
            task_description="Test task",
            action_type="click",
            target_description="test button",
            action_data={"key": "value"},
            config=config
        )

        assert request.url == "https://test.com"
        assert request.task_description == "Test task"
        assert request.action_type == "click"
        assert request.target_description == "test button"
        assert request.action_data == {"key": "value"}
        assert request.show_browser is True
        assert request.enable_stagehand is False
        assert request.force_approach == AutomationApproach.DOM_ANALYSIS

    def test_record_execution(self, unified_interface):
        """Test execution recording for analytics"""
        request_mock = Mock()
        request_mock.url = "https://example.com"
        request_mock.task_description = "Test task"
        request_mock.action_type = "click"
        request_mock.target_description = "button"
        request_mock.force_approach = None

        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.8,
            execution_time=3.0,
            result_data={}
        )

        config = UnifiedAutomationConfig()

        initial_count = len(unified_interface.execution_history)
        unified_interface._record_execution(request_mock, result, config)

        assert len(unified_interface.execution_history) == initial_count + 1
        record = unified_interface.execution_history[-1]
        assert record['success'] is True
        assert record['approach_used'] == 'dom_analysis'
        assert record['confidence'] == 0.8
        assert record['execution_time'] == 3.0

    def test_get_unified_analytics_empty(self, unified_interface):
        """Test analytics when no executions recorded"""
        analytics = unified_interface.get_unified_analytics()

        assert analytics['unified_interface']['total_unified_executions'] == 0
        assert analytics['unified_interface']['success_rate'] == 0.0
        assert analytics['unified_interface']['approach_usage'] == {}
        assert 'detailed_analytics' in analytics

    def test_get_unified_analytics_with_data(self, unified_interface):
        """Test analytics with execution data"""
        # Add test execution records
        unified_interface.execution_history = [
            {
                'success': True,
                'execution_time': 2.0,
                'approach_used': 'dom_analysis'
            },
            {
                'success': False,
                'execution_time': 5.0,
                'approach_used': 'stagehand'
            },
            {
                'success': True,
                'execution_time': 8.0,
                'approach_used': 'dom_analysis'
            },
            {
                'success': True,
                'execution_time': 12.0,
                'approach_used': 'vision_fallback'
            }
        ]

        analytics = unified_interface.get_unified_analytics()

        assert analytics['unified_interface']['total_unified_executions'] == 4
        assert analytics['unified_interface']['successful_executions'] == 3
        assert analytics['unified_interface']['success_rate'] == 0.75
        assert analytics['unified_interface']['average_execution_time'] == 6.75

        # Check approach usage
        usage = analytics['unified_interface']['approach_usage']
        assert 'dom_analysis' in usage
        assert 'stagehand' in usage
        assert 'vision_fallback' in usage

        assert usage['dom_analysis']['count'] == 2
        assert usage['dom_analysis']['success_rate'] == 1.0
        assert usage['stagehand']['count'] == 1
        assert usage['stagehand']['success_rate'] == 0.0
        assert usage['vision_fallback']['count'] == 1
        assert usage['vision_fallback']['success_rate'] == 1.0

    def test_clear_all_history(self, unified_interface, mock_orchestrator):
        """Test clearing all execution history"""
        # Add test data
        unified_interface.execution_history = [{'test': 'data1'}, {'test': 'data2'}]

        result = unified_interface.clear_all_history()

        assert result['unified_interface'] == 2
        assert result['orchestrator'] == 5  # From mock
        assert len(unified_interface.execution_history) == 0
        mock_orchestrator.clear_execution_history.assert_called_once()

    def test_get_system_status(self, unified_interface, mock_orchestrator):
        """Test getting system status"""
        status = unified_interface.get_system_status()

        assert status['dom_analysis']['available'] is True
        assert status['stagehand']['available'] is True
        assert status['vision_fallback']['available'] is True
        assert 'description' in status['dom_analysis']
        assert 'status_info' in status['stagehand']
        assert 'analytics' in status['vision_fallback']
        assert 'orchestrator_analytics' in status

    def test_log_execution_start(self, unified_interface, caplog):
        """Test execution start logging"""
        import logging
        caplog.set_level(logging.INFO)

        request_mock = Mock()
        request_mock.url = "https://example.com"
        request_mock.task_description = "Test task"
        request_mock.action_type = "click"
        request_mock.target_description = "test button"

        config = UnifiedAutomationConfig(
            enable_dom_analysis=True,
            enable_stagehand=False,
            enable_vision_fallback=True,
            preferred_approach=AutomationApproach.DOM_ANALYSIS
        )

        unified_interface._log_execution_start(request_mock, config)

        # Check that appropriate log messages were generated
        assert "Unified Automation Starting" in caplog.text
        assert "Test task" in caplog.text
        assert "DOM → Vision" in caplog.text
        assert "dom_analysis" in caplog.text

    def test_log_execution_result_success(self, unified_interface, caplog):
        """Test execution result logging for success"""
        import logging
        caplog.set_level(logging.INFO)

        request_mock = Mock()
        request_mock.task_description = "Test task"

        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.9,
            execution_time=4.2,
            result_data={}
        )

        unified_interface._log_execution_result(request_mock, result)

        assert "SUCCESS" in caplog.text
        assert "stagehand" in caplog.text
        assert "0.90" in caplog.text
        assert "4.2" in caplog.text

    def test_log_execution_result_failure(self, unified_interface, caplog):
        """Test execution result logging for failure"""
        import logging
        caplog.set_level(logging.INFO)

        request_mock = Mock()

        result = ActionResult(
            success=False,
            approach_used=AutomationApproach.VISION_FALLBACK,
            confidence=0.2,
            execution_time=1.5,
            result_data={},
            error_message="Test error",
            recommendation="Try different approach"
        )

        unified_interface._log_execution_result(request_mock, result)

        assert "FAILED" in caplog.text
        assert "vision_fallback" in caplog.text
        assert "Test error" in caplog.text
        assert "Try different approach" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])