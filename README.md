# WYN360 CLI

An intelligent AI coding assistant CLI tool powered by Anthropic Claude.

## Installation

```bash
pip install wyn360-cli
```

## Usage

Set your Anthropic API key (choose one method):

**Option 1: Environment variable**
```bash
export ANTHROPIC_API_KEY=your_key_here
```

**Option 2: .env file (recommended for local development)**
```bash
# Create a .env file in your project directory
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

**Option 3: Command-line argument**
```bash
wyn360 --api-key your_key_here
```

Run the CLI:
```bash
wyn360
```

## Features

- Interactive chat interface with Claude
- Generate Python code from natural language
- Analyze and improve existing projects
- Automatic code extraction and file creation
- Context-aware project assistance

## Commands

- Type your request to chat with the assistant
- Type `exit` or `quit` to end the session

## Requirements

- Python >= 3.10
- Anthropic API key (get it from https://console.anthropic.com/)
