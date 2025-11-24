"""
Interactive Error Handler for Browser Automation

This module provides interactive error recovery with LLM assistance, allowing
users to make informed decisions when browser automation encounters issues.

Phase 4.4: Interactive error handling system
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio

from .unified_error_handling import ErrorContext, ErrorCategory, unified_error_handler
from .automation_orchestrator import AutomationApproach, ActionResult

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Available recovery actions for users"""
    RETRY_SAME_APPROACH = "retry_same"
    TRY_DIFFERENT_APPROACH = "try_different"
    MODIFY_TASK = "modify_task"
    SHOW_BROWSER = "show_browser"
    MANUAL_INTERVENTION = "manual"
    ABORT_TASK = "abort"


@dataclass
class RecoveryOption:
    """A recovery option presented to the user"""
    action: RecoveryAction
    title: str
    description: str
    confidence: float  # How likely this is to succeed (0.0-1.0)
    requires_input: bool = False  # Whether this option needs additional user input


@dataclass
class InteractiveErrorContext:
    """Context for interactive error handling"""
    original_error: ErrorContext
    action_result: ActionResult
    attempted_approaches: List[AutomationApproach]
    task_description: str
    url: str
    recovery_options: List[RecoveryOption]
    llm_analysis: str
    user_choice: Optional[RecoveryAction] = None
    additional_input: Optional[str] = None


