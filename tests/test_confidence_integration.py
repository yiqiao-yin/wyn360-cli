"""
Integration tests for confidence scoring across the browser automation system

Tests that confidence scoring works consistently across DOM analysis,
automation tools, and orchestrator components.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.wyn360.tools.browser.dom_analyzer import DOMExtractor, DOMElement, DOMAnalysis
from src.wyn360.tools.browser.browser_automation_tools import BrowserAutomationTools
from src.wyn360.tools.browser.automation_orchestrator import (
    AutomationOrchestrator,
    ActionRequest,
    ActionResult,
    AutomationApproach
)


class TestConfidenceScoring:
    """Test confidence scoring integration across components"""

    def test_element_confidence_calculation(self):
        """Test individual element confidence calculation"""
        extractor = DOMExtractor()

        # High confidence element (button with id and text)
        high_conf_element = DOMElement(
            tag='button',
            text='Submit Form',
            attributes={'id': 'submit-btn', 'class': 'btn-primary'},
            xpath='//button[@id="submit-btn"]',
            selector='#submit-btn',
            is_interactive=True,
            element_type='button',
            confidence=0.0  # Will be calculated
        )

        confidence = extractor._calculate_element_confidence(high_conf_element)
        assert confidence >= 0.8, f"Expected high confidence, got {confidence}"

        # Medium confidence element (input with placeholder)
        medium_conf_element = DOMElement(
            tag='input',
            text='',
            attributes={'placeholder': 'Enter email', 'type': 'email'},
            xpath='//input[@placeholder="Enter email"]',
            selector='input[placeholder="Enter email"]',
            is_interactive=True,
            element_type='input',
            confidence=0.0
        )

        confidence = extractor._calculate_element_confidence(medium_conf_element)
        assert 0.5 <= confidence <= 0.8, f"Expected medium confidence, got {confidence}"

        # Low confidence element (generic div)
        low_conf_element = DOMElement(
            tag='div',
            text='Some text',
            attributes={'class': 'generic'},
            xpath='//div[@class="generic"]',
            selector='div.generic',
            is_interactive=False,
            element_type='other',
            confidence=0.0
        )

        confidence = extractor._calculate_element_confidence(low_conf_element)
        assert confidence <= 0.7, f"Expected low confidence, got {confidence}"

    def test_analysis_confidence_calculation(self):
        """Test overall analysis confidence calculation"""
        extractor = DOMExtractor()

        # High confidence scenario - many interactive elements
        high_conf_elements = [
            DOMElement('button', 'Submit', {'id': 'btn1'}, '', '', True, 'button', 0.9),
            DOMElement('input', '', {'id': 'email'}, '', '', True, 'input', 0.8),
            DOMElement('input', '', {'id': 'password'}, '', '', True, 'input', 0.8),
            DOMElement('a', 'Login', {'href': '/login'}, '', '', True, 'link', 0.7),
        ]

        navigation_elements = []
        forms = [{'method': 'post', 'action': '/submit'}]

        confidence = extractor._calculate_analysis_confidence(
            high_conf_elements, forms, navigation_elements
        )
        assert confidence >= 0.6, f"Expected high analysis confidence, got {confidence}"

        # Low confidence scenario - few elements
        low_conf_elements = [
            DOMElement('div', 'Text', {}, '', '', False, 'other', 0.3),
        ]

        confidence = extractor._calculate_analysis_confidence(
            low_conf_elements, [], []
        )
        assert confidence <= 0.5, f"Expected low analysis confidence, got {confidence}"

    @pytest.mark.asyncio
    async def test_browser_tools_confidence_integration(self):
        """Test confidence usage in browser automation tools"""
        tools = BrowserAutomationTools()

        # Mock DOM analysis with specific confidence
        mock_dom = DOMAnalysis(
            url='https://example.com',
            title='Test Page',
            interactive_elements=[
                DOMElement('button', 'Submit', {'id': 'btn'}, '', '', True, 'button', 0.9),
                DOMElement('input', 'Email', {'id': 'email'}, '', '', True, 'input', 0.8),
                DOMElement('input', 'Password', {'id': 'password'}, '', '', True, 'input', 0.8),
                DOMElement('a', 'Link', {'href': '/test'}, '', '', True, 'link', 0.7)
            ],
            forms=[],
            navigation_elements=[],
            content_elements=[],
            total_elements=4,
            analysis_confidence=0.85
        )

        # Test confidence threshold enforcement - should use DOM analysis with high confidence and many elements
        result = tools._determine_automation_approach(mock_dom, 0.7)
        assert result == 'dom_analysis', "High confidence with many elements should recommend DOM analysis"

        result = tools._determine_automation_approach(mock_dom, 0.9)
        assert result == 'stagehand_recommended', "Confidence below threshold should recommend stagehand"

        # Test with lower confidence
        mock_dom.analysis_confidence = 0.4
        result = tools._determine_automation_approach(mock_dom, 0.7)
        assert result == 'vision_fallback', "Low confidence should recommend vision fallback"

    def test_orchestrator_confidence_decisions(self):
        """Test orchestrator decision making based on confidence"""
        orchestrator = AutomationOrchestrator()

        # High confidence scenario
        request = ActionRequest(
            url='https://example.com',
            task_description='Click button',
            action_type='click',
            target_description='submit button',
            confidence_threshold=0.7
        )

        dom_result = {
            'confidence': 0.85,
            'interactive_elements_count': 5,
            'forms_count': 1
        }

        approach, context, reasoning = orchestrator.decide_automation_approach(request, dom_result)
        assert approach == AutomationApproach.DOM_ANALYSIS
        assert "High DOM confidence" in reasoning
        assert context.dom_confidence == 0.85

        # Low confidence scenario
        dom_result['confidence'] = 0.3
        approach, context, reasoning = orchestrator.decide_automation_approach(request, dom_result)
        assert approach == AutomationApproach.VISION_FALLBACK
        assert "Low confidence" in reasoning

    def test_confidence_learning_integration(self):
        """Test confidence-based learning in orchestrator"""
        orchestrator = AutomationOrchestrator()

        # Simulate successful execution with high confidence
        request = ActionRequest(
            url='https://example.com',
            task_description='Test',
            action_type='click',
            target_description='button'
        )

        success_result = ActionResult(
            success=True,
            approach_used=AutomationApproach.DOM_ANALYSIS,
            confidence=0.9,
            execution_time=1.0,
            result_data={'status': 'success'}
        )

        initial_rate = orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS]
        orchestrator.record_execution_result(request, AutomationApproach.DOM_ANALYSIS, success_result)

        # Success rate should improve
        new_rate = orchestrator.approach_success_rates[AutomationApproach.DOM_ANALYSIS]
        assert new_rate >= initial_rate, "Success rate should improve after successful execution"

    def test_confidence_analytics_integration(self):
        """Test confidence tracking in analytics"""
        orchestrator = AutomationOrchestrator()

        # Add decision history with various confidence levels
        orchestrator.decision_history = [
            {'approach': 'dom_analysis', 'dom_confidence': 0.9, 'success': True},
            {'approach': 'dom_analysis', 'dom_confidence': 0.7, 'success': True},
            {'approach': 'stagehand', 'dom_confidence': 0.5, 'success': False},
            {'approach': 'vision_fallback', 'dom_confidence': 0.2, 'success': True},
        ]

        analytics = orchestrator.get_decision_analytics()

        assert analytics['total_decisions'] == 4
        assert abs(analytics['average_confidence'] - 0.575) < 0.01  # (0.9+0.7+0.5+0.2)/4

        # Test suggestions based on confidence patterns
        suggestions = orchestrator.suggest_improvements()

        # Should suggest improving confidence if average is low
        if analytics['average_confidence'] < 0.5:
            assert any('confidence' in suggestion.lower() for suggestion in suggestions)

    @pytest.mark.asyncio
    async def test_end_to_end_confidence_flow(self):
        """Test complete confidence scoring flow from DOM to decision"""

        # This simulates the complete flow:
        # 1. DOM extraction calculates element confidence
        # 2. Overall analysis confidence is calculated
        # 3. Browser tools use confidence for approach selection
        # 4. Orchestrator makes decisions based on confidence
        # 5. Results are recorded for learning

        extractor = DOMExtractor()
        tools = BrowserAutomationTools()
        orchestrator = AutomationOrchestrator()

        # Step 1 & 2: Mock DOM extraction with confidence calculation
        mock_elements = [
            DOMElement('button', 'Submit', {'id': 'submit'}, '', '', True, 'button', 0.0),
            DOMElement('input', '', {'type': 'email'}, '', '', True, 'input', 0.0)
        ]

        # Calculate element confidences
        for element in mock_elements:
            element.confidence = extractor._calculate_element_confidence(element)

        # Calculate overall confidence
        analysis_confidence = extractor._calculate_analysis_confidence(
            mock_elements, [{'method': 'post'}], []
        )

        assert analysis_confidence > 0.0, "Analysis confidence should be calculated"

        # Step 3: Browser tools approach determination
        mock_analysis = Mock()
        mock_analysis.analysis_confidence = analysis_confidence
        mock_analysis.interactive_elements = mock_elements
        mock_analysis.forms = [{'method': 'post'}]

        approach = tools._determine_automation_approach(mock_analysis, 0.7)
        assert approach in ['dom_analysis', 'stagehand_recommended', 'vision_fallback']

        # Step 4: Orchestrator decision making
        request = ActionRequest(
            url='https://example.com',
            task_description='Submit form',
            action_type='click',
            target_description='submit button'
        )

        dom_result = {
            'confidence': analysis_confidence,
            'interactive_elements_count': len(mock_elements),
            'forms_count': 1
        }

        chosen_approach, context, reasoning = orchestrator.decide_automation_approach(request, dom_result)
        assert context.dom_confidence == analysis_confidence
        assert chosen_approach in [AutomationApproach.DOM_ANALYSIS,
                                  AutomationApproach.STAGEHAND,
                                  AutomationApproach.VISION_FALLBACK]

        # Step 5: Record result for learning
        result = ActionResult(
            success=True,
            approach_used=chosen_approach,
            confidence=analysis_confidence,
            execution_time=1.5,
            result_data={'status': 'completed'}
        )

        orchestrator.record_execution_result(request, chosen_approach, result)

        # Verify learning occurred
        assert orchestrator.total_attempts[chosen_approach] > 0
        assert len(orchestrator.decision_history) > 0

    def test_confidence_thresholds_consistency(self):
        """Test that confidence thresholds are used consistently across components"""
        tools = BrowserAutomationTools()
        orchestrator = AutomationOrchestrator()

        # Test various confidence levels with different thresholds
        test_cases = [
            (0.9, 0.7, True),   # High confidence, standard threshold -> should use DOM
            (0.6, 0.7, False),  # Medium confidence, standard threshold -> should not use DOM
            (0.8, 0.9, False),  # High confidence, high threshold -> should not use DOM
            (0.5, 0.4, True),   # Medium confidence, low threshold -> should use DOM
        ]

        for confidence, threshold, should_use_dom in test_cases:
            mock_analysis = Mock()
            mock_analysis.analysis_confidence = confidence
            mock_analysis.interactive_elements = [Mock()] * 5  # Enough elements
            mock_analysis.forms = []

            approach = tools._determine_automation_approach(mock_analysis, threshold)

            if should_use_dom:
                assert approach == 'dom_analysis', f"Confidence {confidence} with threshold {threshold} should use DOM"
            else:
                assert approach != 'dom_analysis', f"Confidence {confidence} with threshold {threshold} should not use DOM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])