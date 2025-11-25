"""
Unit tests for Intelligent Error Recovery

Tests the error analysis, classification, and recovery functionality.
"""

import pytest
import asyncio
import re
from unittest.mock import Mock, AsyncMock, patch

from wyn360_cli.tools.browser.intelligent_error_recovery import (
    IntelligentErrorRecovery,
    RecoveryStrategy,
    RecoveryAttempt,
    RecoverySession
)
from wyn360_cli.tools.browser.error_classification import (
    ErrorClassifier,
    ErrorCategory,
    ErrorSeverity,
    ErrorAnalysis
)
from wyn360_cli.tools.browser.enhanced_code_generator import CodeGenerationContext


class TestErrorClassifier:
    """Test error classification functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.classifier = ErrorClassifier()

    def test_timeout_error_classification(self):
        """Test classification of timeout errors"""
        error = Exception("Element not visible within timeout of 30000ms")
        analysis = self.classifier.classify_error(error)

        assert analysis.category == ErrorCategory.TIMEOUT
        assert analysis.severity == ErrorSeverity.MEDIUM
        assert analysis.confidence > 0.3
        assert "timeout" in analysis.original_error.lower()

    def test_element_not_found_classification(self):
        """Test classification of element not found errors"""
        error = Exception("Locator '.submit-button' not found")
        analysis = self.classifier.classify_error(error)

        assert analysis.category == ErrorCategory.ELEMENT_NOT_FOUND
        assert analysis.severity == ErrorSeverity.MEDIUM
        assert analysis.confidence > 0.3
        assert len(analysis.recovery_suggestions) > 0

    def test_navigation_error_classification(self):
        """Test classification of navigation errors"""
        error = Exception("Navigation failed: URL unreachable")
        analysis = self.classifier.classify_error(error)

        assert analysis.category == ErrorCategory.NAVIGATION_ERROR
        assert analysis.severity == ErrorSeverity.HIGH
        assert analysis.confidence > 0.3

    def test_interaction_error_classification(self):
        """Test classification of interaction errors"""
        error = Exception("Element not interactable: element is disabled")
        analysis = self.classifier.classify_error(error)

        assert analysis.category == ErrorCategory.INTERACTION_ERROR
        assert analysis.severity == ErrorSeverity.MEDIUM
        assert analysis.confidence > 0.3

    def test_unknown_error_classification(self):
        """Test classification of unknown errors"""
        error = Exception("Some random error that doesn't match patterns")
        analysis = self.classifier.classify_error(error)

        # Should classify as unknown if confidence is low
        assert analysis.category in [ErrorCategory.UNKNOWN_ERROR, ErrorCategory.SCRIPT_ERROR]
        assert analysis.confidence >= 0.0

    def test_error_classification_with_context(self):
        """Test error classification with additional context"""
        error = Exception("Element not found")
        context = {
            "code": "await page.locator('.missing-element').click()",
            "url": "https://test.com"
        }

        analysis = self.classifier.classify_error(error, context)

        assert analysis.category == ErrorCategory.ELEMENT_NOT_FOUND
        assert analysis.context_info == context

    def test_confidence_calculation(self):
        """Test confidence calculation accuracy"""
        # High confidence case
        high_conf_error = Exception("TimeoutError: Element not visible within timeout")
        analysis = self.classifier.classify_error(high_conf_error)
        assert analysis.confidence > 0.5

        # Low confidence case
        low_conf_error = Exception("Generic error")
        analysis = self.classifier.classify_error(low_conf_error)
        # Should still classify but with lower confidence


class TestIntelligentErrorRecovery:
    """Test intelligent error recovery system"""

    def setup_method(self):
        """Setup test fixtures"""
        self.recovery = IntelligentErrorRecovery()

    @pytest.mark.asyncio
    async def test_timeout_error_recovery(self):
        """Test recovery from timeout errors"""
        # Mock timeout error
        timeout_error = Exception("Element not visible within timeout of 5000ms")

        original_code = """
