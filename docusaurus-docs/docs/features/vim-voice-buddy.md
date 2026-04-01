# Vim Mode, Voice Input & Buddy

*New in v0.5.0*

## Vim Mode

Full vi-style editing for the terminal input, powered by prompt_toolkit's built-in vi mode.

### Toggle Vim Mode

```bash
/vim            # Toggle vim mode on/off
```

When enabled, the prompt switches to vi editing mode with:
- **Normal mode**: Navigate with `h`, `j`, `k`, `l`, `w`, `b`, `0`, `$`
- **Insert mode**: `i`, `a`, `o`, `A`, `I`
- **Operators**: `d`, `c`, `y`, `p`
- **Visual mode**: `v` for character selection
- **Escape**: Return to normal mode

### Status

The mode indicator shows in the prompt area: `-- NORMAL --`, `-- INSERT --`, or `-- VISUAL --`.

---

## Voice Input

Hands-free coding via speech-to-text. Speak your requests instead of typing.

### Prerequisites

```bash
pip install SpeechRecognition pyaudio
```

### Commands

```bash
/voice          # Toggle voice input on/off
/voice status   # Show voice configuration
```

### Backends

| Backend | Requires | Quality | Cost |
|---------|----------|---------|------|
| Google (default) | Internet | Good | Free |
| Whisper | `OPENAI_API_KEY` | Excellent | Paid |

### Usage

When voice input is enabled, press a designated key to start listening. The system:
1. Adjusts for ambient noise (0.5s)
2. Listens for speech (up to 10s timeout)
3. Transcribes and inserts as your message
4. You can review and edit before submitting

---

## Buddy (Virtual Companion)

A virtual pet companion that lives beside your prompt and reacts to events with speech bubbles.

### Toggle Buddy

```bash
/buddy          # Toggle buddy on/off
/buddy status   # Show companion details
```

### How It Works

Each user gets a **deterministic companion** based on their OS username. Your buddy is always the same across sessions.

### Companion Properties

| Property | Options |
|----------|---------|
| Species | Duck, Cat, Dog, Owl, Fox, Penguin, Rabbit, Panda, Dragon, Robot |
| Eyes | Round, Sleepy, Wide, Sparkly, Winking, Determined |
| Hat | None, Top Hat, Beret, Crown, Beanie, Wizard Hat, Headphones, Bow |
| Rarity | Common (50%), Uncommon (30%), Rare (15%), Epic (4%), Legendary (1%) |
| Personality | Cheerful, Sarcastic, Wise, Silly, Calm, Energetic, Curious, Shy, Bold, Philosophical |

### Example

```
/buddy
Buddy enabled!
🦊 Ember: 🦊 What are we building today?

/buddy status
Your companion: Ember the sparkly-eyed fox wearing a beret
  Rarity: rare
  Personality: curious
```

### Reactions

Your buddy reacts to events:
- **Success**: "Nice one!", "*does a little dance*"
- **Error**: "Hmm, that doesn't look right...", "*concerned look*"
- **Long wait**: "*falls asleep*", "zzz..."

---

**Next:** [Cron, Plugins & LSP](cron-plugins-lsp.md) | [Commands Reference](../usage/commands.md)
