"""Tests for dream (memory consolidation) system."""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock
from wyn360_cli.dream import DreamManager, DreamConfig, DreamState


class TestDreamManager:
    def setup_method(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.dream_dir = self.test_dir / "dream"
        self.session_dir = self.test_dir / "sessions"
        self.session_dir.mkdir(parents=True)
        self.dm = DreamManager(state_dir=self.dream_dir, config=DreamConfig(min_hours=0, min_sessions=1))

    def teardown_method(self):
        shutil.rmtree(self.test_dir)

    def test_initial_state(self):
        assert self.dm.state.total_dreams == 0
        assert not self.dm.state.is_dreaming

    def test_should_dream_no_sessions(self):
        assert not self.dm.should_dream(self.session_dir)

    def test_should_dream_with_sessions(self):
        (self.session_dir / "s1.json").write_text('[]')
        assert self.dm.should_dream(self.session_dir)

    def test_should_dream_disabled(self):
        self.dm.config.enabled = False
        (self.session_dir / "s1.json").write_text('[]')
        assert not self.dm.should_dream(self.session_dir)

    def test_lock_mechanism(self):
        assert self.dm._acquire_lock()
        assert self.dm._is_locked()
        self.dm._release_lock()
        assert not self.dm._is_locked()

    def test_state_persistence(self):
        self.dm.state.total_dreams = 5
        self.dm.state.sessions_reviewed = 10
        self.dm._save_state()
        dm2 = DreamManager(state_dir=self.dream_dir)
        assert dm2.state.total_dreams == 5
        assert dm2.state.sessions_reviewed == 10

    def test_get_status(self):
        status = self.dm.get_status()
        assert "enabled" in status
        assert "total_dreams" in status
        assert "hours_since_last" in status

    def test_parse_memories(self):
        from wyn360_cli.memory import MemoryManager
        mem_dir = self.test_dir / "memory"
        mm = MemoryManager(memory_dir=mem_dir)
        response = """Found some useful info.
MEMORY: user | Coding Style | User prefers type hints
Always use type hints in Python code.
END_MEMORY
MEMORY: project | Tech Stack | Project uses FastAPI
The project is built with FastAPI and PostgreSQL.
END_MEMORY"""
        saved = self.dm._parse_and_save_memories(response, mm)
        assert len(saved) == 2
        assert mm.list_memories()

    def test_parse_no_memories(self):
        mm = MagicMock()
        saved = self.dm._parse_and_save_memories("NO_NEW_MEMORIES", mm)
        assert saved == []

    def test_gather_sessions(self):
        session = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
        (self.session_dir / "s1.json").write_text(json.dumps(session))
        summaries = self.dm._gather_session_summaries(self.session_dir)
        assert len(summaries) == 1
        assert "Hello" in summaries[0]

    def test_state_to_dict(self):
        state = DreamState(total_dreams=3, sessions_reviewed=7)
        d = state.to_dict()
        assert d["total_dreams"] == 3
        assert d["sessions_reviewed"] == 7
