"""
Unit tests for browser automation tools

Tests DOM-first automation approach and pydantic-ai integration.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.wyn360.tools.browser.browser_automation_tools import (
    BrowserAutomationTools,
    browser_tools
)
from src.wyn360.tools.browser.dom_analyzer import DOMAnalysis, DOMElement


class TestBrowserAutomationTools:
    """Test browser automation tools functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.tools = BrowserAutomationTools()
        self.mock_ctx = Mock()

    def test_tools_initialization(self):
        """Test browser automation tools initialization"""
        assert self.tools.dom_extractor is not None
        assert self.tools.page is None

    def test_determine_automation_approach(self):
        """Test automation approach determination"""
        # High confidence with many interactive elements -> DOM
        high_conf_analysis = Mock()
        high_conf_analysis.analysis_confidence = 0.8
        high_conf_analysis.interactive_elements = [Mock()] * 5
        high_conf_analysis.forms = []

        approach = self.tools._determine_automation_approach(high_conf_analysis, 0.7)
        assert approach == 'dom_analysis'

        # High confidence with forms -> DOM
        form_analysis = Mock()
        form_analysis.analysis_confidence = 0.8
        form_analysis.interactive_elements = [Mock()] * 2
        form_analysis.forms = [{'method': 'post'}]

        approach = self.tools._determine_automation_approach(form_analysis, 0.7)
        assert approach == 'dom_analysis'

        # Medium confidence -> Stagehand
        medium_conf_analysis = Mock()
        medium_conf_analysis.analysis_confidence = 0.55
        medium_conf_analysis.interactive_elements = [Mock()] * 2
        medium_conf_analysis.forms = []

        approach = self.tools._determine_automation_approach(medium_conf_analysis, 0.7)
        assert approach == 'stagehand_recommended'

        # Low confidence -> Vision fallback
        low_conf_analysis = Mock()
        low_conf_analysis.analysis_confidence = 0.3
        low_conf_analysis.interactive_elements = []
        low_conf_analysis.forms = []

        approach = self.tools._determine_automation_approach(low_conf_analysis, 0.7)
        assert approach == 'vision_fallback'

    @pytest.mark.asyncio
    async def test_execute_action_on_element_click(self):
        """Test executing click action on element"""
        mock_element = AsyncMock()

        result = await self.tools._execute_action_on_element(mock_element, 'click', None)

        assert result['success'] is True
        assert 'clicked successfully' in result['result']
        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_action_on_element_type(self):
        """Test executing type action on element"""
        mock_element = AsyncMock()
        action_data = {'text': 'Hello World'}

        result = await self.tools._execute_action_on_element(mock_element, 'type', action_data)

        assert result['success'] is True
        assert 'Hello World' in result['result']
        mock_element.fill.assert_called_once_with('Hello World')

    @pytest.mark.asyncio
    async def test_execute_action_on_element_type_no_data(self):
        """Test type action without text data"""
        mock_element = AsyncMock()

        result = await self.tools._execute_action_on_element(mock_element, 'type', None)

        assert result['success'] is False
        assert 'No text provided' in result['error']

    @pytest.mark.asyncio
    async def test_execute_action_on_element_select(self):
        """Test executing select action on element"""
        mock_element = AsyncMock()
        action_data = {'option': 'Option 1'}

        result = await self.tools._execute_action_on_element(mock_element, 'select', action_data)

        assert result['success'] is True
        assert 'Option 1' in result['result']
        mock_element.select_option.assert_called_once_with(label='Option 1')

    @pytest.mark.asyncio
    async def test_execute_action_on_element_clear(self):
        """Test executing clear action on element"""
        mock_element = AsyncMock()

        result = await self.tools._execute_action_on_element(mock_element, 'clear', None)

        assert result['success'] is True
        assert 'cleared' in result['result']
        mock_element.fill.assert_called_once_with('')

    @pytest.mark.asyncio
    async def test_execute_action_on_element_unknown(self):
        """Test unknown action"""
        mock_element = AsyncMock()

        result = await self.tools._execute_action_on_element(mock_element, 'unknown', None)

        assert result['success'] is False
        assert 'Unknown action' in result['error']

    @pytest.mark.asyncio
    async def test_find_element_by_description(self):
        """Test finding element by description"""
        # Mock page with elements
        mock_page = AsyncMock()
        self.tools.page = mock_page

        mock_element1 = AsyncMock()
        mock_element1.text_content.return_value = 'Submit Button'
        mock_element1.get_attribute.return_value = None

        mock_element2 = AsyncMock()
        mock_element2.text_content.return_value = 'Cancel'
        mock_element2.get_attribute.return_value = None

        mock_page.query_selector_all.return_value = [mock_element1, mock_element2]

        # Should find first element by text match
        result = await self.tools._find_element_by_description('submit')
        assert result == mock_element1

        # Should find by attribute
        mock_element2.get_attribute.side_effect = lambda attr: 'Login Button' if attr == 'aria-label' else None
        result = await self.tools._find_element_by_description('login')
        assert result == mock_element2

    @pytest.mark.asyncio
    async def test_find_element_by_description_not_found(self):
        """Test element not found scenario"""
        mock_page = AsyncMock()
        self.tools.page = mock_page

        mock_element = AsyncMock()
        mock_element.text_content.return_value = 'Different Text'
        mock_element.get_attribute.return_value = None

        mock_page.query_selector_all.return_value = [mock_element]

        result = await self.tools._find_element_by_description('nonexistent')
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_page_dom_success(self):
        """Test successful DOM analysis"""
        with patch('src.wyn360.tools.browser.browser_automation_tools.browser_manager') as mock_manager:
            with patch.object(self.tools.dom_extractor, 'extract_dom') as mock_extract:
                # Mock unified browser manager
                mock_page = AsyncMock()
                mock_page.goto = AsyncMock()
                mock_page.wait_for_load_state = AsyncMock()
                mock_manager.initialize = AsyncMock()
                mock_manager.get_page = AsyncMock(return_value=mock_page)
                self.tools.page = mock_page

                # Mock DOM analysis
                mock_dom = DOMAnalysis(
                    url='https://example.com',
                    title='Test Page',
                    interactive_elements=[
                        DOMElement('button', 'Submit', {'id': 'btn'}, '', '', True, 'button', 0.9)
                    ],
                    forms=[],
                    navigation_elements=[],
                    content_elements=[],
                    total_elements=1,
                    analysis_confidence=0.85
                )
                mock_extract.return_value = mock_dom

                result = await self.tools.analyze_page_dom(
                    self.mock_ctx,
                    'https://example.com',
                    'Click submit button'
                )

                assert result['success'] is True
                assert result['url'] == 'https://example.com'
                assert result['title'] == 'Test Page'
                assert result['confidence'] == 0.85
                assert result['interactive_elements_count'] == 1
                assert 'User Task: Click submit button' in result['dom_analysis_text']
                assert result['recommended_approach'] in ['dom_analysis', 'stagehand_recommended']

    @pytest.mark.asyncio
    async def test_analyze_page_dom_failure(self):
        """Test DOM analysis failure"""
        with patch('src.wyn360.tools.browser.browser_automation_tools.browser_manager') as mock_manager:
            mock_manager.initialize.side_effect = Exception("Browser error")
            result = await self.tools.analyze_page_dom(
                self.mock_ctx,
                'https://example.com'
            )

            assert result['success'] is False
            assert 'Browser error' in result['error']
            assert result['confidence'] == 0.0
            assert result['recommended_approach'] == 'vision_fallback'

    @pytest.mark.asyncio
    async def test_execute_dom_action_low_confidence(self):
        """Test DOM action with low confidence"""
        with patch.object(self.tools, 'analyze_page_dom') as mock_analyze:
            mock_analyze.return_value = {
                'success': True,
                'confidence': 0.5,
                'dom_analysis_text': 'Low confidence analysis'
            }

            result = await self.tools.execute_dom_action(
                self.mock_ctx,
                'https://example.com',
                'click',
                'submit button',
                confidence_threshold=0.7
            )

            assert result['success'] is False
            assert 'below threshold' in result['error']
            assert result['recommendation'] == 'Use stagehand fallback'
            assert result['confidence'] == 0.5

    @pytest.mark.asyncio
    async def test_execute_dom_action_element_not_found(self):
        """Test DOM action when element is not found"""
        with patch.object(self.tools, 'analyze_page_dom') as mock_analyze:
            with patch.object(self.tools, '_find_element_by_description', return_value=None):
                mock_analyze.return_value = {
                    'success': True,
                    'confidence': 0.8,
                    'dom_analysis_text': 'High confidence analysis'
                }

                result = await self.tools.execute_dom_action(
                    self.mock_ctx,
                    'https://example.com',
                    'click',
                    'nonexistent button',
                    confidence_threshold=0.7
                )

                assert result['success'] is False
                assert 'Could not find element' in result['error']
                assert result['recommendation'] == 'Use stagehand fallback with this DOM context'

    @pytest.mark.asyncio
    async def test_execute_dom_action_success(self):
        """Test successful DOM action execution"""
        with patch.object(self.tools, 'analyze_page_dom') as mock_analyze:
            with patch.object(self.tools, '_find_element_by_description') as mock_find:
                with patch.object(self.tools, '_execute_action_on_element') as mock_execute:
                    # Mock successful analysis
                    mock_analyze.return_value = {
                        'success': True,
                        'confidence': 0.8,
                        'dom_analysis_text': 'High confidence analysis'
                    }

                    # Mock finding element
                    mock_element = Mock()
                    mock_find.return_value = mock_element

                    # Mock successful action
                    mock_execute.return_value = {
                        'success': True,
                        'result': 'Button clicked'
                    }

                    # Mock page for wait_for_load_state
                    mock_page = AsyncMock()
                    self.tools.page = mock_page

                    result = await self.tools.execute_dom_action(
                        self.mock_ctx,
                        'https://example.com',
                        'click',
                        'submit button',
                        confidence_threshold=0.7
                    )

                    assert result['success'] is True
                    assert result['action'] == 'click'
                    assert result['target'] == 'submit button'
                    assert result['confidence'] == 0.8
                    assert result['approach_used'] == 'dom_analysis'

    @pytest.mark.asyncio
    async def test_close_browser(self):
        """Test browser cleanup"""
        with patch('src.wyn360.tools.browser.browser_automation_tools.browser_manager') as mock_manager:
            mock_page = AsyncMock()
            mock_manager.close_page = AsyncMock()
            self.tools.page = mock_page

            await self.tools.close_browser()

            # Verify that browser manager's close_page was called
            mock_manager.close_page.assert_called_once_with("dom_analysis")
            assert self.tools.page is None


