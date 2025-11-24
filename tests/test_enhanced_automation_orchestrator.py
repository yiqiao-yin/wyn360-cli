"""
Unit tests for Enhanced Automation Orchestrator

Tests the EnhancedAutomationOrchestrator class that integrates DOM, Stagehand,
and Vision approaches with intelligent fallback logic.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.enhanced_automation_orchestrator import (
    EnhancedAutomationOrchestrator,
    EnhancedActionRequest,
    StagehandExecutionPipeline
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionResult,
    DecisionContext
)


class TestEnhancedActionRequest:
    """Test EnhancedActionRequest dataclass"""

    def test_enhanced_request_defaults(self):
        """Test enhanced request with default values"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Test task",
            action_type="click",
            target_description="button"
        )

        assert request.enable_stagehand is True
        assert request.stagehand_config is None
        assert request.fallback_to_vision is True
        assert request.confidence_threshold == 0.7
        assert request.show_browser is False

    def test_enhanced_request_custom_config(self):
        """Test enhanced request with custom configuration"""
        config = StagehandExecutionPipeline(max_retries=5, timeout_seconds=60.0)
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Test task",
            action_type="click",
            target_description="button",
            enable_stagehand=False,
            stagehand_config=config,
            fallback_to_vision=False,
            show_browser=True
        )

        assert request.enable_stagehand is False
        assert request.stagehand_config == config
        assert request.fallback_to_vision is False
        assert request.show_browser is True


