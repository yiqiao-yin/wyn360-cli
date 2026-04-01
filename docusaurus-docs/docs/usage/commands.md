# Commands Reference

Complete reference for WYN360 CLI commands and slash commands.

## Chat Commands

| Command | Description |
|---------|-------------|
| `<message>` | Chat with the AI assistant |
| `Enter` | Submit your message |
| `Shift+Enter` | Add a new line (multi-line input) |
| `exit` or `quit` | End the session |

## Slash Commands

### Session Management

| Command | Description | Example |
|---------|-------------|---------|
| `/clear` | Clear conversation history and reset token counters | `/clear` |
| `/history` | Display conversation history in a table | `/history` |
| `/save <file>` | Save current session to JSON file | `/save analysis_session.json` |
| `/load <file>` | Load session from JSON file | `/load analysis_session.json` |

### Model & Configuration

| Command | Description | Example |
|---------|-------------|---------|
| `/model [name]` | Show current model info or switch models | `/model haiku` |
| `/tokens` | Show detailed token usage statistics and costs | `/tokens` |
| `/config` | Show current configuration | `/config` |

### Agentic Features (v0.4.0)

| Command | Description | Example |
|---------|-------------|---------|
| `/memory list` | List all stored memories | `/memory list` |
| `/memory save <type> <name> \| <content>` | Save a new memory | `/memory save user my_role \| Backend engineer` |
| `/memory search <query>` | Search memories by keyword | `/memory search python style` |
| `/memory delete <file>` | Delete a memory | `/memory delete user_my_role.md` |
| `/plan` | Show current plan status | `/plan` |
| `/plan approve` | Approve plan for execution | `/plan approve` |
| `/plan reject` | Reject and discard current plan | `/plan reject` |
| `/plan skip` | Skip the current plan step | `/plan skip` |
| `/skills` | List available custom skills | `/skills` |
| `/hooks` | Show registered hooks and stats | `/hooks` |
| `/workers` | Show sub-agent task status | `/workers` |
| `/budget` | Show token budget statistics | `/budget` |
| `/dream` | Show dream consolidation status | `/dream` |
| `/compact` | Show context compaction stats | `/compact` |
| `/vim` | Toggle vim editing mode | `/vim` |
| `/voice` | Toggle voice input | `/voice` |
| `/buddy` | Toggle virtual companion | `/buddy` |
| `/cron` | List/manage scheduled jobs | `/cron add 5m CI | gh run list` |
| `/plugins` | List/manage plugins | `/plugins create my-tool` |
| `/diagnostics` | Run linting/type checks | `/diagnostics src/` |
| `/rewind` | View/restore conversation snapshots | `/rewind undo` |

### Help & Information

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Display help message with all commands | `/help` |

## Model Names

Use these names with the `/model` command:

### Anthropic Claude
- `sonnet` - Claude Sonnet 4 (most capable)
- `haiku` - Claude 3.5 Haiku (fastest, cheapest)
- `opus` - Claude Opus 4 (most powerful)

### Google Gemini
- `gemini-2.5-flash` - Fast and cost-effective
- `gemini-2.5-pro` - More powerful

## CLI Arguments

When starting WYN360:

```bash
wyn360 [OPTIONS]

Options:
  --max-token INTEGER             Maximum tokens for model output
  --max-internet-search-limit INTEGER  Maximum internet searches per session
  --help                          Show help message and exit
```

## Examples

### Basic Usage
```bash
# Start with default settings
wyn360

# Start with custom token limit
wyn360 --max-token 8192

# Start with more search quota
wyn360 --max-internet-search-limit 10
```

### Session Management
```
You: Write a data analysis script
WYN360: [Creates analysis.py]

You: /save data_analysis_session.json
✓ Session saved to: data_analysis_session.json

You: /tokens
📊 **Token Usage This Session**
Input: 1,500 tokens | Output: 800 tokens
💰 Cost: $0.02 | Model: claude-sonnet-4

You: /clear
✓ Conversation history cleared. Token counters reset.

You: /load data_analysis_session.json
✓ Session loaded from: data_analysis_session.json
```

### Model Switching
```
You: /model
🤖 **Current Model: claude-sonnet-4-20250514**
💰 Pricing: $3.00/$15.00 per M tokens (input/output)
📊 Context Window: 200K tokens

You: /model haiku
✓ Switched to Claude 3.5 Haiku (claude-3-5-haiku-20241022)
💰 New pricing: $0.25/$1.25 per M tokens

You: /model gemini-2.5-flash
✓ Switched to Google Gemini (gemini-2.5-flash)
💰 New pricing: $0.075/$0.30 per M tokens
📊 Context Window: 2M tokens
```

For more examples, see [Usage Examples](use-cases.md).