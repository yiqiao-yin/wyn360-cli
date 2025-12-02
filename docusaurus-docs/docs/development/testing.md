# Testing

Comprehensive guide to testing WYN360 CLI during development and contribution.

## Test Structure

```
tests/
├── __init__.py
├── test_agent.py          # Agent and tool tests (46 tests)
├── test_cli.py            # CLI and slash command tests (33 tests)
├── test_config.py         # Configuration tests (25 tests)
├── test_utils.py          # Utility function tests (29 tests)
├── test_browser_*.py      # Browser automation tests
├── test_document_*.py     # Document processing tests
└── test_credential_*.py   # Security and credential tests
                          # Total: 133+ tests
```

## Running Tests

### Basic Test Execution

**Run all tests:**
```bash
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
```

**Run specific test file:**
```bash
poetry run pytest tests/test_agent.py -v
```

**Run specific test class:**
```bash
poetry run pytest tests/test_utils.py::TestExecuteCommandSafe -v
```

**Run with short traceback:**
```bash
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v --tb=short
```

### Coverage Analysis

**Generate coverage report:**
```bash
poetry run pytest tests/ --cov=wyn360_cli --cov-report=html
```

**View coverage in browser:**
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Categories

### Unit Tests

**Agent Tests** (`test_agent.py`)
- WYN360Agent initialization
- Tool method functionality
- Conversation history management
- Token tracking
- Model switching

**CLI Tests** (`test_cli.py`)
- Slash command parsing
- Command execution
- Input/output handling
- Error handling

**Configuration Tests** (`test_config.py`)
- Config file loading
- Environment variable handling
- Default value setting
- Hierarchical config merging

**Utility Tests** (`test_utils.py`)
- File operations
- Command execution safety
- Project analysis
- Performance metrics

### Integration Tests

**Browser Tests** (`test_browser_*.py`)
- Browser automation
- Website fetching
- Vision-based navigation
- Authentication flows

**Document Tests** (`test_document_*.py`)
- Multi-format document reading
- Vision mode processing
- Chunking and embedding
- Cost tracking

**Security Tests** (`test_credential_*.py`)
- Credential encryption/decryption
- Session management
- Audit logging
- Permission handling

## Test Environment Setup

### Required Environment Variables

```bash
# Skip interactive confirmations during tests
export WYN360_SKIP_CONFIRM=1

# Test API keys (use test/mock keys)
export ANTHROPIC_API_KEY=test_key_anthropic
export GEMINI_API_KEY=test_key_gemini
export GH_TOKEN=test_key_github
export HF_TOKEN=test_key_huggingface
```

### Mock Configuration

Tests use mocking to avoid real API calls:

```python
# Example from tests
@patch('wyn360_cli.agent.WYN360Agent')
def test_agent_initialization(mock_agent):
    """Test agent initializes with correct parameters."""
    mock_agent.return_value = MagicMock()
    # Test implementation
```

## Writing New Tests

### Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from wyn360_cli.your_module import YourClass

class TestYourClass:
    """Test suite for YourClass functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.instance = YourClass()

    def test_basic_functionality(self):
        """Test basic functionality works as expected."""
        # Arrange
        input_data = "test_input"
        expected_output = "expected_result"

        # Act
        result = self.instance.method(input_data)

        # Assert
        assert result == expected_output

    @patch('wyn360_cli.your_module.external_dependency')
    def test_with_mocking(self, mock_external):
        """Test functionality that depends on external services."""
        # Arrange
        mock_external.return_value = "mocked_response"

        # Act
        result = self.instance.method_with_dependency()

        # Assert
        assert result is not None
        mock_external.assert_called_once()
```

### Async Test Template

```python
import pytest
import asyncio

class TestAsyncFunctionality:
    """Test async methods."""

    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async method functionality."""
        instance = AsyncClass()
        result = await instance.async_method()
        assert result is not None
```

## Testing Best Practices

### 1. Test Categories

**Unit Tests:** Test individual functions/methods in isolation
```python
def test_utility_function():
    """Test utility function with known input/output."""
    result = utility_function("input")
    assert result == "expected_output"
```

**Integration Tests:** Test component interactions
```python
@pytest.mark.asyncio
async def test_agent_tool_integration():
    """Test agent and tool work together."""
    agent = WYN360Agent()
    result = await agent.read_file("test_file.py")
    assert "def " in result  # Contains function definition
```

**End-to-End Tests:** Test complete workflows
```python
def test_complete_workflow():
    """Test entire user workflow."""
    # This would test CLI → Agent → Tools → Output
    pass
```

### 2. Mock External Dependencies

Always mock external services:
```python
@patch('requests.get')
def test_web_fetch(mock_get):
    """Test web fetching with mocked HTTP calls."""
    mock_get.return_value.text = "mocked content"
    result = fetch_website("https://example.com")
    assert result == "mocked content"
```

### 3. Test Error Conditions

```python
def test_error_handling():
    """Test proper error handling."""
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_should_raise("invalid_input")
```

### 4. Use Fixtures for Common Setup

```python
@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return {
        "model": "test-model",
        "max_tokens": 100,
        "custom_instructions": "Test instructions"
    }

def test_with_fixture(sample_config):
    """Test using the fixture."""
    agent = WYN360Agent(config=sample_config)
    assert agent.config["model"] == "test-model"
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests to main branch
- Pushes to main branch
- Release creation

### Test Matrix

Tests run against:
- Python 3.10, 3.11, 3.12
- Linux, macOS, Windows
- Multiple dependency versions

## Debugging Test Failures

### Common Issues

**Import Errors:**
```bash
# Ensure package is installed in development mode
poetry install

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

**API Key Errors:**
```bash
# Ensure skip confirmation is set
export WYN360_SKIP_CONFIRM=1

# Use mock API keys
export ANTHROPIC_API_KEY=test_key
```

**Async Test Issues:**
```python
# Ensure proper async test marking
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Debug Output

**Run with debug output:**
```bash
poetry run pytest tests/ -v -s --tb=long
```

**Run single test with debugging:**
```bash
poetry run pytest tests/test_agent.py::TestWYN360Agent::test_specific_method -v -s
```

## Expected Test Output

When all tests pass:

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.4.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /home/workbench/wyn360-cli/wyn360-cli
configfile: pyproject.toml
plugins: asyncio-1.2.0, mock-3.15.1
collected 133 items

tests/test_agent.py::TestWYN360Agent::test_agent_initialization PASSED   [  1%]
tests/test_agent.py::TestHistoryManagement::test_clear_history PASSED    [ 18%]
tests/test_cli.py::TestSlashCommands::test_clear_command PASSED          [ 42%]
tests/test_config.py::TestWYN360Config::test_default_values PASSED       [ 60%]
tests/test_utils.py::TestExecuteCommandSafe::test_execute_command PASSED [100%]

============================== 133 passed in 2.64s
```

## Performance Testing

### Benchmark Tests

```python
import time

def test_performance_benchmark():
    """Test performance meets expectations."""
    start_time = time.time()

    # Perform operation
    result = expensive_operation()

    end_time = time.time()
    execution_time = end_time - start_time

    assert execution_time < 5.0  # Should complete in under 5 seconds
    assert result is not None
```

For more testing examples, see the existing test files in the `tests/` directory.