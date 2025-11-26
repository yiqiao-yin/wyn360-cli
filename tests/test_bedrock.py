"""Tests for AWS Bedrock integration."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from wyn360_cli.agent import WYN360Agent, _get_client_choice, _validate_aws_credentials, _validate_openai_credentials


class TestClientChoiceDetection:
    """Test client choice detection."""

    def test_client_choice_auto_by_default(self):
        """Test that client choice is 0 (auto-detect) when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _get_client_choice() == 0

    def test_client_choice_anthropic(self):
        """Test that client choice is 1 for Anthropic API."""
        with patch.dict(os.environ, {'CHOOSE_CLIENT': '1'}):
            assert _get_client_choice() == 1

    def test_client_choice_bedrock(self):
        """Test that client choice is 2 for AWS Bedrock."""
        with patch.dict(os.environ, {'CHOOSE_CLIENT': '2'}):
            assert _get_client_choice() == 2

    def test_client_choice_gemini(self):
        """Test that client choice is 3 for Google Gemini."""
        with patch.dict(os.environ, {'CHOOSE_CLIENT': '3'}):
            assert _get_client_choice() == 3

    def test_client_choice_openai(self):
        """Test that client choice is 4 for OpenAI API."""
        with patch.dict(os.environ, {'CHOOSE_CLIENT': '4'}):
            assert _get_client_choice() == 4

    def test_client_choice_invalid_value(self):
        """Test that invalid values default to 0 (auto-detect)."""
        with patch.dict(os.environ, {'CHOOSE_CLIENT': 'invalid'}):
            assert _get_client_choice() == 0


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


class TestOpenAICredentialValidation:
    """Test OpenAI credential validation."""

    def test_valid_openai_credentials(self):
        """Test validation with valid OpenAI API key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
        }):
            is_valid, error = _validate_openai_credentials()
            assert is_valid is True
            assert error == ""

    def test_missing_openai_api_key(self):
        """Test validation with missing OpenAI API key."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, error = _validate_openai_credentials()
            assert is_valid is False
            assert 'OPENAI_API_KEY' in error
            assert 'https://platform.openai.com/api-keys' in error

    def test_empty_openai_api_key(self):
        """Test validation with empty OpenAI API key."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': '',
        }):
            is_valid, error = _validate_openai_credentials()
            assert is_valid is False
            assert 'OPENAI_API_KEY' in error


class TestOpenAIAgent:
    """Test WYN360Agent with OpenAI mode."""

    @patch('wyn360_cli.agent.OpenAIChatModel')
    @patch('wyn360_cli.agent.Agent')
    def test_openai_mode_initialization(self, mock_agent, mock_openai):
        """Test agent initialization in OpenAI mode."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
            'CHOOSE_CLIENT': '4'
        }):
            agent = WYN360Agent()

            # Verify OpenAI mode flags
            assert agent.use_openai is True
            assert agent.use_bedrock is False
            assert agent.use_gemini is False

            # Verify model initialization
            mock_openai.assert_called_once()

    @patch('wyn360_cli.agent.OpenAIChatModel')
    @patch('wyn360_cli.agent.Agent')
    def test_openai_model_selection_from_env(self, mock_agent, mock_openai):
        """Test OpenAI model selection from environment variable."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
            'OPENAI_MODEL': 'gpt-4o',
            'CHOOSE_CLIENT': '4'
        }):
            agent = WYN360Agent()

            # Verify model name from environment
            assert agent.model_name == 'gpt-4o'

            # Verify model was created with correct name
            mock_openai.assert_called_once_with('gpt-4o')

    @patch('wyn360_cli.agent.OpenAIChatModel')
    @patch('wyn360_cli.agent.Agent')
    def test_openai_model_selection_default(self, mock_agent, mock_openai):
        """Test OpenAI model selection with default model."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
            'CHOOSE_CLIENT': '4'
        }):
            agent = WYN360Agent()

            # Verify default model name
            assert agent.model_name == 'gpt-4'

    def test_openai_initialization_missing_key(self):
        """Test OpenAI initialization fails with missing API key."""
        with patch.dict(os.environ, {'CHOOSE_CLIENT': '4'}, clear=True):
            with pytest.raises(ValueError, match="OpenAI mode enabled but API key not found"):
                WYN360Agent()

    @patch('wyn360_cli.agent.OpenAIChatModel')
    @patch('wyn360_cli.agent.Agent')
    def test_openai_auto_detection(self, mock_agent, mock_openai):
        """Test auto-detection selects OpenAI when OPENAI_API_KEY is available."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
            'CHOOSE_CLIENT': '0'  # Auto-detect mode
        }, clear=True):
            agent = WYN360Agent()

            # Should auto-detect and use OpenAI
            assert agent.use_openai is True
            assert agent.use_bedrock is False
            assert agent.use_gemini is False

    @patch('wyn360_cli.agent.OpenAIChatModel')
    @patch('wyn360_cli.agent.Agent')
    def test_openai_priority_in_auto_detection(self, mock_agent, mock_openai):
        """Test OpenAI has correct priority in auto-detection (lowest priority)."""
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'sk-ant-123',
            'AWS_ACCESS_KEY_ID': 'AKIA123',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'GEMINI_API_KEY': 'gem-123',
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
            'CHOOSE_CLIENT': '0'  # Auto-detect mode
        }, clear=True):
            agent = WYN360Agent()

            # Should prioritize Anthropic over everything else
            assert agent.use_openai is False
            assert agent.use_bedrock is False
            assert agent.use_gemini is False
            # Anthropic should be chosen (no use_anthropic flag, but others are False)

    @patch('wyn360_cli.agent.OpenAIChatModel')
    @patch('wyn360_cli.agent.Agent')
    def test_openai_auto_detection_when_only_openai_available(self, mock_agent, mock_openai):
        """Test OpenAI is selected when it's the only available credential."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-1234567890abcdef',
            'CHOOSE_CLIENT': '0'  # Auto-detect mode
        }, clear=True):
            agent = WYN360Agent()

            # Should use OpenAI when it's the only option
            assert agent.use_openai is True
            assert agent.use_bedrock is False
            assert agent.use_gemini is False


