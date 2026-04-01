"""
WYN360 Context Compaction - Auto-summarize old messages when context fills up.

When the conversation history grows large, older messages are summarized
into a compact form to free up context window space while preserving
the essential information.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Default thresholds
DEFAULT_MAX_MESSAGES = 50
DEFAULT_COMPACT_TO = 10
DEFAULT_TOKEN_THRESHOLD = 100000  # ~100K tokens triggers compaction


@dataclass
class CompactionConfig:
    """Configuration for context compaction."""
    enabled: bool = True
    max_messages: int = DEFAULT_MAX_MESSAGES
    compact_to: int = DEFAULT_COMPACT_TO
    token_threshold: int = DEFAULT_TOKEN_THRESHOLD
    preserve_recent: int = 10  # Always keep this many recent messages


@dataclass
class CompactionStats:
    """Track compaction statistics."""
    total_compactions: int = 0
    messages_compacted: int = 0
    tokens_saved_estimate: int = 0
    last_compaction_at: float = 0.0


COMPACTION_PROMPT = """Summarize the following conversation history into a concise summary.
Preserve:
- Key decisions and conclusions
- File paths and code changes mentioned
- User preferences and corrections
- Important context needed for future messages

Be concise but complete. Use bullet points.

Conversation to summarize:
{messages}
"""


class CompactionManager:
    """Manages automatic context compaction."""

    def __init__(self, config: Optional[CompactionConfig] = None):
        self.config = config or CompactionConfig()
        self.stats = CompactionStats()
        self._compaction_summaries: List[str] = []

    def should_compact(self, message_count: int, estimated_tokens: int = 0) -> bool:
        """Check if compaction should be triggered."""
        if not self.config.enabled:
            return False
        if message_count >= self.config.max_messages:
            return True
        if estimated_tokens > 0 and estimated_tokens >= self.config.token_threshold:
            return True
        return False

    async def compact(self, messages: List[Dict[str, Any]], model) -> List[Dict[str, Any]]:
        """
        Compact old messages into a summary, keeping recent messages intact.

        Args:
            messages: Full conversation history (list of dicts with 'role' and 'content')
            model: pydantic-ai model for summarization

        Returns:
            New compacted message list
        """
        if len(messages) <= self.config.preserve_recent:
            return messages

        # Split into old (to compact) and recent (to keep)
        split_point = len(messages) - self.config.preserve_recent
        old_messages = messages[:split_point]
        recent_messages = messages[split_point:]

        # Build summary of old messages
        summary = await self._summarize_messages(old_messages, model)

        # Create compacted history
        compacted = [
            {
                "role": "system",
                "content": f"[Context Summary - {len(old_messages)} earlier messages compacted]\n\n{summary}"
            }
        ] + recent_messages

        # Update stats
        self.stats.total_compactions += 1
        self.stats.messages_compacted += len(old_messages)
        tokens_before = sum(len(str(m.get("content", ""))) // 4 for m in old_messages)
        tokens_after = len(summary) // 4
        self.stats.tokens_saved_estimate += max(0, tokens_before - tokens_after)
        self.stats.last_compaction_at = time.time()

        self._compaction_summaries.append(summary)

        logger.info(
            f"Compacted {len(old_messages)} messages into summary "
            f"(~{tokens_before - tokens_after} tokens saved)"
        )

        return compacted

    def compact_pydantic_messages(self, messages: List, preserve_recent: int = 0) -> List:
        """
        Compact pydantic-ai message objects by dropping old ones.

        This is a simpler approach that doesn't require an LLM call -
        it just keeps the most recent messages. For LLM-based summarization,
        use compact() with plain dict messages.

        Args:
            messages: pydantic-ai ModelMessage objects
            preserve_recent: Number of recent messages to keep (0 = use config)

        Returns:
            Trimmed message list
        """
        keep = preserve_recent or self.config.preserve_recent
        if len(messages) <= keep:
            return messages

        dropped = len(messages) - keep
        self.stats.total_compactions += 1
        self.stats.messages_compacted += dropped
        logger.info(f"Dropped {dropped} old pydantic-ai messages, keeping {keep}")

        return messages[-keep:]

    async def _summarize_messages(self, messages: List[Dict[str, Any]], model) -> str:
        """Use LLM to summarize a set of messages."""
        # Format messages for the summarization prompt
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                # Truncate very long messages
                if len(content) > 1000:
                    content = content[:1000] + "..."
                formatted.append(f"[{role}]: {content}")

        messages_text = "\n\n".join(formatted)
        prompt = COMPACTION_PROMPT.format(messages=messages_text)

        try:
            from pydantic_ai import Agent
            summarizer = Agent(
                model=model,
                system_prompt="You are a conversation summarizer. Be concise.",
                retries=0,
            )
            result = await summarizer.run(prompt)
            response = getattr(result, 'data', None) or getattr(result, 'output', str(result))
            if not isinstance(response, str):
                response = str(response)
            return response
        except Exception as e:
            logger.warning(f"LLM summarization failed: {e}")
            # Fallback: just keep the last few messages as text
            return "\n".join(formatted[-5:])

    def get_stats(self) -> Dict[str, Any]:
        """Get compaction statistics."""
        return {
            "enabled": self.config.enabled,
            "total_compactions": self.stats.total_compactions,
            "messages_compacted": self.stats.messages_compacted,
            "tokens_saved_estimate": self.stats.tokens_saved_estimate,
            "compaction_summaries": len(self._compaction_summaries),
            "max_messages": self.config.max_messages,
            "preserve_recent": self.config.preserve_recent,
        }

    def get_last_summary(self) -> Optional[str]:
        """Get the most recent compaction summary."""
        return self._compaction_summaries[-1] if self._compaction_summaries else None
