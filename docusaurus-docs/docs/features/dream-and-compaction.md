# Dream & Context Compaction

*New in v0.5.0*

## Dream (Auto Memory Consolidation)

The Dream system is a background process that automatically reviews recent conversation sessions and extracts useful information into persistent memories - no manual `/memory save` needed.

### How It Works

1. **Time gate**: Waits at least 24 hours since the last dream
2. **Session gate**: Requires 3+ new sessions since the last dream
3. **Lock gate**: Ensures no other dream is running
4. When all gates pass, a background agent reviews session transcripts and saves extracted memories

### What It Extracts

- User preferences and coding style
- Project architecture decisions
- Feedback (what worked, what was corrected)
- References to external tools and resources

### Commands

```bash
/dream          # Show dream status
/dream now      # Trigger a dream consolidation
```

### Dream Status Output

```
Dream (Memory Consolidation) Status:
  Enabled: True
  Total dreams: 3
  Sessions reviewed: 15
  Hours since last: 26.4
  Min hours between: 24
  Min sessions needed: 3
```

---

## Context Compaction

When conversations grow long, older messages are automatically compacted to free up context window space while preserving essential information.

### How It Works

- **Trigger**: When conversation exceeds 50 messages (configurable)
- **Action**: Drops oldest messages, keeping the 10 most recent
- **LLM summarization** (optional): Summarizes old messages into a compact form using a side-call
- **Result**: Longer conversations without losing critical context

### Commands

```bash
/compact        # Show compaction statistics
```

### Compaction Stats

```
Context Compaction Status:
  Enabled: True
  Total compactions: 2
  Messages compacted: 35
  Tokens saved (est): 12,500
  Max messages: 50
  Preserve recent: 10
```

---

**Next:** [Vim, Voice & Buddy](vim-voice-buddy.md) | [Commands Reference](../usage/commands.md)
