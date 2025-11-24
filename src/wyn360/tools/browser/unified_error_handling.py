"""
Unified Error Handling for Browser Automation

This module provides consistent error handling, retry mechanisms, and graceful
degradation across all browser automation approaches (DOM, Stagehand, Vision).
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass
from enum import Enum

from .automation_orchestrator import AutomationApproach, ActionResult

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of automation errors for intelligent handling"""
    NETWORK_ERROR = "network_error"           # Connection, timeout, DNS issues
    PAGE_LOAD_ERROR = "page_load_error"       # Page failed to load or is broken
    ELEMENT_NOT_FOUND = "element_not_found"   # Target element missing or changed
    INTERACTION_FAILED = "interaction_failed" # Click, type, etc. failed
    PERMISSION_DENIED = "permission_denied"   # Security restrictions
    BROWSER_ERROR = "browser_error"           # Browser crash, automation driver issues
    TIMEOUT_ERROR = "timeout_error"           # Operation timed out
    CONFIGURATION_ERROR = "config_error"      # Setup or configuration problems
    UNKNOWN_ERROR = "unknown_error"           # Unclassified errors


@dataclass
class ErrorContext:
    """Context information about an error for intelligent handling"""
    category: ErrorCategory
    message: str
    approach_used: AutomationApproach
    retryable: bool
    fallback_recommended: bool
    confidence_impact: float  # How much to reduce confidence for retry
    original_exception: Optional[Exception] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    timeout_seconds: float = 120.0


