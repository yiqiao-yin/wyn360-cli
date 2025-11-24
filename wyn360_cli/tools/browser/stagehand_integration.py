"""
Stagehand Integration Pipeline for WYN360 CLI

This module provides the dynamic execution pipeline that integrates Stagehand
code generation with the automation orchestrator and DOM analysis system.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time

from .stagehand_generator import (
    StagehandCodeGenerator,
    StagehandExecutionResult,
    stagehand_generator
)
from .automation_orchestrator import (
    AutomationOrchestrator,
    AutomationApproach,
    ActionRequest,
    ActionResult,
    DecisionContext
)
from .dom_analyzer import DOMExtractor

logger = logging.getLogger(__name__)


@dataclass
class StagehandExecutionPipeline:
    """Configuration for Stagehand execution pipeline"""
    max_retries: int = 2
    timeout_seconds: float = 30.0
    enable_pattern_learning: bool = True
    confidence_threshold: float = 0.6
    show_browser: bool = False


class StagehandIntegration:
    """
    Integrates Stagehand code generation with DOM automation system

    This class provides the dynamic execution pipeline that:
    1. Receives automation decisions from the orchestrator
    2. Generates appropriate Stagehand code
    3. Executes the code with proper error handling
    4. Records results for pattern learning
    5. Provides fallback strategies on failure
    """

    def __init__(self, orchestrator: Optional[AutomationOrchestrator] = None):
        self.orchestrator = orchestrator or AutomationOrchestrator()
        self.stagehand_generator = stagehand_generator
        self.dom_analyzer = DOMExtractor()
        self.execution_history: List[Dict[str, Any]] = []

    async def execute_stagehand_automation(
        self,
        action_request: ActionRequest,
        dom_analysis_result: Dict[str, Any],
        pipeline_config: Optional[StagehandExecutionPipeline] = None
    ) -> ActionResult:
        """
        Execute Stagehand automation for the given action request

        Args:
            action_request: The automation action to perform
            dom_analysis_result: Results from DOM analysis
            pipeline_config: Configuration for execution pipeline

        Returns:
            ActionResult with execution details and results
        """
        config = pipeline_config or StagehandExecutionPipeline()
        start_time = time.time()

        # Check if Stagehand is available
        if not self.stagehand_generator.is_available():
            return ActionResult(
                success=False,
                approach_used=AutomationApproach.STAGEHAND,
                confidence=0.0,
                execution_time=time.time() - start_time,
                result_data={},
                error_message="Stagehand not available",
                recommendation="Use DOM analysis or vision fallback"
            )

        try:
            # Generate Stagehand code
            code_success, actions_or_error = await self._generate_stagehand_code(
                action_request, dom_analysis_result
            )

            if not code_success:
                return ActionResult(
                    success=False,
                    approach_used=AutomationApproach.STAGEHAND,
                    confidence=0.0,
                    execution_time=time.time() - start_time,
                    result_data={},
                    error_message=f"Code generation failed: {actions_or_error}",
                    recommendation="Try DOM analysis approach"
                )

            # Execute with retries
            execution_result = await self._execute_with_retries(
                action_request, actions_or_error, config
            )

            # Calculate confidence based on execution success and pattern history
            confidence = self._calculate_execution_confidence(
                action_request, execution_result, actions_or_error
            )

            # Create result
            result = ActionResult(
                success=execution_result.success,
                approach_used=AutomationApproach.STAGEHAND,
                confidence=confidence,
                execution_time=time.time() - start_time,
                result_data=execution_result.result_data,
                error_message=execution_result.error_message,
                recommendation=self._generate_recommendation(execution_result),
                token_usage=execution_result.token_usage
            )

            # Record for learning if enabled
            if config.enable_pattern_learning:
                await self._record_execution_for_learning(
                    action_request, actions_or_error, execution_result, result
                )

            # Log execution
            self._log_execution(action_request, result, execution_result)

            return result

        except Exception as e:
            logger.error(f"Error in Stagehand execution pipeline: {e}")
            return ActionResult(
                success=False,
                approach_used=AutomationApproach.STAGEHAND,
                confidence=0.0,
                execution_time=time.time() - start_time,
                result_data={},
                error_message=f"Pipeline error: {str(e)}",
                recommendation="Try vision fallback approach"
            )

    async def _generate_stagehand_code(
        self,
        action_request: ActionRequest,
        dom_analysis_result: Dict[str, Any]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Generate Stagehand code for the action request"""
        try:
            dom_context = dom_analysis_result.get('dom_analysis_text', '')

            success, result = await self.stagehand_generator.generate_stagehand_code(
                url=action_request.url,
                task_description=action_request.task_description,
                dom_context=dom_context,
                target_description=action_request.target_description,
                action_type=action_request.action_type,
                action_data=action_request.action_data
            )

            return success, result

        except Exception as e:
            logger.error(f"Error generating Stagehand code: {e}")
            return False, f"Code generation error: {str(e)}"

    async def _execute_with_retries(
        self,
        action_request: ActionRequest,
        actions: List[Dict[str, Any]],
        config: StagehandExecutionPipeline
    ) -> StagehandExecutionResult:
        """Execute Stagehand actions with retry logic"""
        last_error = None

        for attempt in range(config.max_retries + 1):
            try:
                logger.info(f"Stagehand execution attempt {attempt + 1}/{config.max_retries + 1}")

                # Execute actions with timeout
                execution_task = self.stagehand_generator.execute_stagehand_actions(
                    url=action_request.url,
                    actions=actions,
                    show_browser=config.show_browser
                )

                result = await asyncio.wait_for(execution_task, timeout=config.timeout_seconds)

                if result.success:
                    logger.info(f"Stagehand execution succeeded on attempt {attempt + 1}")
                    return result

                last_error = result.error_message
                logger.warning(f"Attempt {attempt + 1} failed: {result.error_message}")

                # Wait before retry (exponential backoff)
                if attempt < config.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)

            except asyncio.TimeoutError:
                last_error = f"Execution timeout after {config.timeout_seconds}s"
                logger.warning(f"Attempt {attempt + 1} timed out")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} error: {e}")

        # All retries failed
        return StagehandExecutionResult(
            success=False,
            pattern_used=None,
            actions_performed=[],
            execution_time=0.0,
            result_data={},
            error_message=f"All {config.max_retries + 1} attempts failed. Last error: {last_error}"
        )

    def _calculate_execution_confidence(
        self,
        action_request: ActionRequest,
        execution_result: StagehandExecutionResult,
        actions: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for the execution"""
        if not execution_result.success:
            return 0.0

        # Base confidence from execution success
        confidence = 0.7

        # Adjust based on execution time (faster = more confident)
        if execution_result.execution_time < 5.0:
            confidence += 0.1
        elif execution_result.execution_time > 15.0:
            confidence -= 0.1

        # Adjust based on number of actions (fewer = more confident for simple tasks)
        action_count = len(actions)
        if action_count <= 3:
            confidence += 0.1
        elif action_count > 6:
            confidence -= 0.1

        # Check pattern success rate if available
        if execution_result.pattern_used:
            pattern_confidence = execution_result.pattern_used.confidence_score
            confidence = (confidence + pattern_confidence) / 2

        return min(1.0, max(0.0, confidence))

    def _generate_recommendation(self, execution_result: StagehandExecutionResult) -> Optional[str]:
        """Generate recommendation based on execution result"""
        if execution_result.success:
            return None

        if not self.stagehand_generator.is_available():
            return "Configure Stagehand environment variables to enable AI-powered automation"

        if "timeout" in str(execution_result.error_message).lower():
            return "Page may be slow to load. Try increasing timeout or use DOM analysis approach"

        if "not found" in str(execution_result.error_message).lower():
            return "Target element may not be present. Try vision fallback for complex layouts"

        return "Consider using vision fallback or DOM analysis approach"

    async def _record_execution_for_learning(
        self,
        action_request: ActionRequest,
        actions: List[Dict[str, Any]],
        execution_result: StagehandExecutionResult,
        final_result: ActionResult
    ) -> None:
        """Record execution results for pattern learning"""
        try:
            # Update pattern success statistics
            if execution_result.pattern_used:
                pattern_key = execution_result.pattern_used.pattern_id
                self.stagehand_generator.update_pattern_success(
                    pattern_key, execution_result.success
                )

            # Record in orchestrator for approach learning
            self.orchestrator.record_execution_result(
                action_request, AutomationApproach.STAGEHAND, final_result
            )

            # Record in local execution history
            execution_record = {
                'timestamp': time.time(),
                'url': action_request.url,
                'task': action_request.task_description,
                'action_type': action_request.action_type,
                'success': execution_result.success,
                'execution_time': execution_result.execution_time,
                'actions_count': len(actions),
                'pattern_used': execution_result.pattern_used.pattern_id if execution_result.pattern_used else None,
                'error': execution_result.error_message
            }

            self.execution_history.append(execution_record)

            # Keep only recent history (last 50 executions)
            if len(self.execution_history) > 50:
                self.execution_history = self.execution_history[-50:]

        except Exception as e:
            logger.error(f"Error recording execution for learning: {e}")

    def _log_execution(
        self,
        action_request: ActionRequest,
        result: ActionResult,
        execution_result: StagehandExecutionResult
    ) -> None:
        """Log execution details"""
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        logger.info(f"{status} Stagehand execution for {action_request.action_type} on {action_request.url}")
        logger.info(f"  Task: {action_request.task_description}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Execution time: {result.execution_time:.2f}s")

        if execution_result.pattern_used:
            logger.info(f"  Pattern: {execution_result.pattern_used.pattern_id} (success rate: {execution_result.pattern_used.success_rate:.1%})")

        if not result.success and result.error_message:
            logger.warning(f"  Error: {result.error_message}")

        if result.recommendation:
            logger.info(f"  Recommendation: {result.recommendation}")

    def get_execution_analytics(self) -> Dict[str, Any]:
        """Get analytics about Stagehand execution performance"""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        successful = sum(1 for ex in self.execution_history if ex['success'])

        # Calculate average execution time
        avg_time = sum(ex['execution_time'] for ex in self.execution_history) / total

        # Count by action type
        action_types = {}
        for ex in self.execution_history:
            action_type = ex['action_type']
            if action_type not in action_types:
                action_types[action_type] = {'total': 0, 'successful': 0}
            action_types[action_type]['total'] += 1
            if ex['success']:
                action_types[action_type]['successful'] += 1

        # Calculate success rates by action type
        for action_type, stats in action_types.items():
            stats['success_rate'] = stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0

        return {
            "total_executions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_execution_time": avg_time,
            "action_types": action_types,
            "pattern_stats": self.stagehand_generator.get_pattern_statistics()
        }

    def clear_execution_history(self) -> int:
        """Clear execution history and return number of records removed"""
        count = len(self.execution_history)
        self.execution_history.clear()
        logger.info(f"Cleared {count} execution records from Stagehand integration history")
        return count


# Global integration instance
stagehand_integration = StagehandIntegration()