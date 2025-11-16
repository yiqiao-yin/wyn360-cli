# AWS Bedrock Integration Roadmap

**Version:** 0.3.45 (Target)
**Date:** 2025-11-15
**Status:** Planning Phase

---

## Executive Summary

Add AWS Bedrock support to WYN360 CLI, allowing users to authenticate using AWS credentials instead of (or in addition to) direct Anthropic API keys.

**Current State:**
- ✅ Authentication: `ANTHROPIC_API_KEY` only
- ✅ Client: `anthropic.Anthropic`
- ✅ Model: `AnthropicModel` from `pydantic_ai.models.anthropic`

**Target State:**
- ✅ Authentication: `ANTHROPIC_API_KEY` (default) OR AWS credentials (opt-in)
- ✅ Client: `anthropic.Anthropic` OR `anthropic.AnthropicBedrock`
- ✅ Model: `AnthropicModel` with either client backend
- ✅ Feature flag: `CLAUDE_CODE_USE_BEDROCK=1` to enable AWS mode

---

## User Experience

### Scenario 1: Current Behavior (No Changes)
```bash
# User sets Anthropic API key (existing behavior)
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
wyn360 "write a script to analyze data.csv"
# ✅ Works as before - uses Anthropic API directly
```

### Scenario 2: AWS Bedrock Authentication (New)
```bash
# User sets AWS credentials + enables Bedrock
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="xxx..."
export AWS_SESSION_TOKEN="xxx..."  # Optional - for temporary credentials
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION="us-west-2"  # Optional - defaults to us-east-1
export ANTHROPIC_MODEL="us.anthropic.claude-sonnet-4-20250514-v1:0"  # Optional - custom model

wyn360 "write a script to analyze data.csv"
# ✅ Uses AWS Bedrock instead of Anthropic API
```

### Scenario 3: Missing Credentials (Error Handling)
```bash
# User enables Bedrock but forgets AWS credentials
export CLAUDE_CODE_USE_BEDROCK=1
wyn360 "hello"

# ❌ Error message:
# Error: AWS Bedrock mode enabled but credentials not found.
#
# Please set the following environment variables:
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#   - AWS_SESSION_TOKEN (optional, for temporary credentials)
#
# Or disable Bedrock mode:
#   unset CLAUDE_CODE_USE_BEDROCK
```

---

## Architecture Changes

### Current Architecture
```
┌─────────────────────────────────────────┐
│ User sets ANTHROPIC_API_KEY             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ WYN360Agent.__init__()                  │
│  - Creates AnthropicModel               │
│  - Uses anthropic.Anthropic client      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ API Calls to api.anthropic.com          │
└─────────────────────────────────────────┘
```

### New Architecture (Dual-Mode)
```
┌────────────────────────────────────────────────────────┐
│ User sets credentials:                                 │
│  Option A: ANTHROPIC_API_KEY                           │
│  Option B: AWS_* + CLAUDE_CODE_USE_BEDROCK=1           │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ WYN360Agent.__init__()                                 │
│  - Checks CLAUDE_CODE_USE_BEDROCK environment variable │
│  - If "1": Creates AnthropicBedrock client             │
│  - If not set: Creates Anthropic client (default)      │
└────────────────┬───────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
┌──────────────┐  ┌──────────────────┐
│ Anthropic    │  │ AnthropicBedrock │
│ Direct API   │  │ AWS Bedrock      │
└──────────────┘  └──────────────────┘
```

---

## Implementation Plan

### Phase 1: Dependency Updates

#### 1.1: Add anthropic[bedrock] Dependency

**File:** `pyproject.toml`

**Current:**
```toml
dependencies = [
    "anthropic>=0.39.0",
    # ... other deps
]
```

**New:**
```toml
dependencies = [
    "anthropic[bedrock]>=0.39.0",  # Changed: added [bedrock] extra
    # ... other deps
]
```

**Note:** The `anthropic[bedrock]` extra includes:
- `anthropic` base package
- `boto3` (AWS SDK for Python)
- `botocore` (AWS core libraries)

**Commands:**
```bash
poetry add "anthropic[bedrock]>=0.39.0"
poetry lock
poetry install
```

---

### Phase 2: Core Authentication Logic

#### 2.1: Add Bedrock Detection Helper

