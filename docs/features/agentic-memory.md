# Memory & Skills System

*New in v0.4.0*

WYN360 CLI now includes a persistent memory system and an extensible skills framework, allowing the assistant to remember context across sessions and users to define custom slash commands.

---

## Memory System

The memory system stores knowledge in `~/.wyn360/memory/` as individual Markdown files with YAML frontmatter. A `MEMORY.md` index file provides a quick reference for all stored memories.

### Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| `user` | Who you are, your role, preferences | "Senior Python developer, prefers type hints" |
| `feedback` | How you want the AI to work | "Don't add docstrings unless asked" |
| `project` | Ongoing work, goals, deadlines | "Merge freeze starts March 5 for mobile release" |
| `reference` | Pointers to external resources | "Bug tracker is in Linear project INGEST" |

### Commands

```bash
# List all stored memories
/memory list

# Save a new memory
/memory save user my_role | I am a backend engineer specializing in Python microservices

# Save feedback about AI behavior
/memory save feedback no_summaries | Don't summarize what you just did at the end of responses

# Search memories by keyword
/memory search python style

# Delete a specific memory
/memory delete user_my_role.md
```

### How It Works

1. **Storage**: Each memory is a `.md` file with YAML frontmatter (`name`, `description`, `type`)
2. **Indexing**: `MEMORY.md` maintains a one-line-per-entry index (max 200 lines)
3. **Retrieval**: On each query, relevant memories are found via keyword matching
4. **LLM Selection** (optional): When available, a lightweight LLM side-call selects the most relevant memories (up to 5)

### Memory File Format

```markdown
---
name: Python Style Preferences
description: User prefers type hints and minimal comments
type: feedback
---

Always use type hints. Only add comments where logic isn't self-evident.
Don't add docstrings to functions I didn't ask you to change.
```

### Relevance Selection

When you send a message, WYN360 automatically searches stored memories for relevant context. The system scores each memory based on keyword overlap with your query and boosts results by type relevance (e.g., "feedback" memories are boosted when you ask about approach or style).

---

## Skills System

Skills are user-defined slash commands loaded from YAML files. They let you create reusable prompt templates for common tasks.

### Skill Directories

| Location | Scope | Priority |
|----------|-------|----------|
| `~/.wyn360/skills/` | User-level (all projects) | Lower |
| `.wyn360/skills/` | Project-level (current repo) | Higher (overrides user) |

Project-level skills override user-level skills with the same name.

### Creating a Skill

Create a `.yaml` file in either skills directory:

```yaml
# ~/.wyn360/skills/review.yaml
name: review
description: Review code changes and suggest improvements
aliases:
  - cr
  - code-review
prompt: |
  Review the following code changes in the current project directory ({cwd}).
  {args}

  Focus on:
  1. Bug risks and edge cases
  2. Performance issues
  3. Code clarity and maintainability
  4. Security concerns

  Provide specific, actionable suggestions with file paths and line numbers.
```

### Using Skills

```bash
# List all available skills
/skills

# Invoke a skill by name
/review the authentication module

# Use an alias
/cr src/auth.py
```

### Skill YAML Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill name (used as `/name`) |
| `description` | Yes | One-line description shown in `/skills` |
| `prompt` | Yes | Prompt template sent to the AI |
| `aliases` | No | Alternative names for the skill |
| `allowed_tools` | No | Restrict which tools the AI can use |
| `model` | No | Override the AI model for this skill |

### Template Variables

| Variable | Replaced With |
|----------|--------------|
| `{args}` | Arguments passed after the skill name |
| `{cwd}` | Current working directory |

### Example Skills

**Commit helper:**
```yaml
name: commit
description: Create a well-formatted git commit
aliases: [ci]
prompt: |
  Review the current git diff and create a commit with a clear message.
  Follow conventional commits format. {args}
```

**Test generator:**
```yaml
name: testgen
description: Generate tests for a module
aliases: [tg]
prompt: |
  Generate comprehensive pytest tests for: {args}
  Include edge cases, error paths, and mocking where appropriate.
  Place tests in the tests/ directory following existing conventions.
```

**Explain code:**
```yaml
name: explain
description: Explain how a piece of code works
aliases: [ex, why]
prompt: |
  Explain the following code in detail: {args}
  Cover the architecture, key decisions, and any non-obvious behavior.
```

---

**Next:** [Planning & Sub-Agents](planning-and-agents.md) | [Commands Reference](../usage/commands.md)
