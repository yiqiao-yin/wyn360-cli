# WYN360 CLI

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

An intelligent AI coding assistant that helps you build projects, generate code, and improve your codebase through natural language conversations.

[![PyPI version](https://badge.fury.io/py/wyn360-cli.svg)](https://pypi.org/project/wyn360-cli/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/yiqiao-yin/wyn360-cli/blob/main/LICENSE)

📚 **Documentation:** [https://yiqiao-yin.github.io/wyn360-cli/](https://yiqiao-yin.github.io/wyn360-cli/)
🚀 **Now powered by Docusaurus** with enhanced AI search capabilities!

🔗 **GitHub Repository:** [https://github.com/yiqiao-yin/wyn360-cli](https://github.com/yiqiao-yin/wyn360-cli)

## Why Choose WYN360 CLI?

- 🤖 **Interactive AI Assistant** - Natural language conversations with Claude
- 📝 **Code Generation** - Generate production-ready Python code from descriptions
- 🔍 **Project Analysis** - Understand and improve existing codebases
- ⚡ **Multi-Provider Support** - Anthropic Claude, AWS Bedrock, Google Gemini
- 🌐 **Web Integration** - Real-time search and autonomous browsing capabilities
- 📄 **Document Processing** - Read Excel, Word, PDF files with vision support
- 🔒 **Enterprise Ready** - Secure credential management and session handling

## Quick Start

### 1. Install
```bash
pip install wyn360-cli
```

### 2. Choose Your AI Provider

WYN360 CLI supports multiple AI providers:

<Tabs>
<TabItem value="anthropic" label="Anthropic Claude" default>

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

</TabItem>
<TabItem value="bedrock" label="AWS Bedrock">

**Why Bedrock?** Enterprise AWS integration, compliance features

**Setup:**
```bash
export CHOOSE_CLIENT=2
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token
export AWS_REGION=us-west-2
export ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-20250514-v1:0
```

**Requirements:** Valid AWS account with Bedrock access

</TabItem>
<TabItem value="gemini" label="Google Gemini (Recommended)">

**Why Gemini?** ~40x cheaper than Claude, 2M context window, fast performance

**Setup:**
```bash
export CHOOSE_CLIENT=3
export GEMINI_API_KEY=your_key_here
export GEMINI_MODEL=gemini-2.5-flash
```

**Get API Key:** [Google AI Studio](https://aistudio.google.com/apikey)

**Pricing:** $0.075 per million input tokens (vs $3.00 for Claude)

</TabItem>
<TabItem value="openai" label="OpenAI">

**Why OpenAI?** Industry-leading performance, competitive pricing, fast response times

**Setup:**
```bash
export CHOOSE_CLIENT=4
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o
```

**Get API Key:** [OpenAI Platform](https://platform.openai.com/api-keys)

**Available Models:**
- `gpt-4o` - Latest and most capable (default)
- `gpt-4` - Stable and reliable
- `gpt-3.5-turbo` - Fast and cost-effective

</TabItem>
<TabItem value="auto" label="Auto-Detection">

**Let WYN360 choose automatically** based on available credentials:

```bash
# Just set your preferred API key - no CHOOSE_CLIENT needed
export GEMINI_API_KEY=your_key_here
# System automatically detects and uses Gemini
```

**Priority order:**
1. `ANTHROPIC_API_KEY` → Use Anthropic
2. AWS credentials → Use Bedrock
3. `GEMINI_API_KEY` → Use Gemini
4. `OPENAI_API_KEY` → Use OpenAI

</TabItem>
</Tabs>

### 3. Start Chatting
```bash
wyn360
```

```
You: Build a Streamlit app for data visualization

WYN360: I'll create a Streamlit app for you...
[Generates complete code and saves to app.py]
```

[Get Started →](getting-started/installation)
[View Examples →](usage/use-cases)

## Core Capabilities

### 🤖 AI-Powered Development
- **Natural Language Interface** - Describe what you want in plain English
- **Code Generation** - From simple scripts to complete applications
- **Smart File Operations** - Context-aware file creation and updates
- **Intent Recognition** - Understands "update" vs "create new" automatically

### ⚡ Advanced Features
- **Real-Time Web Search** - Access current information and resources
- **Autonomous Browsing** - AI navigates websites and extracts data
- **Document Processing** - Read and analyze Excel, Word, PDF files
- **Vision Mode** - Process images, charts, and diagrams
- **GitHub Integration** - Commit, push, create PRs seamlessly
- **HuggingFace Deployment** - Deploy to Spaces with one command

### 🎯 Developer Experience
- **Multi-line Input** - Shift+Enter for newlines, Enter to submit
- **Streaming Responses** - See results as they're generated
- **Session Management** - Save/load conversations
- **Token Tracking** - Monitor usage and costs
- **Model Switching** - Change AI models mid-session

## Recent Updates

### v0.3.60 - Google Gemini Integration 🆕
- **New AI Provider**: Google Gemini support with 2M context window
- **Cost Effective**: ~40x cheaper than Claude ($0.075/M vs $3.00/M tokens)
- **All Tools Supported**: File ops, git, docs, browser automation
- **Auto-Detection**: Intelligent provider selection based on available credentials

### v0.3.52-56 - Autonomous Browsing 🚀
- **Vision-Powered Navigation**: AI "sees" and understands web pages
- **Multi-Step Tasks**: Complex workflows (search, filter, compare, extract)
- **Authenticated Sessions**: Works with saved login credentials
- **Error Resilient**: Automatic retry and timeout handling

### v0.3.30 - Vision Mode 👁️
- **Document Images**: Process charts, diagrams, screenshots in documents
- **AI-Powered OCR**: Extract insights from visual content
- **Cost Transparency**: Separate tracking for vision API usage

## Example Workflows

### Starting a New Project
```
You: Create a FastAPI app with authentication

WYN360:
✓ Generated main.py with FastAPI setup
✓ Created auth middleware
✓ Added example routes
✓ Provided setup instructions
```

### Research and Analysis
```
You: Find the latest Python web frameworks and compare them

WYN360: [Searches web for current information]

## Popular Python Web Frameworks (2025)

1. **FastAPI** ⭐ 76k stars - Modern, fast, OpenAPI support
2. **Django** ⭐ 79k stars - Batteries included, ORM, admin
3. **Flask** ⭐ 67k stars - Lightweight, flexible, minimal

[Provides detailed comparison with current data]
```

### Document Processing
```
You: Analyze quarterly_report.docx with vision mode

WYN360:
📊 Revenue Chart: Q4 shows 23% growth to $2.5M
📐 Architecture Diagram: 3-tier system (React → FastAPI → PostgreSQL)
💰 Vision Cost: $0.06 (2 images processed)

[Full document analysis with image insights]
```

## What's Next?

Explore the documentation to learn more about WYN360 CLI's capabilities:

- **[Getting Started](getting-started/installation.md)** - Installation and setup
- **[Features](features/overview.md)** - Complete feature overview
- **[Usage Examples](usage/use-cases.md)** - Real-world workflows
- **[Architecture](architecture/system.md)** - Technical deep dive

---

**Current Version:** 0.3.64
**Last Updated:** November 22, 2025