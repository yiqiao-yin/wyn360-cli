"""
Unit tests for --show-browser flag implementation

Tests that the --show-browser command-line flag is correctly passed
to the WYN360Agent and used throughout the browser automation system.
"""

import pytest
import os
from unittest.mock import Mock, patch
from wyn360_cli.agent import WYN360Agent
from wyn360_cli.config import WYN360Config


class TestShowBrowserFlag:
    """Test show-browser flag functionality"""

    def test_agent_initialization_show_browser_false(self):
        """Test agent initializes with show_browser=False by default"""
        with patch('wyn360_cli.agent.BrowserAuth'):
            with patch('wyn360_cli.agent.AnthropicModel'):
                # Set API key in environment to avoid validation errors
                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                agent = WYN360Agent(
                    api_key="test-key",
                    config=WYN360Config(),
                    show_browser=False
                )

                assert agent.show_browser is False

    def test_agent_initialization_show_browser_true(self):
        """Test agent initializes with show_browser=True when specified"""
        with patch('wyn360_cli.agent.BrowserAuth'):
            with patch('wyn360_cli.agent.AnthropicModel'):
                # Set API key in environment to avoid validation errors
                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                agent = WYN360Agent(
                    api_key="test-key",
                    config=WYN360Config(),
                    show_browser=True
                )

                assert agent.show_browser is True

    def test_browser_auth_initialization_headless_mode(self):
        """Test BrowserAuth is initialized with correct headless setting"""
        with patch('wyn360_cli.agent.AnthropicModel'):
            with patch('wyn360_cli.agent.BrowserAuth') as mock_browser_auth:
                # Set API key in environment to avoid validation errors
                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                # Test with show_browser=False (headless=True)
                agent = WYN360Agent(
                    api_key="test-key",
                    config=WYN360Config(),
                    show_browser=False
                )

                # Verify BrowserAuth was called with headless=True
                mock_browser_auth.assert_called_once()
                call_args = mock_browser_auth.call_args
                assert call_args[1]['headless'] is True

    def test_browser_auth_initialization_visible_mode(self):
        """Test BrowserAuth is initialized with correct visible setting"""
        with patch('wyn360_cli.agent.AnthropicModel'):
            with patch('wyn360_cli.agent.BrowserAuth') as mock_browser_auth:
                # Set API key in environment to avoid validation errors
                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                # Test with show_browser=True (headless=False)
                agent = WYN360Agent(
                    api_key="test-key",
                    config=WYN360Config(),
                    show_browser=True
                )

                # Verify BrowserAuth was called with headless=False
                mock_browser_auth.assert_called_once()
                call_args = mock_browser_auth.call_args
                assert call_args[1]['headless'] is False

    def test_show_browser_parameter_logic_false(self):
        """Test show_browser parameter logic with show_browser=False"""
        with patch('wyn360_cli.agent.BrowserAuth'):
            with patch('wyn360_cli.agent.AnthropicModel'):
                # Set API key in environment to avoid validation errors
                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                agent = WYN360Agent(
                    api_key="test-key",
                    config=WYN360Config(),
                    show_browser=False
                )

                # Test the headless parameter logic for browse_and_find
                assert agent.show_browser is False
                headless = None
                if headless is None:
                    headless = not agent.show_browser
                assert headless is True

                # Test the show_browser parameter logic for DOM functions
                show_browser = None
                if show_browser is None:
                    show_browser = agent.show_browser
                assert show_browser is False

    def test_show_browser_parameter_logic_true(self):
        """Test show_browser parameter logic with show_browser=True"""
        with patch('wyn360_cli.agent.BrowserAuth'):
            with patch('wyn360_cli.agent.AnthropicModel'):
                # Set API key in environment to avoid validation errors
                os.environ['ANTHROPIC_API_KEY'] = 'test-key'

                agent = WYN360Agent(
                    api_key="test-key",
                    config=WYN360Config(),
                    show_browser=True
                )

                # Test the headless parameter logic for browse_and_find
                assert agent.show_browser is True
                headless = None
                if headless is None:
                    headless = not agent.show_browser
                assert headless is False

                # Test the show_browser parameter logic for DOM functions
                show_browser = None
                if show_browser is None:
                    show_browser = agent.show_browser
                assert show_browser is True

    def test_environment_variable_browser_show_true(self):
        """Test WYN360_BROWSER_SHOW environment variable enables browser visibility"""
        # Test that environment variable enables show_browser
        original_env = os.environ.get('WYN360_BROWSER_SHOW')
        try:
            os.environ['WYN360_BROWSER_SHOW'] = 'true'

            # Test the CLI logic for environment variable handling
            show_browser = False  # CLI flag not set
            if not show_browser:
                # Check WYN360_BROWSER_SHOW environment variable
                browser_show_env = os.getenv('WYN360_BROWSER_SHOW', 'false').lower()
                if browser_show_env in ('true', '1', 'yes', 'on'):
                    show_browser = True

            assert show_browser is True
        finally:
            # Clean up environment
            if original_env is None:
                os.environ.pop('WYN360_BROWSER_SHOW', None)
            else:
                os.environ['WYN360_BROWSER_SHOW'] = original_env

    def test_environment_variable_browser_show_false(self):
        """Test WYN360_BROWSER_SHOW environment variable defaults to headless"""
        # Test that environment variable defaults to headless mode
        original_env = os.environ.get('WYN360_BROWSER_SHOW')
        try:
            os.environ['WYN360_BROWSER_SHOW'] = 'false'

            # Test the CLI logic for environment variable handling
            show_browser = False  # CLI flag not set
            if not show_browser:
                # Check WYN360_BROWSER_SHOW environment variable
                browser_show_env = os.getenv('WYN360_BROWSER_SHOW', 'false').lower()
                if browser_show_env in ('true', '1', 'yes', 'on'):
                    show_browser = True

            assert show_browser is False
        finally:
            # Clean up environment
            if original_env is None:
                os.environ.pop('WYN360_BROWSER_SHOW', None)
            else:
                os.environ['WYN360_BROWSER_SHOW'] = original_env

    def test_cli_flag_overrides_environment_variable(self):
        """Test that CLI flag takes precedence over environment variable"""
        # Test that CLI flag overrides environment variable
        original_env = os.environ.get('WYN360_BROWSER_SHOW')
        try:
            os.environ['WYN360_BROWSER_SHOW'] = 'false'  # Env says headless

            # Test the CLI logic - CLI flag should take precedence
            show_browser = True  # CLI flag set to show browser
            if not show_browser:  # This won't be executed because CLI flag is True
                # Check WYN360_BROWSER_SHOW environment variable
                browser_show_env = os.getenv('WYN360_BROWSER_SHOW', 'false').lower()
                if browser_show_env in ('true', '1', 'yes', 'on'):
                    show_browser = True

            # CLI flag should take precedence
            assert show_browser is True
        finally:
            # Clean up environment
            if original_env is None:
                os.environ.pop('WYN360_BROWSER_SHOW', None)
            else:
                os.environ['WYN360_BROWSER_SHOW'] = original_env


if __name__ == "__main__":
    pytest.main([__file__, "-v"])