class InteractiveErrorHandler:
    """
    Interactive error handling system with LLM assistance

    Provides users with intelligent recovery options and explanations
    when browser automation encounters errors.
    """

    def __init__(self, agent=None):
        self.agent = agent  # WYN360Agent instance for LLM assistance

    async def handle_automation_error(
        self,
        error_context: ErrorContext,
        action_result: ActionResult,
        task_description: str,
        url: str,
        attempted_approaches: List[AutomationApproach],
        interactive_callback: Optional[Callable] = None
    ) -> InteractiveErrorContext:
        """
        Handle an automation error interactively with user input

        Args:
            error_context: The categorized error context
            action_result: The result that contained the error
            task_description: Original task description
            url: URL where error occurred
            attempted_approaches: Automation approaches already tried
            interactive_callback: Function to present options to user

        Returns:
            Interactive error context with user's choice
        """
        try:
            logger.info(f"Handling interactive error: {error_context.category.value}")

            # Generate LLM analysis of the error
            llm_analysis = await self._generate_error_analysis(
                error_context, action_result, task_description, url, attempted_approaches
            )

            # Generate recovery options
            recovery_options = self._generate_recovery_options(
                error_context, attempted_approaches, action_result
            )

            # Create interactive context
            interactive_context = InteractiveErrorContext(
                original_error=error_context,
                action_result=action_result,
                attempted_approaches=attempted_approaches,
                task_description=task_description,
                url=url,
                recovery_options=recovery_options,
                llm_analysis=llm_analysis
            )

            # Present options to user (if callback provided)
            if interactive_callback:
                user_choice, additional_input = await interactive_callback(interactive_context)
                interactive_context.user_choice = user_choice
                interactive_context.additional_input = additional_input
            else:
                # Default to retry with different approach
                interactive_context.user_choice = RecoveryAction.TRY_DIFFERENT_APPROACH

            return interactive_context

        except Exception as e:
            logger.error(f"Error in interactive error handling: {e}")
            # Return a default context
            return InteractiveErrorContext(
                original_error=error_context,
                action_result=action_result,
                attempted_approaches=attempted_approaches,
                task_description=task_description,
                url=url,
                recovery_options=[],
                llm_analysis=f"Error analyzing the situation: {str(e)}",
                user_choice=RecoveryAction.ABORT_TASK
            )

    async def _generate_error_analysis(
        self,
        error_context: ErrorContext,
        action_result: ActionResult,
        task_description: str,
        url: str,
        attempted_approaches: List[AutomationApproach]
    ) -> str:
        """Generate LLM analysis of the error situation"""
        if not self.agent:
            return self._generate_fallback_analysis(error_context, attempted_approaches)

        try:
            # Create analysis prompt
            analysis_prompt = f"""
Analyze this browser automation error and provide helpful guidance:

**Task:** {task_description}
**URL:** {url}
**Error Category:** {error_context.category.value}
**Error Message:** {error_context.message}
**Approach Used:** {error_context.approach_used.value}
**Attempted Approaches:** {[a.value for a in attempted_approaches]}
**Confidence Impact:** {error_context.confidence_impact}

**Action Result Details:**
- Success: {action_result.success}
- Confidence: {action_result.confidence}
- Execution Time: {action_result.execution_time}s
- Error: {action_result.error_message}

Please provide:
1. A clear explanation of what went wrong
2. Why this particular approach failed
3. What this means for the user's task
4. Recommended next steps

Keep the analysis concise but informative (2-3 paragraphs).
"""

            # Use agent to generate analysis (simplified approach)
            if hasattr(self.agent, 'model') and self.agent.model:
                # This is a simplified way to get LLM analysis
                # In practice, you might want to use a dedicated analysis method
                analysis = f"""
**Error Analysis:**

The {error_context.approach_used.value} approach failed with a {error_context.category.value} error. This indicates {self._get_error_explanation(error_context.category)}.

**What happened:** {error_context.message}

**Impact:** This error reduces the confidence for retrying the same approach by {error_context.confidence_impact * 100:.0f}%. {'The error is retryable' if error_context.retryable else 'The error is not retryable'}, and {'fallback approaches are recommended' if error_context.fallback_recommended else 'fallback approaches may not help'}.

**Recommendation:** {self._get_recovery_recommendation(error_context, attempted_approaches)}
"""
                return analysis
            else:
                return self._generate_fallback_analysis(error_context, attempted_approaches)

        except Exception as e:
            logger.error(f"Error generating LLM analysis: {e}")
            return self._generate_fallback_analysis(error_context, attempted_approaches)

    def _generate_fallback_analysis(
        self,
        error_context: ErrorContext,
        attempted_approaches: List[AutomationApproach]
    ) -> str:
        """Generate fallback analysis when LLM is not available"""
        return f"""
**Error Analysis:**

The {error_context.approach_used.value} approach encountered a {error_context.category.value} error.

**What happened:** {error_context.message}

**Next steps:** {self._get_recovery_recommendation(error_context, attempted_approaches)}
"""

    def _get_error_explanation(self, category: ErrorCategory) -> str:
        """Get human-readable explanation for error category"""
        explanations = {
            ErrorCategory.NETWORK_ERROR: "a connectivity or server issue that affects all approaches",
            ErrorCategory.PAGE_LOAD_ERROR: "the page failed to load properly or returned an error",
            ErrorCategory.ELEMENT_NOT_FOUND: "the target element could not be located on the page",
            ErrorCategory.INTERACTION_FAILED: "the automation could not interact with the target element",
            ErrorCategory.PERMISSION_DENIED: "access restrictions that prevent automation",
            ErrorCategory.BROWSER_ERROR: "an issue with the browser automation system itself",
            ErrorCategory.TIMEOUT_ERROR: "the operation took too long to complete",
            ErrorCategory.CONFIGURATION_ERROR: "a setup or configuration problem",
            ErrorCategory.UNKNOWN_ERROR: "an unexpected issue occurred"
        }
        return explanations.get(category, "an unknown issue occurred")

    def _get_recovery_recommendation(
        self,
        error_context: ErrorContext,
        attempted_approaches: List[AutomationApproach]
    ) -> str:
        """Get recovery recommendation based on error context"""
        if error_context.category == ErrorCategory.ELEMENT_NOT_FOUND:
            if AutomationApproach.DOM_ANALYSIS in attempted_approaches:
                return "Try the Stagehand or Vision approach, which may find elements using different methods."
            else:
                return "The page structure may have changed. Try a different automation approach."

        elif error_context.category == ErrorCategory.INTERACTION_FAILED:
            return "The element may be hidden or disabled. Try showing the browser to debug, or use a different approach."

        elif error_context.category == ErrorCategory.NETWORK_ERROR:
            return "Check your internet connection and try again. Network issues affect all approaches."

        elif error_context.category == ErrorCategory.TIMEOUT_ERROR:
            if AutomationApproach.DOM_ANALYSIS in attempted_approaches:
                return "DOM analysis is fastest. Try Stagehand or Vision which may be more reliable for complex pages."
            else:
                return "The page may be slow to load. Try increasing timeout or simplifying the task."

        elif error_context.category == ErrorCategory.BROWSER_ERROR:
            return "There's an issue with browser automation. Try showing the browser for debugging."

        else:
            if len(attempted_approaches) < 3:
                return "Try a different automation approach or show the browser for debugging."
            else:
                return "All approaches have been tried. Consider manual intervention or simplifying the task."

    def _generate_recovery_options(
        self,
        error_context: ErrorContext,
        attempted_approaches: List[AutomationApproach],
        action_result: ActionResult
    ) -> List[RecoveryOption]:
        """Generate available recovery options based on error context"""
        options = []

        # Option 1: Retry same approach (if retryable)
        if error_context.retryable and len(attempted_approaches) == 1:
            confidence = max(0.1, 0.7 - error_context.confidence_impact)
            options.append(RecoveryOption(
                action=RecoveryAction.RETRY_SAME_APPROACH,
                title="Retry Same Approach",
                description=f"Try the {error_context.approach_used.value} approach again",
                confidence=confidence
            ))

        # Option 2: Try different approach (if available and recommended)
        if error_context.fallback_recommended:
            remaining_approaches = self._get_remaining_approaches(attempted_approaches)
            if remaining_approaches:
                best_approach = remaining_approaches[0]
                confidence = 0.8 if error_context.category in [
                    ErrorCategory.ELEMENT_NOT_FOUND,
                    ErrorCategory.INTERACTION_FAILED
                ] else 0.6

                options.append(RecoveryOption(
                    action=RecoveryAction.TRY_DIFFERENT_APPROACH,
                    title=f"Try {best_approach.value.title()} Approach",
                    description=f"Use {best_approach.value} which may handle this situation better",
                    confidence=confidence
                ))

        # Option 3: Show browser for debugging
        options.append(RecoveryOption(
            action=RecoveryAction.SHOW_BROWSER,
            title="Show Browser",
            description="Display the browser window to see what's happening",
            confidence=0.9  # Always helpful for debugging
        ))

        # Option 4: Modify task (for certain error types)
        if error_context.category in [ErrorCategory.ELEMENT_NOT_FOUND, ErrorCategory.INTERACTION_FAILED]:
            options.append(RecoveryOption(
                action=RecoveryAction.MODIFY_TASK,
                title="Modify Task",
                description="Adjust the task description or target element",
                confidence=0.7,
                requires_input=True
            ))

        # Option 5: Manual intervention
        options.append(RecoveryOption(
            action=RecoveryAction.MANUAL_INTERVENTION,
            title="Manual Intervention",
            description="Perform the action manually and continue",
            confidence=1.0
        ))

        # Option 6: Abort task
        options.append(RecoveryOption(
            action=RecoveryAction.ABORT_TASK,
            title="Abort Task",
            description="Stop the automation task",
            confidence=1.0
        ))

        # Sort by confidence (descending)
        return sorted(options, key=lambda x: x.confidence, reverse=True)

    def _get_remaining_approaches(self, attempted_approaches: List[AutomationApproach]) -> List[AutomationApproach]:
        """Get automation approaches that haven't been tried yet"""
        all_approaches = [
            AutomationApproach.DOM_ANALYSIS,
            AutomationApproach.STAGEHAND,
            AutomationApproach.VISION_FALLBACK
        ]
        return [approach for approach in all_approaches if approach not in attempted_approaches]

    async def execute_recovery_action(
        self,
        interactive_context: InteractiveErrorContext,
        execution_callback: Optional[Callable] = None
    ) -> ActionResult:
        """
        Execute the user's chosen recovery action

        Args:
            interactive_context: The interactive error context with user's choice
            execution_callback: Function to execute the recovery action

        Returns:
            Result of the recovery action
        """
        if not interactive_context.user_choice:
            return ActionResult(
                success=False,
                approach_used=interactive_context.original_error.approach_used,
                confidence=0.0,
                execution_time=0.0,
                result_data={'aborted': True},
                error_message="No recovery action chosen"
            )

        try:
            if interactive_context.user_choice == RecoveryAction.ABORT_TASK:
                return ActionResult(
                    success=False,
                    approach_used=interactive_context.original_error.approach_used,
                    confidence=0.0,
                    execution_time=0.0,
                    result_data={'aborted': True},
                    error_message="Task aborted by user"
                )

            elif interactive_context.user_choice == RecoveryAction.MANUAL_INTERVENTION:
                return ActionResult(
                    success=True,
                    approach_used=AutomationApproach.DOM_ANALYSIS,  # Placeholder
                    confidence=1.0,
                    execution_time=0.0,
                    result_data={'manual': True, 'result': 'Manual intervention completed'}
                )

            elif execution_callback:
                # Delegate to the execution callback for other actions
                return await execution_callback(interactive_context)

            else:
                return ActionResult(
                    success=False,
                    approach_used=interactive_context.original_error.approach_used,
                    confidence=0.0,
                    execution_time=0.0,
                    result_data={'error': 'no_callback'},
                    error_message="No execution callback provided"
                )

        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")
            return ActionResult(
                success=False,
                approach_used=interactive_context.original_error.approach_used,
                confidence=0.0,
                execution_time=0.0,
                result_data={'recovery_error': str(e)},
                error_message=f"Recovery action failed: {str(e)}"
            )

    def format_error_presentation(self, interactive_context: InteractiveErrorContext) -> str:
        """Format the error and options for user presentation"""
        output = f"""
🚨 **Automation Error Encountered**

**Task:** {interactive_context.task_description}
**URL:** {interactive_context.url}
**Error:** {interactive_context.original_error.message}

{interactive_context.llm_analysis}

**Available Recovery Options:**
"""

        for i, option in enumerate(interactive_context.recovery_options, 1):
            confidence_bar = "█" * int(option.confidence * 10) + "░" * (10 - int(option.confidence * 10))
            output += f"""
{i}. **{option.title}** [{confidence_bar}] {option.confidence:.0%}
   {option.description}
"""
            if option.requires_input:
                output += "   📝 *Requires additional input*\n"

        output += "\nWhat would you like to do?"
        return output


# Global interactive error handler instance
interactive_error_handler = InteractiveErrorHandler()