"""Tests for v0.5.0 features: compaction, vim, voice, buddy, cron, plugins, LSP, rewind."""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch


# ── Compaction Tests ──

class TestCompactionManager:
    def setup_method(self):
        from wyn360_cli.compaction import CompactionManager, CompactionConfig
        self.mgr = CompactionManager(CompactionConfig(max_messages=10, preserve_recent=3))

    def test_should_not_compact_small(self):
        assert not self.mgr.should_compact(5)

    def test_should_compact_over_limit(self):
        assert self.mgr.should_compact(15)

    def test_should_compact_by_tokens(self):
        self.mgr.config.token_threshold = 1000
        assert self.mgr.should_compact(5, estimated_tokens=1500)

    def test_compact_pydantic_messages(self):
        messages = list(range(20))
        result = self.mgr.compact_pydantic_messages(messages)
        assert len(result) == 3
        assert result == [17, 18, 19]

    def test_compact_preserves_short(self):
        messages = [1, 2]
        result = self.mgr.compact_pydantic_messages(messages)
        assert len(result) == 2

    def test_get_stats(self):
        stats = self.mgr.get_stats()
        assert stats["enabled"]
        assert stats["max_messages"] == 10

    def test_get_last_summary_empty(self):
        assert self.mgr.get_last_summary() is None


# ── Vim Mode Tests ──

class TestVimMode:
    def setup_method(self):
        from wyn360_cli.vim_mode import VimModeManager, VimConfig
        self.vm = VimModeManager(VimConfig(enabled=False))

    def test_initial_state(self):
        assert not self.vm.config.enabled
        assert self.vm.mode_indicator == ""

    def test_toggle(self):
        assert self.vm.toggle() == True
        assert self.vm.config.enabled
        assert self.vm.toggle() == False

    def test_mode_indicator(self):
        self.vm.enable()
        assert "INSERT" in self.vm.mode_indicator

    def test_editing_mode(self):
        from prompt_toolkit.enums import EditingMode
        assert self.vm.get_editing_mode() == EditingMode.EMACS
        self.vm.enable()
        assert self.vm.get_editing_mode() == EditingMode.VI

    def test_get_status(self):
        status = self.vm.get_status()
        assert "enabled" in status
        assert "mode" in status


# ── Voice Tests ──

class TestVoiceInput:
    def test_not_available_without_package(self):
        from wyn360_cli.voice import VoiceInputManager
        vm = VoiceInputManager()
        # May or may not be available depending on environment
        status = vm.get_status()
        assert "available" in status
        assert "backend" in status

    def test_toggle(self):
        from wyn360_cli.voice import VoiceInputManager
        vm = VoiceInputManager()
        assert vm.toggle() == True
        assert vm.config.enabled
        assert vm.toggle() == False


# ── Buddy Tests ──

class TestBuddy:
    def test_generate_companion(self):
        from wyn360_cli.buddy import generate_companion
        c = generate_companion("test_user")
        assert c.name
        assert c.species
        assert c.rarity in ["common", "uncommon", "rare", "epic", "legendary"]

    def test_deterministic(self):
        from wyn360_cli.buddy import generate_companion
        c1 = generate_companion("same_seed")
        c2 = generate_companion("same_seed")
        assert c1.name == c2.name
        assert c1.species == c2.species

    def test_different_seeds(self):
        from wyn360_cli.buddy import generate_companion
        c1 = generate_companion("user_a")
        c2 = generate_companion("user_b")
        # Very unlikely to be identical
        assert c1.seed != c2.seed

    def test_companion_methods(self):
        from wyn360_cli.buddy import generate_companion
        c = generate_companion("test")
        assert c.emoji
        assert c.display_name
        assert c.greet()
        assert c.react("success")
        assert c.idle()
        assert c.to_dict()

    def test_buddy_manager(self):
        from wyn360_cli.buddy import BuddyManager
        bm = BuddyManager(enabled=True, seed="test")
        assert bm.companion is not None
        assert bm.get_greeting()
        assert bm.get_reaction("error")

    def test_buddy_toggle(self):
        from wyn360_cli.buddy import BuddyManager
        bm = BuddyManager(enabled=False)
        assert bm.toggle() == True
        assert bm.companion is not None
        assert bm.toggle() == False

    def test_buddy_disabled_returns_empty(self):
        from wyn360_cli.buddy import BuddyManager
        bm = BuddyManager(enabled=False)
        assert bm.get_greeting() == ""
        assert bm.get_reaction("success") == ""


