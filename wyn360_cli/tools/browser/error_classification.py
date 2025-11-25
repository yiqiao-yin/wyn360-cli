"""
Error Classification System for Browser Automation

This module provides intelligent error analysis and classification for browser
automation failures, enabling adaptive recovery strategies.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import traceback


class ErrorCategory(Enum):
    """Categories of browser automation errors"""
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    NAVIGATION_ERROR = "navigation_error"
    PAGE_LOAD_ERROR = "page_load_error"
    INTERACTION_ERROR = "interaction_error"
    SECURITY_ERROR = "security_error"
    NETWORK_ERROR = "network_error"
    SCRIPT_ERROR = "script_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"           # Minor issues that can be retried easily
    MEDIUM = "medium"     # Moderate issues requiring code adaptation
    HIGH = "high"         # Serious issues requiring significant changes
    CRITICAL = "critical" # Issues that may require manual intervention


@dataclass
class ErrorPattern:
    """Pattern definition for error classification"""
    category: ErrorCategory
    severity: ErrorSeverity
    patterns: List[str]  # Regex patterns to match
    keywords: List[str]  # Keywords to look for
    exception_types: List[str]  # Exception class names
    recovery_hint: str   # Suggestion for recovery


@dataclass
class ErrorAnalysis:
    """Result of error analysis"""
    category: ErrorCategory
    severity: ErrorSeverity
    confidence: float  # 0-1, how confident we are in this classification
    original_error: str
    matched_patterns: List[str]
    recovery_suggestions: List[str]
    context_info: Dict[str, Any]


class ErrorClassifier:
    """
    Intelligent error classification system for browser automation
    """

    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()

    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize error classification patterns"""
        patterns = [
            # Timeout errors
            ErrorPattern(
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                patterns=[
                    r'timeout.*exceeded',
                    r'element.*not.*visible.*within.*timeout',
                    r'page.*load.*timeout',
                    r'wait.*condition.*timed.*out',
                    r'execution.*timeout'
                ],
                keywords=['timeout', 'timed out', 'exceeded', 'wait'],
                exception_types=['TimeoutError', 'ExecutionTimeout', 'PlaywrightTimeoutError'],
                recovery_hint="Increase timeout values or add explicit waits"
            ),

            # Element not found errors
            ErrorPattern(
                category=ErrorCategory.ELEMENT_NOT_FOUND,
                severity=ErrorSeverity.MEDIUM,
                patterns=[
                    r'element.*not.*found',
                    r'locator.*not.*found',
                    r'selector.*not.*found',
                    r'no.*element.*matching',
                    r'element.*is.*not.*attached'
                ],
                keywords=['not found', 'no element', 'selector', 'locator'],
                exception_types=['ElementNotFound', 'NoSuchElementException'],
                recovery_hint="Try alternative selectors or wait for element to appear"
            ),

            # Navigation errors
            ErrorPattern(
                category=ErrorCategory.NAVIGATION_ERROR,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r'navigation.*failed',
                    r'page.*not.*loaded',
                    r'failed.*to.*navigate',
                    r'url.*unreachable',
                    r'navigation.*timeout'
                ],
                keywords=['navigation', 'navigate', 'failed', 'unreachable'],
                exception_types=['NavigationError'],
                recovery_hint="Check URL validity and network connectivity"
            ),

            # Page load errors
            ErrorPattern(
                category=ErrorCategory.PAGE_LOAD_ERROR,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r'page.*failed.*to.*load',
                    r'resource.*loading.*failed',
                    r'page.*crash',
                    r'page.*unresponsive',
                    r'document.*not.*ready'
                ],
                keywords=['page', 'load', 'failed', 'crash', 'unresponsive'],
                exception_types=['PageCrashError'],
                recovery_hint="Reload page or check for network issues"
            ),

            # Interaction errors
            ErrorPattern(
                category=ErrorCategory.INTERACTION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                patterns=[
                    r'element.*not.*interactable',
                    r'element.*not.*clickable',
                    r'element.*is.*disabled',
                    r'element.*obscured',
                    r'click.*intercepted'
                ],
                keywords=['not interactable', 'not clickable', 'disabled', 'obscured'],
                exception_types=['ElementNotInteractableException'],
                recovery_hint="Wait for element to become interactable or scroll into view"
            ),

            # Security errors
            ErrorPattern(
                category=ErrorCategory.SECURITY_ERROR,
                severity=ErrorSeverity.CRITICAL,
                patterns=[
                    r'security.*violation',
                    r'blocked.*by.*cors',
                    r'permission.*denied',
                    r'access.*denied',
                    r'blocked.*by.*security.*policy'
                ],
                keywords=['security', 'cors', 'permission', 'denied', 'blocked'],
                exception_types=['SecurityError', 'SecurityViolation'],
                recovery_hint="Check security policies or use different approach"
            ),

            # Network errors
            ErrorPattern(
                category=ErrorCategory.NETWORK_ERROR,
                severity=ErrorSeverity.HIGH,
                patterns=[
                    r'network.*error',
                    r'connection.*refused',
                    r'dns.*resolution.*failed',
                    r'net::err_.*',
                    r'fetch.*failed'
                ],
                keywords=['network', 'connection', 'dns', 'fetch', 'refused'],
                exception_types=['NetworkError', 'ConnectionError'],
                recovery_hint="Check network connectivity and try again"
            ),

            # Script execution errors
            ErrorPattern(
                category=ErrorCategory.SCRIPT_ERROR,
                severity=ErrorSeverity.MEDIUM,
                patterns=[
                    r'javascript.*error',
                    r'script.*error',
                    r'evaluation.*failed',
                    r'syntax.*error.*in.*script',
                    r'execution.*error'
                ],
                keywords=['javascript', 'script', 'evaluation', 'syntax'],
                exception_types=['JavaScriptException', 'ScriptError', 'SyntaxError'],
                recovery_hint="Check script syntax and execution context"
            )
        ]

        return patterns

    def classify_error(self,
                      error: Exception,
                      error_context: Optional[Dict[str, Any]] = None) -> ErrorAnalysis:
        """
        Classify an error and provide analysis

        Args:
            error: The exception that occurred
            error_context: Additional context about the error

        Returns:
            ErrorAnalysis with classification and suggestions
        """
        error_str = str(error)
        error_type = type(error).__name__

        if error_context is None:
            error_context = {}

        # Get full traceback for additional context
        tb_str = traceback.format_exc()

        best_match = None
        highest_confidence = 0.0

        # Try to match against each pattern
        for pattern in self.error_patterns:
            confidence = self._calculate_confidence(
                error_str, error_type, tb_str, pattern
            )

            if confidence > highest_confidence:
                highest_confidence = confidence
                best_match = pattern

        # If no good match found, classify as unknown
        if highest_confidence < 0.2 or best_match is None:
            category = ErrorCategory.UNKNOWN_ERROR
            severity = ErrorSeverity.MEDIUM
            recovery_hint = "Try general error recovery strategies"
            matched_patterns = []
        else:
            category = best_match.category
            severity = best_match.severity
            recovery_hint = best_match.recovery_hint
            matched_patterns = self._get_matched_patterns(error_str, tb_str, best_match)

        # Generate recovery suggestions
        recovery_suggestions = self._generate_recovery_suggestions(
            category, severity, error_str, error_context
        )

        return ErrorAnalysis(
            category=category,
            severity=severity,
            confidence=highest_confidence,
            original_error=error_str,
            matched_patterns=matched_patterns,
            recovery_suggestions=recovery_suggestions,
            context_info=error_context
        )

    def _calculate_confidence(self,
                            error_str: str,
                            error_type: str,
                            traceback_str: str,
                            pattern: ErrorPattern) -> float:
        """Calculate confidence score for a pattern match"""
        confidence = 0.0

        # Check exception type match
        if error_type in pattern.exception_types:
            confidence += 0.6  # High weight for exact type match

        # Check regex patterns
        pattern_matches = 0
        for regex_pattern in pattern.patterns:
            if re.search(regex_pattern, error_str, re.IGNORECASE) or \
               re.search(regex_pattern, traceback_str, re.IGNORECASE):
                pattern_matches += 1

        if pattern_matches > 0:
            # Give higher confidence for pattern matches
            confidence += 0.5 * (pattern_matches / len(pattern.patterns))

        # Check keywords
        keyword_matches = 0
        for keyword in pattern.keywords:
            if keyword.lower() in error_str.lower() or \
               keyword.lower() in traceback_str.lower():
                keyword_matches += 1

        if keyword_matches > 0:
            # Give additional confidence for keyword matches
            confidence += 0.4 * (keyword_matches / len(pattern.keywords))

        return min(confidence, 1.0)  # Cap at 1.0

    def _get_matched_patterns(self,
                            error_str: str,
                            traceback_str: str,
                            pattern: ErrorPattern) -> List[str]:
        """Get list of patterns that matched"""
        matched = []

        for regex_pattern in pattern.patterns:
            if re.search(regex_pattern, error_str, re.IGNORECASE) or \
               re.search(regex_pattern, traceback_str, re.IGNORECASE):
                matched.append(regex_pattern)

        return matched

    def _generate_recovery_suggestions(self,
                                     category: ErrorCategory,
                                     severity: ErrorSeverity,
                                     error_str: str,
                                     context: Dict[str, Any]) -> List[str]:
        """Generate specific recovery suggestions based on error category"""
        suggestions = []

        if category == ErrorCategory.TIMEOUT:
            suggestions.extend([
                "Increase timeout values (page.wait_for_selector timeout)",
                "Add explicit waits before interactions",
                "Use wait_for_load_state('networkidle') after navigation",
                "Check if elements need time to render"
            ])

        elif category == ErrorCategory.ELEMENT_NOT_FOUND:
            suggestions.extend([
                "Try more robust CSS selectors (data attributes, unique classes)",
                "Use text-based selectors as fallback",
                "Add wait for element to appear",
                "Check if element is in iframe or shadow DOM",
                "Verify page has fully loaded before searching"
            ])

        elif category == ErrorCategory.INTERACTION_ERROR:
            suggestions.extend([
                "Scroll element into view before interaction",
                "Wait for element to become visible and enabled",
                "Check if element is covered by overlay or modal",
                "Use force=True for click operations if safe",
                "Wait for any animations to complete"
            ])

        elif category == ErrorCategory.NAVIGATION_ERROR:
            suggestions.extend([
                "Verify URL is valid and accessible",
                "Check network connectivity",
                "Add retry logic with exponential backoff",
                "Use different navigation approach (direct URL vs clicks)"
            ])

        elif category == ErrorCategory.PAGE_LOAD_ERROR:
            suggestions.extend([
                "Reload the page and retry operation",
                "Check for JavaScript errors on page",
                "Wait longer for page stabilization",
                "Try navigation with different wait conditions"
            ])

        elif category == ErrorCategory.SCRIPT_ERROR:
            suggestions.extend([
                "Check JavaScript syntax in generated code",
                "Verify execution context is correct",
                "Use page.evaluate instead of direct script injection",
                "Add error handling around script execution"
            ])

        # Add severity-based suggestions
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            suggestions.append("Consider using fallback automation approach")
            suggestions.append("May require manual intervention or different strategy")

        return suggestions


