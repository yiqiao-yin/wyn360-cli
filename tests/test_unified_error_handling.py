"""
Unit tests for Unified Error Handling

Tests the comprehensive error handling system that provides consistent
error categorization, retry logic, and graceful degradation across
all automation approaches.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from src.wyn360.tools.browser.unified_error_handling import (
    UnifiedErrorHandler,
    ErrorCategory,
    ErrorContext,
    RetryConfig,
    unified_error_handler
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionResult
)


class TestErrorCategorization:
    """Test error categorization functionality"""

    @pytest.fixture
    def error_handler(self):
        """Create fresh error handler for each test"""
        return UnifiedErrorHandler()

    def test_categorize_network_error(self, error_handler):
        """Test network error categorization"""
        error = ConnectionError("Connection timed out")
        context = error_handler.categorize_error(
            error, AutomationApproach.DOM_ANALYSIS
        )

        assert context.category == ErrorCategory.NETWORK_ERROR
        assert context.retryable is True
        assert context.fallback_recommended is False  # Network affects all approaches
        assert context.confidence_impact == 0.1

    def test_categorize_page_load_error(self, error_handler):
        """Test page load error categorization"""
        error = "Failed to load page: 404 Not Found"
        context = error_handler.categorize_error(
            error, AutomationApproach.STAGEHAND
        )

        assert context.category == ErrorCategory.PAGE_LOAD_ERROR
        assert context.retryable is True
        assert context.fallback_recommended is True
        assert context.confidence_impact == 0.2

    def test_categorize_element_not_found_error(self, error_handler):
        """Test element not found error categorization"""
        error = "Element not found: No such element exception"
        context = error_handler.categorize_error(
            error, AutomationApproach.DOM_ANALYSIS
        )

        assert context.category == ErrorCategory.ELEMENT_NOT_FOUND
        assert context.retryable is True  # DOM is retryable for element errors
        assert context.fallback_recommended is True
        assert context.confidence_impact == 0.3

    def test_categorize_element_not_found_vision(self, error_handler):
        """Test element not found error for vision approach"""
        error = "Element not accessible"
        context = error_handler.categorize_error(
            error, AutomationApproach.VISION_FALLBACK
        )

        assert context.category == ErrorCategory.ELEMENT_NOT_FOUND
        assert context.retryable is False  # Vision is not retryable for element errors
        assert context.fallback_recommended is True

    def test_categorize_interaction_failed(self, error_handler):
        """Test interaction failed error categorization"""
        error = "Click failed: element intercepted"
        context = error_handler.categorize_error(
            error, AutomationApproach.STAGEHAND
        )

        assert context.category == ErrorCategory.INTERACTION_FAILED
        assert context.retryable is True
        assert context.fallback_recommended is True
        assert context.confidence_impact == 0.2

    def test_categorize_permission_denied(self, error_handler):
        """Test permission denied error categorization"""
        error = "Access denied: CORS policy violation"
        context = error_handler.categorize_error(
            error, AutomationApproach.DOM_ANALYSIS
        )

        assert context.category == ErrorCategory.PERMISSION_DENIED
        assert context.retryable is False
        assert context.fallback_recommended is False
        assert context.confidence_impact == 0.5

    def test_categorize_browser_error(self, error_handler):
        """Test browser error categorization"""
        error = "WebDriver session crashed"
        context = error_handler.categorize_error(
            error, AutomationApproach.DOM_ANALYSIS
        )

        assert context.category == ErrorCategory.BROWSER_ERROR
        assert context.retryable is True  # DOM approach can retry browser errors
        assert context.fallback_recommended is True

    def test_categorize_browser_error_vision(self, error_handler):
        """Test browser error categorization for vision"""
        error = "ChromeDriver failed to start"
        context = error_handler.categorize_error(
            error, AutomationApproach.VISION_FALLBACK
        )

        assert context.category == ErrorCategory.BROWSER_ERROR
        assert context.retryable is False  # Vision less dependent on browser
        assert context.fallback_recommended is True

    def test_categorize_timeout_error(self, error_handler):
        """Test timeout error categorization"""
        error = "Operation timed out after 30 seconds"
        context = error_handler.categorize_error(
            error, AutomationApproach.DOM_ANALYSIS
        )

        assert context.category == ErrorCategory.TIMEOUT_ERROR
        assert context.retryable is True
        assert context.fallback_recommended is True  # DOM is fastest
        assert context.confidence_impact == 0.2

    def test_categorize_configuration_error(self, error_handler):
        """Test configuration error categorization"""
        error = "Invalid configuration: missing API key"
        context = error_handler.categorize_error(
            error, AutomationApproach.STAGEHAND
        )

        assert context.category == ErrorCategory.CONFIGURATION_ERROR
        assert context.retryable is False
        assert context.fallback_recommended is True
        assert context.confidence_impact == 0.3

    def test_categorize_unknown_error(self, error_handler):
        """Test unknown error categorization"""
        error = "Some mysterious error"
        context = error_handler.categorize_error(
            error, AutomationApproach.VISION_FALLBACK
        )

        assert context.category == ErrorCategory.UNKNOWN_ERROR
        assert context.retryable is True  # Conservative default
        assert context.fallback_recommended is True
        assert context.confidence_impact == 0.2

    def test_categorize_with_metadata(self, error_handler):
        """Test error categorization with metadata"""
        error = "Network timeout"
        metadata = {"url": "https://example.com", "attempt": 2}
        context = error_handler.categorize_error(
            error, AutomationApproach.DOM_ANALYSIS, metadata
        )

        assert context.category == ErrorCategory.NETWORK_ERROR
        assert context.metadata == metadata
        assert context.original_exception is None

    def test_categorize_exception_object(self, error_handler):
        """Test categorization of exception objects"""
        exception = ValueError("Element not found in DOM")
        context = error_handler.categorize_error(
            exception, AutomationApproach.DOM_ANALYSIS
        )

        assert context.category == ErrorCategory.ELEMENT_NOT_FOUND
        assert context.message == "Element not found in DOM"
        assert context.original_exception == exception


class TestRetryLogic:
    """Test retry logic functionality"""

    @pytest.fixture
    def error_handler(self):
        """Create fresh error handler for each test"""
        return UnifiedErrorHandler()

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_attempt(self, error_handler):
        """Test successful execution on first attempt"""
        async def successful_operation():
            return ActionResult(
                success=True,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.8,
                execution_time=1.0,
                result_data={'status': 'success'}
            )

        result = await error_handler.execute_with_retry(successful_operation)

        assert result.success is True
        assert result.confidence == 0.8
        assert len(error_handler.error_history) == 1
        assert error_handler.error_history[0]['success'] is True
        assert error_handler.error_history[0]['attempts'] == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retries(self, error_handler):
        """Test successful execution after initial failures"""
        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary network error")
            return ActionResult(
                success=True,
                approach_used=AutomationApproach.STAGEHAND,
                confidence=0.7,
                execution_time=2.0,
                result_data={'status': 'success'}
            )

        config = RetryConfig(max_retries=3, base_delay=0.01)  # Fast retry for tests
        result = await error_handler.execute_with_retry(flaky_operation, config)

        assert result.success is True
        assert result.confidence == 0.7
        assert call_count == 3

        # Should have 2 error records and 1 success record
        error_records = [r for r in error_handler.error_history if not r['success']]
        success_records = [r for r in error_handler.error_history if r['success']]
        assert len(error_records) == 2
        assert len(success_records) == 1
        assert success_records[0]['attempts'] == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_final_failure(self, error_handler):
        """Test final failure after all retries exhausted"""
        async def failing_operation():
            raise Exception("Persistent element not found error")

        config = RetryConfig(max_retries=2, base_delay=0.01)
        result = await error_handler.execute_with_retry(failing_operation, config)

        assert result.success is False
        assert "element not found" in result.error_message.lower()
        assert "page structure may have changed" in result.recommendation.lower()

        # Should have 3 error records (initial + 2 retries)
        error_records = [r for r in error_handler.error_history if not r['success']]
        assert len(error_records) == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable_error(self, error_handler):
        """Test that non-retryable errors are not retried"""
        async def failing_operation():
            raise Exception("Permission denied: access forbidden")

        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = await error_handler.execute_with_retry(failing_operation, config)

        assert result.success is False
        assert "permission denied" in result.error_message.lower()

        # Should have only 1 error record (no retries)
        error_records = [r for r in error_handler.error_history if not r['success']]
        assert len(error_records) == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_timeout(self, error_handler):
        """Test timeout handling in retry logic"""
        async def slow_operation():
            await asyncio.sleep(2.0)  # Longer than timeout
            return ActionResult(
                success=True,
                approach_used=AutomationApproach.DOM_ANALYSIS,
                confidence=0.5,
                execution_time=2.0,
                result_data={}
            )

        config = RetryConfig(max_retries=1, timeout_seconds=0.1, base_delay=0.01)
        result = await error_handler.execute_with_retry(slow_operation, config)

        assert result.success is False
        assert "timed out" in result.error_message.lower()

    def test_calculate_retry_delay_exponential_backoff(self, error_handler):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=60.0,
            exponential_backoff=True,
            jitter=False
        )

        delay_0 = error_handler._calculate_retry_delay(0, config, ErrorCategory.NETWORK_ERROR)
        delay_1 = error_handler._calculate_retry_delay(1, config, ErrorCategory.NETWORK_ERROR)
        delay_2 = error_handler._calculate_retry_delay(2, config, ErrorCategory.NETWORK_ERROR)

        # Network error has 1.5x multiplier
        assert abs(delay_0 - 1.5) < 0.01  # 1.0 * 1.5
        assert abs(delay_1 - 3.0) < 0.01  # 2.0 * 1.5
        assert abs(delay_2 - 6.0) < 0.01  # 4.0 * 1.5

    def test_calculate_retry_delay_linear(self, error_handler):
        """Test linear delay calculation"""
        config = RetryConfig(
            base_delay=2.0,
            exponential_backoff=False,
            jitter=False
        )

        delay_0 = error_handler._calculate_retry_delay(0, config, ErrorCategory.ELEMENT_NOT_FOUND)
        delay_1 = error_handler._calculate_retry_delay(1, config, ErrorCategory.ELEMENT_NOT_FOUND)
        delay_2 = error_handler._calculate_retry_delay(2, config, ErrorCategory.ELEMENT_NOT_FOUND)

        # Element not found has 0.8x multiplier
        expected_delay = 2.0 * 0.8
        assert abs(delay_0 - expected_delay) < 0.01
        assert abs(delay_1 - expected_delay) < 0.01
        assert abs(delay_2 - expected_delay) < 0.01

    def test_calculate_retry_delay_max_delay(self, error_handler):
        """Test that delays are capped at max_delay"""
        config = RetryConfig(
            base_delay=10.0,
            max_delay=5.0,
            exponential_backoff=True,
            jitter=False
        )

        delay = error_handler._calculate_retry_delay(5, config, ErrorCategory.BROWSER_ERROR)
        # Browser error has 2.0x multiplier, but should be capped at max_delay
        assert delay <= config.max_delay


class TestErrorAnalytics:
    """Test error analytics functionality"""

    @pytest.fixture
    def error_handler(self):
        """Create fresh error handler for each test"""
        return UnifiedErrorHandler()

    @pytest.fixture
    def error_handler_with_data(self):
        """Create error handler with test data"""
        handler = UnifiedErrorHandler()

        # Add test history
        handler.error_history = [
            {'timestamp': time.time(), 'success': True, 'approach': 'dom_analysis', 'attempts': 1},
            {'timestamp': time.time(), 'success': False, 'approach': 'dom_analysis', 'category': 'element_not_found'},
            {'timestamp': time.time(), 'success': True, 'approach': 'stagehand', 'attempts': 2},
            {'timestamp': time.time(), 'success': False, 'approach': 'stagehand', 'category': 'network_error'},
            {'timestamp': time.time(), 'success': True, 'approach': 'vision_fallback', 'attempts': 1},
        ]

        # Add error patterns
        handler.error_patterns = {
            'dom_analysis:element_not_found': 3,
            'stagehand:network_error': 2,
            'vision_fallback:timeout_error': 1
        }

        return handler

    def test_get_error_analytics_empty(self):
        """Test analytics with no data"""
        handler = UnifiedErrorHandler()
        analytics = handler.get_error_analytics()

        assert analytics['total_operations'] == 0
        assert analytics['success_rate'] == 0.0
        assert analytics['error_patterns'] == {}

    def test_get_error_analytics_with_data(self, error_handler_with_data):
        """Test analytics with test data"""
        analytics = error_handler_with_data.get_error_analytics()

        assert analytics['total_operations'] == 5
        assert analytics['successful_operations'] == 3
        assert analytics['success_rate'] == 0.6

        assert 'element_not_found' in analytics['error_categories']
        assert analytics['error_categories']['element_not_found'] == 1

        assert analytics['error_patterns']['dom_analysis:element_not_found'] == 3

    def test_clear_history(self, error_handler_with_data):
        """Test clearing error history"""
        count = error_handler_with_data.clear_history()

        assert count == 5  # Number of records cleared
        assert len(error_handler_with_data.error_history) == 0
        assert len(error_handler_with_data.error_patterns) == 0

    def test_record_success(self, error_handler):
        """Test recording successful operations"""
        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.STAGEHAND,
            confidence=0.9,
            execution_time=3.0,
            result_data={}
        )

        error_handler._record_success(result, 2)  # 3rd attempt (0-indexed)

        assert len(error_handler.error_history) == 1
        record = error_handler.error_history[0]
        assert record['success'] is True
        assert record['approach'] == 'stagehand'
        assert record['attempts'] == 3
        assert record['confidence'] == 0.9

    def test_record_error(self, error_handler):
        """Test recording error information"""
        error_context = ErrorContext(
            category=ErrorCategory.TIMEOUT_ERROR,
            message="Operation timed out",
            approach_used=AutomationApproach.VISION_FALLBACK,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3,
            metadata={'url': 'https://example.com'}
        )

        error_handler._record_error(error_context, 1)  # 2nd attempt

        assert len(error_handler.error_history) == 1
        record = error_handler.error_history[0]
        assert record['success'] is False
        assert record['category'] == 'timeout_error'
        assert record['approach'] == 'vision_fallback'
        assert record['attempt'] == 2
        assert record['retryable'] is True

        # Check error patterns
        pattern_key = 'vision_fallback:timeout_error'
        assert error_handler.error_patterns[pattern_key] == 1

    def test_generate_failure_recommendation(self, error_handler):
        """Test failure recommendation generation"""
        # Network error
        network_context = ErrorContext(
            category=ErrorCategory.NETWORK_ERROR,
            message="Connection failed",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=False,
            confidence_impact=0.1
        )

        recommendation = error_handler._generate_failure_recommendation(network_context)
        assert "network connectivity" in recommendation.lower()

        # Element not found with fallback
        element_context = ErrorContext(
            category=ErrorCategory.ELEMENT_NOT_FOUND,
            message="Element missing",
            approach_used=AutomationApproach.DOM_ANALYSIS,
            retryable=True,
            fallback_recommended=True,
            confidence_impact=0.3
        )

        recommendation = error_handler._generate_failure_recommendation(element_context)
        assert "page structure" in recommendation.lower()
        assert "different approach" in recommendation.lower()


class TestGlobalErrorHandler:
    """Test the global error handler instance"""

    def test_global_instance_exists(self):
        """Test that global error handler instance exists"""
        from src.wyn360.tools.browser.unified_error_handling import unified_error_handler
        assert unified_error_handler is not None
        assert isinstance(unified_error_handler, UnifiedErrorHandler)

    def test_global_instance_categorization(self):
        """Test that global instance works correctly"""
        from src.wyn360.tools.browser.unified_error_handling import unified_error_handler

        context = unified_error_handler.categorize_error(
            "Network timeout occurred",
            AutomationApproach.STAGEHAND
        )

        assert context.category == ErrorCategory.NETWORK_ERROR
        assert context.approach_used == AutomationApproach.STAGEHAND


if __name__ == "__main__":
    pytest.main([__file__, "-v"])