await page.goto("https://test.com")
await page.locator(".slow-element").click()
result = {"clicked": True}
"""

        context = CodeGenerationContext(
            task_description="Click slow element",
            url="https://test.com"
        )

        browser_context = {'page': Mock()}

        # Mock sandbox execution to succeed on retry
        with patch.object(self.recovery, '_test_code_in_sandbox',
                         side_effect=[(False, "timeout"), (True, None)]):
            success, recovered_code, session = await self.recovery.recover_from_error(
                timeout_error, original_code, context, browser_context, max_attempts=2
            )

        assert success is True
        assert session.final_success is True
        assert len(session.attempts) <= 2
        assert "timeout" in recovered_code  # Should have timeout modifications

    @pytest.mark.asyncio
    async def test_element_not_found_recovery(self):
        """Test recovery from element not found errors"""
        element_error = Exception("Locator '.missing-button' not found")

        original_code = """
await page.goto("https://test.com")
await page.locator(".missing-button").click()
result = {"clicked": True}
"""

        context = CodeGenerationContext(
            task_description="Click missing button",
            url="https://test.com"
        )

        browser_context = {'page': Mock()}

        # Mock successful recovery
        with patch.object(self.recovery, '_test_code_in_sandbox', return_value=(True, None)):
            success, recovered_code, session = await self.recovery.recover_from_error(
                element_error, original_code, context, browser_context, max_attempts=1
            )

        assert success is True
        assert len(session.attempts) == 1
        assert session.attempts[0].strategy == RecoveryStrategy.CODE_MODIFICATION

    @pytest.mark.asyncio
    async def test_multiple_recovery_attempts(self):
        """Test multiple recovery attempts with different strategies"""
        error = Exception("Interaction error: element not interactable")

        original_code = """
await page.locator(".button").click()
result = {"clicked": True}
"""

        context = CodeGenerationContext(
            task_description="Click button",
            url="https://test.com"
        )

        browser_context = {'page': Mock()}

        # Mock failures for first attempts, success on last
        test_results = [(False, "still failing"), (False, "still failing"), (True, None)]

        with patch.object(self.recovery, '_test_code_in_sandbox', side_effect=test_results):
            success, recovered_code, session = await self.recovery.recover_from_error(
                error, original_code, context, browser_context, max_attempts=3
            )

        assert success is True
        assert len(session.attempts) == 3
        assert session.final_success is True

        # Should use different strategies
        strategies_used = [attempt.strategy for attempt in session.attempts]
        assert len(set(strategies_used)) > 1  # Different strategies used

    @pytest.mark.asyncio
    async def test_recovery_failure_all_attempts(self):
        """Test when all recovery attempts fail"""
        error = Exception("Critical error that can't be recovered")

        original_code = """
await page.goto("https://broken.com")
result = {"failed": True}
"""

        context = CodeGenerationContext(
            task_description="Access broken site",
            url="https://broken.com"
        )

        browser_context = {'page': Mock()}

        # Mock all attempts failing
        with patch.object(self.recovery, '_test_code_in_sandbox', return_value=(False, "persistent error")):
            success, recovered_code, session = await self.recovery.recover_from_error(
                error, original_code, context, browser_context, max_attempts=2
            )

        assert success is False
        assert session.final_success is False
        assert len(session.attempts) == 2
        assert all(not attempt.success for attempt in session.attempts)

    @pytest.mark.asyncio
    async def test_code_modification_strategy(self):
        """Test code modification recovery strategy"""
        error_analysis = ErrorAnalysis(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.8,
            original_error="timeout exceeded",
            matched_patterns=["timeout.*exceeded"],
            recovery_suggestions=["increase timeout"],
            context_info={}
        )

        recovery_plan = {
            'code_modifications': [
                {
                    'type': 'timeout_increase',
                    'description': 'Increase timeout values'
                }
            ]
        }

        original_code = """
