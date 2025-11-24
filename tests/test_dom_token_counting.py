"""
Unit tests for DOM automation token counting

Tests the token counting functionality for DOM-first browser automation operations.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.agent import WYN360Agent


class TestDOMTokenCounting:
    """Test DOM automation token counting functionality"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock WYN360Agent for testing"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('wyn360_cli.agent.AnthropicModel'):
                with patch('wyn360_cli.agent.Agent'):
                    agent = WYN360Agent()
                    return agent

    def test_dom_token_tracking_initialization(self, mock_agent):
        """Test that DOM token tracking variables are initialized"""
        assert mock_agent.dom_analysis_count == 0
        assert mock_agent.dom_analysis_input_tokens == 0
        assert mock_agent.dom_analysis_output_tokens == 0
        assert mock_agent.dom_action_count == 0
        assert mock_agent.dom_action_input_tokens == 0
        assert mock_agent.dom_action_output_tokens == 0
        assert mock_agent.intelligent_browse_count == 0
        assert mock_agent.intelligent_browse_input_tokens == 0
        assert mock_agent.intelligent_browse_output_tokens == 0

    def test_track_dom_automation_tokens_analyze(self, mock_agent):
        """Test tracking tokens for DOM analysis operation"""
        input_text = "URL: https://example.com\nTask: Test task"
        output_text = "✅ DOM Analysis Complete\nConfidence: 0.85"

        mock_agent._track_dom_automation_tokens("analyze", input_text, output_text)

        # Check that counts are updated
        assert mock_agent.dom_analysis_count == 1
        assert mock_agent.dom_analysis_input_tokens == len(input_text) // 4
        assert mock_agent.dom_analysis_output_tokens == len(output_text) // 4

        # Check other counters remain zero
        assert mock_agent.dom_action_count == 0
        assert mock_agent.intelligent_browse_count == 0

    def test_track_dom_automation_tokens_action(self, mock_agent):
        """Test tracking tokens for DOM action operation"""
        input_text = "URL: https://example.com\nAction: click\nTarget: button"
        output_text = "✅ Action Executed Successfully\nResult: Button clicked"

        mock_agent._track_dom_automation_tokens("action", input_text, output_text)

        # Check that counts are updated
        assert mock_agent.dom_action_count == 1
        assert mock_agent.dom_action_input_tokens == len(input_text) // 4
        assert mock_agent.dom_action_output_tokens == len(output_text) // 4

        # Check other counters remain zero
        assert mock_agent.dom_analysis_count == 0
        assert mock_agent.intelligent_browse_count == 0

    def test_track_dom_automation_tokens_browse(self, mock_agent):
        """Test tracking tokens for intelligent browse operation"""
        input_text = "Task: Login to website\nURL: https://example.com/login"
        output_text = "✅ Task Analysis Complete\nApproach: DOM Analysis"

        mock_agent._track_dom_automation_tokens("browse", input_text, output_text)

        # Check that counts are updated
        assert mock_agent.intelligent_browse_count == 1
        assert mock_agent.intelligent_browse_input_tokens == len(input_text) // 4
        assert mock_agent.intelligent_browse_output_tokens == len(output_text) // 4

        # Check other counters remain zero
        assert mock_agent.dom_analysis_count == 0
        assert mock_agent.dom_action_count == 0

    def test_multiple_operations_tracking(self, mock_agent):
        """Test tracking multiple operations of different types"""
        # Track various operations
        mock_agent._track_dom_automation_tokens("analyze", "URL: https://test.com", "Analysis result")
        mock_agent._track_dom_automation_tokens("analyze", "URL: https://test2.com", "Another analysis")
        mock_agent._track_dom_automation_tokens("action", "Click button", "Button clicked")
        mock_agent._track_dom_automation_tokens("browse", "Login task", "Browse complete")

        # Verify counts
        assert mock_agent.dom_analysis_count == 2
        assert mock_agent.dom_action_count == 1
        assert mock_agent.intelligent_browse_count == 1

        # Verify tokens are accumulated
        expected_analysis_input = (len("URL: https://test.com") + len("URL: https://test2.com")) // 4
        expected_analysis_output = (len("Analysis result") + len("Another analysis")) // 4

        assert mock_agent.dom_analysis_input_tokens == expected_analysis_input
        assert mock_agent.dom_analysis_output_tokens == expected_analysis_output

    def test_get_token_stats_with_dom_automation(self, mock_agent):
        """Test get_token_stats includes DOM automation statistics"""
        # Add some DOM automation token usage
        mock_agent._track_dom_automation_tokens("analyze", "Test input " * 100, "Test output " * 50)
        mock_agent._track_dom_automation_tokens("action", "Action input " * 50, "Action output " * 25)
        mock_agent._track_dom_automation_tokens("browse", "Browse input " * 75, "Browse output " * 40)

        stats = mock_agent.get_token_stats()

        # Check that DOM automation stats are included
        assert "dom_automation_total_operations" in stats
        assert "dom_analysis_count" in stats
        assert "dom_action_count" in stats
        assert "intelligent_browse_count" in stats
        assert "dom_automation_total_input_tokens" in stats
        assert "dom_automation_total_output_tokens" in stats
        assert "dom_automation_total_tokens" in stats
        assert "dom_automation_cost" in stats
        assert "dom_automation_input_cost" in stats
        assert "dom_automation_output_cost" in stats

        # Verify counts
        assert stats["dom_automation_total_operations"] == 3
        assert stats["dom_analysis_count"] == 1
        assert stats["dom_action_count"] == 1
        assert stats["intelligent_browse_count"] == 1

        # Verify tokens are totaled correctly
        expected_total_input = (
            mock_agent.dom_analysis_input_tokens +
            mock_agent.dom_action_input_tokens +
            mock_agent.intelligent_browse_input_tokens
        )
        expected_total_output = (
            mock_agent.dom_analysis_output_tokens +
            mock_agent.dom_action_output_tokens +
            mock_agent.intelligent_browse_output_tokens
        )

        assert stats["dom_automation_total_input_tokens"] == expected_total_input
        assert stats["dom_automation_total_output_tokens"] == expected_total_output
        assert stats["dom_automation_total_tokens"] == expected_total_input + expected_total_output

        # Verify costs are calculated correctly (Sonnet pricing: $3/1M input, $15/1M output)
        expected_input_cost = expected_total_input / 1_000_000 * 3.0
        expected_output_cost = expected_total_output / 1_000_000 * 15.0
        expected_total_cost = expected_input_cost + expected_output_cost

        assert stats["dom_automation_input_cost"] == expected_input_cost
        assert stats["dom_automation_output_cost"] == expected_output_cost
        assert stats["dom_automation_cost"] == expected_total_cost

    def test_clear_history_resets_dom_counters(self, mock_agent):
        """Test that clear_history resets DOM automation counters"""
        # Add some DOM automation usage
        mock_agent._track_dom_automation_tokens("analyze", "Test", "Result")
        mock_agent._track_dom_automation_tokens("action", "Action", "Done")
        mock_agent._track_dom_automation_tokens("browse", "Browse", "Complete")

        # Verify counters are non-zero
        assert mock_agent.dom_analysis_count > 0
        assert mock_agent.dom_action_count > 0
        assert mock_agent.intelligent_browse_count > 0

        # Clear history
        mock_agent.clear_history()

        # Verify all DOM counters are reset
        assert mock_agent.dom_analysis_count == 0
        assert mock_agent.dom_analysis_input_tokens == 0
        assert mock_agent.dom_analysis_output_tokens == 0
        assert mock_agent.dom_action_count == 0
        assert mock_agent.dom_action_input_tokens == 0
        assert mock_agent.dom_action_output_tokens == 0
        assert mock_agent.intelligent_browse_count == 0
        assert mock_agent.intelligent_browse_input_tokens == 0
        assert mock_agent.intelligent_browse_output_tokens == 0

    def test_token_estimation_method(self, mock_agent):
        """Test the token estimation method with known inputs"""
        # Test the underlying token estimation method
        test_text = "This is a test string with exactly forty chars"  # 44 characters
        estimated_tokens = mock_agent._estimate_tokens(test_text)

        # Should be 44 // 4 = 11 tokens
        assert estimated_tokens == 11

        # Test with empty string
        assert mock_agent._estimate_tokens("") == 0

        # Test with longer text
        long_text = "A" * 1000  # 1000 characters
        assert mock_agent._estimate_tokens(long_text) == 250  # 1000 // 4

    @pytest.mark.asyncio
    async def test_analyze_page_dom_tracks_tokens(self, mock_agent):
        """Test that analyze_page_dom tracks tokens"""
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
                'dom_analysis_text': 'Sample DOM analysis result'
            }

            initial_count = mock_agent.dom_analysis_count
            initial_input_tokens = mock_agent.dom_analysis_input_tokens
            initial_output_tokens = mock_agent.dom_analysis_output_tokens

            await mock_agent.analyze_page_dom(
                mock_ctx, 'https://example.com', 'Test task'
            )

            # Verify that token tracking was called
            assert mock_agent.dom_analysis_count == initial_count + 1
            assert mock_agent.dom_analysis_input_tokens > initial_input_tokens
            assert mock_agent.dom_analysis_output_tokens > initial_output_tokens

    @pytest.mark.asyncio
    async def test_execute_dom_action_tracks_tokens(self, mock_agent):
        """Test that execute_dom_action tracks tokens"""
        mock_ctx = Mock()

        # Mock the browser_tools.execute_dom_action method
        with patch('wyn360_cli.agent.browser_tools.execute_dom_action') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'action': 'click',
                'target': 'button',
                'confidence': 0.9,
                'approach_used': 'dom_analysis',
                'result': 'Button clicked successfully'
            }

            initial_count = mock_agent.dom_action_count
            initial_input_tokens = mock_agent.dom_action_input_tokens
            initial_output_tokens = mock_agent.dom_action_output_tokens

            await mock_agent.execute_dom_action(
                mock_ctx, 'https://example.com', 'click', 'submit button'
            )

            # Verify that token tracking was called
            assert mock_agent.dom_action_count == initial_count + 1
            assert mock_agent.dom_action_input_tokens > initial_input_tokens
            assert mock_agent.dom_action_output_tokens > initial_output_tokens

    @pytest.mark.asyncio
    async def test_intelligent_browse_tracks_tokens(self, mock_agent):
        """Test that intelligent_browse tracks tokens"""
        mock_ctx = Mock()

        # Mock required dependencies
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
                            'dom_analysis_text': 'DOM analysis for test'
                        }

                        from src.wyn360.tools.browser import AutomationApproach
                        mock_context = Mock()
                        mock_context.dom_confidence = 0.85
                        mock_context.page_complexity = 'moderate'

                        mock_decide.return_value = (
                            AutomationApproach.DOM_ANALYSIS,
                            mock_context,
                            'High DOM confidence'
                        )

                        mock_analytics.return_value = {
                            'total_decisions': 1,
                            'success_rates': {'dom_analysis': 1.0},
                            'total_attempts': {'dom_analysis': 1},
                            'average_confidence': 0.85
                        }

                        initial_count = mock_agent.intelligent_browse_count
                        initial_input_tokens = mock_agent.intelligent_browse_input_tokens
                        initial_output_tokens = mock_agent.intelligent_browse_output_tokens

                        await mock_agent.intelligent_browse(
                            mock_ctx, 'Test automation task', 'https://example.com'
                        )

                        # Verify that token tracking was called
                        assert mock_agent.intelligent_browse_count == initial_count + 1
                        assert mock_agent.intelligent_browse_input_tokens > initial_input_tokens
                        assert mock_agent.intelligent_browse_output_tokens > initial_output_tokens

    def test_cost_calculation_accuracy(self, mock_agent):
        """Test that cost calculations are accurate"""
        # Add known token amounts
        mock_agent.dom_analysis_input_tokens = 1000
        mock_agent.dom_analysis_output_tokens = 500
        mock_agent.dom_action_input_tokens = 2000
        mock_agent.dom_action_output_tokens = 1000
        mock_agent.intelligent_browse_input_tokens = 3000
        mock_agent.intelligent_browse_output_tokens = 1500

        stats = mock_agent.get_token_stats()

        # Total tokens: input=6000, output=3000
        total_input = 6000
        total_output = 3000

        # Expected costs (Sonnet pricing: $3/1M input, $15/1M output)
        expected_input_cost = total_input / 1_000_000 * 3.0  # $0.018
        expected_output_cost = total_output / 1_000_000 * 15.0  # $0.045
        expected_total_cost = expected_input_cost + expected_output_cost  # $0.063

        assert stats['dom_automation_total_input_tokens'] == total_input
        assert stats['dom_automation_total_output_tokens'] == total_output
        assert abs(stats['dom_automation_input_cost'] - expected_input_cost) < 0.0001
        assert abs(stats['dom_automation_output_cost'] - expected_output_cost) < 0.0001
        assert abs(stats['dom_automation_cost'] - expected_total_cost) < 0.0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])