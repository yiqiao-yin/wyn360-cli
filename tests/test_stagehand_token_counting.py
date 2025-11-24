"""
Unit tests for Stagehand automation token counting

Tests the token counting functionality for Stagehand automation operations.
"""

import pytest
import os
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.agent import WYN360Agent


class TestStagehandTokenCounting:
    """Test Stagehand automation token counting functionality"""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock WYN360Agent for testing"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('wyn360_cli.agent.AnthropicModel'):
                with patch('wyn360_cli.agent.Agent'):
                    agent = WYN360Agent()
                    return agent

    def test_stagehand_token_tracking_initialization(self, mock_agent):
        """Test that Stagehand token tracking variables are initialized"""
        assert mock_agent.stagehand_generation_count == 0
        assert mock_agent.stagehand_generation_input_tokens == 0
        assert mock_agent.stagehand_generation_output_tokens == 0
        assert mock_agent.stagehand_execution_count == 0
        assert mock_agent.stagehand_execution_input_tokens == 0
        assert mock_agent.stagehand_execution_output_tokens == 0
        assert mock_agent.enhanced_browse_count == 0
        assert mock_agent.enhanced_browse_input_tokens == 0
        assert mock_agent.enhanced_browse_output_tokens == 0

    def test_track_stagehand_automation_tokens_generation(self, mock_agent):
        """Test tracking tokens for Stagehand code generation operation"""
        input_text = "Task: Click the login button\\nURL: https://example.com\\nDOM: <button>Login</button>"
        output_text = "Generated Stagehand actions: [{'type': 'observe'}, {'type': 'act', 'action': 'click'}]"

        mock_agent._track_stagehand_automation_tokens("generation", input_text, output_text)

        # Check that counts are updated
        assert mock_agent.stagehand_generation_count == 1
        assert mock_agent.stagehand_generation_input_tokens == len(input_text) // 4
        assert mock_agent.stagehand_generation_output_tokens == len(output_text) // 4

        # Check other counters remain zero
        assert mock_agent.stagehand_execution_count == 0
        assert mock_agent.enhanced_browse_count == 0

    def test_track_stagehand_automation_tokens_execution(self, mock_agent):
        """Test tracking tokens for Stagehand code execution operation"""
        input_text = "Executing Stagehand actions: [{'type': 'act', 'action': 'click on login button'}]"
        output_text = "✅ Stagehand Execution Complete\\nResult: Login button clicked successfully"

        mock_agent._track_stagehand_automation_tokens("execution", input_text, output_text)

        # Check that counts are updated
        assert mock_agent.stagehand_execution_count == 1
        assert mock_agent.stagehand_execution_input_tokens == len(input_text) // 4
        assert mock_agent.stagehand_execution_output_tokens == len(output_text) // 4

        # Check other counters remain zero
        assert mock_agent.stagehand_generation_count == 0
        assert mock_agent.enhanced_browse_count == 0

    def test_track_stagehand_automation_tokens_enhanced_browse(self, mock_agent):
        """Test tracking tokens for enhanced browse operation"""
        input_text = "Enhanced Browse Task: Login to the website\\nURL: https://example.com/login"
        output_text = "✅ Enhanced Browse Complete\\nApproach: Stagehand Automation\\nResult: Successfully logged in"

        mock_agent._track_stagehand_automation_tokens("enhanced_browse", input_text, output_text)

        # Check that counts are updated
        assert mock_agent.enhanced_browse_count == 1
        assert mock_agent.enhanced_browse_input_tokens == len(input_text) // 4
        assert mock_agent.enhanced_browse_output_tokens == len(output_text) // 4

        # Check other counters remain zero
        assert mock_agent.stagehand_generation_count == 0
        assert mock_agent.stagehand_execution_count == 0

    def test_multiple_stagehand_operations_tracking(self, mock_agent):
        """Test tracking multiple operations of different types"""
        # Track various operations
        mock_agent._track_stagehand_automation_tokens("generation", "Generate code for login", "Generated actions")
        mock_agent._track_stagehand_automation_tokens("generation", "Generate code for submit", "More actions")
        mock_agent._track_stagehand_automation_tokens("execution", "Execute login actions", "Login executed")
        mock_agent._track_stagehand_automation_tokens("enhanced_browse", "Enhanced browse task", "Browse complete")

        # Verify counts
        assert mock_agent.stagehand_generation_count == 2
        assert mock_agent.stagehand_execution_count == 1
        assert mock_agent.enhanced_browse_count == 1

        # Verify tokens are accumulated
        expected_generation_input = (len("Generate code for login") + len("Generate code for submit")) // 4
        expected_generation_output = (len("Generated actions") + len("More actions")) // 4

        assert mock_agent.stagehand_generation_input_tokens == expected_generation_input
        assert mock_agent.stagehand_generation_output_tokens == expected_generation_output

    def test_get_token_stats_with_stagehand_automation(self, mock_agent):
        """Test get_token_stats includes Stagehand automation statistics"""
        # Add some Stagehand automation token usage
        mock_agent._track_stagehand_automation_tokens("generation", "Generate test " * 50, "Generated test " * 25)
        mock_agent._track_stagehand_automation_tokens("execution", "Execute test " * 30, "Executed test " * 20)
        mock_agent._track_stagehand_automation_tokens("enhanced_browse", "Browse test " * 40, "Browse result " * 15)

        stats = mock_agent.get_token_stats()

        # Check that Stagehand automation stats are included
        assert "stagehand_automation_total_operations" in stats
        assert "stagehand_generation_count" in stats
        assert "stagehand_execution_count" in stats
        assert "enhanced_browse_count" in stats
        assert "stagehand_automation_total_input_tokens" in stats
        assert "stagehand_automation_total_output_tokens" in stats
        assert "stagehand_automation_total_tokens" in stats
        assert "stagehand_automation_cost" in stats
        assert "stagehand_automation_input_cost" in stats
        assert "stagehand_automation_output_cost" in stats

        # Verify counts
        assert stats["stagehand_automation_total_operations"] == 3
        assert stats["stagehand_generation_count"] == 1
        assert stats["stagehand_execution_count"] == 1
        assert stats["enhanced_browse_count"] == 1

        # Verify tokens are totaled correctly
        expected_total_input = (
            mock_agent.stagehand_generation_input_tokens +
            mock_agent.stagehand_execution_input_tokens +
            mock_agent.enhanced_browse_input_tokens
        )
        expected_total_output = (
            mock_agent.stagehand_generation_output_tokens +
            mock_agent.stagehand_execution_output_tokens +
            mock_agent.enhanced_browse_output_tokens
        )

        assert stats["stagehand_automation_total_input_tokens"] == expected_total_input
        assert stats["stagehand_automation_total_output_tokens"] == expected_total_output
        assert stats["stagehand_automation_total_tokens"] == expected_total_input + expected_total_output

        # Verify costs are calculated correctly (Sonnet pricing: $3/1M input, $15/1M output)
        expected_input_cost = expected_total_input / 1_000_000 * 3.0
        expected_output_cost = expected_total_output / 1_000_000 * 15.0
        expected_total_cost = expected_input_cost + expected_output_cost

        assert stats["stagehand_automation_input_cost"] == expected_input_cost
        assert stats["stagehand_automation_output_cost"] == expected_output_cost
        assert stats["stagehand_automation_cost"] == expected_total_cost

    def test_total_cost_includes_stagehand(self, mock_agent):
        """Test that total cost includes Stagehand automation costs"""
        # Add some regular conversation tokens
        mock_agent.total_input_tokens = 1000
        mock_agent.total_output_tokens = 500

        # Add some Stagehand automation tokens
        mock_agent._track_stagehand_automation_tokens("generation", "Test " * 100, "Result " * 50)
        mock_agent._track_stagehand_automation_tokens("execution", "Exec " * 50, "Done " * 25)

        stats = mock_agent.get_token_stats()

        # Calculate expected costs
        conversation_cost = (1000 / 1_000_000 * 3.0) + (500 / 1_000_000 * 15.0)
        stagehand_cost = stats["stagehand_automation_cost"]
        expected_total = conversation_cost + stagehand_cost  # Other costs are 0 in this test

        # Verify total cost includes Stagehand costs
        assert abs(stats["total_cost"] - expected_total) < 0.0001

    def test_clear_history_resets_stagehand_counters(self, mock_agent):
        """Test that clear_history resets Stagehand automation counters"""
        # Add some Stagehand automation usage
        mock_agent._track_stagehand_automation_tokens("generation", "Test", "Result")
        mock_agent._track_stagehand_automation_tokens("execution", "Action", "Done")
        mock_agent._track_stagehand_automation_tokens("enhanced_browse", "Browse", "Complete")

        # Verify counters are non-zero
        assert mock_agent.stagehand_generation_count > 0
        assert mock_agent.stagehand_execution_count > 0
        assert mock_agent.enhanced_browse_count > 0

        # Clear history
        mock_agent.clear_history()

        # Verify all Stagehand counters are reset
        assert mock_agent.stagehand_generation_count == 0
        assert mock_agent.stagehand_generation_input_tokens == 0
        assert mock_agent.stagehand_generation_output_tokens == 0
        assert mock_agent.stagehand_execution_count == 0
        assert mock_agent.stagehand_execution_input_tokens == 0
        assert mock_agent.stagehand_execution_output_tokens == 0
        assert mock_agent.enhanced_browse_count == 0
        assert mock_agent.enhanced_browse_input_tokens == 0
        assert mock_agent.enhanced_browse_output_tokens == 0

    def test_cost_calculation_accuracy(self, mock_agent):
        """Test that Stagehand cost calculations are accurate"""
        # Add known token amounts
        mock_agent.stagehand_generation_input_tokens = 2000
        mock_agent.stagehand_generation_output_tokens = 1000
        mock_agent.stagehand_execution_input_tokens = 1500
        mock_agent.stagehand_execution_output_tokens = 750
        mock_agent.enhanced_browse_input_tokens = 2500
        mock_agent.enhanced_browse_output_tokens = 1250

        stats = mock_agent.get_token_stats()

        # Total tokens: input=6000, output=3000
        total_input = 6000
        total_output = 3000

        # Expected costs (Sonnet pricing: $3/1M input, $15/1M output)
        expected_input_cost = total_input / 1_000_000 * 3.0  # $0.018
        expected_output_cost = total_output / 1_000_000 * 15.0  # $0.045
        expected_total_cost = expected_input_cost + expected_output_cost  # $0.063

        assert stats['stagehand_automation_total_input_tokens'] == total_input
        assert stats['stagehand_automation_total_output_tokens'] == total_output
        assert abs(stats['stagehand_automation_input_cost'] - expected_input_cost) < 0.0001
        assert abs(stats['stagehand_automation_output_cost'] - expected_output_cost) < 0.0001
        assert abs(stats['stagehand_automation_cost'] - expected_total_cost) < 0.0001

    def test_stagehand_stats_in_tokens_display(self, mock_agent):
        """Test that Stagehand stats appear in token stats output when present"""
        # Add some Stagehand operations
        mock_agent._track_stagehand_automation_tokens("generation", "Generate actions", "Actions generated")
        mock_agent._track_stagehand_automation_tokens("execution", "Execute code", "Code executed")

        stats = mock_agent.get_token_stats()

        # Should have non-zero Stagehand operations
        assert stats["stagehand_automation_total_operations"] > 0
        assert stats["stagehand_generation_count"] > 0
        assert stats["stagehand_execution_count"] > 0

        # All the required fields for CLI display should be present
        required_fields = [
            "stagehand_automation_total_operations",
            "stagehand_generation_count",
            "stagehand_execution_count",
            "enhanced_browse_count",
            "stagehand_automation_total_input_tokens",
            "stagehand_automation_total_output_tokens",
            "stagehand_automation_total_tokens",
            "stagehand_automation_input_cost",
            "stagehand_automation_output_cost",
            "stagehand_automation_cost"
        ]

        for field in required_fields:
            assert field in stats

    def test_stagehand_operations_breakdown(self, mock_agent):
        """Test detailed breakdown of different Stagehand operations"""
        # Add different types of operations with known token counts
        mock_agent._track_stagehand_automation_tokens("generation", "A" * 400, "B" * 200)  # 100 input, 50 output
        mock_agent._track_stagehand_automation_tokens("generation", "C" * 800, "D" * 400)  # 200 input, 100 output
        mock_agent._track_stagehand_automation_tokens("execution", "E" * 1200, "F" * 600)  # 300 input, 150 output
        mock_agent._track_stagehand_automation_tokens("enhanced_browse", "G" * 1600, "H" * 800)  # 400 input, 200 output

        stats = mock_agent.get_token_stats()

        # Verify individual operation counts
        assert stats["stagehand_generation_count"] == 2
        assert stats["stagehand_execution_count"] == 1
        assert stats["enhanced_browse_count"] == 1
        assert stats["stagehand_automation_total_operations"] == 4

        # Verify individual token tracking
        assert stats["stagehand_generation_input_tokens"] == 300  # 100 + 200
        assert stats["stagehand_generation_output_tokens"] == 150  # 50 + 100
        assert stats["stagehand_execution_input_tokens"] == 300
        assert stats["stagehand_execution_output_tokens"] == 150
        assert stats["enhanced_browse_input_tokens"] == 400
        assert stats["enhanced_browse_output_tokens"] == 200

        # Verify totals
        assert stats["stagehand_automation_total_input_tokens"] == 1000  # 300 + 300 + 400
        assert stats["stagehand_automation_total_output_tokens"] == 500  # 150 + 150 + 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])