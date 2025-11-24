"""
Unit tests for Enhanced Automation Orchestrator with Interactive Error Handling

Tests the integration of interactive error handling into the enhanced automation
orchestrator and the complete error recovery workflow.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.wyn360.tools.browser.enhanced_automation_orchestrator import (
    EnhancedAutomationOrchestrator,
    EnhancedActionRequest,
    enhanced_automation_orchestrator
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionResult,
    DecisionContext
)
from src.wyn360.tools.browser.interactive_error_handler import (
    InteractiveErrorContext,
    RecoveryAction,
    RecoveryOption
)
from src.wyn360.tools.browser.unified_error_handling import (
    ErrorContext,
    ErrorCategory
)


class TestEnhancedActionRequest:
    """Test EnhancedActionRequest with interactive features"""

    def test_enhanced_action_request_creation(self):
        """Test creating enhanced action request with interactive features"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button",
            enable_interactive_error_handling=True,
            interactive_callback=None
        )

        assert request.url == "https://example.com"
        assert request.task_description == "Click submit button"
        assert request.enable_interactive_error_handling is True
        assert request.interactive_callback is None

    def test_enhanced_action_request_defaults(self):
        """Test default values for enhanced action request"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button"
        )

        assert request.enable_interactive_error_handling is False
        assert request.interactive_callback is None
        assert request.enable_stagehand is True
        assert request.fallback_to_vision is True


class TestEnhancedAutomationOrchestratorInteractive:
    """Test EnhancedAutomationOrchestrator interactive features"""

    def setup_method(self):
        """Set up test fixtures"""
        self.orchestrator = EnhancedAutomationOrchestrator()
        self.mock_agent = Mock()
        self.orchestrator.set_agent(self.mock_agent)

    def test_initialization_with_interactive_components(self):
        """Test orchestrator initialization includes interactive components"""
        assert self.orchestrator.unified_error_handler is not None
        assert self.orchestrator.interactive_error_handler is not None
        assert self.orchestrator.interactive_mode is False

    def test_enable_interactive_mode(self):
        """Test enabling interactive mode"""
        assert self.orchestrator.interactive_mode is False

        self.orchestrator.enable_interactive_mode(True)
        assert self.orchestrator.interactive_mode is True

        self.orchestrator.enable_interactive_mode(False)
        assert self.orchestrator.interactive_mode is False

    def test_set_agent_interactive_integration(self):
        """Test agent is set for both vision and interactive error handling"""
        mock_agent = Mock()
        self.orchestrator.set_agent(mock_agent)

        assert self.orchestrator.interactive_error_handler.agent == mock_agent
        assert self.orchestrator.vision_integration.agent == mock_agent

    def test_get_remaining_approaches(self):
        """Test getting remaining automation approaches"""
        attempted = [AutomationApproach.DOM_ANALYSIS]
        remaining = self.orchestrator._get_remaining_approaches(attempted)

        assert AutomationApproach.DOM_ANALYSIS not in remaining
        assert AutomationApproach.STAGEHAND in remaining
        assert AutomationApproach.VISION_FALLBACK in remaining

        attempted = [AutomationApproach.DOM_ANALYSIS, AutomationApproach.STAGEHAND]
        remaining = self.orchestrator._get_remaining_approaches(attempted)

        assert len(remaining) == 1
        assert remaining[0] == AutomationApproach.VISION_FALLBACK

        attempted = list(AutomationApproach)
        remaining = self.orchestrator._get_remaining_approaches(attempted)

        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_execute_approach_directly(self):
        """Test executing approach directly without error handling"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button"
        )

        dom_analysis_result = {
            'success': True,
            'confidence': 0.8,
            'interactive_elements_count': 5,
            'forms_count': 1
        }

        # Mock DOM execution
        with patch.object(self.orchestrator, '_execute_dom_approach') as mock_dom:
            mock_result = ActionResult(
                success=True,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.8,
                execution_time=2.0,
                result_data={'success': True}
            )
            mock_dom.return_value = mock_result

            result = await self.orchestrator._execute_approach_directly(
                request, AutomationApproach.DOM_ANALYSIS, dom_analysis_result
            )

            assert result.success is True
            assert result.approach_used == AutomationApproach.DOM_ANALYSIS
            mock_dom.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_interactive_error_recovery_success(self):
        """Test successful interactive error recovery"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button",
            enable_interactive_error_handling=True
        )

        failed_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        attempted_approaches = [AutomationApproach.DOM_ANALYSIS]
        dom_analysis_result = {'confidence': 0.6}

        # Mock the interactive error handler
        mock_interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=failed_result,
            attempted_approaches=attempted_approaches,
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=RecoveryAction.TRY_DIFFERENT_APPROACH
        )

        with patch.object(self.orchestrator.interactive_error_handler, 'handle_automation_error') as mock_handle:
            with patch.object(self.orchestrator, '_execute_recovery_action') as mock_execute:
                mock_handle.return_value = mock_interactive_context

                # Mock successful recovery
                recovery_result = ActionResult(
                    success=True,
                    approach_used=AutomationApproach.STAGEHAND,
                    confidence=0.8,
                    execution_time=3.0,
                    result_data={'recovered': True}
                )
                mock_execute.return_value = recovery_result

                result = await self.orchestrator._handle_interactive_error_recovery(
                    request, failed_result, attempted_approaches, dom_analysis_result
                )

                assert result.success is True
                assert result.approach_used == AutomationApproach.STAGEHAND
                assert "Recovered from" in result.recommendation
                mock_handle.assert_called_once()
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_interactive_error_recovery_no_choice(self):
        """Test interactive error recovery when no choice is made"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button",
            enable_interactive_error_handling=True
        )

        failed_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        # Mock interactive context with no choice
        mock_interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=failed_result,
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS],
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=None  # No choice made
        )

        with patch.object(self.orchestrator.interactive_error_handler, 'handle_automation_error') as mock_handle:
            mock_handle.return_value = mock_interactive_context

            result = await self.orchestrator._handle_interactive_error_recovery(
                request, failed_result, [AutomationApproach.DOM_ANALYSIS], {}
            )

            # Should return original failure when no choice is made
            assert result == failed_result

    @pytest.mark.asyncio
    async def test_execute_recovery_action_retry_same(self):
        """Test executing retry same approach recovery action"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button"
        )

        interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.6,
                execution_time=2.0,
                result_data={},
                error_message="Element not found"
            ),
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS],
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=RecoveryAction.RETRY_SAME_APPROACH
        )

        with patch.object(self.orchestrator, '_execute_approach_directly') as mock_execute:
            with patch.object(self.orchestrator.interactive_error_handler, 'execute_recovery_action') as mock_recovery:
                # Mock the recovery execution to call our callback
                async def mock_recovery_execution(context, callback):
                    return await callback(context)

                mock_recovery.side_effect = mock_recovery_execution

                # Mock successful retry
                retry_result = ActionResult(
                    success=True,
                    approach_used=AutomationApproach.DOM_ANALYSIS,
                    confidence=0.8,
                    execution_time=2.5,
                    result_data={'retried': True}
                )
                mock_execute.return_value = retry_result

                result = await self.orchestrator._execute_recovery_action(
                    request, interactive_context, [AutomationApproach.DOM_ANALYSIS], {}
                )

                assert result.success is True
                assert result.approach_used == AutomationApproach.DOM_ANALYSIS
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_recovery_action_try_different(self):
        """Test executing try different approach recovery action"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button"
        )

        interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.6,
                execution_time=2.0,
                result_data={},
                error_message="Element not found"
            ),
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS],
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=RecoveryAction.TRY_DIFFERENT_APPROACH
        )

        with patch.object(self.orchestrator, '_execute_approach_directly') as mock_execute:
            with patch.object(self.orchestrator.interactive_error_handler, 'execute_recovery_action') as mock_recovery:
                # Mock the recovery execution to call our callback
                async def mock_recovery_execution(context, callback):
                    return await callback(context)

                mock_recovery.side_effect = mock_recovery_execution

                # Mock successful different approach execution
                different_result = ActionResult(
                    success=True,
                    approach_used=AutomationApproach.STAGEHAND,
                    confidence=0.9,
                    execution_time=3.0,
                    result_data={'different_approach': True}
                )
                mock_execute.return_value = different_result

                result = await self.orchestrator._execute_recovery_action(
                    request, interactive_context, [AutomationApproach.DOM_ANALYSIS], {}
                )

                assert result.success is True
                assert result.approach_used == AutomationApproach.STAGEHAND
                # Should be called with STAGEHAND (next approach)
                mock_execute.assert_called_once()
                call_args = mock_execute.call_args[0]
                assert call_args[1] == AutomationApproach.STAGEHAND

    @pytest.mark.asyncio
    async def test_execute_recovery_action_no_remaining_approaches(self):
        """Test executing try different approach when no approaches remain"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button"
        )

        # All approaches have been attempted
        attempted_approaches = list(AutomationApproach)

        interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.VISION_FALLBACK,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=ActionResult(
                success=False,
                approach_used=AutomationApproach.VISION_FALLBACK,
                confidence=0.6,
                execution_time=2.0,
                result_data={},
                error_message="Element not found"
            ),
            attempted_approaches=attempted_approaches,
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=RecoveryAction.TRY_DIFFERENT_APPROACH
        )

        with patch.object(self.orchestrator.interactive_error_handler, 'execute_recovery_action') as mock_recovery:
            # Mock the recovery execution to call our callback
            async def mock_recovery_execution(context, callback):
                return await callback(context)

            mock_recovery.side_effect = mock_recovery_execution

            result = await self.orchestrator._execute_recovery_action(
                request, interactive_context, attempted_approaches, {}
            )

            assert result.success is False
            assert "No remaining approaches" in result.error_message
            assert result.result_data.get('no_approaches_left') is True

    @pytest.mark.asyncio
    async def test_execute_recovery_action_show_browser(self):
        """Test executing show browser recovery action"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button",
            show_browser=False
        )

        interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.6,
                execution_time=2.0,
                result_data={},
                error_message="Element not found"
            ),
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS],
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=RecoveryAction.SHOW_BROWSER
        )

        with patch.object(self.orchestrator, '_execute_approach_directly') as mock_execute:
            with patch.object(self.orchestrator.interactive_error_handler, 'execute_recovery_action') as mock_recovery:
                # Mock the recovery execution to call our callback
                async def mock_recovery_execution(context, callback):
                    return await callback(context)

                mock_recovery.side_effect = mock_recovery_execution

                # Mock successful execution with browser shown
                browser_result = ActionResult(
                    success=True,
                    approach_used=AutomationApproach.DOM_ANALYSIS,
                    confidence=0.8,
                    execution_time=2.5,
                    result_data={'browser_shown': True}
                )
                mock_execute.return_value = browser_result

                result = await self.orchestrator._execute_recovery_action(
                    request, interactive_context, [AutomationApproach.DOM_ANALYSIS], {}
                )

                assert result.success is True
                # Check that show_browser was enabled in the debug request
                call_args = mock_execute.call_args[0]
                debug_request = call_args[0]
                assert debug_request.show_browser is True

    @pytest.mark.asyncio
    async def test_execute_recovery_action_modify_task(self):
        """Test executing modify task recovery action"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button"
        )

        interactive_context = InteractiveErrorContext(
            original_error=ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            action_result=ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.6,
                execution_time=2.0,
                result_data={},
                error_message="Element not found"
            ),
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS],
            task_description="Click submit button",
            url="https://example.com",
            recovery_options=[],
            llm_analysis="Test analysis",
            user_choice=RecoveryAction.MODIFY_TASK,
            additional_input="Try clicking the 'Submit Form' button instead"
        )

        with patch.object(self.orchestrator.interactive_error_handler, 'execute_recovery_action') as mock_recovery:
            # Mock the recovery execution to call our callback
            async def mock_recovery_execution(context, callback):
                return await callback(context)

            mock_recovery.side_effect = mock_recovery_execution

            result = await self.orchestrator._execute_recovery_action(
                request, interactive_context, [AutomationApproach.DOM_ANALYSIS], {}
            )

            assert result.success is False
            assert "Task modification required" in result.error_message
            assert result.result_data.get('task_modification_required') is True
            assert result.result_data.get('suggested_modification') == "Try clicking the 'Submit Form' button instead"
            assert "User suggested task modification" in result.recommendation

    def test_enhanced_analytics_with_interactive_data(self):
        """Test enhanced analytics include interactive error handling data"""
        # Add some mock execution records with recovery data
        self.orchestrator.execution_history = [
            {
                'timestamp': 1234567890,
                'url': 'https://example.com',
                'approach_used': 'dom_analysis',
                'success': False,
                'interactive_enabled': True,
                'recovery_attempted': True,
                'recovery_action': 'try_different',
                'recovery_successful': False
            },
            {
                'timestamp': 1234567891,
                'url': 'https://example.com',
                'approach_used': 'stagehand',
                'success': True,
                'interactive_enabled': True,
                'recovery_attempted': True,
                'recovery_action': 'try_different',
                'recovery_successful': True
            },
            {
                'timestamp': 1234567892,
                'url': 'https://example.com',
                'approach_used': 'dom_analysis',
                'success': True,
                'interactive_enabled': False,
                'recovery_attempted': False,
                'recovery_action': None,
                'recovery_successful': None
            }
        ]

        with patch.object(self.orchestrator.base_orchestrator, 'get_decision_analytics') as mock_base:
            with patch.object(self.orchestrator.stagehand_integration, 'get_execution_analytics') as mock_stagehand:
                with patch.object(self.orchestrator.vision_integration, 'get_execution_analytics') as mock_vision:
                    with patch.object(self.orchestrator.unified_error_handler, 'get_error_analytics') as mock_error:
                        mock_base.return_value = {}
                        mock_stagehand.return_value = {}
                        mock_vision.return_value = {}
                        mock_error.return_value = {}

                        analytics = self.orchestrator.get_enhanced_analytics()

                        enhanced_data = analytics['enhanced_orchestrator']

                        assert enhanced_data['total_executions'] == 3
                        assert enhanced_data['interactive_mode_enabled'] is False

                        # Check interactive recovery stats
                        recovery_stats = enhanced_data['interactive_recovery_stats']
                        assert recovery_stats['total_interactive_recoveries'] == 2
                        assert recovery_stats['successful_recoveries'] == 1
                        assert recovery_stats['recovery_success_rate'] == 0.5

                        # Check recovery by action
                        assert 'try_different' in recovery_stats['recovery_by_action']
                        try_different_stats = recovery_stats['recovery_by_action']['try_different']
                        assert try_different_stats['total'] == 2
                        assert try_different_stats['successful'] == 1
                        assert try_different_stats['success_rate'] == 0.5

    @pytest.mark.asyncio
    async def test_execute_with_approach_interactive_disabled(self):
        """Test approach execution without interactive error handling"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button",
            enable_interactive_error_handling=False
        )

        dom_analysis_result = {'confidence': 0.8}

        # Mock failed DOM execution
        with patch.object(self.orchestrator, '_execute_dom_approach') as mock_dom:
            failed_result = ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.6,
                execution_time=2.0,
                result_data={},
                error_message="Element not found"
            )
            mock_dom.return_value = failed_result

            result = await self.orchestrator._execute_with_approach(
                request, AutomationApproach.DOM_ANALYSIS, DecisionContext(0.8, "simple", 5, 1, []), dom_analysis_result
            )

            # Should return the failed result without interactive recovery
            assert result == failed_result
            assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_with_approach_interactive_enabled(self):
        """Test approach execution with interactive error handling"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click submit button",
            action_type="click",
            target_description="submit button",
            enable_interactive_error_handling=True
        )

        dom_analysis_result = {'confidence': 0.8}

        # Mock failed DOM execution
        failed_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        # Mock successful recovery
        recovery_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.8,
            execution_time=3.0,
            result_data={'recovered': True}
        )

        with patch.object(self.orchestrator, '_execute_dom_approach') as mock_dom:
            with patch.object(self.orchestrator, '_handle_interactive_error_recovery') as mock_recovery:
                mock_dom.return_value = failed_result
                mock_recovery.return_value = recovery_result

                result = await self.orchestrator._execute_with_approach(
                    request, AutomationApproach.DOM_ANALYSIS, DecisionContext(0.8, "simple", 5, 1, []), dom_analysis_result
                )

                # Should return the recovery result
                assert result == recovery_result
                assert result.success is True
                mock_recovery.assert_called_once()


class TestGlobalEnhancedOrchestrator:
    """Test global enhanced automation orchestrator instance"""

    def test_global_instance_exists(self):
        """Test that global instance exists"""
        assert enhanced_automation_orchestrator is not None
        assert isinstance(enhanced_automation_orchestrator, EnhancedAutomationOrchestrator)

    def test_global_instance_has_interactive_components(self):
        """Test global instance includes interactive error handling"""
        assert enhanced_automation_orchestrator.unified_error_handler is not None
        assert enhanced_automation_orchestrator.interactive_error_handler is not None
        assert enhanced_automation_orchestrator.interactive_mode is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])