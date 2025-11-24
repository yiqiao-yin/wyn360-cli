"""
Unit tests for Vision Optimization

Tests the enhanced routing logic that optimizes vision usage for edge cases only,
ensuring cost-effective and performance-aware automation approach selection.
"""

import pytest
from unittest.mock import Mock, patch
from src.wyn360.tools.browser.enhanced_automation_orchestrator import (
    EnhancedAutomationOrchestrator,
    EnhancedActionRequest
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    DecisionContext
)


class TestVisionOptimization:
    """Test vision optimization and edge case detection"""

    @pytest.fixture
    def enhanced_orchestrator(self):
        """Create enhanced orchestrator with mocked dependencies"""
        orchestrator = EnhancedAutomationOrchestrator()
        orchestrator.base_orchestrator = Mock()
        orchestrator.stagehand_integration = Mock()
        orchestrator.vision_integration = Mock()
        orchestrator.vision_integration.is_available = Mock(return_value=True)
        return orchestrator

    def test_calculate_edge_case_score_simple_task(self, enhanced_orchestrator):
        """Test edge case score calculation for simple tasks"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the button",
            action_type="click",
            target_description="button"
        )

        context = DecisionContext(
            dom_confidence=0.6,
            page_complexity="simple",
            element_count=3,
            forms_count=0,
            previous_failures=[]
        )

        score = enhanced_orchestrator._calculate_edge_case_score(request, context, "simple_interaction")

        # Simple task should have low edge case score
        # 0.1 (simple page) + 0.1 (good confidence) + 0.1 (simple task) = 0.3
        assert abs(score - 0.3) < 0.01

    def test_calculate_edge_case_score_complex_task(self, enhanced_orchestrator):
        """Test edge case score calculation for complex tasks"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Navigate through dynamic React SPA with complex interactions",
            action_type="navigate",
            target_description="react components"
        )

        context = DecisionContext(
            dom_confidence=0.1,
            page_complexity="complex",
            element_count=25,
            forms_count=2,
            previous_failures=["dom_analysis", "stagehand"]
        )

        score = enhanced_orchestrator._calculate_edge_case_score(request, context, "complex_navigation")

        # Complex task should have high edge case score
        # 0.3 (complex page) + 0.3 (low confidence) + 0.3 (complex task) + 0.1 (many elements) + 0.2 (failures) + keywords
        assert score > 0.8

    def test_calculate_edge_case_score_with_keywords(self, enhanced_orchestrator):
        """Test edge case score with complexity keywords"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Interact with animated dropdown and modal popup",
            action_type="interact",
            target_description="UI elements"
        )

        context = DecisionContext(
            dom_confidence=0.5,
            page_complexity="moderate",
            element_count=10,
            forms_count=0,
            previous_failures=[]
        )

        score = enhanced_orchestrator._calculate_edge_case_score(request, context, "general")

        # Should include keyword bonus for "animated", "dropdown", "modal", "popup"
        # Base: 0.2 (moderate) + 0.1 (medium confidence) + 0.1 (general) + 0 (element count) = 0.4
        # Keywords: 4 * 0.05 = 0.2 (but capped at 0.15)
        # Total: 0.4 + 0.15 = 0.55
        assert abs(score - 0.55) < 0.01

    def test_vision_cost_optimization_prefers_stagehand(self, enhanced_orchestrator):
        """Test that cost optimization prefers Stagehand over vision"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Moderate task",
            action_type="click",
            target_description="element",
            enable_stagehand=True
        )

        context = DecisionContext(
            dom_confidence=0.3,
            page_complexity="moderate",
            element_count=10,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "general", True, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.STAGEHAND
        assert "Cost optimization" in reasoning

    def test_simple_task_optimization_prefers_dom(self, enhanced_orchestrator):
        """Test that simple tasks prefer DOM over expensive vision"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click button",
            action_type="click",
            target_description="button"
        )

        context = DecisionContext(
            dom_confidence=0.15,  # Low confidence that triggers vision cost optimization
            page_complexity="simple",
            element_count=5,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "simple_interaction", True, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Simple task optimization" in reasoning

    def test_performance_optimization_for_simple_tasks(self, enhanced_orchestrator):
        """Test performance optimization for simple tasks with adequate confidence"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the submit button",
            action_type="click",
            target_description="submit button"
        )

        context = DecisionContext(
            dom_confidence=0.35,  # Above performance optimization threshold but below simple interaction threshold
            page_complexity="moderate",
            element_count=8,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "simple_interaction", True, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.STAGEHAND
        assert "Cost optimization" in reasoning

    def test_vision_unavailable_fallback_to_stagehand(self, enhanced_orchestrator):
        """Test fallback to Stagehand when vision is unavailable"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Complex task",
            action_type="complex",
            target_description="complex element",
            enable_stagehand=True
        )

        context = DecisionContext(
            dom_confidence=0.15,  # Low enough to trigger vision cost optimization
            page_complexity="complex",
            element_count=20,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "general", False, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.STAGEHAND
        assert "Vision unavailable" in reasoning

    def test_vision_unavailable_fallback_to_dom(self, enhanced_orchestrator):
        """Test fallback to DOM when vision unavailable and Stagehand disabled"""
        enhanced_orchestrator.vision_integration.is_available.return_value = False

        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Task",
            action_type="click",
            target_description="element",
            enable_stagehand=False
        )

        context = DecisionContext(
            dom_confidence=0.2,
            page_complexity="moderate",
            element_count=8,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "general", False, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Vision unavailable" in reasoning

    def test_edge_case_analysis_blocks_vision_for_simple_task(self, enhanced_orchestrator):
        """Test that edge case analysis prevents vision usage for simple tasks"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click button",
            action_type="click",
            target_description="button",
            enable_stagehand=True
        )

        context = DecisionContext(
            dom_confidence=0.01,  # Extremely low confidence for edge case score < 0.5
            page_complexity="simple",
            element_count=3,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "simple_interaction", True, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.VISION_FALLBACK
        assert "Base routing decision" in reasoning

    def test_edge_case_analysis_allows_vision_for_complex_task(self, enhanced_orchestrator):
        """Test that edge case analysis allows vision for truly complex tasks"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Navigate complex React SPA with dynamic content and modal interactions",
            action_type="navigate",
            target_description="dynamic elements",
            enable_stagehand=True
        )

        context = DecisionContext(
            dom_confidence=0.1,
            page_complexity="complex",
            element_count=30,
            forms_count=2,
            previous_failures=["dom_analysis", "stagehand"]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "complex_navigation", True, AutomationApproach.VISION_FALLBACK
        )

        # Should allow vision to proceed for this truly complex edge case
        assert approach == AutomationApproach.VISION_FALLBACK
        assert "visual understanding" in reasoning.lower()

    def test_very_high_confidence_always_prefers_dom(self, enhanced_orchestrator):
        """Test that very high DOM confidence always prefers DOM regardless of other factors"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Some unusual task",
            action_type="unusual",
            target_description="unusual elements"
        )

        context = DecisionContext(
            dom_confidence=0.9,  # Very high confidence
            page_complexity="complex",
            element_count=25,
            forms_count=2,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "general", True, AutomationApproach.STAGEHAND
        )

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Very high DOM confidence" in reasoning

    def test_multiple_optimization_rules_applied(self, enhanced_orchestrator):
        """Test that form interaction rule applies correctly"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Submit form",
            action_type="submit",
            target_description="form",
            enable_stagehand=True
        )

        context = DecisionContext(
            dom_confidence=0.6,
            page_complexity="moderate",
            element_count=10,
            forms_count=1,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "form_interaction", True, AutomationApproach.STAGEHAND
        )

        # Should prefer DOM due to form interaction rule with high confidence
        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Form interaction with high DOM confidence" in reasoning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])