await page.wait_for_selector(".element", timeout=5000)
await page.locator(".element").click()
"""

        modified_code, modifications = await self.recovery._apply_code_modifications(
            original_code, error_analysis, recovery_plan
        )

        assert "timeout=10000" in modified_code or "timeout" in modified_code
        assert len(modifications) > 0
        assert any("timeout" in mod.lower() for mod in modifications)

    @pytest.mark.asyncio
    async def test_parameter_adjustment_strategy(self):
        """Test parameter adjustment recovery strategy"""
        error_analysis = ErrorAnalysis(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.8,
            original_error="timeout",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        recovery_plan = {'retry_strategy': {'timeout_multiplier': 2.0}}

        original_code = """
await page.wait_for_selector(".element", timeout=5000)
"""

        modified_code, modifications = await self.recovery._adjust_parameters(
            original_code, error_analysis, recovery_plan
        )

        # Should increase timeout
        assert "10000" in modified_code
        assert len(modifications) > 0

    @pytest.mark.asyncio
    async def test_alternative_approach_generation(self):
        """Test alternative approach generation"""
        context = CodeGenerationContext(
            task_description="Click submit button",
            url="https://test.com"
        )

        error_analysis = ErrorAnalysis(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.7,
            original_error="element not found",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        recovery_plan = {'alternative_approaches': []}

        with patch.object(self.recovery.code_generator, 'generate_automation_code',
                         return_value="# Alternative automation code"):
            alternative_code, modifications = await self.recovery._generate_alternative_approach(
                context, error_analysis, recovery_plan
            )

        assert "Alternative" in alternative_code or "alternative" in alternative_code
        assert len(modifications) > 0
        assert any("alternative" in mod.lower() for mod in modifications)

    @pytest.mark.asyncio
    async def test_fallback_code_generation(self):
        """Test fallback code generation"""
        context = CodeGenerationContext(
            task_description="Complex automation task",
            url="https://test.com"
        )

        error_analysis = ErrorAnalysis(
            category=ErrorCategory.UNKNOWN_ERROR,
            severity=ErrorSeverity.HIGH,
            confidence=0.3,
            original_error="unknown error",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        fallback_code, modifications = await self.recovery._generate_fallback_code(
            context, error_analysis
        )

        assert "fallback" in fallback_code.lower()
        assert "goto" in fallback_code  # Should have basic navigation
        assert "result" in fallback_code  # Should return result
        assert len(modifications) > 0

    def test_strategy_selection(self):
        """Test recovery strategy selection logic"""
        error_analysis = ErrorAnalysis(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.8,
            original_error="element not found",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        recovery_plan = {}
        previous_attempts = []

        strategy = self.recovery._choose_recovery_strategy(
            error_analysis, recovery_plan, 1, previous_attempts
        )

        # For element not found, should prioritize code modification
        assert strategy == RecoveryStrategy.CODE_MODIFICATION

        # Test second attempt uses different strategy
        first_attempt = RecoveryAttempt(
            attempt_number=1,
            strategy=RecoveryStrategy.CODE_MODIFICATION,
            modifications_made=[],
            success=False,
            error_encountered="still failing",
            execution_time=1.0,
            generated_code="",
            confidence_score=0.5
        )

        strategy2 = self.recovery._choose_recovery_strategy(
            error_analysis, recovery_plan, 2, [first_attempt]
        )

        assert strategy2 != RecoveryStrategy.CODE_MODIFICATION

    def test_timeout_increase_modification(self):
        """Test timeout increase modification"""
        code_with_timeout = """
await page.wait_for_selector(".element", timeout=5000)
await page.goto("https://test.com", timeout=30000)
"""

        modified_code, applied = self.recovery._increase_timeouts(code_with_timeout)

        assert applied is True
        assert "timeout=10000" in modified_code  # Should double the timeout
        assert "timeout=60000" in modified_code  # Should double the other timeout

    def test_wait_addition_modification(self):
        """Test adding wait statements"""
        code_without_waits = """