**File:** `wyn360_cli/agent.py`

**Location:** Add near top of file (after imports, around line 40)

**New Function:**
```python
def _should_use_bedrock() -> bool:
    """
    Check if AWS Bedrock mode is enabled via environment variable.

    Returns:
        True if CLAUDE_CODE_USE_BEDROCK=1, False otherwise
    """
    return os.getenv('CLAUDE_CODE_USE_BEDROCK', '0') == '1'


def _validate_aws_credentials() -> Tuple[bool, str]:
    """
    Validate that required AWS credentials are set.

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if all required credentials present
        - error_message: Error message if invalid, empty string if valid
    """
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        error_msg = f"""AWS Bedrock mode enabled but credentials not found.

Please set the following environment variables:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_SESSION_TOKEN (optional, for temporary credentials)

Missing variables: {', '.join(missing)}

Or disable Bedrock mode:
  unset CLAUDE_CODE_USE_BEDROCK
"""
        return False, error_msg

    return True, ""
```

---

#### 2.2: Update WYN360Agent.__init__()

**File:** `wyn360_cli/agent.py`

**Current Code (lines ~66-100):**
```python
def __init__(
    self,
    api_key: str,
    model_name: str = "claude-sonnet-4-20250514",
    max_history: int = 10
):
    self.api_key = api_key
    self.model_name = model_name

    # Create Anthropic model
    from pydantic_ai.models.anthropic import AnthropicModel
    self.model = AnthropicModel(model_name, api_key=api_key)

    # ... rest of init
```

**New Code:**
```python
def __init__(
    self,
    api_key: Optional[str] = None,  # Changed: now optional
    model_name: str = "claude-sonnet-4-20250514",
    max_history: int = 10,
    use_bedrock: Optional[bool] = None  # New: explicit override
):
    """
    Initialize WYN360 Agent with Anthropic or AWS Bedrock.

    Args:
        api_key: Anthropic API key (required if not using Bedrock)
        model_name: Claude model to use
        max_history: Number of messages to keep in history
        use_bedrock: Explicitly set Bedrock mode (overrides env var)
    """
    # Determine authentication mode
    if use_bedrock is None:
        use_bedrock = _should_use_bedrock()

    self.use_bedrock = use_bedrock
    self.model_name = model_name

    # Import required classes
    from pydantic_ai.models.anthropic import AnthropicModel

    if self.use_bedrock:
        # AWS Bedrock mode
        is_valid, error_msg = _validate_aws_credentials()
        if not is_valid:
            raise ValueError(error_msg)

        # Create Bedrock client
        from anthropic import AnthropicBedrock

        # Map model names to Bedrock model IDs
        bedrock_model_id = self._get_bedrock_model_id(model_name)

        # AnthropicBedrock automatically reads AWS credentials from environment
        # AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
        bedrock_client = AnthropicBedrock()

        # Create model with Bedrock backend
        self.model = AnthropicModel(
            bedrock_model_id,
            http_client=bedrock_client
        )

        self.api_key = None  # Not used in Bedrock mode

        print("🌩️  AWS Bedrock mode enabled")
        print(f"📡 Using model: {bedrock_model_id}")

    else:
        # Direct Anthropic API mode (existing behavior)
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when not using AWS Bedrock.\n"
                "Set environment variable: export ANTHROPIC_API_KEY=sk-ant-xxx\n"
                "Or enable Bedrock mode: export CLAUDE_CODE_USE_BEDROCK=1"
            )

        self.api_key = api_key
        self.model = AnthropicModel(model_name, api_key=api_key)

    # ... rest of existing init code (unchanged)
    self.max_history = max_history
    self.conversation_history = []
    # etc.
```

---

#### 2.3: Add Bedrock Model ID Mapper

**File:** `wyn360_cli/agent.py`

**Location:** Add as new method in `WYN360Agent` class

