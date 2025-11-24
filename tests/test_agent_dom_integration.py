"""
Integration tests for DOM-first browser automation tools in WYN360Agent

Tests that the new DOM-first browser automation tools are properly
integrated into the WYN360 pydantic-ai agent system.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.agent import WYN360Agent


class TestAgentDOMIntegration:
    """Test DOM-first browser automation integration with WYN360Agent"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock WYN360Agent for testing"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('wyn360_cli.agent.AnthropicModel'):
                with patch('wyn360_cli.agent.Agent'):
                    agent = WYN360Agent()
                    return agent

    def test_agent_has_new_tools(self, mock_agent):
        """Test that the new DOM tools are available in the agent"""
        # Check that the new tool methods exist
        assert hasattr(mock_agent, 'analyze_page_dom')
        assert hasattr(mock_agent, 'execute_dom_action')
        assert hasattr(mock_agent, 'intelligent_browse')

        # Check that methods are async
        assert hasattr(mock_agent.analyze_page_dom, '__call__')
        assert hasattr(mock_agent.execute_dom_action, '__call__')
        assert hasattr(mock_agent.intelligent_browse, '__call__')

    @pytest.mark.asyncio
    async def test_analyze_page_dom_integration(self, mock_agent):
        """Test analyze_page_dom tool integration"""
        mock_ctx = Mock()

        # Mock the browser_tools.analyze_page_dom method
        with patch('wyn360_cli.agent.browser_tools.analyze_page_dom') as mock_analyze:
            mock_analyze.return_value = {
                'success': True,
                'title': 'Test Page',
                'confidence': 0.85,
                'interactive_elements_count': 5,
                'forms_count': 1,
                'recommended_approach': 'dom_analysis',
                'dom_analysis_text': 'Sample DOM analysis'
            }

            result = await mock_agent.analyze_page_dom(
                mock_ctx, 'https://example.com', 'Test task'
            )

            # Verify the tool was called correctly
            mock_analyze.assert_called_once_with(
                mock_ctx, 'https://example.com', 'Test task', 0.7, False
            )

            # Verify result formatting
            assert '✅ **DOM Analysis Complete**' in result
            assert 'https://example.com' in result
            assert 'Test Page' in result
            assert '0.85' in result
            assert 'dom_analysis' in result

    @pytest.mark.asyncio
    async def test_execute_dom_action_integration(self, mock_agent):
        """Test execute_dom_action tool integration"""
        mock_ctx = Mock()

        # Mock the browser_tools.execute_dom_action method
        with patch('wyn360_cli.agent.browser_tools.execute_dom_action') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'action': 'click',
                'target': 'submit button',
                'confidence': 0.9,
                'approach_used': 'dom_analysis',
                'result': 'Button clicked successfully'
            }

            result = await mock_agent.execute_dom_action(
                mock_ctx, 'https://example.com', 'click', 'submit button'
            )

            # Verify the tool was called correctly
            mock_execute.assert_called_once_with(
                mock_ctx, 'https://example.com', 'click', 'submit button', None, 0.7, False
            )

            # Verify result formatting
            assert '✅ **Action Executed Successfully**' in result
            assert 'click' in result
            assert 'submit button' in result
            assert '0.90' in result
            assert 'dom_analysis' in result

    @pytest.mark.asyncio
    async def test_execute_dom_action_with_data(self, mock_agent):
        """Test execute_dom_action with action data"""
        mock_ctx = Mock()

        with patch('wyn360_cli.agent.browser_tools.execute_dom_action') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'action': 'type',
                'target': 'email field',
                'confidence': 0.8,
                'approach_used': 'dom_analysis',
                'result': 'Text entered successfully'
            }

            # Test with simple text data
            result = await mock_agent.execute_dom_action(
                mock_ctx, 'https://example.com', 'type', 'email field', 'test@example.com'
            )

            # Check that action_data was parsed correctly
            args, kwargs = mock_execute.call_args
            parsed_data = args[4]  # action_data parameter
            assert parsed_data == {'text': 'test@example.com'}

    @pytest.mark.asyncio
    async def test_intelligent_browse_integration(self, mock_agent):
        """Test intelligent_browse tool integration"""
        mock_ctx = Mock()

        # Mock browser_tools and orchestrator
        with patch('wyn360_cli.agent.browser_tools.analyze_page_dom') as mock_analyze:
            with patch('wyn360_cli.agent.automation_orchestrator.decide_automation_approach') as mock_decide:
                with patch('wyn360_cli.agent.automation_orchestrator.record_execution_result'):
                    with patch('wyn360_cli.agent.automation_orchestrator.get_decision_analytics') as mock_analytics:

                        # Setup mocks
                        mock_analyze.return_value = {
                            'success': True,
                            'confidence': 0.85,
                            'interactive_elements_count': 5,
                            'forms_count': 1,
                            'dom_analysis_text': 'DOM analysis for login page'
                        }

                        # Mock AutomationApproach enum
                        from src.wyn360.tools.browser import AutomationApproach
                        mock_context = Mock()
                        mock_context.dom_confidence = 0.85
                        mock_context.page_complexity = 'moderate'

                        mock_decide.return_value = (
                            AutomationApproach.DOM_ANALYSIS,
                            mock_context,
                            'High DOM confidence (0.85)'
                        )

                        mock_analytics.return_value = {
                            'total_decisions': 1,
                            'success_rates': {'dom_analysis': 1.0},
                            'total_attempts': {'dom_analysis': 1},
                            'average_confidence': 0.85
                        }

                        result = await mock_agent.intelligent_browse(
                            mock_ctx, 'Login to website', 'https://example.com/login'
                        )

                        # Verify integration
                        mock_analyze.assert_called_once()
                        mock_decide.assert_called_once()

                        # Verify result contains expected content
                        assert '✅ **Task Analysis Complete**' in result
                        assert 'DOM Analysis' in result
                        assert '0.85' in result
                        assert 'Decision Analytics' in result

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, mock_agent):
        """Test error handling in DOM tools"""
        mock_ctx = Mock()

        # Test analyze_page_dom error handling
        with patch('wyn360_cli.agent.browser_tools.analyze_page_dom') as mock_analyze:
            mock_analyze.side_effect = Exception('Browser error')

            result = await mock_agent.analyze_page_dom(
                mock_ctx, 'https://example.com'
            )

            assert '❌ Error analyzing DOM: Browser error' in result

        # Test execute_dom_action error handling
        with patch('wyn360_cli.agent.browser_tools.execute_dom_action') as mock_execute:
            mock_execute.side_effect = Exception('Action failed')

            result = await mock_agent.execute_dom_action(
                mock_ctx, 'https://example.com', 'click', 'button'
            )

            assert '❌ Error executing DOM action: Action failed' in result

    @pytest.mark.asyncio
    async def test_failed_dom_analysis_fallback(self, mock_agent):
        """Test fallback recommendations when DOM analysis fails"""
        mock_ctx = Mock()

        # Test analyze_page_dom failure
        with patch('wyn360_cli.agent.browser_tools.analyze_page_dom') as mock_analyze:
            mock_analyze.return_value = {
                'success': False,
                'error': 'Page not accessible',
                'recommended_approach': 'vision_fallback'
            }

            result = await mock_agent.analyze_page_dom(
                mock_ctx, 'https://example.com'
            )

            assert '❌ **DOM Analysis Failed**' in result
            assert 'Page not accessible' in result
            assert 'vision_fallback' in result
            assert 'browse_and_find()' in result

    def test_tool_docstrings(self, mock_agent):
        """Test that tools have proper docstrings for pydantic-ai"""
        # Check that all new tools have comprehensive docstrings
        assert mock_agent.analyze_page_dom.__doc__ is not None
        assert 'Examples:' in mock_agent.analyze_page_dom.__doc__
        assert 'Args:' in mock_agent.analyze_page_dom.__doc__
        assert 'Returns:' in mock_agent.analyze_page_dom.__doc__

        assert mock_agent.execute_dom_action.__doc__ is not None
        assert 'Supported Actions:' in mock_agent.execute_dom_action.__doc__
        assert 'Examples:' in mock_agent.execute_dom_action.__doc__

        assert mock_agent.intelligent_browse.__doc__ is not None
        assert 'Advanced Features:' in mock_agent.intelligent_browse.__doc__
        assert 'Examples:' in mock_agent.intelligent_browse.__doc__

    def test_import_integration(self):
        """Test that all necessary imports are available"""
        # Test that DOM tools can be imported
        from src.wyn360.tools.browser import (
            browser_tools,
            automation_orchestrator,
            AutomationApproach,
            ActionRequest,
            ActionResult
        )

        # Verify imports are available
        assert browser_tools is not None
        assert automation_orchestrator is not None
        assert AutomationApproach is not None
        assert ActionRequest is not None
        assert ActionResult is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])