"""
Automation Orchestrator for WYN360 CLI Browser Automation

This module provides intelligent decision-making for browser automation,
choosing between DOM-first, Stagehand, and Vision approaches based on
context and confidence scores.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import time

logger = logging.getLogger(__name__)


class AutomationApproach(Enum):
    """Available automation approaches"""
    DOM_ANALYSIS = "dom_analysis"
    STAGEHAND = "stagehand"
    VISION_FALLBACK = "vision_fallback"


@dataclass
class ActionRequest:
    """Represents a user action request"""
    url: str
    task_description: str
    action_type: str  # click, type, select, submit, extract, navigate
    target_description: str
    action_data: Optional[Dict[str, Any]] = None
    confidence_threshold: float = 0.7
    show_browser: bool = False


@dataclass
class ActionResult:
    """Result of an automation action"""
    success: bool
    approach_used: AutomationApproach
    confidence: float
    execution_time: float
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    recommendation: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None


@dataclass
class DecisionContext:
    """Context for decision making"""
    dom_confidence: float
    page_complexity: str  # simple, moderate, complex
    element_count: int
    forms_count: int
    previous_failures: List[str]
    user_preference: Optional[AutomationApproach] = None


class AutomationOrchestrator:
    """
    Orchestrates browser automation decisions and executions

    This class implements the core decision logic for choosing between
    DOM-first, Stagehand, and Vision approaches based on page analysis,
    confidence scores, and historical performance.
    """

    def __init__(self):
        self.decision_history: List[Dict[str, Any]] = []
        self.approach_success_rates: Dict[AutomationApproach, float] = {
            AutomationApproach.DOM_ANALYSIS: 0.0,
            AutomationApproach.STAGEHAND: 0.0,
            AutomationApproach.VISION_FALLBACK: 0.0
        }
        self.total_attempts: Dict[AutomationApproach, int] = {
            AutomationApproach.DOM_ANALYSIS: 0,
            AutomationApproach.STAGEHAND: 0,
            AutomationApproach.VISION_FALLBACK: 0
        }

    def decide_automation_approach(
        self,
        action_request: ActionRequest,
        dom_analysis_result: Dict[str, Any]
    ) -> Tuple[AutomationApproach, DecisionContext, str]:
        """
        Decide the best automation approach based on analysis and context

        Args:
            action_request: The user's action request
            dom_analysis_result: Result from DOM analysis

        Returns:
            Tuple of (chosen_approach, decision_context, reasoning)
        """
        try:
            # Create decision context
            context = self._create_decision_context(action_request, dom_analysis_result)

            # Apply decision logic
            approach, reasoning = self._apply_decision_rules(action_request, context)

            # Log decision for learning
            self._log_decision(action_request, context, approach, reasoning)

            logger.info(f"Decision: {approach.value} (confidence: {context.dom_confidence:.2f}, reasoning: {reasoning})")

            return approach, context, reasoning

        except Exception as e:
            logger.error(f"Error in decision making: {e}")
            return AutomationApproach.VISION_FALLBACK, DecisionContext(0.0, "complex", 0, 0, []), "Error in analysis"

    def _create_decision_context(
        self,
        action_request: ActionRequest,
        dom_analysis_result: Dict[str, Any]
    ) -> DecisionContext:
        """Create decision context from analysis results"""

        dom_confidence = dom_analysis_result.get('confidence', 0.0)
        element_count = dom_analysis_result.get('interactive_elements_count', 0)
        forms_count = dom_analysis_result.get('forms_count', 0)

        # Determine page complexity
        if element_count > 15 or forms_count > 2:
            complexity = "complex"
        elif element_count > 5 or forms_count > 0:
            complexity = "moderate"
        else:
            complexity = "simple"

        # Get recent failures for this URL
        recent_failures = self._get_recent_failures(action_request.url)

        return DecisionContext(
            dom_confidence=dom_confidence,
            page_complexity=complexity,
            element_count=element_count,
            forms_count=forms_count,
            previous_failures=recent_failures
        )

    def _apply_decision_rules(
        self,
        action_request: ActionRequest,
        context: DecisionContext
    ) -> Tuple[AutomationApproach, str]:
        """Apply decision rules to choose automation approach"""

        # Rule 1: User preference override
        if context.user_preference:
            return context.user_preference, "User preference override"

        # Rule 2: High confidence DOM analysis
        if context.dom_confidence >= action_request.confidence_threshold:
            if context.page_complexity == "simple" or context.element_count >= 3:
                # Check if DOM approach hasn't failed recently
                if AutomationApproach.DOM_ANALYSIS.value not in context.previous_failures:
                    return AutomationApproach.DOM_ANALYSIS, f"High DOM confidence ({context.dom_confidence:.2f})"

        # Rule 3: Medium confidence with forms
        if context.dom_confidence >= (action_request.confidence_threshold * 0.7):
            if context.forms_count > 0:
                return AutomationApproach.DOM_ANALYSIS, f"Forms detected with medium confidence ({context.dom_confidence:.2f})"

        # Rule 4: Stagehand for medium complexity
        if context.dom_confidence >= 0.4:
            if context.page_complexity in ["moderate", "complex"]:
                if AutomationApproach.STAGEHAND.value not in context.previous_failures:
                    return AutomationApproach.STAGEHAND, f"Medium confidence ({context.dom_confidence:.2f}), {context.page_complexity} page"

        # Rule 5: Adaptive learning - prefer successful approaches
        if len(self.decision_history) > 5:
            best_approach = self._get_best_performing_approach()
            if best_approach and best_approach.value not in context.previous_failures:
                return best_approach, f"Historical success rate: {self.approach_success_rates[best_approach]:.1%}"

        # Rule 6: Default fallback
        return AutomationApproach.VISION_FALLBACK, f"Low confidence ({context.dom_confidence:.2f}) or multiple failures"

    def _get_best_performing_approach(self) -> Optional[AutomationApproach]:
        """Get the approach with highest success rate"""
        best_approach = None
        best_rate = 0.0

        for approach, rate in self.approach_success_rates.items():
            # Only consider approaches that have been tried at least 3 times
            if self.total_attempts[approach] >= 3 and rate > best_rate:
                best_rate = rate
                best_approach = approach

        return best_approach

    def _get_recent_failures(self, url: str, hours: int = 1) -> List[str]:
        """Get recent failures for a specific URL"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)

        failures = []
        for decision in self.decision_history:
            if (decision.get('timestamp', 0) > cutoff_time and
                decision.get('url') == url and
                decision.get('success') is False):
                # Try both 'approach' and 'approach_used' keys for compatibility
                approach = decision.get('approach') or decision.get('approach_used', '')
                failures.append(approach)

        return failures

    def record_execution_result(
        self,
        action_request: ActionRequest,
        approach_used: AutomationApproach,
        result: ActionResult
    ) -> None:
        """Record execution result for learning"""
        try:
            # Update success rates
            self.total_attempts[approach_used] += 1

            if result.success:
                current_rate = self.approach_success_rates[approach_used]
                total = self.total_attempts[approach_used]
                # Running average calculation
                self.approach_success_rates[approach_used] = (current_rate * (total - 1) + 1.0) / total
            else:
                current_rate = self.approach_success_rates[approach_used]
                total = self.total_attempts[approach_used]
                self.approach_success_rates[approach_used] = (current_rate * (total - 1) + 0.0) / total

            # Update decision history
            if len(self.decision_history) > 5:  # Find matching decision
                for i, decision in enumerate(reversed(self.decision_history[:5])):
                    if (decision.get('url') == action_request.url and
                        decision.get('approach') == approach_used.value):
                        decision['success'] = result.success
                        decision['execution_time'] = result.execution_time
                        decision['error'] = result.error_message
                        break

            logger.info(f"Recorded result: {approach_used.value} success={result.success}, "
                       f"new rate: {self.approach_success_rates[approach_used]:.1%}")

        except Exception as e:
            logger.error(f"Error recording execution result: {e}")

    def _log_decision(
        self,
        action_request: ActionRequest,
        context: DecisionContext,
        approach: AutomationApproach,
        reasoning: str
    ) -> None:
        """Log decision for analysis and learning"""
        decision_record = {
            'timestamp': time.time(),
            'url': action_request.url,
            'task': action_request.task_description,
            'action_type': action_request.action_type,
            'approach': approach.value,
            'reasoning': reasoning,
            'dom_confidence': context.dom_confidence,
            'page_complexity': context.page_complexity,
            'element_count': context.element_count,
            'forms_count': context.forms_count,
            'previous_failures': context.previous_failures,
            'success': None,  # Will be updated when result is recorded
            'execution_time': None,
            'error': None
        }

        self.decision_history.append(decision_record)

        # Keep only recent decisions (last 100)
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]

    def get_decision_analytics(self) -> Dict[str, Any]:
        """Get analytics about decision making performance"""
        if not self.decision_history:
            return {
                'total_decisions': 0,
                'approach_distribution': {},
                'success_rates': {},
                'average_confidence': 0.0
            }

        total_decisions = len(self.decision_history)
        approach_counts = {}
        confidence_scores = []

        for decision in self.decision_history:
            approach = decision.get('approach', 'unknown')
            approach_counts[approach] = approach_counts.get(approach, 0) + 1

            if decision.get('dom_confidence'):
                confidence_scores.append(decision['dom_confidence'])

        # Calculate distributions
        approach_distribution = {
            approach: count / total_decisions
            for approach, count in approach_counts.items()
        }

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        return {
            'total_decisions': total_decisions,
            'approach_distribution': approach_distribution,
            'success_rates': {approach.value: rate for approach, rate in self.approach_success_rates.items()},
            'total_attempts': {approach.value: count for approach, count in self.total_attempts.items()},
            'average_confidence': avg_confidence,
            'recent_decisions': self.decision_history[-10:] if self.decision_history else []
        }

    def suggest_improvements(self) -> List[str]:
        """Suggest improvements based on decision history"""
        suggestions = []
        analytics = self.get_decision_analytics()

        if analytics['total_decisions'] < 10:
            suggestions.append("More usage data needed for meaningful suggestions")
            return suggestions

        # Analyze success rates
        success_rates = analytics['success_rates']

        if success_rates.get('dom_analysis', 0) < 0.7:
            suggestions.append("Consider adjusting DOM confidence threshold - current success rate is low")

        if success_rates.get('stagehand', 0) > success_rates.get('dom_analysis', 0):
            suggestions.append("Stagehand is performing better than DOM analysis - consider lowering DOM confidence threshold")

        if analytics['average_confidence'] < 0.5:
            suggestions.append("Average DOM confidence is low - may need to improve DOM analysis or lower thresholds")

        # Analyze approach distribution
        distribution = analytics['approach_distribution']
        if distribution.get('vision_fallback', 0) > 0.5:
            suggestions.append("High vision fallback usage - consider improving DOM analysis or adding Stagehand")

        return suggestions


# Global orchestrator instance
automation_orchestrator = AutomationOrchestrator()