class TestBedrockAgent:
    """Test WYN360Agent with Bedrock mode."""

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
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

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_mode_with_region(self, mock_agent, mock_bedrock):
        """Test Bedrock mode respects AWS_REGION."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'AWS_REGION': 'us-west-2',
        }):
            agent = WYN360Agent(use_bedrock=True)

            # Verify BedrockConverseModel was created
            mock_bedrock.assert_called_once()
            # Verify AWS_DEFAULT_REGION was set
            assert os.getenv('AWS_DEFAULT_REGION') == 'us-west-2'

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_mode_default_region(self, mock_agent, mock_bedrock):
        """Test Bedrock mode defaults to us-east-1."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }, clear=True):
            agent = WYN360Agent(use_bedrock=True)

            # Verify BedrockConverseModel was created
            mock_bedrock.assert_called_once()
            # Verify AWS_DEFAULT_REGION was set to default
            assert os.getenv('AWS_DEFAULT_REGION') == 'us-east-1'

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
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

    @patch('wyn360_cli.agent.Agent')
    def test_anthropic_api_key_takes_precedence(self, mock_agent):
        """Test that ANTHROPIC_API_KEY takes precedence over CLAUDE_CODE_USE_BEDROCK."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '1',  # Bedrock enabled
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'ANTHROPIC_API_KEY': 'sk-ant-xxx',  # But API key present - should use Anthropic API
        }):
            agent = WYN360Agent()

            # ANTHROPIC_API_KEY should take priority
            assert agent.use_bedrock is False
            assert agent.api_key == 'sk-ant-xxx'

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
    @patch('wyn360_cli.agent.Agent')
    def test_bedrock_only_without_api_key(self, mock_agent, mock_bedrock):
        """Test that Bedrock is used when only CLAUDE_CODE_USE_BEDROCK=1 (no API key)."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '1',
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            # No ANTHROPIC_API_KEY
        }, clear=True):
            agent = WYN360Agent()

            # Should use Bedrock mode
            assert agent.use_bedrock is True
            assert agent.api_key is None

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
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

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
    @patch('wyn360_cli.agent.Agent')
    def test_model_priority_order(self, mock_agent, mock_bedrock):
        """Test model selection priority: env var > config > parameter."""
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

            # Environment variable should take precedence
            assert agent.model_name == "env-model"


class TestBedrockImportError:
    """Test handling of missing bedrock dependencies."""

    @pytest.mark.skip(reason="Import mocking is complex; covered by integration tests")
    def test_bedrock_import_error(self):
        """Test clear error when pydantic-ai[bedrock] not installed."""
        # This test is skipped as import mocking is complex
        # The import error path is tested in integration
        pass


class TestBedrockEdgeCases:
    """Test edge cases and error scenarios."""

    @patch('wyn360_cli.agent.Agent')
    def test_both_credentials_set_anthropic_priority(self, mock_agent):
        """Test that ANTHROPIC_API_KEY takes priority when both credentials present."""
        with patch.dict(os.environ, {
            'CLAUDE_CODE_USE_BEDROCK': '1',
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
            'ANTHROPIC_API_KEY': 'sk-ant-xxx',
        }):
            agent = WYN360Agent()

            # ANTHROPIC_API_KEY takes priority over CLAUDE_CODE_USE_BEDROCK
            assert agent.use_bedrock is False
            assert agent.api_key == 'sk-ant-xxx'

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

    @patch('pydantic_ai.models.bedrock.BedrockConverseModel')
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
