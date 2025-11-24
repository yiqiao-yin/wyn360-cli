"""
Unit tests for Interactive Error Handling System

Tests the interactive error handling with LLM assistance, recovery options,
and user choice mechanisms for browser automation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.wyn360.tools.browser.interactive_error_handler import (
    InteractiveErrorHandler,
    InteractiveErrorContext,
    RecoveryAction,
    RecoveryOption,
    interactive_error_handler
)
from src.wyn360.tools.browser.unified_error_handling import (
    ErrorContext,
    ErrorCategory,
    unified_error_handler
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionResult
)


class TestRecoveryOption:
    """Test RecoveryOption dataclass"""

    def test_recovery_option_creation(self):
        """Test creating a recovery option"""
        option = RecoveryOption(
            action=RecoveryAction.RETRY_SAME_APPROACH,
            title="Retry",
            description="Try again with same approach",
            confidence=0.7,
            requires_input=False
        )

        assert option.action == RecoveryAction.RETRY_SAME_APPROACH
        assert option.title == "Retry"
        assert option.description == "Try again with same approach"
        assert option.confidence == 0.7
        assert option.requires_input is False


class TestInteractiveErrorHandler:
    """Test InteractiveErrorHandler functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.handler = InteractiveErrorHandler()
        self.mock_agent = Mock()
        self.mock_agent.model = Mock()
        self.handler.agent = self.mock_agent

    def test_initialization(self):
        """Test handler initialization"""
        handler = InteractiveErrorHandler()
        assert handler.agent is None

        handler_with_agent = InteractiveErrorHandler(self.mock_agent)
        assert handler_with_agent.agent == self.mock_agent

    def test_error_explanation_generation(self):
        """Test error category explanations"""
        explanations = {
            ErrorCategory.NETWORK_ERROR: "a connectivity or server issue",
            ErrorCategory.ELEMENT_NOT_FOUND: "the target element could not be located",
            ErrorCategory.BROWSER_ERROR: "an issue with the browser automation system",
            ErrorCategory.UNKNOWN_ERROR: "an unexpected issue occurred"  # Fixed to match actual text
        }

        for category, expected_text in explanations.items():
            explanation = self.handler._get_error_explanation(category)
            assert expected_text in explanation

    def test_recovery_recommendation_generation(self):
        """Test recovery recommendations for different error categories"""
        attempted_approaches = [AutomationApproach.DOM_ANALYSIS]

        # Element not found with DOM attempted
        recommendation = self.handler._get_recovery_recommendation(
            ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message="Element not found",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.3
            ),
            attempted_approaches
        )
        assert "Stagehand or Vision approach" in recommendation

        # Network error
        recommendation = self.handler._get_recovery_recommendation(
            ErrorContext(
                category=ErrorCategory.NETWORK_ERROR,
                message="Network timeout",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=False,
                confidence_impact=0.1
            ),
            []
        )
        assert "internet connection" in recommendation  # Fixed to match actual text

        # Timeout with DOM attempted
        recommendation = self.handler._get_recovery_recommendation(
            ErrorContext(
                category=ErrorCategory.TIMEOUT_ERROR,
                message="Operation timed out",
                approach_used=AutomationApproach.DOM_ANALYSIS,
                retryable=True,
                fallback_recommended=True,
                confidence_impact=0.2
            ),
            attempted_approaches
        )
        assert "Stagehand or Vision" in recommendation

    def test_recovery_options_generation_retryable_error(self):
        """Test recovery options for retryable errors"""
        error_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element not found",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        attempted_approaches = [AutomationApproach.DOM_ANALYSIS]
        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        options = self.handler._generate_recovery_options(
            error_context, attempted_approaches, action_result
        )

        # Should have multiple options
        assert len(options) >= 4

        # Check for expected options
        option_actions = [opt.action for opt in options]
        assert RecoveryAction.TRY_DIFFERENT_APPROACH in option_actions
        assert RecoveryAction.SHOW_BROWSER in option_actions
        assert RecoveryAction.MODIFY_TASK in option_actions
        assert RecoveryAction.MANUAL_INTERVENTION in option_actions
        assert RecoveryAction.ABORT_TASK in option_actions

        # Options should be sorted by confidence (descending)
        confidences = [opt.confidence for opt in options]
        assert confidences == sorted(confidences, reverse=True)

    def test_recovery_options_generation_non_retryable_error(self):
        """Test recovery options for non-retryable errors"""
        error_context = ErrorContext(
            category=ErrorCategory.PERMISSION_DENIED,
            message="Access denied",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=False,
            fallback_recommended=False,
            confidence_impact=0.5
        )

        attempted_approaches = [AutomationApproach.DOM_ANALYSIS]
        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Access denied"
        )

        options = self.handler._generate_recovery_options(
            error_context, attempted_approaches, action_result
        )

        # Should not include retry same approach
        option_actions = [opt.action for opt in options]
        assert RecoveryAction.RETRY_SAME_APPROACH not in option_actions

        # Should still have basic options
        assert RecoveryAction.SHOW_BROWSER in option_actions
        assert RecoveryAction.MANUAL_INTERVENTION in option_actions
        assert RecoveryAction.ABORT_TASK in option_actions

    def test_remaining_approaches_calculation(self):
        """Test getting remaining automation approaches"""
        attempted = [AutomationApproach.DOM_ANALYSIS]
        remaining = self.handler._get_remaining_approaches(attempted)

        assert AutomationApproach.DOM_ANALYSIS not in remaining
        assert AutomationApproach.STAGEHAND in remaining
        assert AutomationApproach.VISION_FALLBACK in remaining
        assert len(remaining) == 2

        attempted = [AutomationApproach.DOM_ANALYSIS, AutomationApproach.STAGEHAND]
        remaining = self.handler._get_remaining_approaches(attempted)

        assert len(remaining) == 1
        assert remaining[0] == AutomationApproach.VISION_FALLBACK

    @pytest.mark.asyncio
    async def test_handle_automation_error_without_callback(self):
        """Test handling automation error without interactive callback"""
        error_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element not found",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        attempted_approaches = [AutomationApproach.DOM_ANALYSIS]

        interactive_context = await self.handler.handle_automation_error(
            error_context=error_context,
            action_result=action_result,
            task_description="Click submit button",
            url="https://example.com",
            attempted_approaches=attempted_approaches,
            interactive_callback=None
        )

        # Should default to try different approach
        assert interactive_context.user_choice == RecoveryAction.TRY_DIFFERENT_APPROACH
        assert interactive_context.original_error == error_context
        assert interactive_context.action_result == action_result
        assert interactive_context.task_description == "Click submit button"
        assert interactive_context.url == "https://example.com"
        assert len(interactive_context.recovery_options) > 0

    @pytest.mark.asyncio
    async def test_handle_automation_error_with_callback(self):
        """Test handling automation error with interactive callback"""
        error_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element not found",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        attempted_approaches = [AutomationApproach.DOM_ANALYSIS]

        # Mock callback that chooses to show browser
        async def mock_callback(context):
            return RecoveryAction.SHOW_BROWSER, "Enable browser display"

        interactive_context = await self.handler.handle_automation_error(
            error_context=error_context,
            action_result=action_result,
            task_description="Click submit button",
            url="https://example.com",
            attempted_approaches=attempted_approaches,
            interactive_callback=mock_callback
        )

        # Should use callback choice
        assert interactive_context.user_choice == RecoveryAction.SHOW_BROWSER
        assert interactive_context.additional_input == "Enable browser display"

    @pytest.mark.asyncio
    async def test_generate_llm_analysis_without_agent(self):
        """Test LLM analysis generation without agent"""
        handler = InteractiveErrorHandler()  # No agent

        error_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element not found",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        analysis = await handler._generate_error_analysis(
            error_context=error_context,
            action_result=action_result,
            task_description="Click submit button",
            url="https://example.com",
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS]
        )

        assert "Error Analysis" in analysis
        assert "dom_analysis approach" in analysis
        assert "element_not_found error" in analysis

    @pytest.mark.asyncio
    async def test_generate_llm_analysis_with_agent(self):
        """Test LLM analysis generation with agent"""
        error_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element not found",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        analysis = await self.handler._generate_error_analysis(
            error_context=error_context,
            action_result=action_result,
            task_description="Click submit button",
            url="https://example.com",
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS]
        )

        assert "Error Analysis" in analysis
        assert "dom_analysis approach" in analysis

    @pytest.mark.asyncio
    async def test_execute_recovery_action_abort(self):
        """Test executing abort recovery action"""
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
            user_choice=RecoveryAction.ABORT_TASK
        )

        result = await self.handler.execute_recovery_action(interactive_context)

        assert result.success is False
        assert "aborted by user" in result.error_message
        assert result.result_data.get('aborted') is True

    @pytest.mark.asyncio
    async def test_execute_recovery_action_manual_intervention(self):
        """Test executing manual intervention recovery action"""
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
            user_choice=RecoveryAction.MANUAL_INTERVENTION
        )

        result = await self.handler.execute_recovery_action(interactive_context)

        assert result.success is True
        assert result.confidence == 1.0
        assert result.result_data.get('manual') is True

    @pytest.mark.asyncio
    async def test_execute_recovery_action_with_callback(self):
        """Test executing recovery action with callback"""
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

        # Mock execution callback
        async def mock_execution_callback(context):
            return ActionResult(
                success=True,
                approach_used=AutomationApproach.STAGEHAND,
                confidence=0.8,
                execution_time=3.0,
                result_data={'callback_executed': True, 'result': 'Callback executed successfully'}
            )

        result = await self.handler.execute_recovery_action(
            interactive_context, mock_execution_callback
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.STAGEHAND
        assert result.result_data.get('callback_executed') is True

    @pytest.mark.asyncio
    async def test_execute_recovery_action_no_choice(self):
        """Test executing recovery action without user choice"""
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
            user_choice=None
        )

        result = await self.handler.execute_recovery_action(interactive_context)

        assert result.success is False
        assert "No recovery action chosen" in result.error_message

    def test_format_error_presentation(self):
        """Test formatting error presentation for user"""
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
            recovery_options=[
                RecoveryOption(
                    action=RecoveryAction.TRY_DIFFERENT_APPROACH,
                    title="Try Different Approach",
                    description="Use stagehand which may handle this better",
                    confidence=0.8
                ),
                RecoveryOption(
                    action=RecoveryAction.MODIFY_TASK,
                    title="Modify Task",
                    description="Adjust the task description",
                    confidence=0.7,
                    requires_input=True
                )
            ],
            llm_analysis="The DOM analysis failed because the element structure changed."
        )

        presentation = self.handler.format_error_presentation(interactive_context)

        assert "🚨 **Automation Error Encountered**" in presentation
        assert "Click submit button" in presentation
        assert "https://example.com" in presentation
        assert "Element not found" in presentation
        assert "Try Different Approach" in presentation
        assert "Modify Task" in presentation
        assert "📝 *Requires additional input*" in presentation
        assert "What would you like to do?" in presentation

    @pytest.mark.asyncio
    async def test_handle_automation_error_exception_handling(self):
        """Test error handling in handle_automation_error"""
        # Create handler without agent to trigger fallback path
        handler = InteractiveErrorHandler()

        # Create error context that will trigger an exception
        error_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element not found",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        action_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.6,
            execution_time=2.0,
            result_data={},
            error_message="Element not found"
        )

        # Mock a callback that raises an exception
        async def failing_callback(context):
            raise Exception("Callback failed")

        interactive_context = await handler.handle_automation_error(
            error_context=error_context,
            action_result=action_result,
            task_description="Click submit button",
            url="https://example.com",
            attempted_approaches=[AutomationApproach.DOM_ANALYSIS],
            interactive_callback=failing_callback
        )

        # Should return default abort context on error
        assert interactive_context.user_choice == RecoveryAction.ABORT_TASK
        assert "Error analyzing the situation" in interactive_context.llm_analysis


class TestGlobalInteractiveErrorHandler:
    """Test global interactive error handler instance"""

    def test_global_instance_exists(self):
        """Test that global instance exists"""
        assert interactive_error_handler is not None
        assert isinstance(interactive_error_handler, InteractiveErrorHandler)

    def test_global_instance_initialization(self):
        """Test global instance is properly initialized"""
        assert interactive_error_handler.agent is None  # Should be None until set


if __name__ == "__main__":
    pytest.main([__file__, "-v"])