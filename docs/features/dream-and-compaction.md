# Dream & Context Compaction

*New in v0.5.0*

## Dream (Auto Memory Consolidation)

The Dream system **runs automatically in the background** — you don't need to trigger it. It reviews your recent conversation sessions and extracts useful information into persistent memories, so you never have to manually `/memory save`.

### How It's Triggered

**Fully automatic.** After every AI response, the system checks three gates:

```
You chat normally
  → AI responds
    → Dream check runs silently:
      1. Has it been 24+ hours since last dream?  → if no, skip
      2. Have there been 3+ new sessions?          → if no, skip
      3. Is another dream already running?          → if yes, skip
      → All three pass? → Dream starts in background
```

The dream runs as a **background task** — it doesn't block your session. You keep chatting normally while it consolidates memories behind the scenes.

### What Happens During a Dream

1. Gathers your recent session transcripts (up to 10)
2. A background AI agent reads through them
3. Extracts useful patterns into memory files:
   - User preferences and coding style
   - Project architecture decisions
   - Feedback (what worked, what was corrected)
   - References to external tools and resources
4. Saves them to `~/.wyn360/memory/` automatically

### When Will My First Dream Happen?

After you've:
- Used WYN360 for at least **24 hours** (calendar time, not usage time)
- Completed at least **3 separate sessions** (start wyn360, chat, exit = 1 session)

If you just installed WYN360 today, you won't see a dream until tomorrow at the earliest.

### Commands

```bash
/dream          # Check dream status (when was last dream, how many sessions pending)
```

### Example

```
/dream

Dream (Memory Consolidation) Status:
  Enabled: True
  Total dreams: 3
  Sessions reviewed: 15
  Hours since last: 26.4
  Min hours between: 24
  Min sessions needed: 3
```

If you see "Hours since last: 26.4" and "Min sessions needed: 3" with 3+ sessions, the next dream will trigger automatically on your next message.

---

## Context Compaction

Context compaction also **runs automatically** — you don't trigger it. When your conversation gets too long, old messages are silently dropped to keep the context window fresh.

### How It's Triggered

**Fully automatic.** After every AI response:

```
AI responds
  → System checks: are there more than 50 messages in history?
    → Yes → silently drop oldest messages, keep 10 most recent
    → No  → do nothing
```

You'll never notice it happening. Your conversation just keeps working without hitting context limits.

### What Gets Kept vs Dropped

| Kept (always) | Dropped (when over 50 messages) |
|---------------|-------------------------------|
| Your 10 most recent messages | Older messages |
| All recent AI responses | Early conversation turns |
| Recent tool calls and results | Old tool outputs |

### Commands

```bash
/compact        # Check compaction statistics
```

### Example

```
/compact

Context Compaction Status:
  Enabled: True
  Total compactions: 2
  Messages compacted: 35
  Tokens saved (est): 12,500
  Max messages: 50
  Preserve recent: 10
```

### Do I Lose Information?

Old messages are dropped from the active context, but:
- The **Dream system** may have already extracted important info into persistent memories
- Your **session files** still contain the full conversation if you saved them
- The AI won't remember dropped messages in the current session, but memories persist across sessions

---

**Next:** [Vim, Voice & Buddy](vim-voice-buddy.md) | [Commands Reference](../usage/commands.md)