await page.locator(".button").click()
await page.locator(".input").fill("text")
"""

        modified_code, applied = self.recovery._add_waits(code_without_waits)

        assert applied is True
        assert "wait_for_load_state" in modified_code
        assert "wait_for_timeout" in modified_code

    def test_selector_improvement(self):
        """Test CSS selector improvements"""
        code_with_fragile_selectors = """
await page.locator(".btn").click()
await page.locator(".submit").click()
"""

        modified_code, applied = self.recovery._improve_selectors(code_with_fragile_selectors)

        assert applied is True
        # Should have more robust selectors
        assert "data-testid" in modified_code or "button" in modified_code

    @pytest.mark.asyncio
    async def test_sandbox_testing(self):
        """Test code testing in sandbox"""
        test_code = """
result = {"test": "success"}
"""

        browser_context = {'page': Mock()}

        # Test successful execution
        with patch('wyn360_cli.tools.browser.intelligent_error_recovery.SecurePythonSandbox') as MockSandbox:
            mock_instance = MockSandbox.return_value
            mock_instance.execute_automation_script = AsyncMock(return_value={
                'success': True,
                'result': {"test": "success"}
            })

            success, error_msg = await self.recovery._test_code_in_sandbox(test_code, browser_context)

            assert success is True
            assert error_msg is None

        # Test failed execution
        with patch('wyn360_cli.tools.browser.intelligent_error_recovery.SecurePythonSandbox') as MockSandbox:
            mock_instance = MockSandbox.return_value
            mock_instance.execute_automation_script = AsyncMock(return_value={
                'success': False,
                'errors': 'Execution failed'
            })

            success, error_msg = await self.recovery._test_code_in_sandbox(test_code, browser_context)

            assert success is False
            assert error_msg == 'Execution failed'

    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        error_analysis = ErrorAnalysis(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.8,
            original_error="timeout error",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        # Test successful attempt confidence
        confidence = self.recovery._calculate_attempt_confidence(
            RecoveryStrategy.PARAMETER_ADJUSTMENT,
            error_analysis,
            ["increased timeout", "added waits"],
            success=True
        )

        assert confidence > 0.7  # Should be high for successful timeout recovery

        # Test failed attempt confidence
        failed_confidence = self.recovery._calculate_attempt_confidence(
            RecoveryStrategy.CODE_MODIFICATION,
            error_analysis,
            [],
            success=False
        )

        assert failed_confidence < confidence  # Failed should be lower

    def test_lessons_extraction(self):
        """Test extraction of lessons learned"""
        error_analysis = ErrorAnalysis(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.8,
            original_error="element not found",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        attempts = [
            RecoveryAttempt(
                attempt_number=1,
                strategy=RecoveryStrategy.CODE_MODIFICATION,
                modifications_made=["improved selectors"],
                success=False,
                error_encountered="still not found",
                execution_time=1.0,
                generated_code="",
                confidence_score=0.5
            ),
            RecoveryAttempt(
                attempt_number=2,
                strategy=RecoveryStrategy.ALTERNATIVE_APPROACH,
                modifications_made=["used text-based selection"],
                success=True,
                error_encountered=None,
                execution_time=1.5,
                generated_code="",
                confidence_score=0.8
            )
        ]

        lessons = self.recovery._extract_lessons(error_analysis, attempts)

        assert len(lessons) > 0
        assert any("alternative_approach" in lesson.lower() for lesson in lessons)
        assert any("succeeded" in lesson for lesson in lessons)
        assert any("failed" in lesson for lesson in lessons)

    def test_recovery_statistics(self):
        """Test recovery statistics collection"""
        # Add some mock recovery history
        self.recovery.recovery_history = [
            RecoverySession(
                original_error="timeout",
                original_code="test",
                context={},
                attempts=[],
                final_success=True,
                total_recovery_time=5.0,
                lessons_learned=[]
            ),
            RecoverySession(
                original_error="element not found",
                original_code="test",
                context={},
                attempts=[],
                final_success=False,
                total_recovery_time=10.0,
                lessons_learned=[]
            )
        ]

        stats = self.recovery.get_recovery_statistics()

        assert stats['total_sessions'] == 2
        assert stats['successful_sessions'] == 1
        assert stats['success_rate'] == 0.5
        assert stats['average_recovery_time'] == 7.5

    @pytest.mark.asyncio
    async def test_text_based_alternatives(self):
        """Test text-based alternative generation"""
        original_code = """
