"""
Unified Automation Interface for WYN360 CLI

This module provides a single, unified interface for all browser automation approaches:
DOM-first, Stagehand AI-powered, and Vision fallback. It acts as the main entry point
for the enhanced automation system and provides transparent switching between approaches.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

from .enhanced_automation_orchestrator import (
    EnhancedAutomationOrchestrator,
    EnhancedActionRequest,
    enhanced_automation_orchestrator
)
from .automation_orchestrator import AutomationApproach, ActionResult
from .stagehand_integration import StagehandExecutionPipeline
from .vision_fallback_integration import VisionFallbackConfig

logger = logging.getLogger(__name__)


@dataclass
class UnifiedAutomationConfig:
    """Configuration for unified automation interface"""
    # Approach preferences
    preferred_approach: Optional[AutomationApproach] = None
    enable_dom_analysis: bool = True
    enable_stagehand: bool = True
    enable_vision_fallback: bool = True

    # Execution settings
    max_retries_per_approach: int = 2
    total_timeout_seconds: float = 300.0  # 5 minutes total
    show_browser: bool = False

    # Confidence thresholds
    dom_confidence_threshold: float = 0.7
    stagehand_confidence_threshold: float = 0.6
    vision_confidence_threshold: float = 0.5

    # Specific approach configs
    stagehand_config: Optional[StagehandExecutionPipeline] = None
    vision_config: Optional[VisionFallbackConfig] = None


class UnifiedAutomationInterface:
    """
    Unified interface for all browser automation approaches

    This class provides a single entry point for browser automation that:
    1. Abstracts away the complexity of choosing approaches
    2. Provides intelligent fallback between DOM → Stagehand → Vision
    3. Maintains consistent interfaces across all approaches
    4. Tracks performance and learning across approaches
    5. Enables fine-grained control when needed

    Key Features:
    - **Transparent Operation**: Users don't need to know which approach is used
    - **Smart Fallbacks**: Automatically tries approaches in order of speed/cost effectiveness
    - **Flexible Control**: Support for forcing specific approaches when needed
    - **Performance Tracking**: Complete analytics across all approaches
    - **Configuration**: Granular control over thresholds and behaviors
    """

    def __init__(self, orchestrator: Optional[EnhancedAutomationOrchestrator] = None):
        """
        Initialize unified automation interface

        Args:
            orchestrator: Enhanced automation orchestrator (optional)
        """
        self.orchestrator = orchestrator or enhanced_automation_orchestrator
        self.execution_history: List[Dict[str, Any]] = []

    def set_agent(self, agent) -> None:
        """
        Set the WYN360Agent for the automation system

        Args:
            agent: WYN360Agent instance
        """
        self.orchestrator.set_agent(agent)
        logger.info("Agent configured for unified automation interface")

    async def execute_automation(
        self,
        url: str,
        task_description: str,
        action_type: Optional[str] = None,
        target_description: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
        config: Optional[UnifiedAutomationConfig] = None
    ) -> ActionResult:
        """
        Execute browser automation using the best available approach

        This is the main entry point for all browser automation. It intelligently
        selects and executes the most appropriate approach based on the task,
        configuration, and current system state.

        Args:
            url: Target URL
            task_description: Natural language description of the task
            action_type: Specific action type (click, type, select, etc.) - optional
            target_description: Description of target element - optional
            action_data: Additional action data (text to type, etc.) - optional
            config: Automation configuration - optional

        Returns:
            ActionResult with execution details and results
        """
        config = config or UnifiedAutomationConfig()
        start_time = time.time()

        # Create enhanced action request
        enhanced_request = self._create_enhanced_request(
            url, task_description, action_type, target_description, action_data, config
        )

        try:
            # Log execution start
            logger.info(f"Starting unified automation: {task_description}")
            self._log_execution_start(enhanced_request, config)

            # Execute through enhanced orchestrator
            result = await self.orchestrator.execute_automation_task(enhanced_request)

            # Record execution for analytics
            self._record_execution(enhanced_request, result, config)

            # Log final result
            self._log_execution_result(enhanced_request, result)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Unified automation error: {e}")

            # Create error result
            error_result = ActionResult(
                success=False,
                approach_used=AutomationApproach.DOM_ANALYSIS,  # Default
                confidence=0.0,
                execution_time=execution_time,
                result_data={'error': str(e)},
                error_message=f"Unified automation error: {str(e)}",
                recommendation="Check network connectivity and page accessibility"
            )

            self._record_execution(enhanced_request, error_result, config)
            return error_result

    async def execute_with_approach(
        self,
        approach: AutomationApproach,
        url: str,
        task_description: str,
        action_type: Optional[str] = None,
        target_description: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
        config: Optional[UnifiedAutomationConfig] = None
    ) -> ActionResult:
        """
        Execute automation using a specific approach

        This method forces the use of a specific automation approach,
        bypassing the intelligent approach selection.

        Args:
            approach: Specific automation approach to use
            url: Target URL
            task_description: Natural language description of the task
            action_type: Specific action type - optional
            target_description: Description of target element - optional
            action_data: Additional action data - optional
            config: Automation configuration - optional

        Returns:
            ActionResult with execution details
        """
        config = config or UnifiedAutomationConfig()
        config.preferred_approach = approach  # Set the forced approach in config
        start_time = time.time()

        # Create enhanced request with forced approach
        enhanced_request = self._create_enhanced_request(
            url, task_description, action_type, target_description, action_data, config
        )

        logger.info(f"Executing with forced approach: {approach.value}")

        try:
            # Log execution start
            self._log_execution_start(enhanced_request, config)

            # Execute through enhanced orchestrator
            result = await self.orchestrator.execute_automation_task(enhanced_request)

            # Record execution for analytics
            self._record_execution(enhanced_request, result, config)

            # Log final result
            self._log_execution_result(enhanced_request, result)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Forced automation error: {e}")

            # Create error result
            error_result = ActionResult(
                success=False,
                approach_used=approach,  # Use the forced approach
                confidence=0.0,
                execution_time=execution_time,
                result_data={'error': str(e)},
                error_message=f"Forced automation error: {str(e)}",
                recommendation="Check network connectivity and page accessibility"
            )

            self._record_execution(enhanced_request, error_result, config)
            return error_result

    def _create_enhanced_request(
        self,
        url: str,
        task_description: str,
        action_type: Optional[str],
        target_description: Optional[str],
        action_data: Optional[Dict[str, Any]],
        config: UnifiedAutomationConfig
    ) -> EnhancedActionRequest:
        """Create enhanced action request from parameters"""
        return EnhancedActionRequest(
            url=url,
            task_description=task_description,
            action_type=action_type or "automation",
            target_description=target_description or "target element",
            action_data=action_data,
            confidence_threshold=config.dom_confidence_threshold,
            show_browser=config.show_browser,
            enable_stagehand=config.enable_stagehand,
            stagehand_config=config.stagehand_config,
            fallback_to_vision=config.enable_vision_fallback,
            vision_config=config.vision_config,
            force_approach=config.preferred_approach
        )

    def _log_execution_start(
        self,
        request: EnhancedActionRequest,
        config: UnifiedAutomationConfig
    ) -> None:
        """Log execution start details"""
        logger.info(f"🚀 Unified Automation Starting")
        logger.info(f"  URL: {request.url}")
        logger.info(f"  Task: {request.task_description}")
        logger.info(f"  Action: {request.action_type}")
        logger.info(f"  Target: {request.target_description}")

        # Log enabled approaches
        approaches = []
        if config.enable_dom_analysis:
            approaches.append("DOM")
        if config.enable_stagehand:
            approaches.append("Stagehand")
        if config.enable_vision_fallback:
            approaches.append("Vision")

        logger.info(f"  Enabled approaches: {' → '.join(approaches)}")

        if config.preferred_approach:
            logger.info(f"  Preferred approach: {config.preferred_approach.value}")

    def _log_execution_result(
        self,
        request: EnhancedActionRequest,
        result: ActionResult
    ) -> None:
        """Log execution result details"""
        status = "✅ SUCCESS" if result.success else "❌ FAILED"
        logger.info(f"{status} Unified Automation Complete")
        logger.info(f"  Approach used: {result.approach_used.value}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Execution time: {result.execution_time:.2f}s")

        if not result.success and result.error_message:
            logger.warning(f"  Error: {result.error_message}")

        if result.recommendation:
            logger.info(f"  Recommendation: {result.recommendation}")

    def _record_execution(
        self,
        request: EnhancedActionRequest,
        result: ActionResult,
        config: UnifiedAutomationConfig
    ) -> None:
        """Record execution for analytics"""
        try:
            execution_record = {
                'timestamp': time.time(),
                'url': request.url,
                'task_description': request.task_description,
                'action_type': request.action_type,
                'target_description': request.target_description,
                'approach_used': result.approach_used.value,
                'success': result.success,
                'confidence': result.confidence,
                'execution_time': result.execution_time,
                'forced_approach': request.force_approach.value if request.force_approach else None,
                'enabled_approaches': {
                    'dom': config.enable_dom_analysis,
                    'stagehand': config.enable_stagehand,
                    'vision': config.enable_vision_fallback
                },
                'error': result.error_message,
                'recommendation': result.recommendation
            }

            self.execution_history.append(execution_record)

            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]

        except Exception as e:
            logger.error(f"Error recording unified automation execution: {e}")

    def get_unified_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics across the unified automation system

        Returns:
            Dict with complete analytics from all automation approaches
        """
        # Get enhanced orchestrator analytics
        orchestrator_analytics = self.orchestrator.get_enhanced_analytics()

        # Add unified interface analytics
        total_executions = len(self.execution_history)
        if total_executions == 0:
            unified_analytics = {
                'total_unified_executions': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'approach_usage': {},
                'recent_executions': []
            }
        else:
            # Calculate success rate
            successful = sum(1 for ex in self.execution_history if ex['success'])
            success_rate = successful / total_executions

            # Calculate average execution time
            avg_time = sum(ex['execution_time'] for ex in self.execution_history) / total_executions

            # Calculate approach usage
            approach_usage = {}
            for record in self.execution_history:
                approach = record['approach_used']
                if approach not in approach_usage:
                    approach_usage[approach] = {'count': 0, 'success_rate': 0.0}
                approach_usage[approach]['count'] += 1

            # Calculate success rates for each approach
            for approach, stats in approach_usage.items():
                approach_records = [r for r in self.execution_history if r['approach_used'] == approach]
                successful_for_approach = sum(1 for r in approach_records if r['success'])
                stats['success_rate'] = successful_for_approach / len(approach_records)

            unified_analytics = {
                'total_unified_executions': total_executions,
                'successful_executions': successful,
                'success_rate': success_rate,
                'average_execution_time': avg_time,
                'approach_usage': approach_usage,
                'recent_executions': self.execution_history[-10:] if self.execution_history else []
            }

        return {
            'unified_interface': unified_analytics,
            'detailed_analytics': orchestrator_analytics
        }

    def clear_all_history(self) -> Dict[str, int]:
        """
        Clear all execution history across the unified automation system

        Returns:
            Dict with counts of cleared records from each component
        """
        unified_count = len(self.execution_history)
        self.execution_history.clear()

        orchestrator_count = self.orchestrator.clear_execution_history()

        logger.info(f"Cleared all unified automation history: {unified_count} unified records, {orchestrator_count} orchestrator records")

        return {
            'unified_interface': unified_count,
            'orchestrator': orchestrator_count
        }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get current system status for all automation approaches

        Returns:
            Dict with availability and status of all approaches
        """
        return {
            'dom_analysis': {
                'available': True,  # DOM analysis is always available
                'description': "Direct DOM manipulation - fastest and cheapest"
            },
            'stagehand': {
                'available': self.orchestrator.stagehand_integration.stagehand_generator.is_available(),
                'description': "AI-powered browser automation",
                'status_info': self.orchestrator.stagehand_integration.stagehand_generator.get_status_info()
            },
            'vision_fallback': {
                'available': self.orchestrator.vision_integration.is_available(),
                'description': "Claude Vision-based automation - most capable",
                'analytics': self.orchestrator.vision_integration.get_execution_analytics()
            },
            'orchestrator_analytics': self.orchestrator.get_enhanced_analytics()
        }


# Global unified automation interface
unified_automation_interface = UnifiedAutomationInterface()