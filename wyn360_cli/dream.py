"""
WYN360 Dream System - Background memory consolidation.

Automatically reviews recent conversation sessions and consolidates
learnings into persistent memory files. Runs as a background task
after enough sessions have accumulated since the last consolidation.

Gate order (cheapest first):
  1. Time: hours since last consolidation >= min_hours
  2. Sessions: session count since last consolidation >= min_sessions
  3. Lock: no other process is consolidating
"""

import os
import time
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_MIN_HOURS = 24
DEFAULT_MIN_SESSIONS = 3


@dataclass
class DreamConfig:
    """Configuration for auto-dream."""
    min_hours: float = DEFAULT_MIN_HOURS
    min_sessions: int = DEFAULT_MIN_SESSIONS
    enabled: bool = True
    max_sessions_to_review: int = 10


@dataclass
class DreamState:
    """Tracks dream consolidation state."""
    last_consolidated_at: float = 0.0
    sessions_reviewed: int = 0
    total_dreams: int = 0
    is_dreaming: bool = False
    last_dream_duration: float = 0.0
    files_touched: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "last_consolidated_at": self.last_consolidated_at,
            "sessions_reviewed": self.sessions_reviewed,
            "total_dreams": self.total_dreams,
            "last_dream_duration": self.last_dream_duration,
        }


CONSOLIDATION_PROMPT = """You are reviewing recent conversation sessions to consolidate learnings into memory.

Review the session summaries below and extract any information worth remembering:

1. **User preferences** - coding style, communication preferences, expertise level
2. **Project knowledge** - architecture decisions, important patterns, known issues
3. **Feedback** - what approaches worked, what the user corrected
4. **References** - external tools, URLs, resources mentioned

For each memory worth saving, output it in this format:
```
MEMORY: <type> | <name> | <description>
<content>
END_MEMORY
```

Types: user, feedback, project, reference

Only save genuinely useful information. Skip trivial or one-off details.
If there's nothing worth remembering, respond with "NO_NEW_MEMORIES".

Session summaries:
{sessions}
"""