# ── Cron Agent Tests ──

class TestCronAgent:
    def setup_method(self):
        from wyn360_cli.cron_agent import CronManager
        self.mgr = CronManager()

    def test_create_job(self):
        job = self.mgr.create_job("Check CI", "Run gh run list", "5m")
        assert job.name == "Check CI"
        assert job.interval_seconds == 300
        assert job.interval_display == "5m"

    def test_parse_interval(self):
        from wyn360_cli.cron_agent import parse_interval
        assert parse_interval("30s") == 30
        assert parse_interval("5m") == 300
        assert parse_interval("1h") == 3600
        assert parse_interval("2h30m") == 9000
        assert parse_interval("10") == 600  # default to minutes

    def test_parse_interval_invalid(self):
        from wyn360_cli.cron_agent import parse_interval
        with pytest.raises(ValueError):
            parse_interval("abc")

    def test_delete_job(self):
        job = self.mgr.create_job("test", "prompt", "1m")
        assert self.mgr.delete_job(job.id)
        assert not self.mgr.delete_job("nonexistent")

    def test_pause_resume(self):
        job = self.mgr.create_job("test", "prompt", "1m")
        self.mgr.pause_job(job.id)
        assert not job.enabled
        self.mgr.resume_job(job.id)
        assert job.enabled

    def test_list_jobs(self):
        self.mgr.create_job("a", "p", "1m")
        self.mgr.create_job("b", "p", "5m")
        assert len(self.mgr.list_jobs()) == 2

    def test_get_due_jobs(self):
        job = self.mgr.create_job("test", "prompt", "1m")
        # Job was just created, so it should be due (next_run_at = created_at)
        import time
        job.last_run_at = 0  # Never run
        due = self.mgr.get_due_jobs()
        assert len(due) >= 1

    def test_get_stats(self):
        stats = self.mgr.get_stats()
        assert "total_jobs" in stats


# ── Plugin System Tests ──

class TestPluginSystem:
    def setup_method(self):
        self.test_dir = Path(tempfile.mkdtemp()) / "plugins"
        from wyn360_cli.plugin_system import PluginManager
        self.pm = PluginManager(plugins_dir=self.test_dir)

    def teardown_method(self):
        shutil.rmtree(self.test_dir.parent)

    def test_discover_empty(self):
        assert self.pm.discover() == []

    def test_create_plugin(self):
        path = self.pm.create_plugin("test-plugin", "tool", "A test plugin")
        assert path.exists()
        assert (path / "plugin.yaml").exists()
        assert (path / "main.py").exists()

    def test_discover_after_create(self):
        self.pm.create_plugin("my-plugin")
        manifests = self.pm.discover()
        assert len(manifests) == 1
        assert manifests[0].name == "my-plugin"

    def test_load_all(self):
        self.pm.create_plugin("test-plugin")
        plugins = self.pm.load_all()
        assert "test-plugin" in plugins
        assert plugins["test-plugin"].loaded

    def test_uninstall(self):
        self.pm.create_plugin("to-remove")
        self.pm.load_all()
        assert self.pm.uninstall("to-remove")
        assert not (self.test_dir / "to-remove").exists()

    def test_uninstall_nonexistent(self):
        assert not self.pm.uninstall("nope")

    def test_get_stats(self):
        self.pm.create_plugin("p1")
        self.pm.load_all()
        stats = self.pm.get_stats()
        assert stats["total_plugins"] == 1
        assert stats["loaded"] == 1


