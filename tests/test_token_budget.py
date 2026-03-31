"""Unit tests for the token budget system."""

import pytest
from wyn360_cli.token_budget import TokenBudgetManager, BudgetTracker


class TestBudgetTracker:
    def test_reset(self):
        tracker = BudgetTracker()
        tracker.continuation_count = 5
        tracker.total_output_tokens = 1000
        tracker.reset(8000)
        assert tracker.budget == 8000
        assert tracker.continuation_count == 0
        assert tracker.total_output_tokens == 0


class TestTokenBudgetManager:
    def setup_method(self):
        self.mgr = TokenBudgetManager(default_budget=4096, max_continuations=5)

    def test_start_turn(self):
        self.mgr.start_turn(8000)
        assert self.mgr.tracker.budget == 8000
        assert self.mgr.tracker.continuation_count == 0

    def test_start_turn_default(self):
        self.mgr.start_turn()
        assert self.mgr.tracker.budget == 4096

    def test_no_continue_on_natural_stop(self):
        self.mgr.start_turn()
        decision = self.mgr.check_should_continue(100, "end_turn")
        assert not decision.should_continue
        assert "naturally" in decision.reason

    def test_continue_on_max_tokens(self):
        self.mgr.start_turn(10000)
        decision = self.mgr.check_should_continue(500, "max_tokens")
        assert decision.should_continue
        assert decision.nudge_message != ""

    def test_stop_when_near_budget(self):
        self.mgr.start_turn(1000)
        # Use 95% of budget
        self.mgr.tracker.total_output_tokens = 950
        decision = self.mgr.check_should_continue(950, "max_tokens")
        assert not decision.should_continue

    def test_stop_on_max_continuations(self):
        self.mgr.start_turn(100000)
        for i in range(5):
            self.mgr.tracker.continuation_count = i
            decision = self.mgr.check_should_continue(1000, "max_tokens")
        # After 5 continuations, should stop
        self.mgr.tracker.continuation_count = 5
        decision = self.mgr.check_should_continue(1000, "max_tokens")
        assert not decision.should_continue

    def test_diminishing_returns_detection(self):
        self.mgr.start_turn(100000)
        # Simulate diminishing returns: multiple continuations with tiny output
        self.mgr.tracker.continuation_count = 3
        self.mgr.tracker.last_delta_tokens = 100  # Below threshold
        self.mgr.tracker.last_total_tokens = 100
        self.mgr.tracker.total_output_tokens = 500

        decision = self.mgr.check_should_continue(100, "max_tokens")
        assert not decision.should_continue
        assert self.mgr.total_diminishing_stops == 1

    def test_get_stats(self):
        self.mgr.start_turn(4096)
        self.mgr.check_should_continue(500, "max_tokens")
        stats = self.mgr.get_stats()
        assert "budget" in stats
        assert "total_output_tokens" in stats
        assert "pct_used" in stats

    def test_pct_calculation(self):
        self.mgr.start_turn(1000)
        self.mgr.tracker.total_output_tokens = 500
        assert self.mgr._pct() == 50

    def test_pct_zero_budget(self):
        self.mgr.start_turn(0)
        assert self.mgr._pct() == 0

    def test_continuation_message_format(self):
        self.mgr.start_turn(4096)
        self.mgr.tracker.total_output_tokens = 1000
        self.mgr.tracker.continuation_count = 2
        msg = self.mgr._continuation_message(24)
        assert "24%" in msg
        assert "1000/4096" in msg
        assert "2/5" in msg