await page.locator(".submit").click()
"""

        modified_code = self.recovery._apply_text_based_alternatives(original_code)

        assert "text" in modified_code.lower()
        assert "find_element_by_text" in modified_code
        assert original_code in modified_code  # Original code preserved

    @pytest.mark.asyncio
    async def test_keyboard_alternatives(self):
        """Test keyboard navigation alternatives"""
        original_code = """
await page.locator(".button").click()
"""

        modified_code = self.recovery._apply_keyboard_alternatives(original_code)

        assert "keyboard" in modified_code.lower()
        assert "Tab" in modified_code or "Enter" in modified_code
        assert original_code in modified_code  # Original code preserved

    @pytest.mark.asyncio
    async def test_patient_waiting_strategies(self):
        """Test patient waiting strategies"""
        original_code = """
await page.locator(".element").click()
"""

        modified_code = self.recovery._apply_patient_waiting(original_code)

        assert "wait_for_load_state" in modified_code
        assert "networkidle" in modified_code
        assert "wait_for_timeout" in modified_code
        assert original_code in modified_code

    @pytest.mark.asyncio
    async def test_end_to_end_recovery_workflow(self):
        """Test complete end-to-end recovery workflow"""
        # Simulate a realistic error scenario
        timeout_error = Exception("TimeoutError: waiting for selector '.slow-button' to be visible")

        original_code = """
import asyncio
await page.goto("https://slow-site.com")
await page.locator(".slow-button").click()
result = {"button_clicked": True}
"""

        context = CodeGenerationContext(
            task_description="Click slow loading button",
            url="https://slow-site.com"
        )

        mock_page = Mock()
        browser_context = {'page': mock_page}

        # Mock sandbox to fail first attempt, succeed on second
        sandbox_results = [
            (False, "Still timing out"),  # First attempt fails
            (True, None)  # Second attempt succeeds
        ]

        with patch.object(self.recovery, '_test_code_in_sandbox', side_effect=sandbox_results):
            success, recovered_code, session = await self.recovery.recover_from_error(
                timeout_error, original_code, context, browser_context, max_attempts=2
            )

        # Verify successful recovery
        assert success is True
        assert session.final_success is True
        assert len(session.attempts) == 2

        # Verify first attempt failed, second succeeded
        assert session.attempts[0].success is False
        assert session.attempts[1].success is True

        # Verify lessons were learned
        assert len(session.lessons_learned) > 0

        # Verify code was modified appropriately
        assert recovered_code != original_code
        assert "slow-site.com" in recovered_code  # Should preserve original URL

    def test_strategy_learning(self):
        """Test learning from successful strategies"""
        error_analysis = ErrorAnalysis(
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            confidence=0.8,
            original_error="timeout error",
            matched_patterns=[],
            recovery_suggestions=[],
            context_info={}
        )

        successful_attempt = RecoveryAttempt(
            attempt_number=1,
            strategy=RecoveryStrategy.PARAMETER_ADJUSTMENT,
            modifications_made=["increased timeout"],
            success=True,
            error_encountered=None,
            execution_time=2.0,
            generated_code="modified code",
            confidence_score=0.9
        )

        initial_rate = self.recovery.strategy_success_rates.get(
            "timeout_parameter_adjustment", 0.0
        )

        self.recovery._learn_from_success(error_analysis, RecoveryStrategy.PARAMETER_ADJUSTMENT, successful_attempt)

        updated_rate = self.recovery.strategy_success_rates.get(
            "timeout_parameter_adjustment", 0.0
        )

        assert updated_rate > initial_rate