# ── LSP Client Tests ──

class TestLSPClient:
    def test_diagnostic_dataclass(self):
        from wyn360_cli.lsp_client import Diagnostic
        d = Diagnostic(file="test.py", line=10, column=5, severity="error",
                       message="Undefined variable", source="pyright", code="reportUndefined")
        assert d.location == "test.py:10:5"
        assert d.to_dict()["severity"] == "error"

    def test_lsp_client_init(self):
        from wyn360_cli.lsp_client import LSPClient
        client = LSPClient()
        assert isinstance(client.available_servers, list)

    def test_get_summary_empty(self):
        from wyn360_cli.lsp_client import LSPClient
        client = LSPClient()
        summary = client.get_summary()
        assert summary["total"] == 0

    def test_format_diagnostics_empty(self):
        from wyn360_cli.lsp_client import LSPClient
        client = LSPClient()
        assert "No diagnostics" in client.format_diagnostics()

    def test_format_diagnostics_with_items(self):
        from wyn360_cli.lsp_client import LSPClient, Diagnostic
        client = LSPClient()
        diags = [
            Diagnostic("a.py", 1, 0, "error", "Bad", "ruff", "E001"),
            Diagnostic("b.py", 5, 0, "warning", "Warn", "ruff", "W001"),
        ]
        formatted = client.format_diagnostics(diags)
        assert "Bad" in formatted
        assert "Warn" in formatted
        assert "[E]" in formatted
        assert "[W]" in formatted


# ── Rewind Tests ──

class TestRewind:
    def setup_method(self):
        from wyn360_cli.rewind import RewindManager
        self.rm = RewindManager(max_snapshots=5)

    def test_take_snapshot(self):
        messages = [{"role": "user", "content": "hello"}]
        snap = self.rm.take_snapshot(messages, label="test")
        assert snap.id == 1
        assert snap.message_count == 1
        assert snap.label == "test"

    def test_snapshot_auto_increment(self):
        self.rm.take_snapshot([])
        self.rm.take_snapshot([])
        assert self.rm.snapshot_count == 2

    def test_rewind_to(self):
        msgs1 = [{"role": "user", "content": "first"}]
        msgs2 = [{"role": "user", "content": "first"}, {"role": "user", "content": "second"}]
        self.rm.take_snapshot(msgs1, label="turn 1")
        self.rm.take_snapshot(msgs2, label="turn 2")

        result = self.rm.rewind_to(1)
        assert result is not None
        assert len(result) == 1
        assert self.rm.snapshot_count == 1

    def test_rewind_last(self):
        self.rm.take_snapshot([{"role": "user", "content": "a"}])
        self.rm.take_snapshot([{"role": "user", "content": "a"}, {"role": "user", "content": "b"}])
        result = self.rm.rewind_last()
        assert result is not None
        assert len(result) == 1

    def test_rewind_last_nothing(self):
        assert self.rm.rewind_last() is None

    def test_rewind_nonexistent(self):
        assert self.rm.rewind_to(999) is None

    def test_can_rewind(self):
        assert not self.rm.can_rewind
        self.rm.take_snapshot([])
        assert not self.rm.can_rewind
        self.rm.take_snapshot([])
        assert self.rm.can_rewind

    def test_eviction(self):
        for i in range(10):
            self.rm.take_snapshot([{"role": "user", "content": str(i)}])
        assert self.rm.snapshot_count == 5  # max_snapshots=5

    def test_list_snapshots(self):
        for i in range(3):
            self.rm.take_snapshot([], label=f"s{i}")
        listed = self.rm.list_snapshots()
        assert len(listed) == 3
        assert listed[0].label == "s2"  # most recent first

    def test_get_stats(self):
        self.rm.take_snapshot([])
        stats = self.rm.get_stats()
        assert stats["total_snapshots"] == 1
        assert stats["total_rewinds"] == 0
