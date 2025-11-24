"""
Vision Fallback Integration for WYN360 CLI

This module provides the integration layer between the DOM/Stagehand automation
system and the existing vision-based browser automation system. It acts as a
transparent wrapper that makes the vision system compatible with the unified
automation pipeline while preserving all existing functionality.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .automation_orchestrator import (
    AutomationApproach,
    ActionRequest,
    ActionResult
)

logger = logging.getLogger(__name__)


@dataclass
class VisionFallbackConfig:
    """Configuration for vision fallback execution"""
    max_steps: int = 20
    headless: bool = False
    enable_screenshots: bool = True
    timeout_seconds: float = 120.0  # 2 minutes default for complex vision tasks
    confidence_threshold: float = 0.5  # Lower threshold for vision as final fallback


class VisionFallbackIntegration:
    """
    Integrates existing vision-based browser automation as final fallback

    This class provides a unified interface to the existing vision system,
    making it compatible with the DOM-first/Stagehand automation pipeline
    while preserving all existing vision capabilities.

    Key Features:
    - Transparent wrapper around existing browse_and_find function
    - Consistent ActionResult interface matching DOM/Stagehand approaches
    - Error handling and timeout management
    - Performance tracking and analytics
    - Integration with token counting system
    """

    def __init__(self, agent=None):
        """
        Initialize vision fallback integration

        Args:
            agent: WYN360Agent instance (optional, will be injected during execution)
        """
        self.agent = agent
        self.execution_history: List[Dict[str, Any]] = []
        self.total_executions = 0
        self.successful_executions = 0

    def is_available(self, agent=None) -> bool:
        """
        Check if vision fallback is available

        Args:
            agent: WYN360Agent instance to check

        Returns:
            bool: True if vision capabilities are available
        """
        test_agent = agent or self.agent
        if not test_agent:
            return False

        # Check if using Bedrock (vision not supported)
        if hasattr(test_agent, 'use_bedrock') and test_agent.use_bedrock:
            logger.info("Vision fallback unavailable: Bedrock mode detected")
            return False

        # Check if agent has browse_and_find method
        if not hasattr(test_agent, 'browse_and_find') or not callable(getattr(test_agent, 'browse_and_find', None)):
            logger.info("Vision fallback unavailable: browse_and_find method not found")
            return False

        return True

    async def execute_vision_fallback(
        self,
        action_request: ActionRequest,
        config: Optional[VisionFallbackConfig] = None,
        agent=None
    ) -> ActionResult:
        """
        Execute vision-based automation as fallback

        Args:
            action_request: The automation action request
            config: Vision fallback configuration
            agent: WYN360Agent instance (optional override)

        Returns:
            ActionResult with vision execution details
        """
        execution_agent = agent or self.agent
        config = config or VisionFallbackConfig()
        start_time = time.time()

        # Validate agent availability
        if not self.is_available(execution_agent):
            return self._create_unavailable_result(action_request, start_time, execution_agent)

        # Convert ActionRequest to vision-compatible task description
        vision_task = self._convert_request_to_vision_task(action_request)

        try:
            logger.info(f"Executing vision fallback for: {action_request.task_description}")

            # Execute vision-based automation using existing browse_and_find
            result_text = await self._execute_vision_automation(
                execution_agent, vision_task, action_request.url, config
            )

            # Parse result and determine success
            success, confidence, result_data = self._parse_vision_result(result_text)

            execution_time = time.time() - start_time

            # Create unified result
            action_result = ActionResult(
                success=success,
                approach_used=AutomationApproach.VISION_FALLBACK,
                confidence=confidence,
                execution_time=execution_time,
                result_data=result_data,
                error_message=None if success else result_data.get('error'),
                recommendation=self._generate_vision_recommendation(success, result_data)
            )

            # Record execution for analytics
            self._record_execution(action_request, action_result, vision_task)

            logger.info(f"Vision fallback {'succeeded' if success else 'failed'} in {execution_time:.2f}s")
            return action_result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Vision fallback error: {e}")

            return ActionResult(
                success=False,
                approach_used=AutomationApproach.VISION_FALLBACK,
                confidence=0.0,
                execution_time=execution_time,
                result_data={'error': str(e)},
                error_message=f"Vision execution error: {str(e)}",
                recommendation="Check browser accessibility and task complexity"
            )

    def _convert_request_to_vision_task(self, request: ActionRequest) -> str:
        """
        Convert ActionRequest to vision-compatible task description

        Args:
            request: ActionRequest object

        Returns:
            str: Task description optimized for vision system
        """
        # Create comprehensive task description for vision system
        task_parts = [request.task_description]

        if request.action_type and request.target_description:
            action_detail = f"{request.action_type} on {request.target_description}"
            if action_detail.lower() not in request.task_description.lower():
                task_parts.append(action_detail)

        # Add specific action data if available
        if request.action_data:
            if request.action_type == "type" and "text" in request.action_data:
                task_parts.append(f"Type: '{request.action_data['text']}'")
            elif request.action_type == "select" and "value" in request.action_data:
                task_parts.append(f"Select: '{request.action_data['value']}'")

        return ". ".join(task_parts)

    async def _execute_vision_automation(
        self,
        agent,
        task: str,
        url: str,
        config: VisionFallbackConfig
    ) -> str:
        """
        Execute vision automation using existing browse_and_find

        Args:
            agent: WYN360Agent instance
            task: Task description
            url: Target URL
            config: Vision configuration

        Returns:
            str: Result from browse_and_find
        """
        # Create a mock RunContext for the agent call
        from unittest.mock import Mock
        mock_context = Mock()
        mock_context.deps = None

        # Execute existing vision-based automation
        result = await agent.browse_and_find(
            ctx=mock_context,
            task=task,
            url=url,
            max_steps=config.max_steps,
            headless=config.headless
        )

        return result

    def _parse_vision_result(self, result_text: str) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Parse vision result text to extract success, confidence, and data

        Args:
            result_text: Raw result from browse_and_find

        Returns:
            Tuple of (success, confidence, result_data)
        """
        success = False
        confidence = 0.0
        result_data = {'raw_result': result_text}

        # Check for success indicators
        if "✅" in result_text or "Task Completed Successfully" in result_text:
            success = True
            confidence = 0.8  # High confidence for successful vision completion

        elif "⚠️" in result_text or "Task Partially Completed" in result_text:
            success = False  # Treat partial as failure for consistency
            confidence = 0.4  # Medium confidence - partial success
            result_data['partial_success'] = True

        elif "❌" in result_text or "Task Failed" in result_text:
            success = False
            confidence = 0.1  # Low confidence for clear failure

        # Extract specific information
        if "Steps Taken:" in result_text:
            try:
                steps_line = [line for line in result_text.split('\n') if 'Steps Taken:' in line][0]
                steps_taken = steps_line.split('Steps Taken:')[1].strip()
                # Clean up markdown formatting
                steps_taken = steps_taken.replace('**', '').strip()
                result_data['steps_taken'] = steps_taken
            except (IndexError, AttributeError):
                pass

        # Also check for "Steps Attempted:" for failed cases
        if "Steps Attempted:" in result_text:
            try:
                steps_line = [line for line in result_text.split('\n') if 'Steps Attempted:' in line][0]
                steps_taken = steps_line.split('Steps Attempted:')[1].strip()
                # Clean up markdown formatting
                steps_taken = steps_taken.replace('**', '').strip()
                result_data['steps_taken'] = steps_taken
            except (IndexError, AttributeError):
                pass

        # Extract any error or issue information
        if "Issue:" in result_text:
            try:
                issue_line = [line for line in result_text.split('\n') if 'Issue:' in line][0]
                error_msg = issue_line.split('Issue:')[1].strip()
                # Clean up markdown formatting
                error_msg = error_msg.replace('**', '').strip()
                result_data['error'] = error_msg
            except (IndexError, AttributeError):
                pass

        # Look for Bedrock mode error
        if "requires vision capabilities" in result_text:
            result_data['error'] = "Vision capabilities not available in current mode"
            result_data['bedrock_mode'] = True

        return success, confidence, result_data

    def _generate_vision_recommendation(
        self,
        success: bool,
        result_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate recommendation based on vision execution result

        Args:
            success: Whether execution was successful
            result_data: Additional result data

        Returns:
            Optional[str]: Recommendation text or None
        """
        if success:
            return None  # No recommendation needed for success

        if result_data.get('bedrock_mode'):
            return "Switch to Anthropic API mode to enable vision capabilities"

        if result_data.get('partial_success'):
            return "Consider breaking the task into smaller steps or increasing max_steps"

        if 'error' in result_data:
            error = result_data['error']
            if 'timeout' in error.lower():
                return "Task may be too complex for vision automation. Consider manual approach"
            elif 'not accessible' in error.lower() or 'failed to load' in error.lower():
                return "Check URL accessibility and network connectivity"

        return "Vision approach exhausted. Manual intervention may be required"

    def _create_unavailable_result(
        self,
        action_request: ActionRequest,
        start_time: float,
        agent=None
    ) -> ActionResult:
        """
        Create result for when vision is unavailable

        Args:
            action_request: Original request
            start_time: Execution start time

        Returns:
            ActionResult indicating unavailability
        """
        execution_time = time.time() - start_time

        # Check if agent is available and if it's Bedrock mode
        test_agent = agent or self.agent
        if test_agent and hasattr(test_agent, 'use_bedrock') and test_agent.use_bedrock:
            error_msg = "Vision fallback unavailable in Bedrock mode"
            recommendation = "Switch to Anthropic API mode for vision capabilities"
        else:
            error_msg = "Vision fallback system not available"
            recommendation = "Check agent configuration and vision system availability"

        return ActionResult(
            success=False,
            approach_used=AutomationApproach.VISION_FALLBACK,
            confidence=0.0,
            execution_time=execution_time,
            result_data={'unavailable': True},
            error_message=error_msg,
            recommendation=recommendation
        )

    def _record_execution(
        self,
        action_request: ActionRequest,
        result: ActionResult,
        vision_task: str
    ) -> None:
        """
        Record execution for analytics and learning

        Args:
            action_request: Original action request
            result: Execution result
            vision_task: Vision task description used
        """
        try:
            self.total_executions += 1
            if result.success:
                self.successful_executions += 1

            execution_record = {
                'timestamp': time.time(),
                'url': action_request.url,
                'original_task': action_request.task_description,
                'vision_task': vision_task,
                'action_type': action_request.action_type,
                'target_description': action_request.target_description,
                'success': result.success,
                'confidence': result.confidence,
                'execution_time': result.execution_time,
                'steps_taken': result.result_data.get('steps_taken'),
                'error': result.error_message
            }

            self.execution_history.append(execution_record)

            # Keep only recent history (last 50 executions)
            if len(self.execution_history) > 50:
                self.execution_history = self.execution_history[-50:]

        except Exception as e:
            logger.error(f"Error recording vision execution: {e}")

    def get_execution_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about vision fallback performance

        Returns:
            Dict with vision execution statistics
        """
        if self.total_executions == 0:
            return {
                'total_executions': 0,
                'success_rate': 0.0,
                'availability': self.is_available()
            }

        success_rate = self.successful_executions / self.total_executions

        # Calculate average execution time
        execution_times = [ex['execution_time'] for ex in self.execution_history if 'execution_time' in ex]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0

        # Analyze action types
        action_types = {}
        for record in self.execution_history:
            action_type = record.get('action_type', 'unknown')
            if action_type not in action_types:
                action_types[action_type] = {'total': 0, 'successful': 0}

            action_types[action_type]['total'] += 1
            if record.get('success'):
                action_types[action_type]['successful'] += 1

        # Calculate success rates by action type
        for action_type, stats in action_types.items():
            stats['success_rate'] = stats['successful'] / stats['total'] if stats['total'] > 0 else 0.0

        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'success_rate': success_rate,
            'average_execution_time': avg_execution_time,
            'action_types': action_types,
            'recent_executions': self.execution_history[-10:] if self.execution_history else [],
            'availability': self.is_available()
        }

    def clear_execution_history(self) -> int:
        """
        Clear execution history and return number of records removed

        Returns:
            int: Number of records cleared
        """
        count = len(self.execution_history)
        self.execution_history.clear()
        self.total_executions = 0
        self.successful_executions = 0
        logger.info(f"Cleared {count} vision fallback execution records")
        return count


# Global vision fallback integration instance
vision_fallback_integration = VisionFallbackIntegration()