class TestEnhancedAutomationOrchestrator:
    """Test EnhancedAutomationOrchestrator class"""

    @pytest.fixture
    def orchestrator(self):
        """Create enhanced orchestrator with mocked dependencies"""
        with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.stagehand_integration'):
            with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools'):
                return EnhancedAutomationOrchestrator()

    @pytest.fixture
    def sample_request(self):
        """Create sample enhanced action request"""
        return EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the login button",
            action_type="click",
            target_description="login button"
        )

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.base_orchestrator is not None
        assert orchestrator.stagehand_integration is not None
        assert orchestrator.execution_history == []

    @pytest.mark.asyncio
    async def test_dom_analysis_success(self, orchestrator, sample_request):
        """Test successful DOM analysis"""
        mock_result = {
            'success': True,
            'confidence': 0.85,
            'interactive_elements_count': 5,
            'forms_count': 1,
            'dom_analysis_text': '<button>Login</button>'
        }

        with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools') as mock_tools:
            mock_tools.analyze_page_dom = AsyncMock(return_value=mock_result)

            result = await orchestrator._perform_dom_analysis(sample_request)

            assert result['success'] is True
            assert result['confidence'] == 0.85
            mock_tools.analyze_page_dom.assert_called_once_with(
                url=sample_request.url,
                task_description=sample_request.task_description
            )

    @pytest.mark.asyncio
    async def test_dom_analysis_failure(self, orchestrator, sample_request):
        """Test DOM analysis failure handling"""
        with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools') as mock_tools:
            mock_tools.analyze_page_dom = AsyncMock(side_effect=Exception("Analysis failed"))

            result = await orchestrator._perform_dom_analysis(sample_request)

            assert result['success'] is False
            assert 'Analysis failed' in result['error']
            assert result['confidence'] == 0.0

    @pytest.mark.asyncio
    async def test_execute_dom_approach_success(self, orchestrator, sample_request):
        """Test successful DOM approach execution"""
        dom_result = {'success': True, 'confidence': 0.8}
        execution_result = {
            'success': True,
            'confidence': 0.8,
            'execution_time': 2.0,
            'action': 'click',
            'result': 'Button clicked'
        }

        with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools') as mock_tools:
            mock_tools.execute_dom_action = AsyncMock(return_value=execution_result)

            result = await orchestrator._execute_dom_approach(sample_request, dom_result)

            assert result.success is True
            assert result.approach_used == AutomationApproach.DOM_ANALYSIS
            assert result.confidence == 0.8
            assert result.execution_time == 2.0

    @pytest.mark.asyncio
    async def test_execute_dom_approach_failure(self, orchestrator, sample_request):
        """Test DOM approach execution failure"""
        dom_result = {'success': True, 'confidence': 0.8}
        execution_result = {
            'success': False,
            'confidence': 0.3,
            'execution_time': 1.0,
            'error': 'Element not found'
        }

        with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools') as mock_tools:
            mock_tools.execute_dom_action = AsyncMock(return_value=execution_result)

            result = await orchestrator._execute_dom_approach(sample_request, dom_result)

            assert result.success is False
            assert result.approach_used == AutomationApproach.DOM_ANALYSIS
            assert result.error_message == 'Element not found'
            assert result.recommendation is not None

    @pytest.mark.asyncio
    async def test_execute_stagehand_approach_success(self, orchestrator, sample_request):
        """Test successful Stagehand approach execution"""
        dom_result = {'success': True, 'confidence': 0.6}
        stagehand_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.8,
            execution_time=3.0,
            result_data={'status': 'completed'}
        )

        orchestrator.stagehand_integration.execute_stagehand_automation = AsyncMock(
            return_value=stagehand_result
        )

        result = await orchestrator._execute_stagehand_approach(sample_request, dom_result)

        assert result.success is True
        assert result.approach_used == AutomationApproach.STAGEHAND
        assert result.confidence == 0.8

    @pytest.mark.asyncio
    async def test_execute_stagehand_disabled(self, orchestrator):
        """Test Stagehand execution when disabled"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Test",
            action_type="click",
            target_description="button",
            enable_stagehand=False
        )

        result = await orchestrator._execute_stagehand_approach(request, {})

        assert result.success is False
        assert "disabled by request" in result.error_message
        assert result.recommendation == "Use DOM analysis or vision fallback"

    @pytest.mark.asyncio
    async def test_execute_stagehand_with_vision_fallback(self, orchestrator, sample_request):
        """Test Stagehand execution with vision fallback"""
        dom_result = {'success': True, 'confidence': 0.6}

        # Stagehand fails
        stagehand_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.0,
            execution_time=1.0,
            result_data={},
            error_message="Stagehand failed"
        )

        # Vision succeeds
        vision_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.VISION_FALLBACK,
            confidence=0.7,
            execution_time=5.0,
            result_data={'status': 'vision_success'}
        )

        orchestrator.stagehand_integration.execute_stagehand_automation = AsyncMock(
            return_value=stagehand_result
        )

        with patch.object(orchestrator, '_execute_vision_approach', return_value=vision_result):
            result = await orchestrator._execute_stagehand_approach(sample_request, dom_result)

            assert result.success is True
            assert result.approach_used == AutomationApproach.VISION_FALLBACK
            assert "Stagehand failed" in result.recommendation

    @pytest.mark.asyncio
    async def test_execute_vision_approach(self, orchestrator, sample_request):
        """Test vision approach execution (placeholder)"""
        result = await orchestrator._execute_vision_approach(sample_request)

        assert result.success is False  # Placeholder implementation
        assert result.approach_used == AutomationApproach.VISION_FALLBACK
        assert "not yet integrated" in result.error_message

    @pytest.mark.asyncio
    async def test_full_automation_task_dom_success(self, orchestrator, sample_request):
        """Test complete automation task with DOM success"""
        # Mock DOM analysis
        dom_analysis = {
            'success': True,
            'confidence': 0.85,
            'interactive_elements_count': 5,
            'forms_count': 1
        }

        # Mock orchestrator decision
        context = DecisionContext(0.85, "moderate", 5, 1, [])
        orchestrator.base_orchestrator.decide_automation_approach = Mock(
            return_value=(AutomationApproach.DOM_ANALYSIS, context, "High confidence")
        )

        # Mock DOM execution
        execution_result = {
            'success': True,
            'confidence': 0.85,
            'execution_time': 2.0
        }

        with patch.object(orchestrator, '_perform_dom_analysis', return_value=dom_analysis):
            with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools') as mock_tools:
                mock_tools.execute_dom_action = AsyncMock(return_value=execution_result)

                result = await orchestrator.execute_automation_task(sample_request)

                assert result.success is True
                assert result.approach_used == AutomationApproach.DOM_ANALYSIS
                assert len(orchestrator.execution_history) == 1

    @pytest.mark.asyncio
    async def test_full_automation_task_dom_analysis_failure(self, orchestrator, sample_request):
        """Test automation task when DOM analysis fails"""
        with patch.object(orchestrator, '_perform_dom_analysis', return_value={'success': False}):
            result = await orchestrator.execute_automation_task(sample_request)

            assert result.success is False
            assert "DOM analysis failed" in result.error_message

    def test_generate_dom_recommendation(self, orchestrator):
        """Test DOM recommendation generation"""
        # Success case
        success_result = {'success': True, 'confidence': 0.8}
        assert orchestrator._generate_dom_recommendation(success_result) is None

        # Low confidence
        low_conf_result = {'success': False, 'confidence': 0.3}
        recommendation = orchestrator._generate_dom_recommendation(low_conf_result)
        assert "Stagehand" in recommendation

        # Medium confidence
        med_conf_result = {'success': False, 'confidence': 0.5}
        recommendation = orchestrator._generate_dom_recommendation(med_conf_result)
        assert "Stagehand" in recommendation

        # High confidence but failed
        high_conf_result = {'success': False, 'confidence': 0.9}
        recommendation = orchestrator._generate_dom_recommendation(high_conf_result)
        assert "element selectors" in recommendation.lower()

    def test_create_failure_result(self, orchestrator, sample_request):
        """Test failure result creation"""
        result = orchestrator._create_failure_result(
            sample_request,
            "Test error",
            2.5,
            "Test recommendation"
        )

        assert result.success is False
        assert result.error_message == "Test error"
        assert result.execution_time == 2.5
        assert result.recommendation == "Test recommendation"

    def test_record_execution_result(self, orchestrator, sample_request):
        """Test execution result recording"""
        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.8,
            execution_time=3.0,
            result_data={}
        )

        context = DecisionContext(0.8, "moderate", 5, 1, [])

        initial_count = len(orchestrator.execution_history)

        orchestrator._record_execution_result(sample_request, result, context, "Test reasoning")

        assert len(orchestrator.execution_history) == initial_count + 1
        latest_record = orchestrator.execution_history[-1]
        assert latest_record['success'] is True
        assert latest_record['approach_used'] == 'stagehand'
        assert latest_record['reasoning'] == "Test reasoning"

    def test_get_enhanced_analytics_empty(self, orchestrator):
        """Test analytics when no executions recorded"""
        analytics = orchestrator.get_enhanced_analytics()

        assert analytics['enhanced_orchestrator']['total_executions'] == 0
        assert analytics['enhanced_orchestrator']['approach_performance'] == {}
        assert 'base_orchestrator_decisions' in analytics
        assert 'stagehand_execution' in analytics

    def test_get_enhanced_analytics_with_data(self, orchestrator):
        """Test analytics with execution data"""
        # Add test execution records
        orchestrator.execution_history = [
            {
                'timestamp': time.time(),
                'approach_used': 'dom_analysis',
                'success': True,
                'confidence': 0.8
            },
            {
                'timestamp': time.time(),
                'approach_used': 'stagehand',
                'success': False,
                'confidence': 0.6
            },
            {
                'timestamp': time.time(),
                'approach_used': 'dom_analysis',
                'success': True,
                'confidence': 0.9
            }
        ]

        # Mock base analytics
        orchestrator.base_orchestrator.get_decision_analytics = Mock(
            return_value={'total_decisions': 3}
        )

        # Mock stagehand analytics
        orchestrator.stagehand_integration.get_execution_analytics = Mock(
            return_value={'total_executions': 1}
        )

        analytics = orchestrator.get_enhanced_analytics()

        assert analytics['enhanced_orchestrator']['total_executions'] == 3

        # Check approach performance
        perf = analytics['enhanced_orchestrator']['approach_performance']
        assert 'dom_analysis' in perf
        assert 'stagehand' in perf
        assert perf['dom_analysis']['success_rate'] == 1.0  # 2/2
        assert perf['stagehand']['success_rate'] == 0.0     # 0/1

    def test_clear_execution_history(self, orchestrator):
        """Test clearing execution history"""
        # Add test data
        orchestrator.execution_history = [{'test': 'data1'}, {'test': 'data2'}]

        # Mock stagehand clear
        orchestrator.stagehand_integration.clear_execution_history = Mock(return_value=5)

        count = orchestrator.clear_execution_history()

        assert count == 2
        assert len(orchestrator.execution_history) == 0
        orchestrator.stagehand_integration.clear_execution_history.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])