# Installation

## Basic Installation

Install WYN360 CLI from PyPI using pip:

```bash
pip install wyn360-cli
```

## System Requirements

- **Python**: >= 3.10, < 4.0
- **Operating System**: Linux, macOS, Windows
- **Memory**: Minimum 512MB RAM
- **Storage**: ~200MB for full installation with browser capabilities

## Optional: Browser Use Setup

If you want to use the autonomous browsing and direct website fetching features:

```bash
# Install Playwright browser binaries (one-time setup, ~200MB)
playwright install chromium
```

!!! note "When do you need browser capabilities?"
    - **Required for**: Direct URL fetching (`Read https://example.com`), autonomous browsing
    - **Not required for**: Web search, all other features work without it
    - **Recommendation**: Install if you plan to use web automation features

## Verify Installation

Test your installation:

```bash
# Check if wyn360 is installed
wyn360 --help

# Expected output:
Usage: wyn360 [OPTIONS]

An intelligent AI coding assistant CLI tool powered by Anthropic Claude.

Options:
  --max-token INTEGER             Maximum tokens for model output
  --max-internet-search-limit INTEGER  Maximum internet searches per session
  --help                          Show this message and exit.
```

## Dependencies

WYN360 CLI automatically installs these core dependencies:

### Core Framework
- `click>=8.1.0` - CLI framework
- `pydantic-ai>=1.13.0` - AI agent framework with web search support
- `rich>=13.0.0` - Terminal formatting and display

### AI Provider Support
- `anthropic[bedrock]>=0.39.0` - Anthropic Claude API client with AWS Bedrock support
- `google-genai>=1.0.0` - Google Gemini API client

### Advanced Features
- `crawl4ai>=0.7.6` - LLM-optimized web crawler for browser use
- `playwright>=1.40.0` - Browser automation (requires separate binary install)
- `sentence-transformers>=2.2.0` - Document embeddings for semantic search
- `pytesseract>=0.3.10` - OCR capabilities
- `cryptography>=42.0.0` - Secure credential management

### Configuration & Utils
- `python-dotenv>=1.2.1` - Environment variable management
- `prompt-toolkit>=3.0.0` - Advanced input handling (multi-line support)
- `pyyaml>=6.0.0` - Configuration file support
- `huggingface-hub>=0.20.0` - HuggingFace integration

## Development Installation

For contributors or advanced users who want to install from source:

### Prerequisites

- **Poetry** - Python dependency management
- **Git** - Version control

### Setup Steps

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/yiqiao-yin/wyn360-cli.git
   cd wyn360-cli
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Activate the environment**:
   ```bash
   poetry shell
   ```

5. **Run from source**:
   ```bash
   python -m wyn360_cli.cli
   # or
   poetry run wyn360
   ```

### Running Tests

```bash
# Skip command confirmation prompts in tests
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
```

## Next Steps

Once installed, you'll need to configure your AI provider credentials:

- **[Quick Start Guide →](quickstart.md)** - Get up and running in 5 minutes
- **[Configuration →](configuration.md)** - Detailed setup and customization options

## Troubleshooting

### Common Issues

??? question "ImportError: No module named 'wyn360_cli'"
    This usually means the package wasn't installed correctly. Try:
    ```bash
    pip uninstall wyn360-cli
    pip install wyn360-cli
    ```

??? question "playwright command not found"
    Playwright binaries need to be installed separately:
    ```bash
    playwright install chromium
    ```
    If `playwright` command isn't found, try:
    ```bash
    python -m playwright install chromium
    ```

??? question "Permission denied errors"
    On some systems, you may need to install with user permissions:
    ```bash
    pip install --user wyn360-cli
    ```

??? question "Python version errors"
    Ensure you're using Python 3.10 or higher:
    ```bash
    python --version
    # Should show Python 3.10.x or higher
    ```

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/yiqiao-yin/wyn360-cli/issues) page
2. Search existing issues or create a new one
3. Include your Python version, OS, and error message

---

**Next:** [Quick Start Guide →](quickstart.md)