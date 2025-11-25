"""
Intelligent Error Recovery System for Browser Automation

This module provides adaptive error recovery with code regeneration based on
error analysis and context understanding.
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .error_classification import (
    ErrorClassifier,
    ErrorRecoveryPlanner,
    ErrorCategory,
    ErrorSeverity,
    ErrorAnalysis
)
from .enhanced_code_generator import EnhancedCodeGenerator, CodeGenerationContext
from .secure_python_sandbox import SecurePythonSandbox, SandboxConfig, SandboxError


class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    CODE_MODIFICATION = "code_modification"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    ALTERNATIVE_APPROACH = "alternative_approach"
    FALLBACK_MODE = "fallback_mode"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class RecoveryAttempt:
    """Record of a recovery attempt"""
    attempt_number: int
    strategy: RecoveryStrategy
    modifications_made: List[str]
    success: bool
    error_encountered: Optional[str]
    execution_time: float
    generated_code: str
    confidence_score: float


@dataclass
class RecoverySession:
    """Complete recovery session data"""
    original_error: str
    original_code: str
    context: Dict[str, Any]
    attempts: List[RecoveryAttempt]
    final_success: bool
    total_recovery_time: float
    lessons_learned: List[str]


class IntelligentErrorRecovery:
    """
    Main error recovery system with adaptive learning
    """

    def __init__(self,
                 code_generator: Optional[EnhancedCodeGenerator] = None,
                 sandbox_config: Optional[SandboxConfig] = None):
        self.code_generator = code_generator or EnhancedCodeGenerator()
        self.sandbox_config = sandbox_config or SandboxConfig()
        self.error_classifier = ErrorClassifier()
        self.recovery_planner = ErrorRecoveryPlanner(self.error_classifier)
        self.logger = logging.getLogger(__name__)

        # Recovery statistics and learning
        self.recovery_history: List[RecoverySession] = []
        self.strategy_success_rates: Dict[str, float] = {}

    async def recover_from_error(self,
                                error: Exception,
                                original_code: str,
                                context: CodeGenerationContext,
                                browser_context: Dict[str, Any],
                                max_attempts: int = 3) -> Tuple[bool, str, RecoverySession]:
        """
        Attempt to recover from automation error with adaptive strategies

        Args:
            error: The original exception
            original_code: The automation code that failed
            context: Code generation context
            browser_context: Browser objects and state
            max_attempts: Maximum recovery attempts

        Returns:
            Tuple of (success, recovered_code, recovery_session)
        """
        session_start = time.time()
        recovery_session = RecoverySession(
            original_error=str(error),
            original_code=original_code,
            context=asdict(context),
            attempts=[],
            final_success=False,
            total_recovery_time=0.0,
            lessons_learned=[]
        )

        self.logger.info(f"Starting error recovery for: {type(error).__name__}")

        try:
            # Analyze the error
            error_analysis = self.error_classifier.classify_error(
                error, {"code": original_code, "context": context}
            )

            self.logger.info(f"Error classified as: {error_analysis.category.value} "
                           f"(confidence: {error_analysis.confidence:.2f})")

            # Get recovery plan
            recovery_plan = self.recovery_planner.plan_recovery(
                error, original_code, browser_context
            )

            # Attempt recovery with different strategies
            for attempt_num in range(1, max_attempts + 1):
                self.logger.info(f"Recovery attempt {attempt_num}/{max_attempts}")

                # Choose strategy for this attempt
                strategy = self._choose_recovery_strategy(
                    error_analysis, recovery_plan, attempt_num, recovery_session.attempts
                )

                # Execute recovery attempt
                attempt_result = await self._execute_recovery_attempt(
                    strategy, error_analysis, recovery_plan, context,
                    browser_context, original_code, attempt_num
                )

                recovery_session.attempts.append(attempt_result)

                if attempt_result.success:
                    recovery_session.final_success = True
                    recovery_session.total_recovery_time = time.time() - session_start

                    self.logger.info(f"Recovery successful on attempt {attempt_num}")

                    # Learn from successful recovery
                    self._learn_from_success(error_analysis, strategy, attempt_result)

                    # Record lessons learned
                    recovery_session.lessons_learned = self._extract_lessons(
                        error_analysis, recovery_session.attempts
                    )

                    self.recovery_history.append(recovery_session)

                    return True, attempt_result.generated_code, recovery_session

                else:
                    self.logger.warning(f"Recovery attempt {attempt_num} failed: "
                                      f"{attempt_result.error_encountered}")

            # All attempts failed
            recovery_session.final_success = False
            recovery_session.total_recovery_time = time.time() - session_start
            recovery_session.lessons_learned = self._extract_lessons(
                error_analysis, recovery_session.attempts
            )

            self.recovery_history.append(recovery_session)

            self.logger.error("All recovery attempts failed")

            return False, original_code, recovery_session

        except Exception as recovery_error:
            self.logger.error(f"Error during recovery process: {recovery_error}")
            recovery_session.total_recovery_time = time.time() - session_start
            self.recovery_history.append(recovery_session)

            return False, original_code, recovery_session

    def _choose_recovery_strategy(self,
                                 error_analysis: ErrorAnalysis,
                                 recovery_plan: Dict[str, Any],
                                 attempt_number: int,
                                 previous_attempts: List[RecoveryAttempt]) -> RecoveryStrategy:
        """Choose the best recovery strategy for this attempt"""

        # Get strategies that haven't been tried yet
        tried_strategies = {attempt.strategy for attempt in previous_attempts}

        # Strategy priority based on error category and attempt number
        if error_analysis.category == ErrorCategory.TIMEOUT:
            strategy_priority = [
                RecoveryStrategy.PARAMETER_ADJUSTMENT,
                RecoveryStrategy.CODE_MODIFICATION,
                RecoveryStrategy.ALTERNATIVE_APPROACH
            ]
        elif error_analysis.category == ErrorCategory.ELEMENT_NOT_FOUND:
            strategy_priority = [
                RecoveryStrategy.CODE_MODIFICATION,
                RecoveryStrategy.ALTERNATIVE_APPROACH,
                RecoveryStrategy.PARAMETER_ADJUSTMENT
            ]
        elif error_analysis.category == ErrorCategory.INTERACTION_ERROR:
            strategy_priority = [
                RecoveryStrategy.CODE_MODIFICATION,
                RecoveryStrategy.PARAMETER_ADJUSTMENT,
                RecoveryStrategy.ALTERNATIVE_APPROACH
            ]
        else:
            # General fallback order
            strategy_priority = [
                RecoveryStrategy.CODE_MODIFICATION,
                RecoveryStrategy.PARAMETER_ADJUSTMENT,
                RecoveryStrategy.ALTERNATIVE_APPROACH,
                RecoveryStrategy.FALLBACK_MODE
            ]

        # Choose first strategy that hasn't been tried
        for strategy in strategy_priority:
            if strategy not in tried_strategies:
                return strategy

        # If all strategies tried, use manual intervention
        return RecoveryStrategy.MANUAL_INTERVENTION

    async def _execute_recovery_attempt(self,
                                       strategy: RecoveryStrategy,
                                       error_analysis: ErrorAnalysis,
                                       recovery_plan: Dict[str, Any],
                                       context: CodeGenerationContext,
                                       browser_context: Dict[str, Any],
                                       original_code: str,
                                       attempt_number: int) -> RecoveryAttempt:
        """Execute a specific recovery strategy"""

        attempt_start = time.time()

        try:
            if strategy == RecoveryStrategy.CODE_MODIFICATION:
                modified_code, modifications = await self._apply_code_modifications(
                    original_code, error_analysis, recovery_plan
                )

            elif strategy == RecoveryStrategy.PARAMETER_ADJUSTMENT:
                modified_code, modifications = await self._adjust_parameters(
                    original_code, error_analysis, recovery_plan
                )

            elif strategy == RecoveryStrategy.ALTERNATIVE_APPROACH:
                modified_code, modifications = await self._generate_alternative_approach(
                    context, error_analysis, recovery_plan
                )

            elif strategy == RecoveryStrategy.FALLBACK_MODE:
                modified_code, modifications = await self._generate_fallback_code(
                    context, error_analysis
                )

            else:  # MANUAL_INTERVENTION
                modified_code = original_code
                modifications = ["Manual intervention required"]

            # Test the modified code in sandbox
            success, error_msg = await self._test_code_in_sandbox(
                modified_code, browser_context
            )

            # Calculate confidence score
            confidence = self._calculate_attempt_confidence(
                strategy, error_analysis, modifications, success
            )

            return RecoveryAttempt(
                attempt_number=attempt_number,
                strategy=strategy,
                modifications_made=modifications,
                success=success,
                error_encountered=error_msg,
                execution_time=time.time() - attempt_start,
                generated_code=modified_code,
                confidence_score=confidence
            )

        except Exception as e:
            return RecoveryAttempt(
                attempt_number=attempt_number,
                strategy=strategy,
                modifications_made=[],
                success=False,
                error_encountered=str(e),
                execution_time=time.time() - attempt_start,
                generated_code=original_code,
                confidence_score=0.0
            )

    async def _apply_code_modifications(self,
                                      original_code: str,
                                      error_analysis: ErrorAnalysis,
                                      recovery_plan: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Apply intelligent code modifications based on error analysis"""

        modified_code = original_code
        modifications = []

        # Get suggested modifications from recovery plan
        code_modifications = recovery_plan.get('code_modifications', [])

        for modification in code_modifications:
            mod_type = modification.get('type')
            description = modification.get('description')

            if mod_type == 'timeout_increase':
                modified_code, applied = self._increase_timeouts(modified_code)
                if applied:
                    modifications.append(f"Increased timeouts: {description}")

            elif mod_type == 'add_wait':
                modified_code, applied = self._add_waits(modified_code)
                if applied:
                    modifications.append(f"Added waits: {description}")

            elif mod_type == 'selector_improvement':
                modified_code, applied = self._improve_selectors(modified_code)
                if applied:
                    modifications.append(f"Improved selectors: {description}")

            elif mod_type == 'scroll_into_view':
                modified_code, applied = self._add_scrolling(modified_code)
                if applied:
                    modifications.append(f"Added scrolling: {description}")

            elif mod_type == 'force_click':
                modified_code, applied = self._add_force_clicks(modified_code)
                if applied:
                    modifications.append(f"Added force clicks: {description}")

        return modified_code, modifications

    async def _adjust_parameters(self,
                               original_code: str,
                               error_analysis: ErrorAnalysis,
                               recovery_plan: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Adjust parameters like timeouts, delays, etc."""

        modified_code = original_code
        modifications = []

        # Increase timeout values
        timeout_pattern = r'timeout=(\d+)'
        timeouts_found = re.findall(timeout_pattern, modified_code)

        if timeouts_found:
            for timeout_val in timeouts_found:
                new_timeout = int(timeout_val) * 2
                modified_code = re.sub(
                    f'timeout={timeout_val}',
                    f'timeout={new_timeout}',
                    modified_code
                )
                modifications.append(f"Increased timeout from {timeout_val}s to {new_timeout}s")

        # Add delays for rapid interactions
        if 'click' in modified_code.lower():
            # Add small delay after clicks
            click_pattern = r'(await .*\.click\(\))'
            modified_code = re.sub(
                click_pattern,
                r'\1\n    await page.wait_for_timeout(500)',
                modified_code
            )
            modifications.append("Added 500ms delay after clicks")

        return modified_code, modifications

    async def _generate_alternative_approach(self,
                                           context: CodeGenerationContext,
                                           error_analysis: ErrorAnalysis,
                                           recovery_plan: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Generate completely alternative automation approach"""

        modifications = ["Generated alternative automation approach"]

        # Create modified context with alternative strategy
        alt_context = CodeGenerationContext(
            task_description=f"Alternative approach: {context.task_description}",
            url=context.url,
            expected_output_schema=context.expected_output_schema,
            complexity=context.complexity,
            optimization_level=context.optimization_level,
            include_error_handling=True,  # Always include error handling in alternatives
            include_waits=True,  # Always include waits
            max_retries=context.max_retries + 1  # More retries
        )

        # Generate new code with alternative approach
        alternative_code = await self.code_generator.generate_automation_code(alt_context)

        # Apply category-specific alternative strategies
        if error_analysis.category == ErrorCategory.ELEMENT_NOT_FOUND:
            alternative_code = self._apply_text_based_alternatives(alternative_code)
            modifications.append("Used text-based element selection")

        elif error_analysis.category == ErrorCategory.INTERACTION_ERROR:
            alternative_code = self._apply_keyboard_alternatives(alternative_code)
            modifications.append("Used keyboard navigation alternatives")

        elif error_analysis.category == ErrorCategory.TIMEOUT:
            alternative_code = self._apply_patient_waiting(alternative_code)
            modifications.append("Applied patient waiting strategies")

        return alternative_code, modifications

    async def _generate_fallback_code(self,
                                    context: CodeGenerationContext,
                                    error_analysis: ErrorAnalysis) -> Tuple[str, List[str]]:
        """Generate simple, robust fallback automation code"""

        fallback_code = f'''
# Fallback automation approach for: {context.task_description}
import asyncio
import json

try:
    # Navigate to page with extended timeout
    await page.goto("{context.url}", timeout=60000, wait_until="networkidle")

    # Wait for page to stabilize
    await page.wait_for_timeout(3000)

    # Simple interaction strategy
    # Try to find any interactive elements
    buttons = await page.locator("button, input[type=submit], [role=button]").all()
    links = await page.locator("a").all()

    # Collect basic page information
    title = await page.title()
    url = page.url

    # Try to extract any visible text content
    content = await page.locator("body").inner_text()

    result = {{
        "success": True,
        "title": title,
        "url": url,
        "content_preview": content[:500],
        "found_buttons": len(buttons),
        "found_links": len(links),
        "approach": "fallback",
        "note": "Used simple fallback approach due to automation difficulties"
    }}

except Exception as fallback_error:
    result = {{
        "success": False,
        "error": str(fallback_error),
        "approach": "fallback_failed"
    }}
'''

        modifications = [
            "Generated simple fallback automation code",
            "Focused on basic page interaction and data collection",
            "Added comprehensive error handling"
        ]

        return fallback_code, modifications

    async def _test_code_in_sandbox(self,
                                  code: str,
                                  browser_context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Test modified code in secure sandbox"""

        try:
            sandbox = SecurePythonSandbox(self.sandbox_config)

            # Execute code with timeout
            result = await sandbox.execute_automation_script(code, browser_context)

            if result['success']:
                return True, None
            else:
                return False, result.get('errors', 'Unknown execution error')

        except Exception as e:
            return False, str(e)

    def _increase_timeouts(self, code: str) -> Tuple[str, bool]:
        """Increase timeout values in code"""
        original_code = code

        # Increase explicit timeouts
        code = re.sub(r'timeout=(\d+)', lambda m: f'timeout={int(m.group(1)) * 2}', code)

        # Add default timeouts where missing
        patterns_to_fix = [
            (r'(await page\.wait_for_selector\([^)]+)\)', r'\1, timeout=30000)'),
            (r'(await page\.goto\([^)]+)\)', r'\1, timeout=60000)'),
            (r'(await .*\.click\(\))', r'\1  # Added timeout handling')
        ]

        for pattern, replacement in patterns_to_fix:
            code = re.sub(pattern, replacement, code)

        return code, code != original_code

    def _add_waits(self, code: str) -> Tuple[str, bool]:
        """Add wait statements before interactions"""
        original_code = code

        # Add waits before clicks
        code = re.sub(
            r'(await .*\.click\(\))',
            r'await page.wait_for_load_state("networkidle")\n    \1',
            code
        )

        # Add waits before form fills
        code = re.sub(
            r'(await .*\.fill\([^)]+\))',
            r'await page.wait_for_timeout(500)\n    \1',
            code
        )

        return code, code != original_code

    def _improve_selectors(self, code: str) -> Tuple[str, bool]:
        """Improve CSS selectors with more robust alternatives"""
        original_code = code

        # Replace fragile selectors with more robust ones
        improvements = [
            # Replace generic classes with data attributes
            (r'\.locator\([\'"]\.btn[\'"]', r'.locator(\'[data-testid*="btn"], .btn, button\''),
            (r'\.locator\([\'"]\.submit[\'"]', r'.locator(\'[type="submit"], .submit, [data-testid*="submit"]\''),
            # Add text-based fallbacks
            (r'\.locator\([\'"]([^\'"\]]+)[\'"]', r'.locator(\'\1\').or_(page.get_by_text(\'\1\', exact=False))')
        ]

        for pattern, replacement in improvements:
            code = re.sub(pattern, replacement, code)

        return code, code != original_code

    def _add_scrolling(self, code: str) -> Tuple[str, bool]:
        """Add scroll-into-view before interactions"""
        original_code = code

        # Add scrolling before clicks
        code = re.sub(
            r'(element = .*\.locator[^\\n]+)\\n(\s*)(await element\.click)',
            r'\1\n\2await element.scroll_into_view_if_needed()\n\2\3',
            code
        )

        return code, code != original_code

    def _add_force_clicks(self, code: str) -> Tuple[str, bool]:
        """Add force=True to click operations"""
        original_code = code

        # Add force parameter to clicks
        code = re.sub(r'\.click\(\)', '.click(force=True)', code)

        return code, code != original_code

    def _apply_text_based_alternatives(self, code: str) -> str:
        """Apply text-based element selection alternatives"""

        # Add text-based selection fallbacks
        text_alternatives = '''
# Text-based element selection fallbacks
async def find_element_by_text(page, text_options, element_type="button"):
    for text in text_options:
        try:
            if element_type == "button":
                element = page.get_by_role("button", name=text)
            elif element_type == "link":
                element = page.get_by_role("link", name=text)
            else:
                element = page.get_by_text(text)

            if await element.is_visible():
                return element
        except:
            continue
    return None

'''
        return text_alternatives + code

    def _apply_keyboard_alternatives(self, code: str) -> str:
        """Apply keyboard navigation alternatives"""

        keyboard_alternatives = '''
# Keyboard navigation alternatives
async def keyboard_navigate_and_activate(page):
    # Try keyboard navigation as fallback
    await page.keyboard.press("Tab")  # Navigate to next element
    await page.keyboard.press("Enter")  # Activate current element

'''
        return keyboard_alternatives + code

    def _apply_patient_waiting(self, code: str) -> str:
        """Apply patient waiting strategies"""

        # Add comprehensive waiting before any interaction
        patient_waiting = '''
# Patient waiting strategies
await page.wait_for_load_state("load")
await page.wait_for_load_state("networkidle")
await page.wait_for_timeout(2000)  # Additional stabilization time

'''
        return patient_waiting + code

    def _calculate_attempt_confidence(self,
                                    strategy: RecoveryStrategy,
                                    error_analysis: ErrorAnalysis,
                                    modifications: List[str],
                                    success: bool) -> float:
        """Calculate confidence score for recovery attempt"""

        base_confidence = 0.5

        # Adjust based on strategy effectiveness for error type
        strategy_effectiveness = {
            (ErrorCategory.TIMEOUT, RecoveryStrategy.PARAMETER_ADJUSTMENT): 0.8,
            (ErrorCategory.ELEMENT_NOT_FOUND, RecoveryStrategy.CODE_MODIFICATION): 0.9,
            (ErrorCategory.INTERACTION_ERROR, RecoveryStrategy.CODE_MODIFICATION): 0.8,
            (ErrorCategory.NAVIGATION_ERROR, RecoveryStrategy.ALTERNATIVE_APPROACH): 0.7,
        }

        effectiveness = strategy_effectiveness.get(
            (error_analysis.category, strategy), 0.6
        )

        # Boost confidence based on number of modifications
        modification_boost = min(len(modifications) * 0.1, 0.3)

        # Success strongly increases confidence
        success_boost = 0.4 if success else 0.0

        # Factor in original error classification confidence
        classification_factor = error_analysis.confidence * 0.2

        total_confidence = min(
            base_confidence + effectiveness + modification_boost +
            success_boost + classification_factor, 1.0
        )

        return total_confidence

    def _learn_from_success(self,
                          error_analysis: ErrorAnalysis,
                          strategy: RecoveryStrategy,
                          attempt: RecoveryAttempt):
        """Learn from successful recovery attempts"""

        # Update strategy success rates
        strategy_key = f"{error_analysis.category.value}_{strategy.value}"

        if strategy_key not in self.strategy_success_rates:
            self.strategy_success_rates[strategy_key] = 0.0

        # Simple learning rate adjustment
        current_rate = self.strategy_success_rates[strategy_key]
        self.strategy_success_rates[strategy_key] = current_rate * 0.9 + 0.1 * 1.0

        self.logger.info(f"Updated success rate for {strategy_key}: "
                        f"{self.strategy_success_rates[strategy_key]:.2f}")

    def _extract_lessons(self,
                        error_analysis: ErrorAnalysis,
                        attempts: List[RecoveryAttempt]) -> List[str]:
        """Extract lessons learned from recovery session"""

        lessons = []

        # Analyze what worked
        successful_attempts = [a for a in attempts if a.success]
        if successful_attempts:
            successful_attempt = successful_attempts[0]
            lessons.append(f"Strategy '{successful_attempt.strategy.value}' succeeded "
                         f"for {error_analysis.category.value} errors")

            for modification in successful_attempt.modifications_made:
                lessons.append(f"Effective modification: {modification}")

        # Analyze what didn't work
        failed_attempts = [a for a in attempts if not a.success]
        for attempt in failed_attempts:
            lessons.append(f"Strategy '{attempt.strategy.value}' failed "
                         f"for {error_analysis.category.value} errors")

        # General lessons based on error category
        if error_analysis.category == ErrorCategory.TIMEOUT:
            lessons.append("Timeout errors often require increased wait times and patience")
        elif error_analysis.category == ErrorCategory.ELEMENT_NOT_FOUND:
            lessons.append("Element not found errors benefit from robust selector strategies")
        elif error_analysis.category == ErrorCategory.INTERACTION_ERROR:
            lessons.append("Interaction errors require element visibility and interactability checks")

        return lessons

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """Get statistics about recovery performance"""

        if not self.recovery_history:
            return {"total_sessions": 0}

        total_sessions = len(self.recovery_history)
        successful_sessions = len([s for s in self.recovery_history if s.final_success])

        avg_attempts = sum(len(s.attempts) for s in self.recovery_history) / total_sessions
        avg_recovery_time = sum(s.total_recovery_time for s in self.recovery_history) / total_sessions

        # Category success rates
        category_stats = {}
        for session in self.recovery_history:
            # Extract error category from first attempt if available
            if session.attempts:
                category = "unknown"  # Would need to store category in session
                if category not in category_stats:
                    category_stats[category] = {"total": 0, "successful": 0}
                category_stats[category]["total"] += 1
                if session.final_success:
                    category_stats[category]["successful"] += 1

        return {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate": successful_sessions / total_sessions if total_sessions > 0 else 0,
            "average_attempts": avg_attempts,
            "average_recovery_time": avg_recovery_time,
            "strategy_success_rates": self.strategy_success_rates.copy(),
            "category_stats": category_stats
        }


# Export main classes
__all__ = [
    'RecoveryStrategy',
    'RecoveryAttempt',
    'RecoverySession',
    'IntelligentErrorRecovery'
]