class UnifiedErrorHandler:
    """
    Unified error handling system for all automation approaches

    This class provides:
    - Consistent error categorization and reporting
    - Smart retry logic with exponential backoff
    - Graceful degradation between approaches
    - Error learning and pattern recognition
    """

    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.error_patterns: Dict[str, int] = {}

    def categorize_error(
        self,
        error: Union[Exception, str],
        approach: AutomationApproach,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        Categorize an error and determine handling strategy

        Args:
            error: Exception or error message
            approach: Automation approach that encountered the error
            metadata: Additional context about the error

        Returns:
            ErrorContext with categorization and handling recommendations
        """
        if isinstance(error, Exception):
            error_message = str(error)
            original_exception = error
        else:
            error_message = error
            original_exception = None

        error_lower = error_message.lower()

        # Network-related errors
        if any(keyword in error_lower for keyword in [
            'connection', 'timeout', 'network', 'dns', 'host', 'unreachable',
            'connectionerror', 'httperror', 'urlerror'
        ]):
            return ErrorContext(
                category=ErrorCategory.NETWORK_ERROR,
                message=error_message,
                approach_used=approach,
                retryable=True,
                fallback_recommended=False,  # Network issues affect all approaches
                confidence_impact=0.1,
                original_exception=original_exception,
                metadata=metadata
            )

        # Page loading errors
        if any(keyword in error_lower for keyword in [
            'page load', 'failed to load', 'navigation', 'page crash',
            'page not found', '404', '500', 'server error'
        ]):
            return ErrorContext(
                category=ErrorCategory.PAGE_LOAD_ERROR,
                message=error_message,
                approach_used=approach,
                retryable=True,
                fallback_recommended=True,  # Different approaches might handle differently
                confidence_impact=0.2,
                original_exception=original_exception,
                metadata=metadata
            )

        # Element not found errors
        if any(keyword in error_lower for keyword in [
            'element not found', 'no such element', 'element not visible',
            'element not accessible', 'selector', 'xpath'
        ]):
            return ErrorContext(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                message=error_message,
                approach_used=approach,
                retryable=approach == AutomationApproach.DOM_ANALYSIS,  # DOM is most brittle
                fallback_recommended=True,  # Other approaches might find the element
                confidence_impact=0.3,
                original_exception=original_exception,
                metadata=metadata
            )

        # Interaction failures
        if any(keyword in error_lower for keyword in [
            'click failed', 'type failed', 'interaction', 'element not interactable',
            'element intercepted', 'element obscured'
        ]):
            return ErrorContext(
                category=ErrorCategory.INTERACTION_FAILED,
                message=error_message,
                approach_used=approach,
                retryable=True,
                fallback_recommended=True,  # Different approaches use different interaction methods
                confidence_impact=0.2,
                original_exception=original_exception,
                metadata=metadata
            )

        # Permission/security errors
        if any(keyword in error_lower for keyword in [
            'permission denied', 'access denied', 'security', 'blocked',
            'cors', 'cross-origin', 'forbidden'
        ]):
            return ErrorContext(
                category=ErrorCategory.PERMISSION_DENIED,
                message=error_message,
                approach_used=approach,
                retryable=False,
                fallback_recommended=False,  # Security restrictions affect all approaches
                confidence_impact=0.5,
                original_exception=original_exception,
                metadata=metadata
            )

        # Browser/driver errors
        if any(keyword in error_lower for keyword in [
            'webdriver', 'chromedriver', 'browser', 'session', 'driver',
            'automation', 'playwright', 'selenium'
        ]):
            return ErrorContext(
                category=ErrorCategory.BROWSER_ERROR,
                message=error_message,
                approach_used=approach,
                retryable=approach != AutomationApproach.VISION_FALLBACK,  # Vision less dependent on browser
                fallback_recommended=True,
                confidence_impact=0.4,
                original_exception=original_exception,
                metadata=metadata
            )

        # Timeout errors
        if any(keyword in error_lower for keyword in [
            'timeout', 'timed out', 'time limit', 'deadline'
        ]):
            return ErrorContext(
                category=ErrorCategory.TIMEOUT_ERROR,
                message=error_message,
                approach_used=approach,
                retryable=True,
                fallback_recommended=approach == AutomationApproach.DOM_ANALYSIS,  # DOM fastest, others might work
                confidence_impact=0.2,
                original_exception=original_exception,
                metadata=metadata
            )

        # Configuration errors
        if any(keyword in error_lower for keyword in [
            'configuration', 'config', 'setup', 'initialization', 'missing',
            'not configured', 'invalid config'
        ]):
            return ErrorContext(
                category=ErrorCategory.CONFIGURATION_ERROR,
                message=error_message,
                approach_used=approach,
                retryable=False,
                fallback_recommended=True,  # Other approaches might be configured correctly
                confidence_impact=0.3,
                original_exception=original_exception,
                metadata=metadata
            )

        # Unknown error - be conservative
        return ErrorContext(
            category=ErrorCategory.UNKNOWN_ERROR,
            message=error_message,
            approach_used=approach,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.2,
            original_exception=original_exception,
            metadata=metadata
        )

    async def execute_with_retry(
        self,
        operation: Callable,
        retry_config: Optional[RetryConfig] = None,
        error_context_metadata: Optional[Dict[str, Any]] = None
    ) -> ActionResult:
        """
        Execute an operation with intelligent retry logic

        Args:
            operation: Async function that returns ActionResult
            retry_config: Configuration for retry behavior
            error_context_metadata: Additional metadata for error context

        Returns:
            ActionResult from the operation (successful or final failure)
        """
        config = retry_config or RetryConfig()
        last_result = None
        last_error_context = None

        for attempt in range(config.max_retries + 1):
            try:
                start_time = time.time()

                # Apply timeout
                result = await asyncio.wait_for(
                    operation(),
                    timeout=config.timeout_seconds
                )

                # Record successful execution
                self._record_success(result, attempt)
                return result

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                error_context = ErrorContext(
                    category=ErrorCategory.TIMEOUT_ERROR,
                    message=f"Operation timed out after {config.timeout_seconds}s",
                    approach_used=AutomationApproach.DOM_ANALYSIS,  # Default
                    retryable=True,
                    fallback_recommended=True,
                    confidence_impact=0.3,
                    metadata=error_context_metadata
                )

                last_result = ActionResult(
                    success=False,
                    approach_used=AutomationApproach.DOM_ANALYSIS,
                    confidence=0.0,
                    execution_time=execution_time,
                    result_data={'timeout': True},
                    error_message=error_context.message
                )

                last_error_context = error_context

            except Exception as e:
                execution_time = time.time() - start_time

                # Categorize the error
                error_context = self.categorize_error(
                    e,
                    AutomationApproach.DOM_ANALYSIS,  # Default, should be passed by caller
                    error_context_metadata
                )

                last_result = ActionResult(
                    success=False,
                    approach_used=error_context.approach_used,
                    confidence=0.0,
                    execution_time=execution_time,
                    result_data={'error_category': error_context.category.value},
                    error_message=error_context.message
                )

                last_error_context = error_context

                # Record error for learning
                self._record_error(error_context, attempt)

                # Check if we should retry
                if not error_context.retryable or attempt >= config.max_retries:
                    break

                # Calculate delay for next attempt
                if attempt < config.max_retries:
                    delay = self._calculate_retry_delay(
                        attempt, config, error_context.category
                    )

                    logger.warning(
                        f"Attempt {attempt + 1} failed ({error_context.category.value}). "
                        f"Retrying in {delay:.1f}s: {error_context.message}"
                    )

                    await asyncio.sleep(delay)

        # All retries exhausted
        if last_error_context and last_result:
            last_result.recommendation = self._generate_failure_recommendation(last_error_context)

        return last_result or ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.0,
            execution_time=0.0,
            result_data={},
            error_message="Unknown error in retry loop"
        )

    def _calculate_retry_delay(
        self,
        attempt: int,
        config: RetryConfig,
        error_category: ErrorCategory
    ) -> float:
        """Calculate delay before next retry attempt"""
        if config.exponential_backoff:
            delay = config.base_delay * (2 ** attempt)
        else:
            delay = config.base_delay

        # Apply category-specific multipliers
        category_multipliers = {
            ErrorCategory.NETWORK_ERROR: 1.5,  # Network issues benefit from longer delays
            ErrorCategory.PAGE_LOAD_ERROR: 1.2,
            ErrorCategory.TIMEOUT_ERROR: 1.3,
            ErrorCategory.BROWSER_ERROR: 2.0,  # Browser issues need recovery time
            ErrorCategory.ELEMENT_NOT_FOUND: 0.8,  # Quick retry for element issues
            ErrorCategory.INTERACTION_FAILED: 0.9,
        }

        multiplier = category_multipliers.get(error_category, 1.0)
        delay *= multiplier

        # Apply jitter if enabled
        if config.jitter:
            import random
            jitter_factor = 0.1  # ±10% jitter
            delay *= (1 + random.uniform(-jitter_factor, jitter_factor))

        # Respect max delay
        return min(delay, config.max_delay)

    def _generate_failure_recommendation(self, error_context: ErrorContext) -> str:
        """Generate recommendation based on error context"""
        recommendations = {
            ErrorCategory.NETWORK_ERROR:
                "Check network connectivity and try again later. Consider using a different network.",
            ErrorCategory.PAGE_LOAD_ERROR:
                "Verify the URL is accessible. The page may be temporarily unavailable.",
            ErrorCategory.ELEMENT_NOT_FOUND:
                "The page structure may have changed. Consider updating element selectors or using a different approach.",
            ErrorCategory.INTERACTION_FAILED:
                "The element may be hidden or disabled. Try waiting longer or using a different interaction method.",
            ErrorCategory.PERMISSION_DENIED:
                "Access is restricted. Check authentication or try from a different context.",
            ErrorCategory.BROWSER_ERROR:
                "Browser automation failed. Try restarting the browser or using a different approach.",
            ErrorCategory.TIMEOUT_ERROR:
                "Operation took too long. Try increasing timeout or breaking into smaller steps.",
            ErrorCategory.CONFIGURATION_ERROR:
                "Check system configuration and ensure all required dependencies are installed.",
            ErrorCategory.UNKNOWN_ERROR:
                "An unexpected error occurred. Check logs and consider manual intervention."
        }

        base_recommendation = recommendations.get(
            error_context.category,
            "Review the error and try a different approach."
        )

        if error_context.fallback_recommended:
            base_recommendation += " Consider trying a different automation approach."

        return base_recommendation

    def _record_success(self, result: ActionResult, attempts: int) -> None:
        """Record successful execution for learning"""
        try:
            record = {
                'timestamp': time.time(),
                'success': True,
                'approach': result.approach_used.value,
                'attempts': attempts + 1,
                'execution_time': result.execution_time,
                'confidence': result.confidence
            }

            self.error_history.append(record)

            # Keep only recent history
            if len(self.error_history) > 500:
                self.error_history = self.error_history[-500:]

        except Exception as e:
            logger.error(f"Error recording success: {e}")

    def _record_error(self, error_context: ErrorContext, attempt: int) -> None:
        """Record error for learning and pattern recognition"""
        try:
            record = {
                'timestamp': time.time(),
                'success': False,
                'approach': error_context.approach_used.value,
                'category': error_context.category.value,
                'attempt': attempt + 1,
                'retryable': error_context.retryable,
                'fallback_recommended': error_context.fallback_recommended,
                'message': error_context.message,
                'metadata': error_context.metadata
            }

            self.error_history.append(record)

            # Update error patterns
            pattern_key = f"{error_context.approach_used.value}:{error_context.category.value}"
            self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1

            # Keep only recent history
            if len(self.error_history) > 500:
                self.error_history = self.error_history[-500:]

        except Exception as e:
            logger.error(f"Error recording error: {e}")

    def get_error_analytics(self) -> Dict[str, Any]:
        """Get analytics about error patterns and handling"""
        if not self.error_history:
            return {
                'total_operations': 0,
                'success_rate': 0.0,
                'error_patterns': {},
                'recovery_stats': {}
            }

        total_operations = len(self.error_history)
        successful_operations = sum(1 for r in self.error_history if r['success'])
        success_rate = successful_operations / total_operations

        # Calculate retry success rates
        retry_stats = {}
        for record in self.error_history:
            if record['success'] and record.get('attempts', 1) > 1:
                attempts = record['attempts']
                if attempts not in retry_stats:
                    retry_stats[attempts] = {'count': 0, 'success_rate': 0.0}
                retry_stats[attempts]['count'] += 1

        # Calculate error category distribution
        error_categories = {}
        for record in self.error_history:
            if not record['success']:
                category = record.get('category', 'unknown')
                error_categories[category] = error_categories.get(category, 0) + 1

        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': success_rate,
            'error_patterns': self.error_patterns.copy(),
            'error_categories': error_categories,
            'retry_stats': retry_stats,
            'recent_errors': [r for r in self.error_history[-20:] if not r['success']]
        }

    def clear_history(self) -> int:
        """Clear error history and return number of records cleared"""
        count = len(self.error_history)
        self.error_history.clear()
        self.error_patterns.clear()
        logger.info(f"Cleared {count} error handling records")
        return count


# Global unified error handler instance
unified_error_handler = UnifiedErrorHandler()