class DreamManager:
    """Manages background memory consolidation."""

    def __init__(self, state_dir: Optional[Path] = None,
                 config: Optional[DreamConfig] = None):
        self.state_dir = state_dir or (Path.home() / ".wyn360" / "dream")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or DreamConfig()
        self.state = self._load_state()
        self._lock_path = self.state_dir / ".dream.lock"

    def should_dream(self, session_dir: Optional[Path] = None) -> bool:
        """Check if conditions are met for a dream consolidation."""
        if not self.config.enabled:
            return False
        if self.state.is_dreaming:
            return False

        # Time gate
        hours_since = (time.time() - self.state.last_consolidated_at) / 3600
        if hours_since < self.config.min_hours:
            return False

        # Session count gate
        sessions = self._count_new_sessions(session_dir)
        if sessions < self.config.min_sessions:
            return False

        # Lock gate
        if self._is_locked():
            return False

        return True

    async def dream(self, model, memory_manager, session_dir: Optional[Path] = None) -> DreamState:
        """
        Run the dream consolidation process.

        Args:
            model: pydantic-ai model for the consolidation agent
            memory_manager: MemoryManager instance to save extracted memories
            session_dir: Directory containing session JSON files
        """
        if not self._acquire_lock():
            logger.warning("Could not acquire dream lock")
            return self.state

        self.state.is_dreaming = True
        start_time = time.time()

        try:
            # Gather recent session summaries
            summaries = self._gather_session_summaries(session_dir)
            if not summaries:
                logger.info("No sessions to review")
                return self.state

            # Build prompt
            sessions_text = "\n\n---\n\n".join(summaries)
            prompt = CONSOLIDATION_PROMPT.format(sessions=sessions_text)

            # Run consolidation agent
            from pydantic_ai import Agent
            dreamer = Agent(
                model=model,
                system_prompt="You are a memory consolidation assistant.",
                retries=0,
            )

            result = await dreamer.run(prompt)
            response = getattr(result, 'data', None) or getattr(result, 'output', str(result))
            if not isinstance(response, str):
                response = str(response)

            # Parse and save memories
            memories_saved = self._parse_and_save_memories(response, memory_manager)

            # Update state
            self.state.last_consolidated_at = time.time()
            self.state.sessions_reviewed += len(summaries)
            self.state.total_dreams += 1
            self.state.last_dream_duration = time.time() - start_time
            self.state.files_touched = memories_saved
            self._save_state()

            logger.info(
                f"Dream complete: reviewed {len(summaries)} sessions, "
                f"saved {len(memories_saved)} memories in {self.state.last_dream_duration:.1f}s"
            )

        except Exception as e:
            logger.error(f"Dream failed: {e}")
        finally:
            self.state.is_dreaming = False
            self._release_lock()

        return self.state

    def get_status(self) -> Dict[str, Any]:
        """Get current dream status."""
        hours_since = (time.time() - self.state.last_consolidated_at) / 3600 if self.state.last_consolidated_at else float('inf')
        return {
            "enabled": self.config.enabled,
            "is_dreaming": self.state.is_dreaming,
            "total_dreams": self.state.total_dreams,
            "sessions_reviewed": self.state.sessions_reviewed,
            "hours_since_last": round(hours_since, 1),
            "last_duration_s": round(self.state.last_dream_duration, 1),
            "min_hours": self.config.min_hours,
            "min_sessions": self.config.min_sessions,
        }

    def _gather_session_summaries(self, session_dir: Optional[Path] = None,
                                   max_sessions: int = 0) -> List[str]:
        """Load and summarize recent session files."""
        if not session_dir:
            session_dir = Path.home() / ".wyn360" / "sessions"
        if not session_dir.exists():
            return []

        max_sessions = max_sessions or self.config.max_sessions_to_review
        cutoff = self.state.last_consolidated_at

        session_files = []
        for f in session_dir.glob("*.json"):
            if f.stat().st_mtime > cutoff:
                session_files.append((f.stat().st_mtime, f))

        session_files.sort(reverse=True)
        session_files = session_files[:max_sessions]

        summaries = []
        for _, filepath in session_files:
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                # Extract conversation content
                messages = data if isinstance(data, list) else data.get("messages", data.get("history", []))
                if not messages:
                    continue

                # Build a summary from user/assistant messages
                parts = []
                for msg in messages[:20]:  # Cap at 20 messages per session
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if isinstance(content, str) and content.strip():
                        truncated = content[:500] + "..." if len(content) > 500 else content
                        parts.append(f"[{role}]: {truncated}")

                if parts:
                    summaries.append(f"Session: {filepath.name}\n" + "\n".join(parts))
            except Exception as e:
                logger.debug(f"Could not read session {filepath}: {e}")

        return summaries

    def _parse_and_save_memories(self, response: str, memory_manager) -> List[str]:
        """Parse MEMORY blocks from dream response and save them."""
        if "NO_NEW_MEMORIES" in response:
            return []

        import re
        pattern = r'MEMORY:\s*(\w+)\s*\|\s*(.+?)\s*\|\s*(.+?)\n(.*?)END_MEMORY'
        matches = re.findall(pattern, response, re.DOTALL)

        saved = []
        for mem_type, name, description, content in matches:
            mem_type = mem_type.strip().lower()
            if mem_type not in {"user", "feedback", "project", "reference"}:
                continue
            try:
                filename = memory_manager.save_memory(
                    name=name.strip(),
                    description=description.strip(),
                    memory_type=mem_type,
                    content=content.strip(),
                )
                saved.append(filename)
            except Exception as e:
                logger.warning(f"Failed to save dream memory '{name}': {e}")

        return saved

    def _count_new_sessions(self, session_dir: Optional[Path] = None) -> int:
        """Count sessions created since last consolidation."""
        if not session_dir:
            session_dir = Path.home() / ".wyn360" / "sessions"
        if not session_dir.exists():
            return 0
        cutoff = self.state.last_consolidated_at
        return sum(1 for f in session_dir.glob("*.json") if f.stat().st_mtime > cutoff)

    def _load_state(self) -> DreamState:
        """Load dream state from disk."""
        state_file = self.state_dir / "dream_state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                return DreamState(
                    last_consolidated_at=data.get("last_consolidated_at", 0),
                    sessions_reviewed=data.get("sessions_reviewed", 0),
                    total_dreams=data.get("total_dreams", 0),
                    last_dream_duration=data.get("last_dream_duration", 0),
                )
            except Exception:
                pass
        return DreamState()

    def _save_state(self):
        """Save dream state to disk."""
        state_file = self.state_dir / "dream_state.json"
        state_file.write_text(json.dumps(self.state.to_dict(), indent=2), encoding="utf-8")

    def _is_locked(self) -> bool:
        """Check if another process holds the dream lock."""
        if not self._lock_path.exists():
            return False
        # Stale lock detection (1 hour timeout)
        age = time.time() - self._lock_path.stat().st_mtime
        if age > 3600:
            self._lock_path.unlink(missing_ok=True)
            return False
        return True

    def _acquire_lock(self) -> bool:
        """Try to acquire the dream lock."""
        if self._is_locked():
            return False
        try:
            self._lock_path.write_text(str(os.getpid()), encoding="utf-8")
            return True
        except Exception:
            return False

    def _release_lock(self):
        """Release the dream lock."""
        self._lock_path.unlink(missing_ok=True)
