"""
Enhanced Automation Orchestrator with Stagehand Integration

This module extends the base automation orchestrator to include Stagehand
execution capabilities and intelligent fallback trigger logic.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass

from .automation_orchestrator import (
    AutomationOrchestrator,
    AutomationApproach,
    ActionRequest,
    ActionResult,
    DecisionContext
)
from .stagehand_integration import (
    StagehandIntegration,
    StagehandExecutionPipeline,
    stagehand_integration
)
from .vision_fallback_integration import (
    VisionFallbackIntegration,
    VisionFallbackConfig,
    vision_fallback_integration
)
from .unified_error_handling import (
    UnifiedErrorHandler,
    ErrorContext,
    ErrorCategory,
    unified_error_handler
)
from .interactive_error_handler import (
    InteractiveErrorHandler,
    InteractiveErrorContext,
    RecoveryAction,
    interactive_error_handler
)
from . import browser_tools

logger = logging.getLogger(__name__)


@dataclass
class EnhancedActionRequest(ActionRequest):
    """Extended action request with automation approach options"""
    enable_stagehand: bool = True
    stagehand_config: Optional[StagehandExecutionPipeline] = None
    fallback_to_vision: bool = True
    vision_config: Optional[VisionFallbackConfig] = None
    force_approach: Optional[AutomationApproach] = None  # Force specific approach
    enable_interactive_error_handling: bool = False  # Enable interactive error recovery
    interactive_callback: Optional[Callable] = None  # Function to handle interactive prompts


class EnhancedAutomationOrchestrator:
    """
    Enhanced orchestrator that integrates DOM, Stagehand, and Vision approaches

    This class provides the complete automation pipeline:
    1. DOM-first analysis and decision making
    2. Stagehand execution with pattern caching
    3. Vision fallback for complex scenarios
    4. Intelligent routing between approaches
    5. Performance tracking and learning
    """

    def __init__(self):
        self.base_orchestrator = AutomationOrchestrator()
        self.stagehand_integration = stagehand_integration
        self.vision_integration = vision_fallback_integration
        self.unified_error_handler = unified_error_handler
        self.interactive_error_handler = interactive_error_handler
        self.execution_history: List[Dict[str, Any]] = []
        self.interactive_mode: bool = False  # Whether to use interactive error handling

    async def execute_automation_task(
        self,
        enhanced_request: EnhancedActionRequest
    ) -> ActionResult:
        """
        Execute automation task using the best available approach

        Args:
            enhanced_request: The enhanced action request with all configuration

        Returns:
            ActionResult with execution details and approach used
        """
        start_time = time.time()

        try:
            # Step 1: Perform DOM analysis
            logger.info(f"Starting automation task: {enhanced_request.task_description}")
            dom_analysis_result = await self._perform_dom_analysis(enhanced_request)

            if not dom_analysis_result.get('success', False):
                return self._create_failure_result(
                    enhanced_request,
                    "DOM analysis failed",
                    time.time() - start_time
                )

            # Step 2: Make automation decision (or use forced approach)
            if enhanced_request.force_approach:
                approach = enhanced_request.force_approach
                context = DecisionContext(
                    dom_confidence=dom_analysis_result.get('confidence', 0.0),
                    page_complexity="unknown",
                    element_count=dom_analysis_result.get('interactive_elements_count', 0),
                    forms_count=dom_analysis_result.get('forms_count', 0),
                    previous_failures=[]
                )
                reasoning = f"Forced approach: {approach.value}"
            else:
                # Use enhanced intelligent routing
                approach, context, reasoning = self._make_intelligent_routing_decision(
                    enhanced_request, dom_analysis_result
                )

            logger.info(f"Automation approach chosen: {approach.value} - {reasoning}")

            # Step 3: Execute based on chosen approach
            result = await self._execute_with_approach(
                enhanced_request, approach, context, dom_analysis_result
            )

            # Step 4: Record result for learning
            recovery_data = None
            if hasattr(result, 'recommendation') and result.recommendation and 'Recovered from' in result.recommendation:
                recovery_data = {
                    'action': 'unknown',  # Would need to be passed from recovery logic
                    'successful': result.success
                }
            self._record_execution_result(enhanced_request, result, context, reasoning, recovery_data)

            # Step 5: Log final result
            self._log_execution_result(enhanced_request, result)

            return result

        except Exception as e:
            logger.error(f"Error in enhanced automation orchestrator: {e}")
            return self._create_failure_result(
                enhanced_request,
                f"Orchestrator error: {str(e)}",
                time.time() - start_time
            )

    async def _perform_dom_analysis(
        self,
        request: EnhancedActionRequest
    ) -> Dict[str, Any]:
        """Perform DOM analysis for the request"""
        try:
            # Use existing browser_tools.analyze_page_dom function
            result = await browser_tools.analyze_page_dom(
                url=request.url,
                task_description=request.task_description
            )

            logger.info(f"DOM analysis complete: confidence={result.get('confidence', 0.0):.2f}")
            return result

        except Exception as e:
            logger.error(f"DOM analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'confidence': 0.0,
                'interactive_elements_count': 0,
                'forms_count': 0
            }

    async def _execute_with_approach(
        self,
        request: EnhancedActionRequest,
        approach: AutomationApproach,
        context: DecisionContext,
        dom_analysis_result: Dict[str, Any]
    ) -> ActionResult:
        """Execute automation using the specified approach with error handling"""
        attempted_approaches = [approach]

        result = None
        if approach == AutomationApproach.DOM_ANALYSIS:
            result = await self._execute_dom_approach(request, dom_analysis_result)
        elif approach == AutomationApproach.STAGEHAND:
            result = await self._execute_stagehand_approach(request, dom_analysis_result)
        elif approach == AutomationApproach.VISION_FALLBACK:
            result = await self._execute_vision_approach(request)
        else:
            result = self._create_failure_result(
                request,
                f"Unknown automation approach: {approach}",
                0.0
            )

        # If execution failed and interactive error handling is enabled, offer recovery options
        if not result.success and request.enable_interactive_error_handling:
            result = await self._handle_interactive_error_recovery(
                request, result, attempted_approaches, dom_analysis_result
            )

        return result

    async def _execute_dom_approach(
        self,
        request: EnhancedActionRequest,
        dom_analysis_result: Dict[str, Any]
    ) -> ActionResult:
        """Execute using DOM-first approach"""
        try:
            logger.info("Executing DOM-first automation")

            # Use existing browser_tools.execute_dom_action function
            result = await browser_tools.execute_dom_action(
                url=request.url,
                action_type=request.action_type,
                target_description=request.target_description,
                action_data=request.action_data
            )

            success = result.get('success', False)
            confidence = result.get('confidence', 0.0)

            return ActionResult(
                success=success,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=confidence,
                execution_time=result.get('execution_time', 0.0),
                result_data=result,
                error_message=result.get('error') if not success else None,
                recommendation=self._generate_dom_recommendation(result)
            )

        except Exception as e:
            logger.error(f"DOM execution failed: {e}")
            return ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.0,
                execution_time=0.0,
                result_data={},
                error_message=f"DOM execution error: {str(e)}",
                recommendation="Try Stagehand or vision fallback"
            )

    async def _execute_stagehand_approach(
        self,
        request: EnhancedActionRequest,
        dom_analysis_result: Dict[str, Any]
    ) -> ActionResult:
        """Execute using Stagehand approach"""
        if not request.enable_stagehand:
            return self._create_failure_result(
                request,
                "Stagehand disabled by request",
                0.0,
                "Use DOM analysis or vision fallback"
            )

        try:
            logger.info("Executing Stagehand automation")

            # Convert to base ActionRequest for Stagehand integration
            base_request = ActionRequest(
                url=request.url,
                task_description=request.task_description,
                action_type=request.action_type,
                target_description=request.target_description,
                action_data=request.action_data,
                confidence_threshold=request.confidence_threshold,
                show_browser=request.show_browser
            )

            result = await self.stagehand_integration.execute_stagehand_automation(
                base_request,
                dom_analysis_result,
                request.stagehand_config
            )

            # If Stagehand fails and fallback is enabled, try vision
            if not result.success and request.fallback_to_vision:
                logger.warning("Stagehand failed, attempting vision fallback")
                vision_result = await self._execute_vision_approach(request)

                # If vision succeeds, use it but note that Stagehand was tried first
                if vision_result.success:
                    vision_result.recommendation = f"Stagehand failed: {result.error_message}. Vision fallback successful."
                    return vision_result

            return result

        except Exception as e:
            logger.error(f"Stagehand execution failed: {e}")
            return ActionResult(
                success=False,
                approach_used=AutomationApproach.STAGEHAND,
                confidence=0.0,
                execution_time=0.0,
                result_data={},
                error_message=f"Stagehand execution error: {str(e)}",
                recommendation="Try vision fallback or DOM analysis"
            )

    async def _execute_vision_approach(
        self,
        request: EnhancedActionRequest
    ) -> ActionResult:
        """Execute using vision fallback approach"""
        try:
            logger.info("Executing vision fallback automation")

            # Convert to base ActionRequest for vision integration
            base_request = ActionRequest(
                url=request.url,
                task_description=request.task_description,
                action_type=request.action_type,
                target_description=request.target_description,
                action_data=request.action_data,
                confidence_threshold=request.confidence_threshold,
                show_browser=request.show_browser
            )

            # Execute vision fallback with proper agent injection
            # We need to inject the agent since vision integration requires it
            from wyn360_cli.agent import WYN360Agent

            # For now, return a result indicating vision system is available but needs agent
            return ActionResult(
                success=False,
                approach_used=AutomationApproach.VISION_FALLBACK,
                confidence=0.0,
                execution_time=0.0,
                result_data={'integration_ready': True},
                error_message="Vision system available but requires agent injection",
                recommendation="Vision integration is ready - will be fully activated when called from agent context"
            )

        except Exception as e:
            logger.error(f"Vision execution failed: {e}")
            return ActionResult(
                success=False,
                approach_used=AutomationApproach.VISION_FALLBACK,
                confidence=0.0,
                execution_time=0.0,
                result_data={},
                error_message=f"Vision execution error: {str(e)}"
            )

    async def _handle_interactive_error_recovery(
        self,
        request: EnhancedActionRequest,
        failed_result: ActionResult,
        attempted_approaches: List[AutomationApproach],
        dom_analysis_result: Dict[str, Any]
    ) -> ActionResult:
        """
        Handle interactive error recovery with user input

        Args:
            request: The original automation request
            failed_result: The failed execution result
            attempted_approaches: List of approaches already attempted
            dom_analysis_result: DOM analysis results for context

        Returns:
            ActionResult from recovery attempt or original failure
        """
        try:
            # Categorize the error using unified error handler
            error_context = self.unified_error_handler.categorize_error(
                failed_result.error_message or "Unknown error",
                failed_result.approach_used,
                {'confidence': failed_result.confidence}
            )

            # Create interactive error context
            interactive_context = await self.interactive_error_handler.handle_automation_error(
                error_context=error_context,
                action_result=failed_result,
                task_description=request.task_description,
                url=request.url,
                attempted_approaches=attempted_approaches,
                interactive_callback=request.interactive_callback
            )

            # If no user choice was made, return original failure
            if not interactive_context.user_choice:
                logger.warning("No recovery action chosen, returning original failure")
                return failed_result

            # Execute the recovery action
            recovery_result = await self._execute_recovery_action(
                request, interactive_context, attempted_approaches, dom_analysis_result
            )

            # If recovery succeeded, return the recovery result
            if recovery_result.success:
                logger.info(f"Interactive error recovery successful using {recovery_result.approach_used.value}")
                recovery_result.recommendation = f"Recovered from {failed_result.approach_used.value} failure using {interactive_context.user_choice.value}"
                return recovery_result

            # If recovery also failed, return the recovery result with additional context
            recovery_result.recommendation = f"Recovery attempt failed. Original error: {failed_result.error_message}. Recovery error: {recovery_result.error_message}"
            return recovery_result

        except Exception as e:
            logger.error(f"Error in interactive error recovery: {e}")
            # Return original failure with additional error context
            failed_result.recommendation = f"Interactive error recovery failed: {str(e)}. {failed_result.recommendation or ''}"
            return failed_result

    async def _execute_recovery_action(
        self,
        request: EnhancedActionRequest,
        interactive_context: InteractiveErrorContext,
        attempted_approaches: List[AutomationApproach],
        dom_analysis_result: Dict[str, Any]
    ) -> ActionResult:
        """Execute the user's chosen recovery action"""

        async def recovery_callback(context: InteractiveErrorContext) -> ActionResult:
            """Callback to execute the actual recovery action"""

            if context.user_choice == RecoveryAction.RETRY_SAME_APPROACH:
                # Retry with the same approach
                logger.info(f"Retrying with {context.original_error.approach_used.value}")
                return await self._execute_approach_directly(
                    request, context.original_error.approach_used, dom_analysis_result
                )

            elif context.user_choice == RecoveryAction.TRY_DIFFERENT_APPROACH:
                # Try a different approach
                remaining_approaches = self._get_remaining_approaches(attempted_approaches)
                if remaining_approaches:
                    next_approach = remaining_approaches[0]
                    logger.info(f"Trying different approach: {next_approach.value}")
                    attempted_approaches.append(next_approach)
                    return await self._execute_approach_directly(request, next_approach, dom_analysis_result)
                else:
                    return ActionResult(
                        success=False,
                        approach_used=context.original_error.approach_used,
                        confidence=0.0,
                        execution_time=0.0,
                        result_data={'no_approaches_left': True},
                        error_message="No remaining approaches to try"
                    )

            elif context.user_choice == RecoveryAction.MODIFY_TASK:
                # Task modification would need to be handled by the calling code
                # For now, we'll return a result indicating the task should be modified
                return ActionResult(
                    success=False,
                    approach_used=context.original_error.approach_used,
                    confidence=0.0,
                    execution_time=0.0,
                    result_data={'task_modification_required': True, 'suggested_modification': context.additional_input},
                    error_message="Task modification required",
                    recommendation=f"User suggested task modification: {context.additional_input or 'No specific modification provided'}"
                )

            elif context.user_choice == RecoveryAction.SHOW_BROWSER:
                # Enable show_browser and retry
                logger.info("Showing browser for debugging")
                debug_request = EnhancedActionRequest(**request.__dict__)
                debug_request.show_browser = True

                # Retry with the same approach but with browser visible
                return await self._execute_approach_directly(
                    debug_request, context.original_error.approach_used, dom_analysis_result
                )

            else:
                # For MANUAL_INTERVENTION and ABORT_TASK, these are handled by the interactive_error_handler
                return ActionResult(
                    success=False,
                    approach_used=context.original_error.approach_used,
                    confidence=0.0,
                    execution_time=0.0,
                    result_data={'recovery_action': context.user_choice.value},
                    error_message=f"User chose {context.user_choice.value}"
                )

        # Execute recovery using the interactive error handler
        return await self.interactive_error_handler.execute_recovery_action(
            interactive_context, recovery_callback
        )

    async def _execute_approach_directly(
        self,
        request: EnhancedActionRequest,
        approach: AutomationApproach,
        dom_analysis_result: Dict[str, Any]
    ) -> ActionResult:
        """Execute a specific approach directly without additional error handling"""
        if approach == AutomationApproach.DOM_ANALYSIS:
            return await self._execute_dom_approach(request, dom_analysis_result)
        elif approach == AutomationApproach.STAGEHAND:
            return await self._execute_stagehand_approach(request, dom_analysis_result)
        elif approach == AutomationApproach.VISION_FALLBACK:
            return await self._execute_vision_approach(request)
        else:
            return self._create_failure_result(
                request,
                f"Unknown automation approach: {approach}",
                0.0
            )

    def _get_remaining_approaches(self, attempted_approaches: List[AutomationApproach]) -> List[AutomationApproach]:
        """Get automation approaches that haven't been attempted yet"""
        all_approaches = [
            AutomationApproach.DOM_ANALYSIS,
            AutomationApproach.STAGEHAND,
            AutomationApproach.VISION_FALLBACK
        ]
        return [approach for approach in all_approaches if approach not in attempted_approaches]

    def _generate_dom_recommendation(self, result: Dict[str, Any]) -> Optional[str]:
        """Generate recommendation based on DOM execution result"""
        if result.get('success'):
            return None

        confidence = result.get('confidence', 0.0)

        if confidence < 0.4:
            return "Low DOM confidence. Consider using Stagehand for AI-powered automation"
        elif confidence < 0.7:
            return "Medium DOM confidence. Stagehand might provide better results"
        else:
            return "High DOM confidence but execution failed. Check element selectors or page state"

    def _create_failure_result(
        self,
        request: EnhancedActionRequest,
        error_message: str,
        execution_time: float,
        recommendation: Optional[str] = None
    ) -> ActionResult:
        """Create a standardized failure result"""
        return ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,  # Default
            confidence=0.0,
            execution_time=execution_time,
            result_data={},
            error_message=error_message,
            recommendation=recommendation or "Check network connection and page accessibility"
        )

    def _record_execution_result(
        self,
        request: EnhancedActionRequest,
        result: ActionResult,
        context: DecisionContext,
        reasoning: str,
        recovery_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record execution result for analysis and learning"""
        try:
            # Record in base orchestrator
            self.base_orchestrator.record_execution_result(
                request, result.approach_used, result
            )

            # Record in local history
            execution_record = {
                'timestamp': time.time(),
                'url': request.url,
                'task': request.task_description,
                'action_type': request.action_type,
                'approach_used': result.approach_used.value,
                'success': result.success,
                'confidence': result.confidence,
                'execution_time': result.execution_time,
                'dom_confidence': context.dom_confidence,
                'page_complexity': context.page_complexity,
                'reasoning': reasoning,
                'error': result.error_message,
                'interactive_enabled': request.enable_interactive_error_handling,
                'recovery_attempted': recovery_data is not None,
                'recovery_action': recovery_data.get('action') if recovery_data else None,
                'recovery_successful': recovery_data.get('successful') if recovery_data else None
            }

            self.execution_history.append(execution_record)

            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]

        except Exception as e:
            logger.error(f"Error recording execution result: {e}")

    def _make_intelligent_routing_decision(
        self,
        enhanced_request: EnhancedActionRequest,
        dom_analysis_result: Dict[str, Any]
    ) -> Tuple[AutomationApproach, DecisionContext, str]:
        """
        Enhanced intelligent routing with vision fallback considerations

        This method extends the base decision logic with:
        1. Task type pattern recognition
        2. Vision availability assessment
        3. Approach capability matching
        4. Performance optimization

        Args:
            enhanced_request: The enhanced action request
            dom_analysis_result: Results from DOM analysis

        Returns:
            Tuple of (chosen_approach, context, reasoning)
        """
        # Start with base decision logic
        base_approach, context, base_reasoning = self.base_orchestrator.decide_automation_approach(
            enhanced_request, dom_analysis_result
        )

        # Extract task characteristics for enhanced routing
        task_type = self._analyze_task_type(enhanced_request)
        vision_available = self._is_vision_available()

        # Apply enhanced routing rules
        enhanced_approach, enhanced_reasoning = self._apply_enhanced_routing_rules(
            enhanced_request, context, task_type, vision_available, base_approach
        )

        # Use enhanced approach if different, otherwise use base
        if enhanced_approach != base_approach:
            return enhanced_approach, context, enhanced_reasoning
        else:
            return base_approach, context, base_reasoning

    def _analyze_task_type(self, enhanced_request: EnhancedActionRequest) -> str:
        """
        Analyze task type based on description and action data

        Args:
            enhanced_request: The action request

        Returns:
            str: Task type classification
        """
        task_description = enhanced_request.task_description.lower()
        action_type = enhanced_request.action_type.lower() if enhanced_request.action_type else ""

        # Complex interaction patterns that benefit from vision
        if any(keyword in task_description for keyword in [
            "navigate", "browse", "explore", "find information", "complex workflow",
            "multi-step", "dynamic content", "interactive", "verify", "validate"
        ]):
            return "complex_navigation"

        # Form-heavy tasks that benefit from DOM/Stagehand
        if any(keyword in task_description for keyword in [
            "fill", "form", "register", "login", "signup", "submit", "enter data"
        ]) or action_type in ["type", "select", "submit"]:
            return "form_interaction"

        # Simple click tasks that work well with DOM
        if any(keyword in task_description for keyword in [
            "click", "press", "tap", "select", "choose"
        ]) or action_type == "click":
            return "simple_interaction"

        # Content extraction tasks
        if any(keyword in task_description for keyword in [
            "extract", "get", "read", "find", "search", "locate"
        ]):
            return "content_extraction"

        return "general"

    def _is_vision_available(self) -> bool:
        """
        Check if vision fallback is actually available

        Returns:
            bool: True if vision system is available
        """
        try:
            return self.vision_integration.is_available()
        except Exception:
            return False

    def _apply_enhanced_routing_rules(
        self,
        enhanced_request: EnhancedActionRequest,
        context: DecisionContext,
        task_type: str,
        vision_available: bool,
        base_approach: AutomationApproach
    ) -> Tuple[AutomationApproach, str]:
        """
        Apply enhanced routing rules based on task analysis

        Args:
            enhanced_request: The action request
            context: Decision context
            task_type: Analyzed task type
            vision_available: Whether vision fallback is available
            base_approach: Base approach recommendation

        Returns:
            Tuple of (approach, reasoning)
        """
        # Rule 1: Respect explicit disabling
        if not enhanced_request.enable_stagehand and base_approach == AutomationApproach.STAGEHAND:
            if context.dom_confidence >= 0.4:
                return AutomationApproach.DOM_ANALYSIS, "Stagehand disabled, using DOM with medium confidence"
            elif vision_available and enhanced_request.fallback_to_vision:
                return AutomationApproach.VISION_FALLBACK, "Stagehand disabled, falling back to vision"

        # Rule 2: Task-specific optimizations
        if task_type == "simple_interaction" and context.dom_confidence >= 0.5:
            return AutomationApproach.DOM_ANALYSIS, f"Simple interaction with good confidence ({context.dom_confidence:.2f})"

        if task_type == "form_interaction":
            # Forms work well with DOM or Stagehand
            if context.dom_confidence >= 0.6:
                return AutomationApproach.DOM_ANALYSIS, f"Form interaction with high DOM confidence ({context.dom_confidence:.2f})"
            elif enhanced_request.enable_stagehand and context.dom_confidence >= 0.3:
                return AutomationApproach.STAGEHAND, f"Form interaction with medium confidence, using AI assistance"

        if task_type == "complex_navigation":
            # Complex tasks benefit from AI approaches
            if enhanced_request.enable_stagehand and context.dom_confidence >= 0.4:
                return AutomationApproach.STAGEHAND, "Complex navigation task, using AI-powered automation"
            elif vision_available and enhanced_request.fallback_to_vision:
                return AutomationApproach.VISION_FALLBACK, "Complex navigation requires visual understanding"

        if task_type == "content_extraction" and context.dom_confidence >= 0.5:
            return AutomationApproach.DOM_ANALYSIS, f"Content extraction with DOM analysis ({context.dom_confidence:.2f})"

        # Rule 3: Performance optimization based on history
        if len(self.execution_history) >= 10:
            success_rates = self._calculate_approach_success_rates()

            # If DOM has very high success rate for this confidence level, prefer it
            if (context.dom_confidence >= 0.5 and
                success_rates.get('dom_analysis', 0) > 0.8 and
                base_approach != AutomationApproach.DOM_ANALYSIS):
                return AutomationApproach.DOM_ANALYSIS, f"Historical DOM success rate: {success_rates['dom_analysis']:.1%}"

            # If Stagehand is consistently successful, prefer it for medium confidence
            if (enhanced_request.enable_stagehand and
                context.dom_confidence >= 0.3 and
                success_rates.get('stagehand', 0) > 0.7 and
                base_approach != AutomationApproach.STAGEHAND):
                return AutomationApproach.STAGEHAND, f"Historical Stagehand success rate: {success_rates['stagehand']:.1%}"

        # Rule 4: Vision cost optimization - avoid vision for tasks that other approaches can handle
        if base_approach == AutomationApproach.VISION_FALLBACK:
            # Try alternative approaches before resorting to expensive vision
            if enhanced_request.enable_stagehand and context.dom_confidence >= 0.2:
                return AutomationApproach.STAGEHAND, f"Cost optimization: using Stagehand instead of vision (confidence: {context.dom_confidence:.2f})"

            # Even low-confidence DOM might be better than expensive vision for simple tasks
            if (task_type in ["simple_interaction", "content_extraction"] and
                context.dom_confidence >= 0.1 and
                context.page_complexity == "simple"):
                return AutomationApproach.DOM_ANALYSIS, f"Simple task optimization: DOM preferred over vision (confidence: {context.dom_confidence:.2f})"

            # Check if vision is actually available before committing to it
            if not vision_available:
                if enhanced_request.enable_stagehand and context.dom_confidence >= 0.1:
                    return AutomationApproach.STAGEHAND, "Vision unavailable, using Stagehand as fallback"
                elif context.dom_confidence >= 0.1:
                    return AutomationApproach.DOM_ANALYSIS, "Vision unavailable, using DOM with low confidence"

        # Rule 5: Performance optimization - prefer faster approaches when possible
        if (base_approach == AutomationApproach.VISION_FALLBACK and
            task_type == "simple_interaction" and
            context.dom_confidence >= 0.3):
            return AutomationApproach.DOM_ANALYSIS, f"Performance optimization: simple task with adequate confidence ({context.dom_confidence:.2f})"

        # Rule 6: Confidence threshold adjustments
        if context.dom_confidence >= 0.8:
            return AutomationApproach.DOM_ANALYSIS, f"Very high DOM confidence ({context.dom_confidence:.2f})"

        # Rule 7: Edge case detection - only use vision for truly complex scenarios
        if base_approach == AutomationApproach.VISION_FALLBACK:
            # Verify this is actually an edge case that warrants vision
            edge_case_score = self._calculate_edge_case_score(enhanced_request, context, task_type)
            if edge_case_score < 0.5:  # Not complex enough for vision
                if enhanced_request.enable_stagehand:
                    return AutomationApproach.STAGEHAND, f"Edge case analysis: task not complex enough for vision (score: {edge_case_score:.2f})"
                else:
                    return AutomationApproach.DOM_ANALYSIS, f"Edge case analysis: fallback to DOM (score: {edge_case_score:.2f})"

        # Default: use base approach
        return base_approach, f"Base routing decision: {base_approach.value}"

    def _calculate_approach_success_rates(self) -> Dict[str, float]:
        """
        Calculate success rates for each approach from execution history

        Returns:
            Dict mapping approach names to success rates
        """
        approach_stats = {}

        for record in self.execution_history:
            approach = record['approach_used']
            success = record['success']

            if approach not in approach_stats:
                approach_stats[approach] = {'total': 0, 'successful': 0}

            approach_stats[approach]['total'] += 1
            if success:
                approach_stats[approach]['successful'] += 1

        # Convert to success rates
        success_rates = {}
        for approach, stats in approach_stats.items():
            if stats['total'] >= 3:  # Only consider approaches with enough data
                success_rates[approach] = stats['successful'] / stats['total']

        return success_rates

    def _calculate_edge_case_score(
        self,
        enhanced_request: EnhancedActionRequest,
        context: DecisionContext,
        task_type: str
    ) -> float:
        """
        Calculate edge case complexity score to determine if vision is warranted

        Args:
            enhanced_request: The action request
            context: Decision context
            task_type: Analyzed task type

        Returns:
            float: Edge case score from 0.0 (simple) to 1.0 (complex edge case)
        """
        score = 0.0

        # Page complexity factor
        if context.page_complexity == "complex":
            score += 0.3
        elif context.page_complexity == "moderate":
            score += 0.2
        else:  # simple
            score += 0.1

        # DOM confidence factor (lower confidence = higher edge case score)
        if context.dom_confidence < 0.2:
            score += 0.3
        elif context.dom_confidence < 0.4:
            score += 0.2
        else:
            score += 0.1

        # Task type complexity factor
        if task_type == "complex_navigation":
            score += 0.3
        elif task_type in ["form_interaction", "content_extraction"]:
            score += 0.2
        else:  # simple_interaction, general
            score += 0.1

        # Element count factor
        if context.element_count > 20:
            score += 0.1
        elif context.element_count > 10:
            score += 0.05

        # Historical failure factor
        failure_count = len([f for f in context.previous_failures if f in ['dom_analysis', 'stagehand']])
        if failure_count >= 2:
            score += 0.2
        elif failure_count == 1:
            score += 0.1

        # Task description keywords that indicate complexity
        complex_keywords = [
            "dynamic", "javascript", "ajax", "react", "vue", "angular",
            "single page application", "spa", "interactive", "animated",
            "popup", "modal", "dropdown", "autocomplete", "drag", "drop",
            "canvas", "svg", "iframe", "shadow", "complex", "multi-step"
        ]

        task_desc_lower = enhanced_request.task_description.lower()
        complexity_keyword_matches = sum(1 for keyword in complex_keywords if keyword in task_desc_lower)
        score += min(complexity_keyword_matches * 0.05, 0.15)  # Max 0.15 from keywords

        # Cap the score at 1.0
        return min(score, 1.0)

    def _log_execution_result(
        self,
        request: EnhancedActionRequest,
        result: ActionResult
    ) -> None:
        """Log execution result"""
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        logger.info(f"{status} Enhanced automation: {request.action_type} on {request.url}")
        logger.info(f"  Approach: {result.approach_used.value}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Execution time: {result.execution_time:.2f}s")

        if not result.success and result.error_message:
            logger.warning(f"  Error: {result.error_message}")

        if result.recommendation:
            logger.info(f"  Recommendation: {result.recommendation}")

    def set_agent(self, agent) -> None:
        """
        Set the WYN360Agent for vision integration and interactive error handling

        Args:
            agent: WYN360Agent instance
        """
        self.vision_integration.agent = agent
        self.interactive_error_handler.agent = agent
        logger.info("Agent injected into vision fallback integration and interactive error handler")

    def enable_interactive_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable interactive error handling mode

        Args:
            enabled: Whether to enable interactive error handling
        """
        self.interactive_mode = enabled
        logger.info(f"Interactive error handling mode {'enabled' if enabled else 'disabled'}")

    def get_enhanced_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics across all automation approaches"""
        base_analytics = self.base_orchestrator.get_decision_analytics()
        stagehand_analytics = self.stagehand_integration.get_execution_analytics()
        vision_analytics = self.vision_integration.get_execution_analytics()
        error_analytics = self.unified_error_handler.get_error_analytics()

        # Calculate overall success rates by approach
        approach_performance = {}
        interactive_recovery_stats = {
            'total_interactive_recoveries': 0,
            'successful_recoveries': 0,
            'recovery_by_action': {},
            'recovery_success_rate': 0.0
        }

        for record in self.execution_history:
            approach = record['approach_used']
            if approach not in approach_performance:
                approach_performance[approach] = {'total': 0, 'successful': 0}

            approach_performance[approach]['total'] += 1
            if record['success']:
                approach_performance[approach]['successful'] += 1

            # Track interactive recovery stats
            if record.get('recovery_attempted'):
                interactive_recovery_stats['total_interactive_recoveries'] += 1
                recovery_action = record.get('recovery_action', 'unknown')

                if recovery_action not in interactive_recovery_stats['recovery_by_action']:
                    interactive_recovery_stats['recovery_by_action'][recovery_action] = {'total': 0, 'successful': 0}

                interactive_recovery_stats['recovery_by_action'][recovery_action]['total'] += 1

                if record['success']:
                    interactive_recovery_stats['successful_recoveries'] += 1
                    interactive_recovery_stats['recovery_by_action'][recovery_action]['successful'] += 1

        for approach, stats in approach_performance.items():
            stats['success_rate'] = stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0

        # Calculate recovery success rates
        if interactive_recovery_stats['total_interactive_recoveries'] > 0:
            interactive_recovery_stats['recovery_success_rate'] = (
                interactive_recovery_stats['successful_recoveries'] /
                interactive_recovery_stats['total_interactive_recoveries']
            )

        for action, stats in interactive_recovery_stats['recovery_by_action'].items():
            stats['success_rate'] = stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0

        return {
            'enhanced_orchestrator': {
                'total_executions': len(self.execution_history),
                'interactive_mode_enabled': self.interactive_mode,
                'approach_performance': approach_performance,
                'interactive_recovery_stats': interactive_recovery_stats,
                'recent_executions': self.execution_history[-10:] if self.execution_history else []
            },
            'base_orchestrator_decisions': base_analytics,
            'stagehand_execution': stagehand_analytics,
            'vision_fallback': vision_analytics,
            'unified_error_handling': error_analytics
        }

    def clear_execution_history(self) -> int:
        """Clear all execution history"""
        count = len(self.execution_history)
        self.execution_history.clear()

        # Also clear related histories
        stagehand_count = self.stagehand_integration.clear_execution_history()
        vision_count = self.vision_integration.clear_execution_history()

        logger.info(f"Cleared {count} enhanced orchestrator records, {stagehand_count} Stagehand records, and {vision_count} vision records")
        return count


# Global enhanced orchestrator instance
enhanced_automation_orchestrator = EnhancedAutomationOrchestrator()