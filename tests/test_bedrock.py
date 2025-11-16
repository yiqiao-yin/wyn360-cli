"""Tests for AWS Bedrock integration."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from wyn360_cli.agent import WYN360Agent, _should_use_bedrock, _validate_aws_credentials


class TestBedrockDetection:
    """Test Bedrock mode detection."""

    def test_bedrock_disabled_by_default(self):
        """Test that Bedrock is disabled when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _should_use_bedrock() is False

    def test_bedrock_enabled_with_1(self):
        """Test that Bedrock is enabled with CLAUDE_CODE_USE_BEDROCK=1."""
        with patch.dict(os.environ, {'CLAUDE_CODE_USE_BEDROCK': '1'}):
            assert _should_use_bedrock() is True

    def test_bedrock_disabled_with_0(self):
        """Test that Bedrock is disabled with CLAUDE_CODE_USE_BEDROCK=0."""
        with patch.dict(os.environ, {'CLAUDE_CODE_USE_BEDROCK': '0'}):
            assert _should_use_bedrock() is False

    def test_bedrock_disabled_with_invalid_value(self):
        """Test that Bedrock is disabled with invalid env var values."""
        with patch.dict(os.environ, {'CLAUDE_CODE_USE_BEDROCK': 'yes'}):
            assert _should_use_bedrock() is False


class TestAWSCredentialValidation:
    """Test AWS credential validation."""

    def test_valid_credentials(self):
        """Test validation with all required credentials."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }):
            is_valid, error = _validate_aws_credentials()
            assert is_valid is True
            assert error == ""

    def test_valid_credentials_with_session_token(self):
        """Test validation with session token (temporary credentials)."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'ASIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'AWS_SESSION_TOKEN': 'token123',
        }):
            is_valid, error = _validate_aws_credentials()
            assert is_valid is True
            assert error == ""

    def test_missing_access_key(self):
        """Test validation with missing access key."""
        with patch.dict(os.environ, {
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }, clear=True):
            is_valid, error = _validate_aws_credentials()
            assert is_valid is False
            assert 'AWS_ACCESS_KEY_ID' in error

    def test_missing_secret_key(self):
        """Test validation with missing secret key."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
        }, clear=True):
            is_valid, error = _validate_aws_credentials()
            assert is_valid is False
            assert 'AWS_SECRET_ACCESS_KEY' in error

    def test_missing_all_credentials(self):
        """Test validation with no credentials."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = _validate_aws_credentials()
            assert is_valid is False
            assert 'AWS_ACCESS_KEY_ID' in error
            assert 'AWS_SECRET_ACCESS_KEY' in error