**New Method:**
```python
def _get_bedrock_model_id(self, model_name: str) -> str:
    """
    Map pydantic-ai model names to AWS Bedrock model IDs.

    Args:
        model_name: Model name from user (e.g., "claude-sonnet-4-20250514")

    Returns:
        Bedrock model ID (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")

    Reference:
        https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
    """
    # Model mapping: pydantic-ai name → Bedrock ARN
    bedrock_models = {
        # Claude 3.5 Sonnet (latest)
        "claude-sonnet-4-20250514": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "claude-3-5-sonnet-20241022": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "claude-3-5-sonnet-20240620": "anthropic.claude-3-5-sonnet-20240620-v1:0",

        # Claude 3 Opus
        "claude-3-opus-20240229": "anthropic.claude-3-opus-20240229-v1:0",

        # Claude 3 Sonnet
        "claude-3-sonnet-20240229": "anthropic.claude-3-sonnet-20240229-v1:0",

        # Claude 3 Haiku
        "claude-3-haiku-20240307": "anthropic.claude-3-haiku-20240307-v1:0",
    }

    # Try exact match first
    if model_name in bedrock_models:
        return bedrock_models[model_name]

    # Try partial match (e.g., "sonnet" → latest sonnet)
    model_lower = model_name.lower()
    if "sonnet" in model_lower:
        return bedrock_models["claude-sonnet-4-20250514"]  # Default to latest
    elif "opus" in model_lower:
        return bedrock_models["claude-3-opus-20240229"]
    elif "haiku" in model_lower:
        return bedrock_models["claude-3-haiku-20240307"]

    # Fallback: use as-is (might be a direct Bedrock ARN)
    print(f"⚠️  Unknown model '{model_name}', using as-is")
    return model_name
```

---

### Phase 3: CLI Integration

#### 3.1: Update main() to Handle Bedrock Mode

**File:** `wyn360_cli/cli.py`

**Current Code:**
```python
def main():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        typer.echo("Error: ANTHROPIC_API_KEY not set")
        raise typer.Exit(code=1)

    agent = WYN360Agent(api_key=api_key)
    # ...
```

**New Code:**
```python
def main():
    """Main entry point for WYN360 CLI."""

    # Check if Bedrock mode is enabled
    use_bedrock = os.getenv('CLAUDE_CODE_USE_BEDROCK', '0') == '1'

    if use_bedrock:
        # AWS Bedrock mode - no API key needed
        try:
            agent = WYN360Agent(use_bedrock=True)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        # Direct Anthropic API mode - API key required
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            typer.echo(
                "Error: ANTHROPIC_API_KEY not set\n\n"
                "Options:\n"
                "  1. Set Anthropic API key: export ANTHROPIC_API_KEY=sk-ant-xxx\n"
                "  2. Use AWS Bedrock: export CLAUDE_CODE_USE_BEDROCK=1\n"
                "     (requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)",
                err=True
            )
            raise typer.Exit(code=1)

        agent = WYN360Agent(api_key=api_key)

    # ... rest of main() unchanged
```

---

### Phase 4: Model Switching Support

#### 4.1: Update switch_model() for Bedrock

**File:** `wyn360_cli/agent.py`

**Current Code (lines ~3574-3593):**
```python
async def switch_model(self, ctx: RunContext[None], model_name: str) -> str:
    # ... validation code ...

    # Create new model instance
    from pydantic_ai.models.anthropic import AnthropicModel
    new_model = AnthropicModel(full_model_name)

    # Update agent
    self.model = new_model
    self.model_name = full_model_name
```

**New Code:**
```python
async def switch_model(self, ctx: RunContext[None], model_name: str) -> str:
    """
    Switch to a different Claude model.

    Works in both Anthropic API and AWS Bedrock modes.
    """
    # ... existing validation code ...

    # Create new model instance
    from pydantic_ai.models.anthropic import AnthropicModel

    if self.use_bedrock:
        # Bedrock mode: map to Bedrock model ID
        from anthropic import AnthropicBedrock

        bedrock_model_id = self._get_bedrock_model_id(model_name)
        bedrock_client = AnthropicBedrock()

        new_model = AnthropicModel(
            bedrock_model_id,
            http_client=bedrock_client
        )

        self.model_name = bedrock_model_id

    else:
        # Direct API mode
        new_model = AnthropicModel(full_model_name, api_key=self.api_key)
        self.model_name = full_model_name

    # Update agent with new model
    self.model = new_model

    # Recreate agent (existing code continues...)
```

---

### Phase 5: Documentation Updates

#### 5.1: Update README.md

**File:** `README.md`

**Add New Section:** "Authentication Methods"

