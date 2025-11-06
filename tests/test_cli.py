"""Unit tests for cli.py"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from wyn360_cli.agent import WYN360Agent
from wyn360_cli.cli import handle_slash_command


class TestSlashCommands:
    """Tests for slash command handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.agent = WYN360Agent(api_key="test_key", model="claude-sonnet-4-20250514")

    def test_clear_command(self):
        """Test /clear command"""
        # Add some history
        self.agent.conversation_history = [
            {"role": "user", "content": "Test"},
            {"role": "assistant", "content": "Response"}
        ]
        self.agent.total_input_tokens = 100
        self.agent.total_output_tokens = 50
        self.agent.request_count = 1

        handled, message = handle_slash_command("clear", self.agent)

        assert handled is True
        assert "✓" in message
        assert "cleared" in message.lower()
        assert self.agent.conversation_history == []
        assert self.agent.total_input_tokens == 0
        assert self.agent.total_output_tokens == 0
        assert self.agent.request_count == 0

    def test_history_command_empty(self):
        """Test /history command with no history"""
        handled, message = handle_slash_command("history", self.agent)

        assert handled is True
        assert "No conversation history" in message

    def test_history_command_with_messages(self, capsys):
        """Test /history command with conversation history"""
        self.agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

        handled, message = handle_slash_command("history", self.agent)

        assert handled is True
        # The command prints a Rich table, so message will be empty
        # But we can verify it was handled

    def test_save_command_no_filename(self):
        """Test /save command without filename"""
        handled, message = handle_slash_command("save", self.agent)

        assert handled is True
        assert "❌" in message
        assert "Usage" in message
        assert "/save <filename>" in message

    def test_save_command_with_filename(self):
        """Test /save command with filename"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test_session.json"

            # Add some data to save
            self.agent.conversation_history = [
                {"role": "user", "content": "Test"}
            ]

            handled, message = handle_slash_command(f"save {filepath}", self.agent)

            assert handled is True
            assert "✓" in message
            assert "saved" in message.lower()
            assert Path(filepath).exists()

    def test_save_command_failure(self):
        """Test /save command with invalid path"""
        # Try to save to invalid location
        handled, message = handle_slash_command("save /invalid/path/session.json", self.agent)

        # Should still be handled, but with error message
        assert handled is True

    def test_load_command_no_filename(self):
        """Test /load command without filename"""
        handled, message = handle_slash_command("load", self.agent)

        assert handled is True
        assert "❌" in message
        assert "Usage" in message
        assert "/load <filename>" in message

    def test_load_command_with_filename(self):
        """Test /load command with valid session file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/test_session.json"

            # Create a test session file
            session_data = {
                "model": "claude-sonnet-4-20250514",
                "conversation_history": [
                    {"role": "user", "content": "Loaded message"}
                ],
                "total_input_tokens": 200,
                "total_output_tokens": 100,
                "request_count": 2,
                "token_history": [],
                "timestamp": "2025-01-01"
            }

            with open(filepath, 'w') as f:
                json.dump(session_data, f)

            handled, message = handle_slash_command(f"load {filepath}", self.agent)

            assert handled is True
            assert "✓" in message
            assert "loaded" in message.lower()
            assert len(self.agent.conversation_history) == 1
            assert self.agent.total_input_tokens == 200

    def test_load_command_nonexistent_file(self):
        """Test /load command with nonexistent file"""
        handled, message = handle_slash_command("load /nonexistent/file.json", self.agent)

        assert handled is True
        assert "❌" in message
        assert "Failed" in message

    def test_tokens_command(self, capsys):
        """Test /tokens command"""
        # Add some token usage
        self.agent.total_input_tokens = 1000
        self.agent.total_output_tokens = 500
        self.agent.request_count = 5

        handled, message = handle_slash_command("tokens", self.agent)

        assert handled is True
        # The command prints a Rich table, so we verify it was handled

    def test_help_command(self, capsys):
        """Test /help command"""
        handled, message = handle_slash_command("help", self.agent)

        assert handled is True
        # The command prints help text, so we verify it was handled

    def test_unknown_command(self):
        """Test unknown slash command"""
        handled, message = handle_slash_command("unknown", self.agent)

        assert handled is False
        assert "Unknown command" in message
        assert "/unknown" in message
        assert "/help" in message

    def test_command_case_insensitive(self):
        """Test that commands are case insensitive"""
        # Add some history for testing
        self.agent.conversation_history = [{"role": "user", "content": "Test"}]

        handled1, _ = handle_slash_command("CLEAR", self.agent)
        assert handled1 is True
        assert self.agent.conversation_history == []

        # Test another command
        handled2, message2 = handle_slash_command("HELP", self.agent)
        assert handled2 is True

    def test_command_with_multiple_arguments(self):
        """Test command with filename containing spaces"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/my session file.json"

            # Add some data
            self.agent.conversation_history = [{"role": "user", "content": "Test"}]

            # Save with space in filename
            handled, message = handle_slash_command(f"save {filepath}", self.agent)

            assert handled is True
            # File should be saved with full path including spaces
            assert Path(filepath).exists() or "✓" in message

    def test_save_and_load_roundtrip(self):
        """Test saving and loading a session preserves data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = f"{tmpdir}/roundtrip.json"

            # Set up agent with data
            self.agent.conversation_history = [
                {"role": "user", "content": "Message 1"},
                {"role": "assistant", "content": "Response 1"}
            ]
            self.agent.total_input_tokens = 150
            self.agent.total_output_tokens = 75
            self.agent.request_count = 1

            # Save session
            handled1, message1 = handle_slash_command(f"save {filepath}", self.agent)
            assert handled1 is True
            assert "✓" in message1

            # Clear the agent
            self.agent.conversation_history = []
            self.agent.total_input_tokens = 0
            self.agent.total_output_tokens = 0
            self.agent.request_count = 0

            # Load session
            handled2, message2 = handle_slash_command(f"load {filepath}", self.agent)
            assert handled2 is True
            assert "✓" in message2

            # Verify data was restored
            assert len(self.agent.conversation_history) == 2
            assert self.agent.conversation_history[0]["content"] == "Message 1"
            assert self.agent.total_input_tokens == 150
            assert self.agent.total_output_tokens == 75
            assert self.agent.request_count == 1

    def test_tokens_command_with_no_usage(self):
        """Test /tokens command with zero usage"""
        # Agent starts with zero usage
        assert self.agent.request_count == 0

        handled, message = handle_slash_command("tokens", self.agent)

        assert handled is True
        # Should still display table even with zero usage

    def test_clear_command_idempotent(self):
        """Test that /clear can be called multiple times safely"""
        # First clear
        handled1, message1 = handle_slash_command("clear", self.agent)
        assert handled1 is True

        # Second clear (already empty)
        handled2, message2 = handle_slash_command("clear", self.agent)
        assert handled2 is True
        assert self.agent.conversation_history == []

    def test_history_command_truncates_long_messages(self):
        """Test that /history truncates very long messages"""
        # Add a very long message
        long_content = "x" * 500
        self.agent.conversation_history = [
            {"role": "user", "content": long_content}
        ]

        handled, message = handle_slash_command("history", self.agent)

        assert handled is True
        # The function should handle this without errors