class TestBedrockAgent:
    """Test WYN360Agent with Bedrock mode."""

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_mode_initialization(self, mock_agent, mock_bedrock):
        """Test agent initialization in Bedrock mode."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }):
            agent = WYN360Agent(use_bedrock=True)

            assert agent.use_bedrock is True
            assert agent.api_key is None
            mock_bedrock.assert_called_once()

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_mode_with_region(self, mock_agent, mock_bedrock):
        """Test Bedrock mode respects AWS_REGION."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'AWS_REGION': 'us-west-2',
        }):
            agent = WYN360Agent(use_bedrock=True)

            # Verify bedrock client was created with correct region
            mock_bedrock.assert_called_once_with(aws_region='us-west-2')

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_mode_default_region(self, mock_agent, mock_bedrock):
        """Test Bedrock mode defaults to us-east-1."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }, clear=True):
            agent = WYN360Agent(use_bedrock=True)

            # Verify bedrock client was created with default region
            mock_bedrock.assert_called_once_with(aws_region='us-east-1')

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_mode_default_model(self, mock_agent, mock_bedrock):
        """Test Bedrock mode uses correct default model ARN."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }, clear=True):
            agent = WYN360Agent(use_bedrock=True)

            # Verify Bedrock default model ARN is used
            assert agent.model_name == "us.anthropic.claude-sonnet-4-20250514-v1:0"

    def test_bedrock_mode_missing_credentials(self):
        """Test that Bedrock mode raises error with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="credentials not found"):
                WYN360Agent(use_bedrock=True)

    def test_bedrock_mode_missing_access_key(self):
        """Test Bedrock mode error with missing access key."""
        with patch.dict(os.environ, {
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }, clear=True):
            with pytest.raises(ValueError, match="AWS_ACCESS_KEY_ID"):
                WYN360Agent(use_bedrock=True)

    @patch('wyn360_cli.agent.Agent')
    def test_anthropic_mode_initialization(self, mock_agent):
        """Test agent initialization in Anthropic API mode."""
        agent = WYN360Agent(api_key="sk-ant-xxx", use_bedrock=False)

        assert agent.use_bedrock is False
        assert agent.api_key == "sk-ant-xxx"

    def test_anthropic_mode_missing_api_key(self):
        """Test that Anthropic mode requires API key."""
        # Clear environment to ensure no API key is present
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
                WYN360Agent(use_bedrock=False)

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_env_var_takes_precedence(self, mock_agent, mock_bedrock):
        """Test that CLAUDE_CODE_USE_BEDROCK env var is respected."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '1',
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'ANTHROPIC_API_KEY': 'sk-ant-xxx',  # This should be ignored
        }):
            agent = WYN360Agent()

            assert agent.use_bedrock is True
            assert agent.api_key is None  # Bedrock doesn't use API key

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_anthropic_model_env_var(self, mock_agent, mock_bedrock):
        """Test that ANTHROPIC_MODEL env var is respected."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'ANTHROPIC_MODEL': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
        }):
            agent = WYN360Agent(use_bedrock=True)

            assert agent.model_name == 'us.anthropic.claude-sonnet-4-20250514-v1:0'

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_model_priority_order(self, mock_agent, mock_bedrock):
        """Test model selection priority: config > env var > parameter."""
        from wyn360_cli.config import WYN360Config

        # Mock config with model
        mock_config = Mock(spec=WYN360Config)
        mock_config.model = "config-model"
        mock_config.browser_use_cache_enabled = False
        mock_config.custom_instructions = None
        mock_config.project_context = None
        mock_config.project_dependencies = None
        mock_config.browser_use_cache_ttl = 3600
        mock_config.browser_use_cache_max_size_mb = 100

        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'ANTHROPIC_MODEL': 'env-model',
        }):
            agent = WYN360Agent(
                model="param-model",
                config=mock_config,
                use_bedrock=True
            )

            # Config should take precedence
            assert agent.model_name == "config-model"


class TestBedrockImportError:
    """Test handling of missing bedrock dependencies."""

    def test_bedrock_import_error(self):
        """Test clear error when anthropic[bedrock] not installed."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }):
            # Patch the import to raise ImportError
            with patch.dict('sys.modules', {'anthropic': MagicMock()}):
                # Make the AnthropicBedrock import fail
                sys.modules['anthropic'].AnthropicBedrock = None
                del sys.modules['anthropic'].AnthropicBedrock

                # This will cause AttributeError when trying to import
                with pytest.raises((ImportError, AttributeError)):
                    WYN360Agent(use_bedrock=True)


class TestBedrockEdgeCases:
    """Test edge cases and error scenarios."""

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_both_credentials_set_bedrock_priority(self, mock_agent, mock_bedrock):
        """Test that Bedrock flag takes priority when both credentials present."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '1',
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'ANTHROPIC_API_KEY': 'sk-ant-xxx',
        }):
            agent = WYN360Agent()

            assert agent.use_bedrock is True
            mock_bedrock.assert_called_once()

    @patch('wyn360_cli.agent.Agent')
    def test_explicit_use_bedrock_false(self, mock_agent):
        """Test explicit use_bedrock=False parameter."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '1',  # Env var says yes
            'ANTHROPIC_API_KEY': 'sk-ant-xxx',
        }):
            # But parameter says no - parameter wins
            agent = WYN360Agent(use_bedrock=False)

            assert agent.use_bedrock is False
            assert agent.api_key == 'sk-ant-xxx'

    @patch('anthropic.AnthropicBedrock')
    @patch('wyn360_cli.agent.Agent')
    def test_explicit_use_bedrock_true(self, mock_agent, mock_bedrock):
        """Test explicit use_bedrock=True parameter."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '0',  # Env var says no
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }):
            # But parameter says yes - parameter wins
            agent = WYN360Agent(use_bedrock=True)

            assert agent.use_bedrock is True
            mock_bedrock.assert_called_once()
