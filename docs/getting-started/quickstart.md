# Quick Start Guide

Get up and running with WYN360 CLI in under 5 minutes!

## Step 1: Choose Your AI Provider

WYN360 CLI supports three AI providers. Choose the one that works best for you:

=== "Google Gemini (Recommended)"

    **Why Gemini?** ~40x cheaper than Claude, 2M context window, fast performance

    **Setup:**
    ```bash
    export CHOOSE_CLIENT=3
    export GEMINI_API_KEY=your_key_here
    export GEMINI_MODEL=gemini-2.5-flash
    ```

    **Get API Key:** [Google AI Studio](https://aistudio.google.com/apikey)

    **Pricing:** $0.075 per million input tokens (vs $3.00 for Claude)

=== "Anthropic Claude"

    **Why Claude?** Most capable, excellent for complex coding tasks

    **Setup:**
    ```bash
    export CHOOSE_CLIENT=1
    export ANTHROPIC_API_KEY=your_key_here
    export ANTHROPIC_MODEL=claude-sonnet-4-20250514
    ```

    **Get API Key:** [Anthropic Console](https://console.anthropic.com/)

    **Available Models:**
    - `claude-sonnet-4-20250514` - Most capable (default)
    - `claude-3-5-haiku-20241022` - Fastest and cheapest
    - `claude-opus-4-1-20250805` - Most powerful

=== "AWS Bedrock"

    **Why Bedrock?** Enterprise AWS integration, compliance features

    **Setup:**
    ```bash
    export CHOOSE_CLIENT=2
    export AWS_ACCESS_KEY_ID=your_access_key
    export AWS_SECRET_ACCESS_KEY=your_secret_key
    export AWS_REGION=us-west-2
    export ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
    ```

    **Requirements:** Valid AWS account with Bedrock access

=== "Auto-Detection"

    **Let WYN360 choose automatically** based on available credentials:

    ```bash
    # Just set your preferred API key - no CHOOSE_CLIENT needed
    export GEMINI_API_KEY=your_key_here
    # System automatically detects and uses Gemini
    ```

    **Priority order:**
    1. `ANTHROPIC_API_KEY` → Use Anthropic
    2. `GEMINI_API_KEY` → Use Gemini
    3. AWS credentials → Use Bedrock

## Step 2: Set Up Environment

### Option A: Using .env File (Recommended)

Create a `.env` file in your project directory:

```bash
# .env file - choose one provider
CHOOSE_CLIENT=3
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
MAX_TOKEN=4096
MAX_INTERNET_SEARCH_LIMIT=5
```

### Option B: Using Environment Variables

```bash
export CHOOSE_CLIENT=3
export GEMINI_API_KEY=your_gemini_key
export GEMINI_MODEL=gemini-2.5-flash
```

### Additional Configuration (Optional)

```bash
# Token limits
export MAX_TOKEN=4096
export MAX_INTERNET_SEARCH_LIMIT=5

# Integration tokens (optional)
export GH_TOKEN=ghp_your_github_token        # For GitHub features
export HF_TOKEN=hf_your_huggingface_token    # For HuggingFace features

# Skip confirmations (useful for automation)
export WYN360_SKIP_CONFIRM=0
```

## Step 3: Start WYN360 CLI

```bash
wyn360
```

You should see:

```
🤖 WYN360 CLI v0.3.60
🔍 AI Provider: Google Gemini (gemini-2.5-flash)
💡 Model: gemini-2.5-flash | Context: 2M tokens
💰 Cost: $0.075/$0.30 per M tokens (input/output)

Type your message (Shift+Enter for newline, Enter to send, 'exit' to quit):
You:
```

## Step 4: Try Your First Commands

### Basic Chat
```
You: Hello! Can you help me create a Python function?

WYN360: Hello! I'd be happy to help you create a Python function.
What kind of function would you like me to create for you?
```

### Code Generation
```
You: Create a function that calculates the factorial of a number

WYN360: I'll create a factorial function for you.

[Creates factorial.py with the function and saves it]

✓ Created factorial.py with factorial function
✓ Added error handling for negative numbers
✓ Included docstring and example usage
```

### Project Analysis
```
You: List all Python files in this project

WYN360: [Scans directory]

📁 **Python Files Found:**
- `wyn360_cli/cli.py` (840 lines)
- `wyn360_cli/agent.py` (4,259 lines)
- `wyn360_cli/config.py` (308 lines)
- `tests/test_agent.py` (46 tests)
[... complete listing]
```

## Step 5: Explore Slash Commands

WYN360 CLI includes powerful slash commands for session management:

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show all available commands | `/help` |
| `/model` | Show current model or switch | `/model haiku` |
| `/tokens` | Show token usage and costs | `/tokens` |
| `/history` | Display conversation history | `/history` |
| `/save <file>` | Save session to file | `/save my_session.json` |
| `/load <file>` | Load session from file | `/load my_session.json` |
| `/clear` | Clear history and reset | `/clear` |
| `/config` | Show current configuration | `/config` |

### Example Session Management
```
You: Create a web scraper for Python packages

WYN360: [Creates scraper.py with full implementation]

You: /save scraper_session.json
✓ Session saved to: scraper_session.json

You: /tokens
📊 **Token Usage This Session**
Input: 1,245 tokens | Output: 892 tokens
💰 Cost: $0.002 | Model: gemini-2.5-flash

You: /model
🤖 **Current Model: gemini-2.5-flash**
💰 Pricing: $0.075/$0.30 per M tokens (input/output)
📊 Context Window: 2M tokens
🔧 Max Output: 4096 tokens
```

## Common First Tasks

### File Operations
```
You: Read the contents of config.py
You: Update main.py to add logging
You: Create a new FastAPI app in app.py
You: Delete the old backup files
```

### Development Workflow
```
You: Run the tests for this project
You: Check git status and show me what's changed
You: Install the requirements from requirements.txt
You: Create a virtual environment and activate it
```

### Web and Research
```
You: Search for the latest Python web frameworks
You: Read https://docs.python.org/3/tutorial/
You: Find GitHub repositories for machine learning
You: What's the current weather in San Francisco?
```

## Next Steps

Now that you're set up, explore these advanced features:

- **[Configuration →](configuration.md)** - Customize WYN360 for your workflow
- **[Features Overview →](../features/overview.md)** - Discover all capabilities
- **[Usage Examples →](../usage/use-cases.md)** - Real-world workflows and examples
- **[Cost Management →](../usage/cost.md)** - Optimize token usage and costs

## Quick Tips

!!! tip "Multi-line Input"
    - **Enter** = Submit message
    - **Shift+Enter** = Add new line
    - **Ctrl+C** = Cancel current input

!!! tip "Cost Optimization"
    - Use Gemini for cost-effective operations
    - Switch to Claude for complex reasoning tasks
    - Use `/model haiku` for simple tasks
    - Monitor usage with `/tokens`

!!! tip "Session Management"
    - Save important conversations with `/save`
    - Use `/clear` to reset token counters
    - Load previous sessions with `/load`

---

**Next:** [Configuration Guide →](configuration.md)