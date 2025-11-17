"""Tests for VisionDecisionEngine class."""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.vision_engine import VisionDecisionEngine, VisionDecisionError


class TestVisionDecisionEngineInitialization:
    """Test VisionDecisionEngine initialization."""

    def test_initialize_with_agent(self):
        """Test initialization with agent."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        assert engine.agent == mock_agent


class TestPromptBuilding:
    """Test prompt building."""

    def test_build_analysis_prompt_no_history(self):
        """Test prompt building with no action history."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        page_state = {
            'url': 'https://example.com',
            'title': 'Example Page',
            'loaded': True
        }

        prompt = engine._build_analysis_prompt(
            goal="Find the price",
            history=[],
            page_state=page_state
        )

        assert "Find the price" in prompt
        assert "https://example.com" in prompt
        assert "Example Page" in prompt
        assert "Available actions:" in prompt

    def test_build_analysis_prompt_with_history(self):
        """Test prompt building with action history."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        page_state = {
            'url': 'https://example.com/products',
            'title': 'Products',
            'loaded': True
        }

        history = [
            {
                'step': 1,
                'action': {'type': 'click', 'selector': '#search-btn'},
                'result': {'success': True}
            },
            {
                'step': 2,
                'action': {'type': 'type', 'selector': '#search', 'text': 'shoes'},
                'result': {'success': True}
            }
        ]

        prompt = engine._build_analysis_prompt(
            goal="Find cheapest shoes",
            history=history,
            page_state=page_state
        )

        assert "Find cheapest shoes" in prompt
        assert "Actions taken so far:" in prompt
        assert "click" in prompt
        assert "type" in prompt


class TestDecisionParsing:
    """Test decision parsing."""

    def test_parse_valid_json_decision(self):
        """Test parsing valid JSON decision."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        response = json.dumps({
            "status": "continue",
            "action": {"type": "click", "selector": "#btn"},
            "reasoning": "I see a button to click",
            "confidence": 85
        })

        page_state = {'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        decision = engine._parse_decision(response, "test goal", page_state)

        assert decision['status'] == 'continue'
        assert decision['action']['type'] == 'click'
        assert decision['reasoning'] == "I see a button to click"
        assert decision['confidence'] == 85

    def test_parse_decision_with_missing_fields(self):
        """Test parsing decision with missing optional fields."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        response = json.dumps({
            "status": "complete",
            "extracted_data": {"price": "$99.99"}
        })

        page_state = {'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        decision = engine._parse_decision(response, "test goal", page_state)

        assert decision['status'] == 'complete'
        assert 'action' in decision
        assert 'reasoning' in decision
        assert 'confidence' in decision
        assert decision['confidence'] == 50  # Default

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON falls back gracefully."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        response = "This is not valid JSON"

        page_state = {'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        decision = engine._parse_decision(response, "test goal", page_state)

        assert decision['status'] == 'continue'
        assert decision['action']['type'] == 'wait'
        assert decision['confidence'] == 0
        assert "Could not parse" in decision['reasoning']

    def test_parse_decision_confidence_bounds(self):
        """Test that confidence is bounded to 0-100."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        # Test confidence > 100
        response = json.dumps({
            "status": "continue",
            "action": {"type": "wait", "seconds": 1},
            "confidence": 150
        })

        page_state = {'url': 'https://example.com', 'title': 'Test', 'loaded': True}
        decision = engine._parse_decision(response, "test", page_state)
        assert decision['confidence'] == 100

        # Test confidence < 0
        response = json.dumps({
            "status": "continue",
            "action": {"type": "wait", "seconds": 1},
            "confidence": -50
        })

        decision = engine._parse_decision(response, "test", page_state)
        assert decision['confidence'] == 0


class TestActionValidation:
    """Test action validation."""

    def test_validate_click_action_with_selector(self):
        """Test validating click action with selector."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'click', 'selector': '#button'}
        assert engine._validate_action(action) is True

    def test_validate_click_action_with_text(self):
        """Test validating click action with text."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'click', 'text': 'Submit'}
        assert engine._validate_action(action) is True

    def test_validate_type_action(self):
        """Test validating type action."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'type', 'selector': '#input', 'text': 'hello'}
        assert engine._validate_action(action) is True

    def test_validate_type_action_missing_text(self):
        """Test validating type action without text fails."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'type', 'selector': '#input'}
        assert engine._validate_action(action) is False

    def test_validate_scroll_action(self):
        """Test validating scroll action."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'scroll', 'direction': 'down', 'amount': 500}
        assert engine._validate_action(action) is True

    def test_validate_navigate_action(self):
        """Test validating navigate action."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'navigate', 'url': 'https://example.com'}
        assert engine._validate_action(action) is True

    def test_validate_extract_action(self):
        """Test validating extract action."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'extract', 'selector': '.price'}
        assert engine._validate_action(action) is True

    def test_validate_wait_action(self):
        """Test validating wait action."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'wait', 'seconds': 2}
        assert engine._validate_action(action) is True

    def test_validate_invalid_action_type(self):
        """Test validating invalid action type."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        action = {'type': 'invalid_action'}
        assert engine._validate_action(action) is False

    def test_validate_non_dict_action(self):
        """Test validating non-dictionary action."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        assert engine._validate_action("not a dict") is False
        assert engine._validate_action(None) is False


class TestAnalyzeAndDecide:
    """Test main analyze_and_decide method."""

    @pytest.mark.asyncio
    async def test_analyze_and_decide_success(self):
        """Test successful analysis and decision."""
        mock_agent = AsyncMock()
        engine = VisionDecisionEngine(mock_agent)

        # Mock the _analyze_with_vision to return valid JSON
        mock_response = json.dumps({
            "status": "continue",
            "action": {"type": "click", "selector": "#next"},
            "reasoning": "Found next button",
            "confidence": 90
        })

        engine._analyze_with_vision = AsyncMock(return_value=mock_response)

        screenshot = b'fake_screenshot_data'
        goal = "Navigate to next page"
        history = []
        page_state = {'url': 'https://example.com', 'title': 'Page 1', 'loaded': True}

        decision = await engine.analyze_and_decide(screenshot, goal, history, page_state)

        assert decision['status'] == 'continue'
        assert decision['action']['type'] == 'click'
        assert decision['action']['selector'] == '#next'
        assert decision['confidence'] == 90

    @pytest.mark.asyncio
    async def test_analyze_and_decide_complete_status(self):
        """Test analysis returns complete status."""
        mock_agent = AsyncMock()
        engine = VisionDecisionEngine(mock_agent)

        mock_response = json.dumps({
            "status": "complete",
            "action": {"type": "extract", "selector": ".price"},
            "reasoning": "Found price information",
            "confidence": 95,
            "extracted_data": {"price": "$29.99"}
        })

        engine._analyze_with_vision = AsyncMock(return_value=mock_response)

        screenshot = b'fake_screenshot_data'
        goal = "Find product price"
        history = [{'step': 1, 'action': {'type': 'click', 'selector': '#product'}}]
        page_state = {'url': 'https://example.com/product', 'title': 'Product', 'loaded': True}

        decision = await engine.analyze_and_decide(screenshot, goal, history, page_state)

        assert decision['status'] == 'complete'
        assert decision['extracted_data'] == {"price": "$29.99"}

    @pytest.mark.asyncio
    async def test_analyze_and_decide_error(self):
        """Test error handling in analysis."""
        mock_agent = AsyncMock()
        engine = VisionDecisionEngine(mock_agent)

        # Mock _analyze_with_vision to raise an exception
        engine._analyze_with_vision = AsyncMock(side_effect=Exception("API error"))

        screenshot = b'fake_screenshot_data'
        goal = "Test goal"
        history = []
        page_state = {'url': 'https://example.com', 'title': 'Test', 'loaded': True}

        with pytest.raises(VisionDecisionError, match="Failed to analyze screenshot"):
            await engine.analyze_and_decide(screenshot, goal, history, page_state)


class TestCostEstimation:
    """Test cost estimation."""

    def test_estimate_cost_small_screenshot(self):
        """Test cost estimation for small screenshot."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        cost = engine.estimate_cost(screenshot_bytes=10000, history_length=0)

        # Should include base vision cost + minimal text cost
        assert cost > 0.01  # At least base vision cost
        assert cost < 0.02  # Not too expensive

    def test_estimate_cost_with_history(self):
        """Test cost estimation increases with history."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        cost_no_history = engine.estimate_cost(screenshot_bytes=10000, history_length=0)
        cost_with_history = engine.estimate_cost(screenshot_bytes=10000, history_length=10)

        # Cost should increase with history
        assert cost_with_history > cost_no_history

    def test_estimate_cost_large_screenshot(self):
        """Test cost estimation for large screenshot."""
        mock_agent = Mock()
        engine = VisionDecisionEngine(mock_agent)

        cost = engine.estimate_cost(screenshot_bytes=1000000, history_length=5)

        # Should be reasonable (not drastically different based on size alone)
        assert cost > 0
        assert cost < 1.0  # Sanity check