```markdown
## Authentication Methods

WYN360 supports two authentication methods:

### Method 1: Direct Anthropic API (Default)

```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
wyn360 "write a script to analyze data.csv"
```

**Pros:**
- Simple setup
- Direct access to latest models
- Lower latency

**Cons:**
- Requires Anthropic API account
- May have different pricing than AWS

---

### Method 2: AWS Bedrock

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="xxx..."
export AWS_SESSION_TOKEN="xxx..."  # Optional
export CLAUDE_CODE_USE_BEDROCK=1

wyn360 "write a script to analyze data.csv"
```

**Pros:**
- Use existing AWS credentials
- AWS billing and governance
- Works with AWS IAM roles/policies
- Supports AWS temporary credentials (STS)

**Cons:**
- Requires AWS Bedrock access
- May have limited model availability
- Additional AWS setup required

---

### Switching Between Methods

**To switch to Bedrock:**
```bash
export CLAUDE_CODE_USE_BEDROCK=1
# Also ensure AWS credentials are set
```

**To switch back to Anthropic API:**
```bash
unset CLAUDE_CODE_USE_BEDROCK
# Or: export CLAUDE_CODE_USE_BEDROCK=0
```
```

---

#### 5.2: Update USE_CASES.md

**File:** `docs/USE_CASES.md`

**Add New Use Case:** "Use Case 27: AWS Bedrock Authentication"

```markdown
## Use Case 27: AWS Bedrock Authentication

### Use Case 27.1: Basic AWS Bedrock Setup

**Scenario:** You have an AWS account with Bedrock access and want to use WYN360 with AWS credentials.

**Setup:**
```bash
# Step 1: Set AWS credentials
export AWS_ACCESS_KEY_ID="your_aws_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"

# Step 2: Enable Bedrock mode
export CLAUDE_CODE_USE_BEDROCK=1

# Step 3: Use WYN360
wyn360 "write a Python script to process data.csv"
```

**Output:**
```
🌩️  AWS Bedrock mode enabled
📡 Using model: anthropic.claude-3-5-sonnet-20241022-v2:0

WYN360: I'll create a Python script to process data.csv...
```

---

### Use Case 27.2: Using AWS IAM Roles (EC2/ECS/Lambda)

**Scenario:** Running WYN360 on AWS infrastructure with IAM roles.

**Setup:**
```bash
# No need to set AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY
# The boto3 SDK automatically uses the instance IAM role

# Just enable Bedrock mode
export CLAUDE_CODE_USE_BEDROCK=1

wyn360 "analyze logs.txt"
```

**IAM Policy Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
    }
  ]
}
```

---

### Use Case 27.3: Using AWS Temporary Credentials (STS)

**Scenario:** Using temporary AWS credentials from `aws sts assume-role`.

**Setup:**
```bash
# Get temporary credentials
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/WYN360Role \
  --role-session-name wyn360-session \
  --output json > /tmp/aws-creds.json

# Extract and export credentials
export AWS_ACCESS_KEY_ID=$(jq -r '.Credentials.AccessKeyId' /tmp/aws-creds.json)
export AWS_SECRET_ACCESS_KEY=$(jq -r '.Credentials.SecretAccessKey' /tmp/aws-creds.json)
export AWS_SESSION_TOKEN=$(jq -r '.Credentials.SessionToken' /tmp/aws-creds.json)

# Enable Bedrock
export CLAUDE_CODE_USE_BEDROCK=1

wyn360 "help me debug this code"
```

---

### Use Case 27.4: Model Switching in Bedrock Mode

**Scenario:** Switching between Claude models while using Bedrock.

**Commands:**
```bash
# Start with default (Sonnet)
wyn360 "switch to claude-3-opus-20240229"
# ✅ Now using: anthropic.claude-3-opus-20240229-v1:0

wyn360 "switch to claude-3-haiku-20240307"
# ✅ Now using: anthropic.claude-3-haiku-20240307-v1:0

wyn360 "switch to sonnet"
# ✅ Now using: anthropic.claude-3-5-sonnet-20241022-v2:0 (latest)
```

---

### Use Case 27.5: Troubleshooting Bedrock Authentication

**Problem:** Missing AWS credentials

```bash
export CLAUDE_CODE_USE_BEDROCK=1
wyn360 "hello"

