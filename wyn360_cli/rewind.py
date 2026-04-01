"""
WYN360 Rewind - Undo/revert to previous conversation states.

Saves conversation snapshots at key points (before tool execution,
after responses) and allows reverting to any previous state.
"""

import time
import copy
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_SNAPSHOTS = 50


@dataclass
class ConversationSnapshot:
    """A snapshot of conversation state at a point in time."""
    id: int
    timestamp: float
    label: str
    message_count: int
    last_user_message: str = ""
    last_assistant_message: str = ""
    # The actual conversation history (stored as a serializable copy)
    messages: List = field(default_factory=list)
    # Token counts at this point
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def age_display(self) -> str:
        """Human-readable age of the snapshot."""
        age_s = time.time() - self.timestamp
        if age_s < 60:
            return f"{int(age_s)}s ago"
        elif age_s < 3600:
            return f"{int(age_s // 60)}m ago"
        else:
            return f"{int(age_s // 3600)}h {int((age_s % 3600) // 60)}m ago"


class RewindManager:
    """Manages conversation state snapshots and rewind."""

    def __init__(self, max_snapshots: int = MAX_SNAPSHOTS):
        self.max_snapshots = max_snapshots
        self._snapshots: List[ConversationSnapshot] = []
        self._next_id: int = 1
        self._rewind_count: int = 0

    def take_snapshot(self, messages: List, label: str = "",
                      input_tokens: int = 0, output_tokens: int = 0) -> ConversationSnapshot:
        """
        Save a snapshot of the current conversation state.

        Args:
            messages: The conversation history to snapshot
            label: Human-readable label for this snapshot
            input_tokens: Total input tokens at this point
            output_tokens: Total output tokens at this point
        """
        # Extract last user/assistant messages for display
        last_user = ""
        last_assistant = ""
        for msg in reversed(messages):
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "")
                content = str(msg)

            if not last_assistant and role == "assistant":
                last_assistant = str(content)[:100]
            elif not last_user and role == "user":
                last_user = str(content)[:100]
            if last_user and last_assistant:
                break

        snapshot = ConversationSnapshot(
            id=self._next_id,
            timestamp=time.time(),
            label=label or f"Turn {self._next_id}",
            message_count=len(messages),
            last_user_message=last_user,
            last_assistant_message=last_assistant,
            messages=self._copy_messages(messages),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        self._snapshots.append(snapshot)
        self._next_id += 1

        # Evict oldest if over limit
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots.pop(0)

        return snapshot

    def rewind_to(self, snapshot_id: int) -> Optional[List]:
        """
        Rewind to a specific snapshot, returning the messages from that point.

        Also removes all snapshots after the rewind point.
        """
        target_idx = None
        for i, snap in enumerate(self._snapshots):
            if snap.id == snapshot_id:
                target_idx = i
                break

        if target_idx is None:
            logger.warning(f"Snapshot {snapshot_id} not found")
            return None

        snapshot = self._snapshots[target_idx]

        # Remove all snapshots after this one
        self._snapshots = self._snapshots[:target_idx + 1]
        self._rewind_count += 1

        logger.info(f"Rewound to snapshot {snapshot_id} ({snapshot.label})")
        return self._copy_messages(snapshot.messages)

    def rewind_last(self) -> Optional[List]:
        """Rewind to the previous snapshot (undo last turn)."""
        if len(self._snapshots) < 2:
            return None
        # Remove the current state, rewind to the one before it
        self._snapshots.pop()
        target = self._snapshots[-1]
        self._rewind_count += 1
        return self._copy_messages(target.messages)

    def list_snapshots(self, limit: int = 10) -> List[ConversationSnapshot]:
        """List recent snapshots (most recent first)."""
        return list(reversed(self._snapshots[-limit:]))

    def get_snapshot(self, snapshot_id: int) -> Optional[ConversationSnapshot]:
        """Get a specific snapshot by ID."""
        for snap in self._snapshots:
            if snap.id == snapshot_id:
                return snap
        return None

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @property
    def can_rewind(self) -> bool:
        return len(self._snapshots) >= 2

    def get_stats(self) -> Dict[str, Any]:
        """Get rewind system statistics."""
        return {
            "total_snapshots": len(self._snapshots),
            "max_snapshots": self.max_snapshots,
            "total_rewinds": self._rewind_count,
            "can_rewind": self.can_rewind,
            "oldest_snapshot": self._snapshots[0].age_display if self._snapshots else None,
            "newest_snapshot": self._snapshots[-1].age_display if self._snapshots else None,
        }

    def _copy_messages(self, messages: List) -> List:
        """Create a safe copy of messages for storage."""
        try:
            return copy.deepcopy(messages)
        except Exception:
            # If deepcopy fails (some pydantic objects), store as-is
            return list(messages)
