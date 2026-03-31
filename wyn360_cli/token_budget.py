"""
WYN360 Token Budget - Auto-continue when model hits max_tokens, with diminishing returns detection.

Tracks token usage against a budget per turn and automatically continues
the conversation when the model stops mid-response due to token limits.
Detects when continuation produces diminishing returns and stops.
"""

import time
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# If we've used less than 90% of budget, continue
COMPLETION_THRESHOLD = 0.9

# If fewer than this many tokens produced in consecutive continuations, stop
DIMINISHING_THRESHOLD = 500

# Maximum number of auto-continuations per user turn
MAX_CONTINUATIONS = 5


@dataclass
class BudgetTracker:
    """Tracks token budget for a single user turn."""
    budget: int = 0
    continuation_count: int = 0
    last_delta_tokens: int = 0
    last_total_tokens: int = 0
    started_at: float = field(default_factory=time.time)
    total_output_tokens: int = 0

    def reset(self, budget: int):
        """Reset for a new user turn."""
        self.budget = budget
        self.continuation_count = 0
        self.last_delta_tokens = 0
        self.last_total_tokens = 0
        self.started_at = time.time()
        self.total_output_tokens = 0


class ContinueDecision:
    """Decision about whether to auto-continue."""
    def __init__(self, should_continue: bool, reason: str = "",
                 nudge_message: str = "", pct: int = 0):
        self.should_continue = should_continue
        self.reason = reason
        self.nudge_message = nudge_message
        self.pct = pct


class TokenBudgetManager:
    """Manages token budget and auto-continuation logic."""

    def __init__(self, default_budget: int = 4096, max_continuations: int = MAX_CONTINUATIONS):
        self.default_budget = default_budget
        self.max_continuations = max_continuations
        self.tracker = BudgetTracker()
        self.total_auto_continues = 0
        self.total_diminishing_stops = 0

    def start_turn(self, budget: Optional[int] = None):
        """Start tracking a new user turn."""
        self.tracker.reset(budget or self.default_budget)

    def check_should_continue(self, output_tokens: int, stop_reason: str) -> ContinueDecision:
        """
        Check whether to auto-continue after a model response.

        Args:
            output_tokens: Number of output tokens in the last response
            stop_reason: The stop reason from the API ('end_turn', 'max_tokens', etc.)

        Returns:
            ContinueDecision with should_continue flag and details
        """
        # Only auto-continue if the model was cut off by max_tokens
        if stop_reason != "max_tokens":
            return ContinueDecision(False, reason="Model finished naturally")

        # Don't exceed max continuations
        if self.tracker.continuation_count >= self.max_continuations:
            return ContinueDecision(
                False,
                reason=f"Max continuations ({self.max_continuations}) reached",
            )

        self.tracker.total_output_tokens += output_tokens
        delta = output_tokens - self.tracker.last_delta_tokens if self.tracker.last_delta_tokens else output_tokens

        # Check for diminishing returns
        is_diminishing = (
            self.tracker.continuation_count >= 2
            and delta < DIMINISHING_THRESHOLD
            and self.tracker.last_delta_tokens < DIMINISHING_THRESHOLD
        )

        if is_diminishing:
            self.total_diminishing_stops += 1
            return ContinueDecision(
                False,
                reason="Diminishing returns detected",
                pct=self._pct(),
            )

        # Check if we're near the budget
        if self.tracker.total_output_tokens >= self.tracker.budget * COMPLETION_THRESHOLD:
            return ContinueDecision(
                False,
                reason="Near budget limit",
                pct=self._pct(),
            )

        # Continue
        self.tracker.continuation_count += 1
        self.tracker.last_delta_tokens = delta
        self.tracker.last_total_tokens = output_tokens
        self.total_auto_continues += 1

        pct = self._pct()
        nudge = self._continuation_message(pct)

        return ContinueDecision(
            True,
            reason="Token budget has room",
            nudge_message=nudge,
            pct=pct,
        )

    def get_stats(self) -> dict:
        """Get budget tracking statistics."""
        return {
            "budget": self.tracker.budget,
            "total_output_tokens": self.tracker.total_output_tokens,
            "continuation_count": self.tracker.continuation_count,
            "pct_used": self._pct(),
            "total_auto_continues": self.total_auto_continues,
            "total_diminishing_stops": self.total_diminishing_stops,
        }

    def _pct(self) -> int:
        if self.tracker.budget <= 0:
            return 0
        return min(100, round((self.tracker.total_output_tokens / self.tracker.budget) * 100))

    def _continuation_message(self, pct: int) -> str:
        """Build the nudge message sent to the model to continue."""
        return (
            f"[Auto-continue: {pct}% of token budget used "
            f"({self.tracker.total_output_tokens}/{self.tracker.budget} tokens). "
            f"Continuation {self.tracker.continuation_count}/{self.max_continuations}. "
            f"Please continue where you left off.]"
        )