class ErrorRecoveryPlanner:
    """
    Plans recovery strategies based on error analysis
    """

    def __init__(self, classifier: Optional[ErrorClassifier] = None):
        self.classifier = classifier or ErrorClassifier()

    def plan_recovery(self,
                     error: Exception,
                     automation_code: str,
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan recovery strategy for failed automation

        Args:
            error: The exception that occurred
            automation_code: The original automation code that failed
            context: Execution context and browser state

        Returns:
            Recovery plan with suggested modifications
        """
        # Classify the error
        analysis = self.classifier.classify_error(error, context)

        # Generate recovery plan
        recovery_plan = {
            'error_analysis': analysis,
            'code_modifications': self._suggest_code_modifications(analysis, automation_code),
            'retry_strategy': self._suggest_retry_strategy(analysis),
            'alternative_approaches': self._suggest_alternatives(analysis, automation_code),
            'confidence_score': analysis.confidence
        }

        return recovery_plan

    def _suggest_code_modifications(self,
                                  analysis: ErrorAnalysis,
                                  original_code: str) -> List[Dict[str, str]]:
        """Suggest specific code modifications"""
        modifications = []

        if analysis.category == ErrorCategory.TIMEOUT:
            modifications.extend([
                {
                    'type': 'timeout_increase',
                    'description': 'Increase timeout values',
                    'pattern': r'timeout=(\d+)',
                    'replacement': lambda m: f'timeout={int(m.group(1)) * 2}'
                },
                {
                    'type': 'add_wait',
                    'description': 'Add explicit wait before interactions',
                    'insert_before': r'(await page\.(click|fill|press))',
                    'code': 'await page.wait_for_load_state("networkidle")\n'
                }
            ])

        elif analysis.category == ErrorCategory.ELEMENT_NOT_FOUND:
            modifications.extend([
                {
                    'type': 'selector_improvement',
                    'description': 'Try multiple selector strategies',
                    'pattern': r'page\.locator\([\'"]([^\'"]+)[\'"]\)',
                    'replacement': self._generate_robust_selector_code
                },
                {
                    'type': 'add_element_wait',
                    'description': 'Wait for element to appear',
                    'insert_before': r'(await page\.locator)',
                    'code': 'await page.wait_for_selector("{selector}", state="visible")\n'
                }
            ])

        elif analysis.category == ErrorCategory.INTERACTION_ERROR:
            modifications.extend([
                {
                    'type': 'scroll_into_view',
                    'description': 'Scroll element into view before interaction',
                    'insert_before': r'(await .*\.(click|fill|press))',
                    'code': 'await {element}.scroll_into_view_if_needed()\n'
                },
                {
                    'type': 'force_click',
                    'description': 'Use force click if element is covered',
                    'pattern': r'\.click\(\)',
                    'replacement': '.click(force=True)'
                }
            ])

        return modifications

    def _suggest_retry_strategy(self, analysis: ErrorAnalysis) -> Dict[str, Any]:
        """Suggest retry strategy based on error type"""
        base_strategy = {
            'max_retries': 3,
            'backoff_factor': 1.0,
            'retry_exceptions': [type(analysis.original_error).__name__]
        }

        if analysis.category == ErrorCategory.TIMEOUT:
            base_strategy.update({
                'max_retries': 2,  # Fewer retries for timeouts
                'backoff_factor': 2.0,  # Longer delays
                'timeout_multiplier': 1.5  # Increase timeouts on retry
            })

        elif analysis.category == ErrorCategory.NETWORK_ERROR:
            base_strategy.update({
                'max_retries': 5,  # More retries for network issues
                'backoff_factor': 2.0,
                'initial_delay': 5.0  # Start with longer delay
            })

        elif analysis.category in [ErrorCategory.SECURITY_ERROR, ErrorCategory.SCRIPT_ERROR]:
            base_strategy.update({
                'max_retries': 1,  # Don't retry much for these
                'requires_code_change': True
            })

        return base_strategy

    def _suggest_alternatives(self,
                            analysis: ErrorAnalysis,
                            original_code: str) -> List[Dict[str, str]]:
        """Suggest alternative automation approaches"""
        alternatives = []

        if analysis.category == ErrorCategory.ELEMENT_NOT_FOUND:
            alternatives.extend([
                {
                    'approach': 'text_based_selection',
                    'description': 'Use text content instead of selectors',
                    'example': 'page.get_by_text("Submit").click()'
                },
                {
                    'approach': 'keyboard_navigation',
                    'description': 'Use keyboard navigation instead of clicks',
                    'example': 'page.keyboard.press("Tab"); page.keyboard.press("Enter")'
                }
            ])

        elif analysis.category == ErrorCategory.INTERACTION_ERROR:
            alternatives.extend([
                {
                    'approach': 'javascript_injection',
                    'description': 'Use JavaScript to trigger interactions',
                    'example': 'page.evaluate("document.querySelector(selector).click()")'
                },
                {
                    'approach': 'hover_first',
                    'description': 'Hover before clicking to reveal element',
                    'example': 'await element.hover(); await element.click()'
                }
            ])

        return alternatives

    def _generate_robust_selector_code(self, selector: str) -> str:
        """Generate code with multiple selector fallbacks"""
        return f'''
# Try multiple selector strategies
selectors = [
    "{selector}",
    "[data-testid*='{selector.split()[-1] if selector.split() else selector}']",
    "[aria-label*='{selector.split()[-1] if selector.split() else selector}']"
]

element = None
for sel in selectors:
    try:
        element = page.locator(sel)
        if await element.is_visible():
            break
    except:
        continue

if not element or not await element.is_visible():
    # Fallback to text-based selection
    element = page.get_by_text("{selector}", exact=False)
'''


# Export the main classes
__all__ = [
    'ErrorCategory',
    'ErrorSeverity',
    'ErrorAnalysis',
    'ErrorClassifier',
    'ErrorRecoveryPlanner'
]