"""
Unit tests for automation orchestrator

Tests decision-making logic, learning capabilities, and analytics.
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationOrchestrator,
    ActionRequest,
    ActionResult,
    DecisionContext,
    AutomationApproach,
    automation_orchestrator
)


class TestActionRequest:
    """Test ActionRequest dataclass"""

    def test_action_request_creation(self):
        """Test creating an action request"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Login to website",
            action_type="click",
            target_description="submit button",
            action_data={"username": "test"},
            confidence_threshold=0.8,
            show_browser=True
        )

        assert request.url == "https://example.com"
        assert request.task_description == "Login to website"
        assert request.action_type == "click"
        assert request.target_description == "submit button"
        assert request.action_data == {"username": "test"}
        assert request.confidence_threshold == 0.8
        assert request.show_browser is True

    def test_action_request_defaults(self):
        """Test action request default values"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Test task",
            action_type="click",
            target_description="button"
        )

        assert request.action_data is None
        assert request.confidence_threshold == 0.7
        assert request.show_browser is False


class TestActionResult:
    """Test ActionResult dataclass"""

    def test_action_result_creation(self):
        """Test creating an action result"""
        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.9,
            execution_time=2.5,
            result_data={"status": "completed"},
            error_message=None,
            recommendation="Continue with DOM approach",
            token_usage={"input": 100, "output": 50}
        )

        assert result.success is True
        assert result.approach_used == AutomationApproach.DOM_ANALYSIS
        assert result.confidence == 0.9
        assert result.execution_time == 2.5
        assert result.result_data == {"status": "completed"}
        assert result.error_message is None
        assert result.recommendation == "Continue with DOM approach"
        assert result.token_usage == {"input": 100, "output": 50}


class TestDecisionContext:
    """Test DecisionContext dataclass"""

    def test_decision_context_creation(self):
        """Test creating decision context"""
        context = DecisionContext(
            dom_confidence=0.8,
            page_complexity="moderate",
            element_count=10,
            forms_count=2,
            previous_failures=["stagehand"],
            user_preference=AutomationApproach.DOM_ANALYSIS
        )

        assert context.dom_confidence == 0.8
        assert context.page_complexity == "moderate"
        assert context.element_count == 10
        assert context.forms_count == 2
        assert context.previous_failures == ["stagehand"]
        assert context.user_preference == AutomationApproach.DOM_ANALYSIS


class TestAutomationOrchestrator:
    """Test automation orchestrator functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.orchestrator = AutomationOrchestrator()

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        assert self.orchestrator.decision_history == []
        assert len(self.orchestrator.approach_success_rates) == 3
        assert len(self.orchestrator.total_attempts) == 3

        # All success rates should start at 0
        for approach in AutomationApproach:
            assert self.orchestrator.approach_success_rates[approach] == 0.0
            assert self.orchestrator.total_attempts[approach] == 0

    def test_create_decision_context_simple_page(self):
        """Test creating decision context for simple page"""
        request = ActionRequest(
            url="https://simple.com",
            task_description="Click button",
            action_type="click",
            target_description="submit"
        )

        dom_result = {
            'confidence': 0.9,
            'interactive_elements_count': 3,
            'forms_count': 0
        }

        context = self.orchestrator._create_decision_context(request, dom_result)

        assert context.dom_confidence == 0.9
        assert context.page_complexity == "simple"
        assert context.element_count == 3
        assert context.forms_count == 0
        assert context.previous_failures == []

    def test_create_decision_context_complex_page(self):
        """Test creating decision context for complex page"""
        request = ActionRequest(
            url="https://complex.com",
            task_description="Fill form",
            action_type="type",
            target_description="email field"
        )

        dom_result = {
            'confidence': 0.6,
            'interactive_elements_count': 20,
            'forms_count': 3
        }

        context = self.orchestrator._create_decision_context(request, dom_result)

        assert context.dom_confidence == 0.6
        assert context.page_complexity == "complex"
        assert context.element_count == 20
        assert context.forms_count == 3

    def test_apply_decision_rules_high_confidence(self):
        """Test decision rules for high confidence scenarios"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Click",
            action_type="click",
            target_description="button",
            confidence_threshold=0.7
        )

        # High confidence, simple page
        context = DecisionContext(
            dom_confidence=0.9,
            page_complexity="simple",
            element_count=5,
            forms_count=1,
            previous_failures=[]
        )

        approach, reasoning = self.orchestrator._apply_decision_rules(request, context)

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "High DOM confidence" in reasoning

    def test_apply_decision_rules_medium_confidence_with_forms(self):
        """Test decision rules for medium confidence with forms"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Submit form",
            action_type="submit",
            target_description="form",
            confidence_threshold=0.8
        )

        # Medium confidence but has forms
        context = DecisionContext(
            dom_confidence=0.6,  # 0.6 >= 0.8 * 0.7 = 0.56
            page_complexity="moderate",
            element_count=8,
            forms_count=2,
            previous_failures=[]
        )

        approach, reasoning = self.orchestrator._apply_decision_rules(request, context)

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Forms detected" in reasoning

    def test_apply_decision_rules_stagehand_fallback(self):
        """Test decision rules choosing Stagehand"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Navigate",
            action_type="click",
            target_description="menu item",
            confidence_threshold=0.8
        )

        # Medium confidence, complex page
        context = DecisionContext(
            dom_confidence=0.5,
            page_complexity="complex",
            element_count=15,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = self.orchestrator._apply_decision_rules(request, context)

        assert approach == AutomationApproach.STAGEHAND
        assert "complex page" in reasoning

    def test_apply_decision_rules_vision_fallback(self):
        """Test decision rules choosing Vision fallback"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Complex task",
            action_type="extract",
            target_description="dynamic content",
            confidence_threshold=0.8
        )

        # Low confidence
        context = DecisionContext(
            dom_confidence=0.2,
            page_complexity="complex",
            element_count=2,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = self.orchestrator._apply_decision_rules(request, context)

        assert approach == AutomationApproach.VISION_FALLBACK
        assert "Low confidence" in reasoning

    def test_apply_decision_rules_user_preference(self):
        """Test user preference override"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Test",
            action_type="click",
            target_description="button"
        )

        # Low confidence but user prefers DOM
        context = DecisionContext(
            dom_confidence=0.3,
            page_complexity="simple",
            element_count=2,
            forms_count=0,
            previous_failures=[],
            user_preference=AutomationApproach.DOM_ANALYSIS
        )

        approach, reasoning = self.orchestrator._apply_decision_rules(request, context)

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "User preference" in reasoning

    def test_apply_decision_rules_previous_failures(self):
        """Test avoiding approaches that failed recently"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Test",
            action_type="click",
            target_description="button"
        )

        # High confidence but DOM failed recently
        context = DecisionContext(
            dom_confidence=0.9,
            page_complexity="simple",
            element_count=5,
            forms_count=0,
            previous_failures=[AutomationApproach.DOM_ANALYSIS.value]
        )

        approach, reasoning = self.orchestrator._apply_decision_rules(request, context)

        # Should fall back to Stagehand or Vision
        assert approach in [AutomationApproach.STAGEHAND, AutomationApproach.VISION_FALLBACK]

    def test_get_recent_failures(self):
        """Test retrieving recent failures for a URL"""
        current_time = time.time()

        # Add some decision history
        self.orchestrator.decision_history = [
            {
                'timestamp': current_time - 1800,  # 30 minutes ago
                'url': 'https://example.com',
                'approach': 'dom_analysis',
                'success': False
            },
            {
                'timestamp': current_time - 7200,  # 2 hours ago
                'url': 'https://example.com',
                'approach': 'stagehand',
                'success': False
            },
            {
                'timestamp': current_time - 300,   # 5 minutes ago
                'url': 'https://different.com',
                'approach': 'dom_analysis',
                'success': False
            }
        ]

        # Should only return failures within 1 hour for the specific URL
        failures = self.orchestrator._get_recent_failures('https://example.com', hours=1)
        assert len(failures) == 1
        assert 'dom_analysis' in failures

    def test_record_execution_result_success(self):
        """Test recording successful execution result"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Test",
            action_type="click",
            target_description="button"
        )

        result = ActionResult(
            success=True,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.9,
            execution_time=1.5,
            result_data={"status": "clicked"}
        )

        initial_rate = self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS]
        initial_attempts = self.orchestrator.total_attempts[AutomationApproach.DOM_ANALYSIS]

        self.orchestrator.record_execution_result(request, AutomationApproach.DOM_ANALYSIS, result)

        assert self.orchestrator.total_attempts[AutomationApproach.DOM_ANALYSIS] == initial_attempts + 1
        assert self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS] > initial_rate

    def test_record_execution_result_failure(self):
        """Test recording failed execution result"""
        request = ActionRequest(
            url="https://example.com",
            task_description="Test",
            action_type="click",
            target_description="button"
        )

        # First record a success to establish a baseline
        success_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.9,
            execution_time=1.5,
            result_data={"status": "clicked"}
        )
        self.orchestrator.record_execution_result(request, AutomationApproach.DOM_ANALYSIS, success_result)

        initial_rate = self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS]

        # Now record a failure
        failure_result = ActionResult(
            success=False,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.9,
            execution_time=1.5,
            result_data={},
            error_message="Element not found"
        )

        self.orchestrator.record_execution_result(request, AutomationApproach.DOM_ANALYSIS, failure_result)

        # Success rate should decrease
        assert self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS] < initial_rate

    def test_get_best_performing_approach(self):
        """Test identifying best performing approach"""
        # Need at least 3 attempts for each approach
        for _ in range(5):
            self.orchestrator.total_attempts[AutomationApproach.DOM_ANALYSIS] += 1
            self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS] = 0.8

        for _ in range(3):
            self.orchestrator.total_attempts[AutomationApproach.STAGEHAND] += 1
            self.orchestrator.approach_success_rates[AutomationApproach.STAGEHAND] = 0.9

        best = self.orchestrator._get_best_performing_approach()
        assert best == AutomationApproach.STAGEHAND

    def test_get_best_performing_approach_insufficient_data(self):
        """Test when there's insufficient data"""
        # Only 2 attempts, should return None
        self.orchestrator.total_attempts[AutomationApproach.DOM_ANALYSIS] = 2
        self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS] = 1.0

        best = self.orchestrator._get_best_performing_approach()
        assert best is None

    def test_decide_automation_approach_integration(self):
        """Test complete decision making flow"""
        request = ActionRequest(
            url="https://test.com",
            task_description="Click submit",
            action_type="click",
            target_description="submit button"
        )

        dom_result = {
            'confidence': 0.85,
            'interactive_elements_count': 5,
            'forms_count': 1,
            'recommended_approach': 'dom_analysis'
        }

        approach, context, reasoning = self.orchestrator.decide_automation_approach(request, dom_result)

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert isinstance(context, DecisionContext)
        assert context.dom_confidence == 0.85
        assert "High DOM confidence" in reasoning

        # Should have added to decision history
        assert len(self.orchestrator.decision_history) == 1
        assert self.orchestrator.decision_history[0]['url'] == "https://test.com"

    def test_get_decision_analytics_empty(self):
        """Test analytics with no decision history"""
        analytics = self.orchestrator.get_decision_analytics()

        assert analytics['total_decisions'] == 0
        assert analytics['approach_distribution'] == {}
        assert analytics['average_confidence'] == 0.0

    def test_get_decision_analytics_with_data(self):
        """Test analytics with decision history"""
        # Add some decision history
        self.orchestrator.decision_history = [
            {
                'approach': 'dom_analysis',
                'dom_confidence': 0.8,
                'success': True
            },
            {
                'approach': 'dom_analysis',
                'dom_confidence': 0.9,
                'success': False
            },
            {
                'approach': 'stagehand',
                'dom_confidence': 0.6,
                'success': True
            }
        ]

        # Add some attempt data
        self.orchestrator.total_attempts[AutomationApproach.DOM_ANALYSIS] = 10
        self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS] = 0.7

        analytics = self.orchestrator.get_decision_analytics()

        assert analytics['total_decisions'] == 3
        assert analytics['approach_distribution']['dom_analysis'] == 2/3
        assert analytics['approach_distribution']['stagehand'] == 1/3
        assert abs(analytics['average_confidence'] - 0.77) < 0.01  # (0.8+0.9+0.6)/3

    def test_suggest_improvements_insufficient_data(self):
        """Test suggestions with insufficient data"""
        suggestions = self.orchestrator.suggest_improvements()
        assert len(suggestions) == 1
        assert "More usage data needed" in suggestions[0]

    def test_suggest_improvements_with_data(self):
        """Test suggestions with sufficient data"""
        # Mock sufficient decision history
        self.orchestrator.decision_history = [{'approach': 'dom_analysis'} for _ in range(15)]

        # Mock low DOM success rate
        self.orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS] = 0.5

        suggestions = self.orchestrator.suggest_improvements()

        assert len(suggestions) > 0
        assert any("DOM confidence threshold" in suggestion for suggestion in suggestions)


class TestGlobalOrchestrator:
    """Test global orchestrator instance"""

    def test_global_instance_exists(self):
        """Test that global instance exists"""
        assert automation_orchestrator is not None
        assert isinstance(automation_orchestrator, AutomationOrchestrator)

    def test_global_instance_initialization(self):
        """Test global instance is properly initialized"""
        assert automation_orchestrator.decision_history == []
        assert len(automation_orchestrator.approach_success_rates) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])