# ❌ Error:
# AWS Bedrock mode enabled but credentials not found.
#
# Please set the following environment variables:
#   - AWS_ACCESS_KEY_ID
#   - AWS_SECRET_ACCESS_KEY
#
# Missing variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
```

**Solution:**
```bash
# Option 1: Set credentials
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="xxx"

# Option 2: Use AWS CLI configured credentials
aws configure
# (Follow prompts to set credentials)

# Option 3: Disable Bedrock mode
unset CLAUDE_CODE_USE_BEDROCK
export ANTHROPIC_API_KEY="sk-ant-xxx"
```
```

---

### Phase 6: Testing Strategy

#### 6.1: Unit Tests

**File:** `tests/test_bedrock.py` (NEW)

```python
"""Tests for AWS Bedrock integration."""

import pytest
import os
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


class TestBedrockAgent:
    """Test WYN360Agent with Bedrock mode."""

    @patch('wyn360_cli.agent.AnthropicBedrock')
    @patch('wyn360_cli.agent.AnthropicModel')
    def test_bedrock_mode_initialization(self, mock_model, mock_bedrock):
        """Test agent initialization in Bedrock mode."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }):
            agent = WYN360Agent(use_bedrock=True)

            assert agent.use_bedrock is True
            assert agent.api_key is None
            mock_bedrock.assert_called_once()

    def test_bedrock_mode_missing_credentials(self):
        """Test that Bedrock mode raises error with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="credentials not found"):
                WYN360Agent(use_bedrock=True)

    @patch('wyn360_cli.agent.AnthropicModel')
    def test_anthropic_mode_initialization(self, mock_model):
        """Test agent initialization in Anthropic API mode."""
        agent = WYN360Agent(api_key="sk-ant-xxx", use_bedrock=False)

        assert agent.use_bedrock is False
        assert agent.api_key == "sk-ant-xxx"
        mock_model.assert_called_once()


class TestModelMapping:
    """Test Bedrock model ID mapping."""

    @patch('wyn360_cli.agent.AnthropicBedrock')
    @patch('wyn360_cli.agent.AnthropicModel')
    def test_sonnet_model_mapping(self, mock_model, mock_bedrock):
        """Test that Sonnet model maps to correct Bedrock ID."""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'AKIA...',
            'AWS_SECRET_ACCESS_KEY': 'secret',
        }):
            agent = WYN360Agent(
                model_name="claude-sonnet-4-20250514",
                use_bedrock=True
            )

            expected_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
            # Verify model was created with Bedrock ID
            mock_model.assert_called()
            call_args = mock_model.call_args
            assert expected_id in str(call_args)
```

---

#### 6.2: Integration Tests

**File:** `tests/test_bedrock_integration.py` (NEW)

```python
"""Integration tests for Bedrock (requires real AWS credentials)."""

import pytest
import os
from wyn360_cli.agent import WYN360Agent


@pytest.mark.skipif(
    not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('RUN_BEDROCK_TESTS'),
    reason="Requires AWS credentials and RUN_BEDROCK_TESTS=1"
)
class TestBedrockIntegration:
    """Integration tests with real AWS Bedrock (expensive, skip by default)."""

    async def test_bedrock_simple_query(self):
        """Test a simple query using real Bedrock credentials."""
        agent = WYN360Agent(use_bedrock=True)

        result = await agent.agent.run("Say 'hello' in one word")

        assert result.data
        assert len(result.data) > 0

    async def test_bedrock_model_switching(self):
        """Test switching models in Bedrock mode."""
        agent = WYN360Agent(use_bedrock=True)

        # Switch to Haiku
        from pydantic_ai import RunContext
        ctx = RunContext(deps=None)
        result = await agent.switch_model(ctx, "claude-3-haiku-20240307")

        assert "haiku" in result.lower()
        assert "anthropic.claude-3-haiku" in agent.model_name
```

---

### Phase 7: Error Handling & Edge Cases

#### 7.1: Edge Cases to Handle

1. **Both API key and Bedrock credentials set**
   - Solution: Prioritize `CLAUDE_CODE_USE_BEDROCK` flag
   - If flag=1, use Bedrock regardless of API key presence

2. **Invalid AWS credentials**
   - Solution: Let boto3 raise natural error, catch and show friendly message

3. **Bedrock model not available in region**
   - Solution: Catch error, suggest checking AWS region and model availability

