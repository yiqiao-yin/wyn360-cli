# WYN360 CLI

An intelligent AI coding assistant CLI tool powered by Anthropic Claude.

[![PyPI version](https://badge.fury.io/py/wyn360-cli.svg)](https://pypi.org/project/wyn360-cli/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

📚 **Documentation:** https://yiqiao-yin.github.io/wyn360-cli/

🔗 **GitHub Repository:** https://github.com/yiqiao-yin/wyn360-cli

## 📑 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Features](#-features)
  - [Core Capabilities](#core-capabilities)
  - [Intelligent Features](#intelligent-features-v02x)
  - [Context Management](#context-management-v028)
  - [Model Selection & Optimization](#model-selection--optimization-v030)
  - [Configuration & Personalization](#configuration--personalization-v031)
  - [Streaming Responses](#streaming-responses-v032)
  - [HuggingFace Integration](#huggingface-integration-v033---v0313)
  - [Automatic Test Generation](#automatic-test-generation-v0318)
  - [GitHub Integration](#github-integration-v0322)
  - [Web Search](#web-search-v0321-enhanced-v0323)
  - [Browser Use / Direct Website Fetching](#browser-use--direct-website-fetching-v0324)
  - [Vision Mode for Document Images](#vision-mode-for-document-images-v0330)
  - [Autonomous Vision-Based Browsing](#autonomous-vision-based-browsing-v0352---v0356-)
- [Usage Examples](#-usage-examples)
- [Commands](#-commands)
- [Documentation](#-documentation)
- [Development & Testing](#-development--testing)
- [Environment Variables](#-environment-variables)
- [Requirements](#-requirements)
- [Web Terminal](#web-terminal)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)
- [Acknowledgments](#-acknowledgments)
- [Links](#-links)

## 🎯 Overview

WYN360 CLI is an AI-powered coding assistant that helps you build projects, generate code, and improve your codebase through natural language conversations. Built with pydantic-ai and Anthropic Claude, it provides intelligent file operations, command execution, and context-aware assistance.

## 🏗️ System Architecture

For a detailed architecture overview including all components, layers, and data flows, see **[SYSTEM.md](docs/SYSTEM.md)**.

## 📦 Installation

### Basic Installation
```bash
pip install wyn360-cli
```

### Optional: Enable Browser Use (Direct Website Fetching)

If you want to use the `fetch_website` feature to read specific URLs directly:

```bash
# Install Playwright browser binaries (one-time setup, ~200MB)
playwright install chromium
```

**Note:** Browser use is optional. Web search and all other features work without it. Only install if you need direct URL fetching (e.g., "Read https://github.com/user/repo").

## 🚀 Quick Start

### 1. Choose your AI provider and set up credentials:

WYN360 CLI supports four AI providers. Choose one:

---

#### **Option 1: Anthropic Claude (Direct API)**

**Using environment variables:**
```bash
export CHOOSE_CLIENT=1
export ANTHROPIC_API_KEY=your_key_here
export ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**Using .env file (recommended):**
```bash
# Create .env file in your project directory
CHOOSE_CLIENT=1
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

**Get your API key:** [Anthropic Console](https://console.anthropic.com/)
**Available models:** See [Claude Model Overview](https://docs.claude.com/en/docs/about-claude/models/overview)

---

#### **Option 2: AWS Bedrock (Claude via AWS)**

**Using environment variables:**
```bash
export CHOOSE_CLIENT=2
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token
export AWS_REGION=us-west-2
export ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
```

**Using .env file (recommended):**
```bash
# Create .env file in your project directory
CHOOSE_CLIENT=2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=us-west-2
ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
```

**Requirements:** Valid AWS account with Bedrock access

---

#### **Option 3: Google Gemini** 🆕

**Using environment variables:**
```bash
export CHOOSE_CLIENT=3
export GEMINI_API_KEY=your_key_here
export GEMINI_MODEL=gemini-2.5-flash
```

**Using .env file (recommended):**
```bash
# Create .env file in your project directory
CHOOSE_CLIENT=3
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

**Get your API key:** [Google AI Studio](https://aistudio.google.com/apikey)
**Available models:** `gemini-2.5-flash` (fast, cheap), `gemini-2.5-pro` (powerful)
**Cost:** ~40x cheaper than Claude! ($0.075/M vs $3.00/M input tokens)

**Features:**
- ✅ All tools supported (file ops, git, docs, browser, etc.)
- ✅ 2M token context window (vs 200K for Claude)
- ✅ Fast and cost-effective
- ⚠️ Web search temporarily disabled (will be added as custom tool)

---

#### **Option 4: OpenAI** 🆕

**Using environment variables:**
```bash
export CHOOSE_CLIENT=4
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o
```

**Using .env file (recommended):**
```bash
# Create .env file in your project directory
CHOOSE_CLIENT=4
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o
```

**Get your API key:** [OpenAI Platform](https://platform.openai.com/api-keys)
**Available models:** `gpt-4o` (latest), `gpt-4` (stable), `gpt-3.5-turbo` (fast)
**Cost:** Competitive pricing with good performance

**Features:**
- ✅ All tools supported (file ops, git, docs, browser, etc.)
- ✅ 128K token context window
- ✅ Industry-leading performance
- ✅ Fast response times

---

#### **Auto-Detection (No CHOOSE_CLIENT)**

If you don't set `CHOOSE_CLIENT`, the system will auto-detect based on available credentials:

**Priority order:**
1. `ANTHROPIC_API_KEY` → Use Anthropic
2. AWS credentials → Use Bedrock
3. `GEMINI_API_KEY` → Use Google Gemini
4. `OPENAI_API_KEY` → Use OpenAI

```bash
# Just set your preferred API key
export GEMINI_API_KEY=your_key_here
# System will automatically use Gemini
``` 

### 2. Run the CLI:
```bash
wyn360
```

### 3. Start chatting:
```
You: Build a Streamlit app for data visualization

WYN360: I'll create a Streamlit app for you...
[Generates complete code and saves to app.py]
```

## ✨ Features

### Core Capabilities
- 🤖 **Interactive AI Assistant** - Natural language conversations with Claude
- 📝 **Code Generation** - Generate production-ready Python code from descriptions
- 🔍 **Project Analysis** - Understand and improve existing codebases
- 📁 **Smart File Operations** - Context-aware file creation and updates
- ⚡ **Command Execution** - Run Python scripts, UV commands, shell scripts, any CLI tool
- ⌨️ **Multi-line Input** - Press Enter to submit, Shift+Enter for newline
- 🔒 **Safety First** - Confirmation prompts before executing commands

### Intelligent Features (v0.2.x)
- 🧠 **Intent Recognition** - Understands "update" vs "create new" from natural language
- 🔄 **Context-Aware Updates** - Reads files before modifying them
- 🔁 **Self-Correcting** - Smart retry mechanism with 3 attempts
- ⏱️ **Timeout Protection** - Prevents infinite loops (5 min default)
- 📊 **Comprehensive Output** - Captures stdout, stderr, and exit codes

### Context Management (v0.2.8)
- 💬 **Conversation History** - Maintains context across multiple interactions
- 📊 **Token Tracking** - Real-time monitoring of API usage and costs
- 💾 **Session Save/Load** - Preserve conversations for later continuation
- 🎯 **Slash Commands** - Quick access to history, stats, and session management

### Model Selection & Optimization (v0.3.0)
- 🔄 **Dynamic Model Switching** - Switch between Haiku, Sonnet, and Opus mid-session
- 💰 **Cost Optimization** - Choose the right model for your task complexity
- 📊 **Model Information** - View current model, pricing, and capabilities
- ⚡ **Flexible Performance** - Balance between speed, capability, and cost

### Configuration & Personalization (v0.3.1)
- ⚙️ **User Configuration** - Personal preferences via `~/.wyn360/config.yaml`
- 📁 **Project Configuration** - Project-specific settings via `.wyn360.yaml`
- 🎯 **Custom Instructions** - Add your coding standards to every conversation
- 🏗️ **Project Context** - Help AI understand your tech stack automatically

### Streaming Responses (v0.3.2)
- ⚡ **Real-Time Output** - See responses as they're generated, token-by-token
- 🎯 **Immediate Feedback** - Start reading while AI is still generating
- 📺 **Progress Visibility** - Watch code and explanations appear in real-time
- 💨 **Faster Perceived Speed** - Feels 2-3x faster with instant feedback

### HuggingFace Integration (v0.3.3 - v0.3.13)
- 🤗 **HuggingFace Authentication** - Auto-login with HF_TOKEN environment variable
- 📝 **README Generation** - Create professional README files for Spaces
- 🚀 **Space Creation** - Create Streamlit/Gradio Spaces directly from CLI
- 📤 **File Upload** - Push your code to HuggingFace Spaces automatically
- 🎯 **One-Command Deploy** - From code to live Space in seconds

### Automatic Test Generation (v0.3.18)
- 🧪 **Test Generation** - Automatically generate pytest tests for Python files
- 📊 **Smart Analysis** - Analyzes functions and classes to create comprehensive tests
- ⚡ **Quick Setup** - Creates test files with proper structure and imports
- 🎯 **Code Coverage** - Generates tests for edge cases and error handling

### GitHub Integration (v0.3.22)
- 🔐 **GitHub Authentication** - Auto-login with GH_TOKEN/GITHUB_TOKEN
- 💾 **Commit & Push** - Stage, commit, and push changes with one command
- 🔀 **Pull Requests** - Create PRs with generated descriptions
- 🌿 **Branch Management** - Create, checkout, and merge branches seamlessly
- 🔄 **Merge Operations** - Smart branch merging with conflict detection

### Web Search (v0.3.21, Enhanced v0.3.23)
- 🔍 **Real-Time Search** - Access current information from the web
- 🌦️ **Weather Queries** - Get current weather for any location
- 🔗 **URL Reading** - Fetch and summarize web page content
- 📚 **Resource Finding** - Find GitHub repos, libraries, and tutorials
- 📊 **Current Data** - Latest package versions, documentation, and trends
- 💰 **Cost Effective** - Limited to 5 searches per session, $10 per 1K searches

### Browser Use / Direct Website Fetching (v0.3.24+)
- 🌐 **Direct URL Fetching** - Fetch specific websites directly (not just search results)
- 📄 **Full DOM Extraction** - Get complete page content, not just search snippets
- 🧠 **LLM-Optimized** - Automatic conversion to clean, structured markdown
- ⚡ **Smart Caching** - 30-minute TTL cache for faster repeated access
- 📏 **Smart Truncation** - Preserves document structure while staying under token limits
- 🎯 **Configurable** - Adjust max tokens, cache settings, truncation strategy
- 💾 **Cache Management** - View stats, clear cache, manage storage
- 🖥️ **Browser Debugging** - Use `--show-browser` flag or `WYN360_BROWSER_SHOW=1` to see automation in action
- 🔄 **Interactive Error Recovery** - LLM-assisted error analysis with intelligent recovery options when automation fails

### Vision Mode for Document Images (v0.3.30)
- 🖼️ **Image Processing** - Intelligently describe images in Word and PDF documents
- 📊 **Chart Recognition** - Extract insights from charts, graphs, and data visualizations
- 📐 **Diagram Understanding** - Analyze flowcharts, architecture diagrams, and technical illustrations
- 🖥️ **Screenshot Analysis** - Understand UI mockups and interface screenshots
- 💰 **Cost Transparency** - Separate tracking of vision API costs vs. text processing
- 🎯 **Three Processing Modes** - skip (default), describe (alt text only), vision (full AI processing)
- ⚡ **Batch Processing** - Efficient handling of documents with multiple images

### Autonomous Vision-Based Browsing (v0.3.52 - v0.3.56)
- 🤖 **Fully Autonomous** - Agent navigates websites and completes tasks without manual intervention
- 👁️ **Vision-Powered** - Uses Claude Vision API to "see" and understand web pages
- 🎯 **Multi-Step Tasks** - Handles complex workflows (search, filter, compare, extract)
- 🔗 **Tool Chaining** - Seamlessly integrates with WebSearchTool and login_to_website
- 🔒 **Authenticated Browsing** - Works with saved login sessions

### Agentic Features (v0.4.0) 🆕
- 🧠 **[Persistent Memory](https://yiqiao-yin.github.io/wyn360-cli/docs/features/agentic-memory)** - Cross-session memory with YAML frontmatter files and keyword relevance selection
- 🤖 **[Sub-Agent Workers](https://yiqiao-yin.github.io/wyn360-cli/docs/features/planning-and-agents)** - Spawn parallel pydantic-ai agents for concurrent research and verification
- 📋 **[Plan Mode](https://yiqiao-yin.github.io/wyn360-cli/docs/features/planning-and-agents)** - AI proactively enters plan mode for complex tasks, presents step-by-step plans for approval
- 🔄 **[Token Budget Auto-Continue](https://yiqiao-yin.github.io/wyn360-cli/docs/features/hooks-and-budget)** - Automatically continues responses cut off by max_tokens
- ⚡ **[Extensible Skills](https://yiqiao-yin.github.io/wyn360-cli/docs/features/agentic-memory)** - User-defined slash commands via YAML files in `~/.wyn360/skills/`
- 🔧 **[Hook System](https://yiqiao-yin.github.io/wyn360-cli/docs/features/hooks-and-budget)** - Pre/post response hooks with built-in safety checks (runs automatically)

### Advanced Agentic Features (v0.5.0) 🆕
- 💤 **[Dream System](https://yiqiao-yin.github.io/wyn360-cli/docs/features/dream-and-compaction)** - Background memory consolidation reviews recent sessions automatically
- 📦 **[Context Compaction](https://yiqiao-yin.github.io/wyn360-cli/docs/features/dream-and-compaction)** - Auto-drops old messages when conversation exceeds 50 messages
- ⌨️ **[Vim Mode](https://yiqiao-yin.github.io/wyn360-cli/docs/features/vim-voice-buddy)** - Vi-style editing in the terminal (toggle with `/vim`)
- 🎙️ **[Voice Input](https://yiqiao-yin.github.io/wyn360-cli/docs/features/vim-voice-buddy)** - Speech-to-text via Google (free) or OpenAI Whisper
- 🐱 **[Buddy Companion](https://yiqiao-yin.github.io/wyn360-cli/docs/features/vim-voice-buddy)** - Virtual pet with species, rarity, personality, and event reactions
- ⏰ **[Cron Agents](https://yiqiao-yin.github.io/wyn360-cli/docs/features/cron-plugins-lsp)** - Schedule recurring background tasks (e.g., monitor CI every 5 minutes)
- 🔌 **[Plugin System](https://yiqiao-yin.github.io/wyn360-cli/docs/features/cron-plugins-lsp)** - Install/create plugins in `~/.wyn360/plugins/` with YAML manifests
- 🔍 **[LSP Diagnostics](https://yiqiao-yin.github.io/wyn360-cli/docs/features/cron-plugins-lsp)** - Run pyright/ruff diagnostics with `/diagnostics`
- ⏪ **[Rewind](https://yiqiao-yin.github.io/wyn360-cli/docs/features/cron-plugins-lsp)** - Undo mistakes by reverting to previous conversation states

## 🎮 Usage Examples

### Starting a New Project
```
You: Create a FastAPI app with authentication

WYN360:
- Generates main.py with FastAPI setup
- Creates auth middleware
- Adds example routes
- Provides setup instructions
```

### Updating Existing Code
```
You: Add logging to my script.py

WYN360:
- Reads current script.py
- Adds logging configuration
- Updates functions with log statements
- Preserves existing functionality
```

### Executing Commands
```
You: Run the analysis script

WYN360: [Generates the command to run]

======================================================================
⚠️  COMMAND EXECUTION CONFIRMATION
======================================================================
Command: python analysis.py
Directory: /current/working/directory
Permissions: Full user permissions
======================================================================

>>> WAITING FOR YOUR RESPONSE <<<

Execute this command? (y/N): y

✅ Command executed successfully
[Shows output]
```

**Note:** When you see the confirmation prompt, the "thinking" spinner may still appear in the background. This is normal - just type `y` and press Enter to proceed, or `N` to cancel.

### Web Search & Resource Finding
```
You: Find a popular GitHub repo for machine learning

WYN360: [Searches the web]

Here are some popular GitHub repositories for machine learning:

1. **tensorflow/tensorflow** ⭐ 185k stars
   https://github.com/tensorflow/tensorflow
   - End-to-end machine learning platform
   - Used by Google and industry leaders

2. **pytorch/pytorch** ⭐ 82k stars
   https://github.com/pytorch/pytorch
   - Deep learning framework by Meta
   - Popular in research and production

3. **scikit-learn/scikit-learn** ⭐ 59k stars
   https://github.com/scikit-learn/scikit-learn
   - Classic ML algorithms for Python
   - Great for beginners and experts

[Sources: GitHub search results, updated recently]
```

```
You: What's the weather in San Francisco?

WYN360: [Searches for current weather]

Current weather in San Francisco:
🌤️ 62°F (17°C), Partly cloudy
💨 Wind: 12 mph
💧 Humidity: 65%
🌅 Sunrise: 7:15 AM | Sunset: 5:02 PM

Source: [Weather service URL]
```

### Direct Website Fetching
```
You: Read https://github.com/yiqiao-yin/deepspeed-course

WYN360: [Fetches the specific URL directly]

📄 **Fetched:** https://github.com/yiqiao-yin/deepspeed-course

# DeepSpeed Course Repository

## Overview
This repository contains comprehensive course materials for DeepSpeed training...

## Course Contents
1. **Distributed Training** - Multi-GPU training strategies
2. **Memory Optimization** - ZeRO optimization techniques
3. **Pipeline Parallelism** - Efficient model parallelism
4. **Performance Tuning** - Best practices and optimizations

[Full page content extracted and converted to markdown]
```

**When to use what:**
- **fetch_website**: When you have a specific URL → `Read https://example.com`
- **Web Search**: When you want to find something → `Find ML repos`

```
You: Show cache stats

WYN360: 📊 **Website Cache Statistics**

**Location:** `~/.wyn360/cache/fetched_sites`

**Total Entries:** 3
**Total Size:** 2.4 MB
**Expired Entries:** 0

**Cached URLs:**
- ✓ 5m old: https://github.com/yiqiao-yin/deepspeed-course
- ✓ 12m old: https://python.org/downloads
- ✓ 25m old: https://docs.anthropic.com
```

### Document Reading with Vision Mode
```
You: Read quarterly_report.docx with vision mode

WYN360: [Extracts and processes document with image descriptions]

# Quarterly Report Summary

## Executive Overview
Revenue increased by 23% year-over-year, driven by strong performance in...

📊 **[Image 1]:** Bar chart showing quarterly revenue growth from Q1 to Q4.
Q4 shows the highest revenue at approximately $2.5M, representing a 23%
increase from Q3. All quarters show positive growth compared to the previous year.

## Market Analysis
Our market share expanded across all regions...

📐 **[Image 2]:** System architecture diagram depicting three layers:
frontend (React), API layer (FastAPI), and database (PostgreSQL).
Shows data flow from user requests through authentication middleware
to the backend services.

💰 **Vision API Cost:** $0.06 (2 images processed)
📊 **Token Usage:** 1,175 input tokens, 125 output tokens

[Use /tokens to see detailed cost breakdown]
```

**Image Handling Modes:**
- `skip` (default) - Ignore images entirely, no API calls
- `describe` - Extract alt text and captions only (no API calls)
- `vision` - Full Claude Vision API processing (costs ~$0.01-0.05 per image)

## 🎯 Commands

### Chat Commands

| Command | Description |
|---------|-------------|
| `<message>` | Chat with the AI assistant |
| `Enter` | Submit your message |
| `Ctrl+Enter` | Add a new line (multi-line input) |
| `exit` or `quit` | End the session |

### Slash Commands

| Command | Description | Version |
|---------|-------------|---------|
| `/clear` | Clear conversation history and reset counters | v0.2.8 |
| `/history` | Display conversation history | v0.2.8 |
| `/save <file>` | Save session to JSON | v0.2.8 |
| `/load <file>` | Load session from JSON | v0.2.8 |
| `/tokens` | Show token usage and costs | v0.2.8 |
| `/model [name]` | Show/switch model (haiku/sonnet/opus) | v0.3.0 |
| `/config` | Show current configuration | v0.3.1 |
| `/help` | Display help | v0.2.8 |
| `/memory [list\|save\|search\|delete]` | Manage persistent memories | v0.4.0 |
| `/plan [approve\|reject\|skip\|status]` | Manage execution plans | v0.4.0 |
| `/skills` | List custom skills | v0.4.0 |
| `/hooks` | Show registered hooks and stats | v0.4.0 |
| `/workers` | Show sub-agent task status | v0.4.0 |
| `/budget` | Show token budget stats | v0.4.0 |
| `/dream` | Show dream consolidation status | v0.5.0 |
| `/compact` | Show context compaction stats | v0.5.0 |
| `/vim` | Toggle vim editing mode | v0.5.0 |
| `/voice` | Toggle voice input | v0.5.0 |
| `/buddy` | Toggle virtual companion | v0.5.0 |
| `/cron [add\|delete\|pause\|resume]` | Manage scheduled jobs | v0.5.0 |
| `/plugins [create\|install\|uninstall\|reload]` | Manage plugins | v0.5.0 |
| `/diagnostics` | Run pyright/ruff diagnostics | v0.5.0 |
| `/rewind [undo\|<id>]` | Revert conversation state | v0.5.0 |

**Example Usage:**
```
You: Write a data analysis script
WYN360: [Creates analysis.py]

You: /tokens
[Shows token usage: 1,500 input tokens, 800 output tokens, $0.02 cost]

You: /model
[Shows current model: Sonnet 4, pricing: $3.00/$15.00 per M tokens]

You: /model haiku
✓ Switched to Haiku (claude-3-5-haiku-20241022)

You: /save my_analysis_session.json
✓ Session saved to: my_analysis_session.json

You: /clear
✓ Conversation history cleared. Token counters reset.

You: /load my_analysis_session.json
✓ Session loaded from: my_analysis_session.json
```

## 📚 Documentation

**Full documentation:** https://yiqiao-yin.github.io/wyn360-cli/docs/

Key pages:
- **[Features Overview](https://yiqiao-yin.github.io/wyn360-cli/docs/features/overview)** - All features with comparisons
- **[Memory & Skills](https://yiqiao-yin.github.io/wyn360-cli/docs/features/agentic-memory)** - Persistent memory and custom commands
- **[Planning & Sub-Agents](https://yiqiao-yin.github.io/wyn360-cli/docs/features/planning-and-agents)** - Plan mode and parallel workers
- **[Hooks & Token Budget](https://yiqiao-yin.github.io/wyn360-cli/docs/features/hooks-and-budget)** - Pipeline hooks and auto-continue
- **[Dream & Compaction](https://yiqiao-yin.github.io/wyn360-cli/docs/features/dream-and-compaction)** - Background memory consolidation
- **[Vim, Voice & Buddy](https://yiqiao-yin.github.io/wyn360-cli/docs/features/vim-voice-buddy)** - Input modes and companion
- **[Cron, Plugins & LSP](https://yiqiao-yin.github.io/wyn360-cli/docs/features/cron-plugins-lsp)** - Scheduled agents, plugins, diagnostics, rewind
- **[System Architecture](https://yiqiao-yin.github.io/wyn360-cli/docs/architecture/system)** - Architecture overview with diagrams
- **[Commands Reference](https://yiqiao-yin.github.io/wyn360-cli/docs/usage/commands)** - All slash commands

## 🛠️ Development & Testing

### Prerequisites

- Python >= 3.10
- Poetry (package manager)
- Anthropic API key

### Setting Up Development Environment

1. **Clone the repository:**
```bash
git clone https://github.com/yiqiao-yin/wyn360-cli.git
cd wyn360-cli
```

2. **Install Poetry** (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies:**
```bash
poetry install
```

This will:
- Create a virtual environment
- Install all production dependencies from `pyproject.toml`
- Install development dependencies (pytest, pytest-asyncio, pytest-mock)
- Install the package in editable mode

### Running Tests

**Run all tests with verbose output:**
```bash
# Skip command confirmation prompts in tests
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
```

**Run tests with short traceback:**
```bash
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v --tb=short
```

**Run specific test file:**
```bash
poetry run pytest tests/test_agent.py -v
```

**Run specific test class:**
```bash
poetry run pytest tests/test_utils.py::TestExecuteCommandSafe -v
```

**Run with coverage report:**
```bash
poetry run pytest tests/ --cov=wyn360_cli --cov-report=html
```

### Test Structure

```
tests/
├── __init__.py
├── test_agent.py          # Agent and tool tests (93 tests)
├── test_cli.py            # CLI and slash command tests (33 tests)
├── test_config.py         # Configuration tests (25 tests)
├── test_utils.py          # Utility function tests (29 tests)
├── test_memory.py         # Memory system tests (14 tests)
├── test_subagent.py       # Sub-agent worker tests (14 tests)
├── test_planner.py        # Plan mode tests (26 tests)
├── test_token_budget.py   # Token budget tests (12 tests)
├── test_skills.py         # Skills system tests (13 tests)
├── test_hooks.py          # Hook system tests (20 tests)
├── test_dream.py          # Dream consolidation tests (11 tests)
└── test_v050_features.py  # Compaction, vim, voice, buddy, cron,
                           # plugins, LSP, rewind tests (62 tests)
                           # Total: 333+ tests
```

### Expected Output

When all tests pass, you should see:
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
tests/test_agent.py::TestStreaming::test_chat_stream_method_exists PASSED [ 40%]
tests/test_cli.py::TestSlashCommands::test_clear_command PASSED          [ 42%]
tests/test_config.py::TestWYN360Config::test_default_values PASSED       [ 60%]
...
tests/test_utils.py::TestExecuteCommandSafe::test_execute_python_script PASSED [100%]

============================== 133 passed in 2.64s
```

### Building and Publishing

**Build the package:**
```bash
poetry build
```

This creates:
- `dist/wyn360_cli-X.Y.Z.tar.gz` (source distribution)
- `dist/wyn360_cli-X.Y.Z-py3-none-any.whl` (wheel)

**Publish to PyPI:**
```bash
poetry publish
```

**Build and publish in one command:**
```bash
poetry build && poetry publish
```

### Version Management

Update version in these files:
- `pyproject.toml` - `version = "X.Y.Z"`
- `wyn360_cli/__init__.py` - `__version__ = "X.Y.Z"`
- `USE_CASES.md` - Update changelog and version number

### Development Workflow

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and test:**
```bash
# Make your changes
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v
```

3. **Update version and documentation:**
```bash
# Update version in pyproject.toml, __init__.py, USE_CASES.md
```

4. **Commit and push:**
```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

5. **Build and publish:**
```bash
poetry build && poetry publish
git push origin main
```

## 🧪 Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `CHOOSE_CLIENT` | AI provider selection: `1`=Anthropic, `2`=Bedrock, `3`=Gemini, `0`=Auto-detect | `0` (auto) |
| `MAX_TOKEN` | Maximum tokens for model output (can also use `--max-token` CLI arg) | `4096` |
| `MAX_INTERNET_SEARCH_LIMIT` | Maximum web searches per session (can also use `--max-internet-search-limit` CLI arg) | `5` |
| `WYN360_SKIP_CONFIRM` | Skip command execution confirmations | `0` (disabled) |
| `WYN360_BROWSER_SHOW` | Show browser window during automation (can also use `--show-browser` CLI arg) | `0` (headless) |

### Anthropic Claude (CHOOSE_CLIENT=1)

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | None (required) |
| `ANTHROPIC_MODEL` | Model to use (e.g., claude-sonnet-4-20250514) | Auto-selected |

### Google Gemini (CHOOSE_CLIENT=3) 🆕

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Google Gemini API key | None (required) |
| `GEMINI_MODEL` | Model to use (e.g., gemini-2.5-flash, gemini-2.5-pro) | `gemini-2.5-flash` |

### AWS Bedrock (CHOOSE_CLIENT=2)

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key ID | None (required) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key | None (required) |
| `AWS_SESSION_TOKEN` | AWS session token (optional, for temporary credentials) | None |
| `AWS_REGION` | AWS region for Bedrock (e.g., us-west-2) | `us-east-1` |
| `ANTHROPIC_MODEL` | Model ARN (e.g., us.anthropic.claude-sonnet-4-20250514-v1:0) | Auto-selected |

### Integration Tokens (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` or `HUGGINGFACE_TOKEN` | HuggingFace API token (for HF features) | None |
| `GH_TOKEN` or `GITHUB_TOKEN` | GitHub access token (for GitHub features) | None |

**Setup Example (Anthropic API):**
```bash
# .env file
CHOOSE_CLIENT=1
ANTHROPIC_API_KEY=your_anthropic_key
MAX_TOKEN=4096
MAX_INTERNET_SEARCH_LIMIT=5
GH_TOKEN=ghp_your_github_token
HF_TOKEN=hf_your_huggingface_token
WYN360_SKIP_CONFIRM=0
WYN360_BROWSER_SHOW=0
```

**Setup Example (Google Gemini):** 🆕
```bash
# .env file
CHOOSE_CLIENT=3
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
MAX_TOKEN=4096
GH_TOKEN=ghp_your_github_token
HF_TOKEN=hf_your_huggingface_token
WYN360_SKIP_CONFIRM=0
WYN360_BROWSER_SHOW=0
```

**Setup Example (AWS Bedrock):**
```bash
# .env file
CHOOSE_CLIENT=2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=us-west-2
ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
MAX_TOKEN=4096
GH_TOKEN=ghp_your_github_token
HF_TOKEN=hf_your_huggingface_token
WYN360_SKIP_CONFIRM=0
WYN360_BROWSER_SHOW=0
```

**Notes:**
- Set `CHOOSE_CLIENT=0` (or omit it) for auto-detection based on available API keys
- Set `WYN360_SKIP_CONFIRM=1` to skip confirmation prompts (useful for testing or automation)
- Set `WYN360_BROWSER_SHOW=1` to show browser window during automation (useful for debugging)
- Gemini is ~40x cheaper than Claude and has 2M context window!

## 📋 Requirements

- Python >= 3.10, < 4.0
- Dependencies (automatically installed):
  - `click>=8.1.0` - CLI framework
  - `pydantic-ai>=1.13.0` - AI agent framework with web search support
  - `anthropic>=0.39.0` - Anthropic API client
  - `rich>=13.0.0` - Terminal formatting
  - `python-dotenv>=1.2.1` - Environment variable management
  - `prompt-toolkit>=3.0.0` - Advanced input handling
  - `pyyaml>=6.0.0` - Configuration file support
  - `huggingface-hub>=0.20.0` - HuggingFace integration
  - `crawl4ai>=0.7.6` - LLM-optimized web crawler for browser use

**Note:** Browser use requires Playwright browser binaries (~200MB):
```bash
playwright install chromium
```

## Web Terminal

WYN360 is also available as a browser-based terminal at:

**https://wyn360terminal-app.azurewebsites.net**

This is a real Linux terminal running in your browser with `wyn360` pre-installed. No account or login required -- just open the URL and start using it.

### Usage

1. Open the terminal URL in your browser
2. Export your API key:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
3. Launch the assistant:
   ```bash
   wyn360
   ```

All four AI providers are supported (Anthropic, AWS Bedrock, Google Gemini, OpenAI). Your API keys are never stored on the server -- they only exist in your browser terminal session and are discarded when you close the tab.

### Self-Hosting

To deploy your own instance, you need Docker and Azure CLI:

```bash
az login
bash deploy-azure.sh
```

This creates four Azure resources (all prefixed `wyn360terminal`):

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `wyn360terminal-rg` | Container for all resources |
| Container Registry | `wyn360terminalacr` | Stores the Docker image |
| App Service Plan | `wyn360terminal-plan` (B1) | Compute for the web app |
| Web App | `wyn360terminal-app` | Serves the terminal UI |

The container uses [ttyd](https://github.com/tsl0922/ttyd) to expose a bash shell over WebSocket, with `wyn360` pre-installed. No secrets are baked into the image.

To tear down:
```bash
az group delete --name wyn360terminal-rg --yes
```

### Related Files

- `Dockerfile.web` -- Container image definition
- `deploy-azure.sh` -- Azure deployment script
- `terminal-motd.sh` -- Welcome message shown on terminal connect
- `docker-compose.web.yml` -- Local development with Docker Compose

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v`)
4. Commit your changes (`git commit -m 'feat: add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Yiqiao Yin**
- Email: yiqiao.yin@wyn-associates.com
- GitHub: [@yiqiao-yin](https://github.com/yiqiao-yin)

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/claude) - Advanced AI assistant
- Powered by [pydantic-ai](https://github.com/pydantic/pydantic-ai) - Python agent framework
- CLI framework by [Click](https://click.palletsprojects.com/)
- Terminal UI by [Rich](https://rich.readthedocs.io/)

## 🔗 Links

- **PyPI:** https://pypi.org/project/wyn360-cli/
- **GitHub:** https://github.com/yiqiao-yin/wyn360-cli
- **Documentation:**
  - [USE_CASES.md](docs/USE_CASES.md) - Usage examples and workflows
  - [COST.md](docs/COST.md) - Pricing and token configuration
  - [SYSTEM.md](docs/SYSTEM.md) - Architecture overview
- **Get API Key:** https://console.anthropic.com/

---

**Current Version:** 0.5.3
**Last Updated:** April 2026