class TestGlobalBrowserTools:
    """Test global browser tools instance"""

    def test_global_instance_exists(self):
        """Test that global instance exists"""
        assert browser_tools is not None
        assert isinstance(browser_tools, BrowserAutomationTools)

    def test_global_instance_initialization(self):
        """Test global instance is properly initialized"""
        assert browser_tools.dom_extractor is not None
        assert browser_tools.page is None  # Should be None until initialized


class TestIntegration:
    """Integration tests for browser automation tools"""

    def test_workflow_integration(self):
        """Test the expected integration workflow"""
        # This test demonstrates how the tools would be used in the agent
        tools = BrowserAutomationTools()

        # 1. The agent would call analyze_page_dom first
        # 2. Based on confidence, decide approach
        # 3. Execute actions using the appropriate method

        # Mock a high-confidence scenario
        mock_analysis = {
            'success': True,
            'confidence': 0.9,
            'recommended_approach': 'dom_analysis',
            'interactive_elements_count': 5,
            'dom_analysis_text': 'Page has login form with email and password fields'
        }

        # Simulate decision logic
        if mock_analysis['confidence'] >= 0.7:
            if mock_analysis['recommended_approach'] == 'dom_analysis':
                approach = 'dom'
            else:
                approach = 'stagehand'
        else:
            approach = 'vision'

        assert approach == 'dom'

        # Mock a low-confidence scenario
        mock_low_analysis = {
            'success': True,
            'confidence': 0.4,
            'recommended_approach': 'vision_fallback'
        }

        if mock_low_analysis['confidence'] >= 0.7:
            approach = 'dom'
        elif mock_low_analysis['confidence'] >= 0.5:
            approach = 'stagehand'
        else:
            approach = 'vision'

        assert approach == 'vision'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])