4. **AWS session token expiration**
   - Solution: boto3 handles automatically, suggest refreshing credentials on auth error

---

#### 7.2: Enhanced Error Messages

**File:** `wyn360_cli/agent.py`

**Add to `__init__()` Bedrock section:**

```python
try:
    bedrock_client = AnthropicBedrock()
except Exception as e:
    raise ValueError(
        f"Failed to create AWS Bedrock client: {e}\n\n"
        "Common causes:\n"
        "  - Invalid AWS credentials\n"
        "  - Bedrock not enabled in your AWS account\n"
        "  - Incorrect AWS region (check AWS_DEFAULT_REGION)\n"
        "  - Network connectivity issues\n\n"
        "Verify your setup:\n"
        "  1. Check credentials: aws sts get-caller-identity\n"
        "  2. Check Bedrock access: aws bedrock list-foundation-models\n"
        "  3. Ensure region supports Bedrock (us-east-1, us-west-2, etc.)"
    )
```

---

### Phase 8: Version & Deployment

#### 8.1: Version Update

- **Current:** 0.3.44
- **Target:** 0.3.45
- **Type:** Minor version (new feature)

#### 8.2: Changelog Entry

**File:** `docs/USE_CASES.md` (Version History section)

```markdown
### v0.3.45
- ✨ **NEW FEATURE:** AWS Bedrock authentication support
- 🔐 Use AWS credentials instead of Anthropic API key (opt-in)
- 🌩️ Enable with `export CLAUDE_CODE_USE_BEDROCK=1`
- 📦 Added `anthropic[bedrock]` dependency (includes boto3)
- 🛠️ Automatic model mapping to Bedrock ARNs
- 📚 New Use Case 27: AWS Bedrock Authentication
- ✅ Full support for AWS IAM roles and temporary credentials (STS)
- 🧪 26 new unit tests for Bedrock integration
```

---

## File Modification Summary

### Files to Modify

| File | Changes | Lines Changed |
|------|---------|---------------|
| `pyproject.toml` | Update anthropic dependency | ~1 |
| `wyn360_cli/agent.py` | Add Bedrock support | ~150 |
| `wyn360_cli/cli.py` | Update credential handling | ~20 |
| `README.md` | Add authentication docs | ~80 |
| `docs/USE_CASES.md` | Add Use Case 27 | ~200 |
| `tests/test_bedrock.py` | New test file | ~120 |
| `tests/test_bedrock_integration.py` | New integration tests | ~40 |

**Total:** ~611 lines of new/modified code

---

## Implementation Checklist

### Phase 1: Dependencies ✅
- [ ] Update `pyproject.toml` with `anthropic[bedrock]`
- [ ] Run `poetry lock` and `poetry install`
- [ ] Verify boto3 is installed

### Phase 2: Core Logic ✅
- [ ] Add `_should_use_bedrock()` helper
- [ ] Add `_validate_aws_credentials()` helper
- [ ] Add `_get_bedrock_model_id()` method
- [ ] Update `WYN360Agent.__init__()` for dual-mode
- [ ] Update `switch_model()` for Bedrock

### Phase 3: CLI Integration ✅
- [ ] Update `cli.py` main() function
- [ ] Add improved error messages

### Phase 4: Testing ✅
- [ ] Create `tests/test_bedrock.py`
- [ ] Create `tests/test_bedrock_integration.py`
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Test with real AWS credentials (manual)

### Phase 5: Documentation ✅
- [ ] Update `README.md` with authentication methods
- [ ] Add Use Case 27 to `docs/USE_CASES.md`
- [ ] Update version history in docs

### Phase 6: Deployment ✅
- [ ] Update version to 0.3.45
- [ ] Run `poetry publish --build`
- [ ] Commit to GitHub
- [ ] Verify PyPI release

---

## Testing Plan

### Manual Testing Scenarios

#### Test 1: Anthropic API Mode (Existing Behavior)
```bash
unset CLAUDE_CODE_USE_BEDROCK
export ANTHROPIC_API_KEY="sk-ant-xxx"
wyn360 "write a hello world script"
# ✅ Expected: Works as before
```

