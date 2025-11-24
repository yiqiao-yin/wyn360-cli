"""
Unit tests for Enhanced Automation Orchestrator - Intelligent Routing

Tests the intelligent routing capabilities of the EnhancedAutomationOrchestrator
that automatically selects the best approach based on task analysis,
performance history, and system capabilities.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.enhanced_automation_orchestrator import (
    EnhancedAutomationOrchestrator,
    EnhancedActionRequest
)
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationApproach,
    ActionResult,
    DecisionContext
)


class TestEnhancedIntelligentRouting:
    """Test enhanced intelligent routing functionality"""

    @pytest.fixture
    def mock_base_orchestrator(self):
        """Create mock base orchestrator"""
        orchestrator = Mock()
        orchestrator.decide_automation_approach = Mock()
        orchestrator.record_execution_result = Mock()
        return orchestrator

    @pytest.fixture
    def mock_stagehand_integration(self):
        """Create mock Stagehand integration"""
        integration = Mock()
        integration.execute_stagehand_automation = AsyncMock()
        return integration

    @pytest.fixture
    def mock_vision_integration(self):
        """Create mock vision integration"""
        integration = Mock()
        integration.is_available = Mock(return_value=True)
        integration.execute_vision_fallback = AsyncMock()
        return integration

    @pytest.fixture
    def enhanced_orchestrator(self, mock_base_orchestrator, mock_stagehand_integration, mock_vision_integration):
        """Create enhanced orchestrator with mocked dependencies"""
        orchestrator = EnhancedAutomationOrchestrator()
        orchestrator.base_orchestrator = mock_base_orchestrator
        orchestrator.stagehand_integration = mock_stagehand_integration
        orchestrator.vision_integration = mock_vision_integration
        return orchestrator

    @pytest.fixture
    def sample_request(self):
        """Create sample enhanced action request"""
        return EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the login button",
            action_type="click",
            target_description="login button"
        )

    def test_analyze_task_type_simple_interaction(self, enhanced_orchestrator):
        """Test task type analysis for simple interactions"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the continue button",
            action_type="click",
            target_description="continue button"
        )

        task_type = enhanced_orchestrator._analyze_task_type(request)
        assert task_type == "simple_interaction"

    def test_analyze_task_type_form_interaction(self, enhanced_orchestrator):
        """Test task type analysis for form interactions"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Fill out the registration form",
            action_type="type",
            target_description="form fields"
        )

        task_type = enhanced_orchestrator._analyze_task_type(request)
        assert task_type == "form_interaction"

    def test_analyze_task_type_complex_navigation(self, enhanced_orchestrator):
        """Test task type analysis for complex navigation"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Navigate to the settings page and explore options",
            action_type="navigate",
            target_description="settings page"
        )

        task_type = enhanced_orchestrator._analyze_task_type(request)
        assert task_type == "complex_navigation"

    def test_analyze_task_type_content_extraction(self, enhanced_orchestrator):
        """Test task type analysis for content extraction"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Extract the product price from the page",
            action_type="extract",
            target_description="product price"
        )

        task_type = enhanced_orchestrator._analyze_task_type(request)
        assert task_type == "content_extraction"

    def test_analyze_task_type_general(self, enhanced_orchestrator):
        """Test task type analysis for general tasks"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Do something weird",
            action_type="custom",
            target_description="custom element"
        )

        task_type = enhanced_orchestrator._analyze_task_type(request)
        assert task_type == "general"

    def test_is_vision_available_true(self, enhanced_orchestrator, mock_vision_integration):
        """Test vision availability check when available"""
        mock_vision_integration.is_available.return_value = True

        available = enhanced_orchestrator._is_vision_available()
        assert available is True

    def test_is_vision_available_false(self, enhanced_orchestrator, mock_vision_integration):
        """Test vision availability check when unavailable"""
        mock_vision_integration.is_available.return_value = False

        available = enhanced_orchestrator._is_vision_available()
        assert available is False

    def test_is_vision_available_exception(self, enhanced_orchestrator, mock_vision_integration):
        """Test vision availability check with exception"""
        mock_vision_integration.is_available.side_effect = Exception("Vision error")

        available = enhanced_orchestrator._is_vision_available()
        assert available is False

    def test_apply_enhanced_routing_simple_interaction_high_confidence(self, enhanced_orchestrator):
        """Test routing for simple interaction with high confidence"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the button",
            action_type="click",
            target_description="the button"
        )
        context = DecisionContext(
            dom_confidence=0.8,
            page_complexity="simple",
            element_count=5,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "simple_interaction", True, AutomationApproach.STAGEHAND
        )

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Simple interaction" in reasoning

    def test_apply_enhanced_routing_form_interaction_medium_confidence(self, enhanced_orchestrator):
        """Test routing for form interaction with medium confidence"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Fill form fields",
            action_type="type",
            target_description="form fields",
            enable_stagehand=True
        )
        context = DecisionContext(
            dom_confidence=0.4,
            page_complexity="moderate",
            element_count=10,
            forms_count=2,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "form_interaction", True, AutomationApproach.DOM_ANALYSIS
        )

        assert approach == AutomationApproach.STAGEHAND
        assert "AI assistance" in reasoning

    def test_apply_enhanced_routing_complex_navigation(self, enhanced_orchestrator):
        """Test routing for complex navigation task"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Navigate through multiple pages to find information",
            action_type="navigate",
            target_description="multiple pages",
            enable_stagehand=True
        )
        context = DecisionContext(
            dom_confidence=0.5,
            page_complexity="complex",
            element_count=20,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "complex_navigation", True, AutomationApproach.DOM_ANALYSIS
        )

        assert approach == AutomationApproach.STAGEHAND
        assert "Complex navigation" in reasoning

    def test_apply_enhanced_routing_stagehand_disabled(self, enhanced_orchestrator):
        """Test routing when Stagehand is disabled"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Complex task",
            action_type="complex",
            target_description="complex element",
            enable_stagehand=False,
            fallback_to_vision=True
        )
        context = DecisionContext(
            dom_confidence=0.3,
            page_complexity="complex",
            element_count=15,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "complex_navigation", True, AutomationApproach.STAGEHAND
        )

        assert approach == AutomationApproach.VISION_FALLBACK
        assert "Stagehand disabled" in reasoning

    def test_apply_enhanced_routing_vision_unavailable(self, enhanced_orchestrator):
        """Test routing when vision is unavailable"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Complex task requiring vision",
            action_type="complex",
            target_description="complex element",
            enable_stagehand=True
        )
        context = DecisionContext(
            dom_confidence=0.15,  # Lower than cost optimization threshold
            page_complexity="complex",
            element_count=20,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "complex_navigation", False, AutomationApproach.VISION_FALLBACK
        )

        assert approach == AutomationApproach.STAGEHAND
        assert "Vision unavailable" in reasoning

    def test_apply_enhanced_routing_very_high_confidence(self, enhanced_orchestrator):
        """Test routing with very high DOM confidence"""
        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Any task",
            action_type="any",
            target_description="any element"
        )
        context = DecisionContext(
            dom_confidence=0.9,
            page_complexity="moderate",
            element_count=10,
            forms_count=1,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "general", True, AutomationApproach.STAGEHAND
        )

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Very high DOM confidence" in reasoning

    def test_calculate_approach_success_rates(self, enhanced_orchestrator):
        """Test calculation of approach success rates"""
        # Add test execution history
        enhanced_orchestrator.execution_history = [
            {'approach_used': 'dom_analysis', 'success': True},
            {'approach_used': 'dom_analysis', 'success': True},
            {'approach_used': 'dom_analysis', 'success': False},
            {'approach_used': 'stagehand', 'success': True},
            {'approach_used': 'stagehand', 'success': True},
            {'approach_used': 'stagehand', 'success': True},
            {'approach_used': 'stagehand', 'success': False},
            {'approach_used': 'vision_fallback', 'success': True},  # Only 1, should be excluded
        ]

        success_rates = enhanced_orchestrator._calculate_approach_success_rates()

        assert 'dom_analysis' in success_rates
        assert 'stagehand' in success_rates
        assert 'vision_fallback' not in success_rates  # Insufficient data

        assert success_rates['dom_analysis'] == 2/3  # 2 successes out of 3
        assert success_rates['stagehand'] == 3/4      # 3 successes out of 4

    def test_apply_enhanced_routing_with_historical_data(self, enhanced_orchestrator):
        """Test routing with historical performance data"""
        # Set up history showing high DOM success rate
        enhanced_orchestrator.execution_history = [
            {'approach_used': 'dom_analysis', 'success': True},
            {'approach_used': 'dom_analysis', 'success': True},
            {'approach_used': 'dom_analysis', 'success': True},
            {'approach_used': 'stagehand', 'success': False},
            {'approach_used': 'stagehand', 'success': False},
            {'approach_used': 'stagehand', 'success': True},
        ] + [{'approach_used': 'dom_analysis', 'success': True}] * 10  # 13 total DOM records

        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Test task",
            action_type="test",
            target_description="test element"
        )
        context = DecisionContext(
            dom_confidence=0.6,
            page_complexity="moderate",
            element_count=8,
            forms_count=0,
            previous_failures=[]
        )

        approach, reasoning = enhanced_orchestrator._apply_enhanced_routing_rules(
            request, context, "general", True, AutomationApproach.STAGEHAND
        )

        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Historical DOM success rate" in reasoning

    def test_make_intelligent_routing_decision_enhanced_override(self, enhanced_orchestrator, mock_base_orchestrator):
        """Test that enhanced routing can override base decision"""
        # Mock base orchestrator to return Stagehand
        mock_base_orchestrator.decide_automation_approach.return_value = (
            AutomationApproach.STAGEHAND,
            DecisionContext(dom_confidence=0.8, page_complexity="simple", element_count=3, forms_count=0, previous_failures=[]),
            "Base reasoning"
        )

        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Click the button",  # Simple interaction
            action_type="click",
            target_description="the button"
        )

        with patch('src.wyn360.tools.browser.enhanced_automation_orchestrator.browser_tools') as mock_browser_tools:
            mock_browser_tools.analyze_page_dom.return_value = {'success': True, 'confidence': 0.8}

            approach, context, reasoning = enhanced_orchestrator._make_intelligent_routing_decision(
                request, {'success': True, 'confidence': 0.8}
            )

        # Should override to DOM analysis due to high confidence simple interaction
        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "Simple interaction" in reasoning

    def test_make_intelligent_routing_decision_use_base(self, enhanced_orchestrator, mock_base_orchestrator):
        """Test that enhanced routing uses base decision when appropriate"""
        # Mock base orchestrator
        mock_base_orchestrator.decide_automation_approach.return_value = (
            AutomationApproach.DOM_ANALYSIS,
            DecisionContext(dom_confidence=0.7, page_complexity="moderate", element_count=8, forms_count=1, previous_failures=[]),
            "Base reasoning"
        )

        request = EnhancedActionRequest(
            url="https://example.com",
            task_description="Some general task",
            action_type="general",
            target_description="general element"
        )

        approach, context, reasoning = enhanced_orchestrator._make_intelligent_routing_decision(
            request, {'success': True, 'confidence': 0.7}
        )

        # Should use base decision
        assert approach == AutomationApproach.DOM_ANALYSIS
        assert reasoning == "Base reasoning"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])