# Hooks & Token Budget

*New in v0.4.0*

WYN360 CLI provides a hook system for customizing the request/response pipeline and a token budget manager that automatically continues responses cut short by token limits.

---

## Hook System

Hooks are functions that run **automatically** at specific points in every request/response cycle. You don't trigger them — they fire on their own every time you send a message or the AI responds. Think of them as invisible middleware that watches everything flowing through the pipeline.

### How Hooks Are Triggered

**You do nothing.** Hooks run automatically:

```
You type a message
  → pre_query hooks fire (validate/transform your message)
    → Message sent to AI
      → AI calls a tool (e.g., read_file)
        → pre_tool hooks fire (can block the tool)
        → Tool executes
        → post_tool hooks fire (track results)
      → AI generates response
    → post_response hooks fire (filter/log the response)
  → You see the response

If anything crashes → on_error hooks fire
```

Every message, every response, every tool call — hooks are watching. The built-in hooks are already running from the moment you start a session.

### Hook Points

| Hook Point | Fires automatically... | Every... | Use Case |
|------------|----------------------|----------|----------|
| `pre_query` | When you press Enter | Message you send | Input validation, message transformation |
| `post_response` | When AI finishes responding | AI response | Response filtering, logging |
| `pre_tool` | When AI is about to use a tool | Tool call | Block dangerous operations |
| `post_tool` | When a tool finishes | Tool call | Track tool usage, validate results |
| `on_error` | When something crashes | Error | Error reporting, recovery |

### Built-in Hooks (Always Running)

WYN360 ships with two hooks that are **active by default** in every session:

**Safety Check** (`builtin_safety_check`) — runs on every message you type:
- Scans for destructive patterns: `rm -rf`, `DROP TABLE`, `DELETE FROM`, `format c:`
- If found, adds a warning message (does not block — just warns)
- Example: you type "please rm -rf /tmp" → you'll see "Warning: Detected potentially destructive pattern 'rm -rf'"

**Response Tracker** (`builtin_response_tracker`) — runs on every AI response:
- Silently logs when responses exceed 50,000 characters
- You won't see anything unless you check the logs — it's for debugging

### Commands

```bash
# List all registered hooks with execution stats
/hooks
```

Output shows:
```
Registered hooks (2 total):
  builtin_safety_check [pre_query] (enabled, ran 3x)
  builtin_response_tracker [post_response] (enabled, ran 15x)

Total execution time: 2.4ms
```

### Programmatic Hook Registration

For advanced users, hooks can be registered in Python:

```python
from wyn360_cli.hooks import HookManager, HookPoint, HookContext, HookResult

manager = HookManager()

# Sync hook
def log_queries(ctx: HookContext) -> HookResult:
    print(f"Query: {ctx.message[:100]}")
    return HookResult()

manager.register("query_logger", HookPoint.PRE_QUERY, log_queries)

# Async hook
async def validate_response(ctx: HookContext) -> HookResult:
    if "TODO" in ctx.response:
        return HookResult(
            extra_messages=["Warning: Response contains TODO items"]
        )
    return HookResult()

manager.register("todo_checker", HookPoint.POST_RESPONSE, validate_response)

# Block dangerous tool calls
def block_rm(ctx: HookContext) -> HookResult:
    if ctx.tool_name == "execute_command" and "rm -rf" in str(ctx.tool_args):
        return HookResult(block_action=True, block_reason="Blocked rm -rf")
    return HookResult()

manager.register("rm_blocker", HookPoint.PRE_TOOL, block_rm, priority=-10)
```

### Hook Features

- **Priority ordering**: Lower priority numbers run first (`-100` before `0` before `100`)
- **Chain stopping**: A hook can set `stop_chain=True` to prevent subsequent hooks from running
- **Message modification**: `pre_query` hooks can modify the user message before it reaches the AI
- **Response modification**: `post_response` hooks can modify the AI response before display
- **Action blocking**: `pre_tool` hooks can block tool execution with a reason
- **Sync and async**: Both synchronous and async hook functions are supported
- **Error isolation**: A failing hook logs a warning but doesn't crash the session

### HookResult Fields

| Field | Type | Description |
|-------|------|-------------|
| `stop_chain` | `bool` | Stop running further hooks at this point |
| `modified_message` | `str` | Replace the user message (pre_query) |
| `modified_response` | `str` | Replace the AI response (post_response) |
| `extra_messages` | `list[str]` | Additional messages to display |
| `block_action` | `bool` | Prevent a tool from executing (pre_tool) |
| `block_reason` | `str` | Reason for blocking |

---

## Token Budget & Auto-Continue

The token budget manager **runs automatically** on every AI response. You don't need to configure or trigger it — it watches for cut-off responses and continues them seamlessly.

### The Problem

When the AI generates a long response, it may hit the `max_tokens` limit and stop mid-sentence. Previously, you had to manually ask "please continue" to get the rest.

### The Solution (Fully Automatic)

After every AI response, the system automatically:
1. Checks if the response was cut off (doesn't end with a sentence terminator)
2. If cut off, sends a continuation message behind the scenes
3. Appends the continuation to the original response seamlessly
4. Repeats until the response is complete or diminishing returns are detected

**You see one complete response** — the auto-continue happens invisibly. You never need to type "please continue."

### How It Works

```
You: Explain the entire authentication architecture

WYN360: [Generates 4096 tokens, gets cut off mid-paragraph]
        [Auto-continue: 25% of budget used (1024/4096 tokens). Continuation 1/5.]
        [AI continues where it left off...]
        [Auto-continue: 50% of budget used (2048/4096 tokens). Continuation 2/5.]
        [AI finishes the explanation]
```

### Diminishing Returns Detection

The system detects when continuations produce very little new content (under 500 tokens for 2+ consecutive continuations) and stops automatically. This prevents infinite loops where the AI keeps repeating itself.

### Configuration

The budget is set by your `max_token` setting:

```bash
# Set a higher budget for longer responses
wyn360 --max-token 8192

# Or via environment variable
export MAX_TOKEN=8192
```

### Commands

```bash
# Show token budget statistics
/budget
```

Output:
```
Token Budget Status:
  Budget: 4096 tokens
  Used: 2048 tokens (50%)
  Continuations this turn: 2
  Total auto-continues (session): 5
  Diminishing returns stops: 1
```

### Budget Stats Explained

| Metric | Description |
|--------|-------------|
| Budget | Max tokens per turn (from `--max-token`) |
| Used | Tokens generated in current turn |
| Continuations this turn | How many times auto-continue fired |
| Total auto-continues | Session-wide count of auto-continuations |
| Diminishing returns stops | Times the system stopped due to low output |

### Safety Limits

| Limit | Value | Purpose |
|-------|-------|---------|
| Completion threshold | 90% | Stop continuing when 90% of budget used |
| Max continuations | 5 | Hard cap on auto-continues per turn |
| Diminishing threshold | 500 tokens | Minimum useful output per continuation |

---

**Next:** [Memory & Skills](agentic-memory.md) | [Commands Reference](../usage/commands.md)
