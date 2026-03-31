# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WYN360 CLI is a Python CLI tool (v0.3.80) that provides an AI-powered coding assistant using multiple LLM providers. Built with Click (CLI framework) and pydantic-ai (AI agent framework). Published on PyPI as `wyn360-cli`.

## Build & Development Commands

```bash
# Install dependencies (creates venv, installs all deps, editable mode)
poetry install

# Run the CLI
poetry run wyn360

# Run all tests (WYN360_SKIP_CONFIRM=1 suppresses command confirmation prompts)
WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v

# Run a single test file
poetry run pytest tests/test_agent.py -v

# Run a specific test class or method
poetry run pytest tests/test_utils.py::TestExecuteCommandSafe -v

# Run with coverage
poetry run pytest tests/ --cov=wyn360_cli --cov-report=html

# Build package
poetry build
```

## Architecture

### Entry Flow
`wyn360` CLI entry point -> `wyn360_cli/cli.py:main()` (Click) -> loads config -> initializes `WYN360Agent` -> runs async chat loop with slash command handling.

### Core Modules (`wyn360_cli/`)
- **`cli.py`** - Click CLI definition, slash commands (/clear, /history, /save, /load, /tokens, /model, /config), async chat loop
- **`agent.py`** - `WYN360Agent` class using pydantic-ai. Registers all tools (file ops, git, code execution, web search, browser, HuggingFace, GitHub). Routes to providers via `_get_client_choice()`: 1=Anthropic, 2=Bedrock, 3=Gemini, 4=OpenAI
- **`config.py`** - Three-tier config system: user (`~/.wyn360/config.yaml`) < project (`.wyn360.yaml`) < env vars (`WYN360_*`). Merges into `WYN360Config` dataclass
- **`utils.py`** - File operations, code parsing, safe command execution, performance metrics
- **`document_readers.py`** - Multi-format document processing (Excel/Word/PDF) with OCR, chunking, and embedding support
- **`browser_use.py`** / **`browser_controller.py`** - Website fetching with caching, Playwright-based browser automation
- **`session_manager.py`** - Conversation history persistence (JSON)
- **`credential_manager.py`** - Encrypted token storage for GitHub/HuggingFace
- **`vision_engine.py`** - Claude Vision API for image analysis

### Browser Tools (`wyn360_cli/tools/browser/`)
Modular browser automation subsystem with DOM analysis, screenshot-based fallback via Claude Vision, Stagehand integration, sandboxed Python execution, and intelligent error recovery. The orchestrator (`automation_orchestrator.py`) selects between DOM-first and screenshot approaches.

### Tool Registration Pattern
Tools are registered on the pydantic-ai agent using the `@agent.tool` decorator in `agent.py`.

## Configuration

Provider selection is interactive (prompted at startup) or set via environment:
- `ANTHROPIC_API_KEY` - Direct Anthropic API
- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_DEFAULT_REGION` - AWS Bedrock
- `GOOGLE_API_KEY` - Google Gemini
- `OPENAI_API_KEY` - OpenAI

## Documentation

Two doc systems coexist:
- **Primary**: `docusaurus-docs/` (Docusaurus + Node.js, deployed via `.github/workflows/deploy-docusaurus.yml`)
- **Legacy**: `docs/` + `mkdocs.yml` (MkDocs, deployed via `.github/workflows/docs-ai-prep.yml`)

Version is tracked in both `pyproject.toml` and `wyn360_cli/__init__.py`.