#### Test 2: Bedrock Mode with Valid Credentials
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="xxx"
export CLAUDE_CODE_USE_BEDROCK=1
wyn360 "write a hello world script"
# ✅ Expected: Shows "AWS Bedrock mode enabled", generates code
```

#### Test 3: Bedrock Mode with Missing Credentials
```bash
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
export CLAUDE_CODE_USE_BEDROCK=1
wyn360 "hello"
# ✅ Expected: Clear error message with missing variables
```

#### Test 4: Model Switching in Bedrock
```bash
export CLAUDE_CODE_USE_BEDROCK=1
# (AWS credentials set)
wyn360 "switch to claude-3-opus-20240229"
wyn360 "what model are you using?"
# ✅ Expected: Confirms using Opus Bedrock ARN
```

#### Test 5: Both Credentials Set
```bash
export ANTHROPIC_API_KEY="sk-ant-xxx"
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="xxx"
export CLAUDE_CODE_USE_BEDROCK=1
wyn360 "hello"
# ✅ Expected: Uses Bedrock (flag takes precedence)
```

---

## Security Considerations

1. **Credential Storage:**
   - ✅ No credentials stored in code or config files
   - ✅ All credentials from environment variables
   - ✅ AWS credentials follow boto3 best practices

2. **AWS IAM Permissions:**
   - ✅ Minimal required permissions documented
   - ✅ Support for least-privilege IAM policies
   - ✅ Works with AWS temporary credentials (STS)

3. **Error Messages:**
   - ✅ Don't expose full credentials in errors
   - ✅ Only show presence/absence of variables
   - ✅ Provide actionable troubleshooting steps

---

## Cost Considerations

### AWS Bedrock Pricing (as of 2024)

**Claude 3.5 Sonnet:**
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

**Claude 3 Opus:**
- Input: $15.00 per 1M tokens
- Output: $75.00 per 1M tokens

**Claude 3 Haiku:**
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

**Note:** Pricing may vary by AWS region. Check AWS Bedrock pricing page.

---

## Rollback Plan

If issues arise after deployment:

1. **Emergency rollback:**
   ```bash
   git revert <commit-hash>
   git push origin main
   poetry publish --build  # Re-publish v0.3.44
   ```

2. **User mitigation:**
   ```bash
   pip install wyn360-cli==0.3.44  # Downgrade to previous version
   ```

3. **Feature disable:**
   - Users can avoid Bedrock by not setting `CLAUDE_CODE_USE_BEDROCK`
   - Existing Anthropic API flow completely unchanged
   - No breaking changes to existing users

---

## Success Metrics

- ✅ All existing tests pass (no regressions)
- ✅ 26+ new tests added with >90% coverage
- ✅ Documentation complete for both auth methods
- ✅ Manual testing successful with real AWS credentials
- ✅ PyPI deployment successful
- ✅ No breaking changes to existing users

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|---------------|------------|
| Phase 1: Dependencies | 15 minutes | Low |
| Phase 2: Core Logic | 2-3 hours | High |
| Phase 3: CLI Integration | 30 minutes | Medium |
| Phase 4: Testing | 1-2 hours | Medium |
| Phase 5: Documentation | 1 hour | Low |
| Phase 6: Deployment | 30 minutes | Low |

**Total:** ~5-7 hours

---

## Future Enhancements (Out of Scope for v0.3.45)

1. **AWS Region Configuration:**
   - Allow `AWS_DEFAULT_REGION` customization
   - Auto-detect optimal region based on latency

2. **Cross-Region Inference:**
   - Support AWS Bedrock cross-region inference profiles
   - Load balancing across regions

3. **Cost Tracking:**
   - Estimate and display token costs per session
   - AWS CloudWatch integration for usage monitoring

4. **AWS Secrets Manager Integration:**
   - Store Anthropic API key in AWS Secrets Manager
   - Automatic rotation support

5. **AWS CloudTrail Logging:**
   - Audit trail for all Bedrock API calls
   - Compliance and governance features

---

## References

- **Anthropic Bedrock Docs:** https://docs.anthropic.com/en/api/claude-on-amazon-bedrock
- **AWS Bedrock User Guide:** https://docs.aws.amazon.com/bedrock/latest/userguide/
- **Boto3 Credentials:** https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
- **pydantic-ai AnthropicModel:** https://ai.pydantic.dev/models/#anthropic

---

**End of Roadmap**
