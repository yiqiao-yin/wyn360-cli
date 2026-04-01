# Cron Agents, Plugins & LSP

*New in v0.5.0*

## Cron Agents (Scheduled Tasks)

Schedule recurring background agents that run on an interval - monitor CI, check for updates, or run periodic checks.

### Commands

```bash
/cron                                           # List all cron jobs
/cron add 5m Check CI | Run gh run list         # Create a job (every 5 minutes)
/cron add 1h Status Check | Check disk usage    # Create an hourly job
/cron delete <job_id>                           # Delete a job
/cron pause <job_id>                            # Pause a job
/cron resume <job_id>                           # Resume a paused job
```

### Interval Format

| Format | Duration |
|--------|----------|
| `30s` | 30 seconds |
| `5m` | 5 minutes |
| `1h` | 1 hour |
| `2h30m` | 2 hours 30 minutes |
| `10` | 10 minutes (plain number = minutes) |

### Example

```
/cron add 10m Monitor Deploy | Check if the deployment at https://myapp.com is healthy

Created cron job 'Monitor Deploy' (every 10m): cron-a1b2c3

/cron
┌────────────────┬──────────────────────┬──────────┬──────┬────────┐
│ ID             │ Name                 │ Interval │ Runs │ Status │
├────────────────┼──────────────────────┼──────────┼──────┼────────┤
│ cron-a1b2c3    │ Monitor Deploy       │ 10m      │ 3    │ active │
└────────────────┴──────────────────────┴──────────┴──────┴────────┘
```

---

## Plugin System

Install and manage plugins that extend WYN360 with new tools, hooks, or skills.

### Plugin Directory

Plugins live in `~/.wyn360/plugins/`. Each plugin is a subdirectory with a `plugin.yaml` manifest and a Python entry point.

### Commands

```bash
/plugins                    # List installed plugins
/plugins create my-tool     # Create a plugin scaffold
/plugins install ./my-tool  # Install from local directory
/plugins uninstall my-tool  # Remove a plugin
/plugins reload             # Reload all plugins
```

### Creating a Plugin

```bash
/plugins create my-analyzer
```

This creates:
```
~/.wyn360/plugins/my-analyzer/
  plugin.yaml    # Plugin metadata
  main.py        # Entry point
```

### Plugin Manifest (plugin.yaml)

```yaml
name: my-analyzer
version: 0.1.0
description: Custom code analyzer
author: Your Name
entry_point: main.py
type: tool              # tool, skill, or hook
```

### Plugin Types

| Type | Purpose | Registration |
|------|---------|-------------|
| `tool` | New AI tools | `register(agent)` |
| `hook` | Pre/post processing | `register(hook_manager)` |
| `skill` | Custom commands | `register(skill_registry)` |

### Example Plugin (main.py)

```python
"""Custom tool plugin."""

def register(agent):
    """Called when the plugin loads."""
    pass

def get_tools():
    """Return tool functions to register."""
    return []
```

---

## LSP Integration (Diagnostics)

Run language server diagnostics (type checking, linting) directly from WYN360.

### Commands

```bash
/diagnostics              # Run diagnostics on current directory
/diagnostics src/         # Run on a specific directory
/lint                     # Alias for /diagnostics
```

### Supported Tools

The LSP client auto-detects available tools:

| Tool | Language | Install |
|------|----------|---------|
| pyright | Python | `pip install pyright` |
| ruff | Python | `pip install ruff` |
| typescript-language-server | TypeScript/JS | `npm i -g typescript-language-server` |

### Output

```
/diagnostics

Diagnostics: 3 errors, 5 warnings, 1 info
  [E] src/auth.py:42:5: Variable "user" is undefined (pyright:reportUndefined)
  [E] src/api.py:15:0: Import "flask" could not be resolved (pyright:reportMissing)
  [W] src/utils.py:8:0: `os` imported but unused (ruff:F401)
  [W] src/main.py:22:80: Line too long (95 > 88) (ruff:E501)
  ...
```

---

## Rewind (Conversation State)

Undo mistakes by reverting to previous conversation states.

### How It Works

After each turn, WYN360 automatically takes a snapshot of the conversation. You can rewind to any previous snapshot.

### Commands

```bash
/rewind              # List available snapshots
/rewind undo         # Undo the last turn
/rewind <id>         # Rewind to a specific snapshot
```

### Example

```
/rewind
┌────┬──────────────────────────────────────────┬──────────┬──────────┐
│ ID │ Label                                    │ Messages │ Age      │
├────┼──────────────────────────────────────────┼──────────┼──────────┤
│ 5  │ Add error handling to the auth module    │ 12       │ 2m ago   │
│ 4  │ Refactor the database connection         │ 10       │ 5m ago   │
│ 3  │ Write tests for user authentication      │ 8        │ 8m ago   │
│ 2  │ Create the user model                    │ 4        │ 12m ago  │
│ 1  │ Start the project                        │ 2        │ 15m ago  │
└────┴──────────────────────────────────────────┴──────────┴──────────┘

/rewind undo
Rewound to previous state.

/rewind 2
Rewound to snapshot 2.
```

### Limits

- Maximum 50 snapshots retained (oldest evicted first)
- Rewinding removes all snapshots after the rewind point

---

**Next:** [Memory & Skills](agentic-memory.md) | [Commands Reference](../usage/commands.md)
