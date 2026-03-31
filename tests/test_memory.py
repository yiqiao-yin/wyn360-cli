"""Unit tests for the memory system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from wyn360_cli.memory import MemoryManager, MemoryEntry


class TestMemoryManager:
    """Tests for MemoryManager class."""

    def setup_method(self):
        self.test_dir = Path(tempfile.mkdtemp()) / "memory"
        self.mm = MemoryManager(memory_dir=self.test_dir)

    def teardown_method(self):
        shutil.rmtree(self.test_dir.parent)

    def test_save_and_get_memory(self):
        filename = self.mm.save_memory(
            name="Test User Role",
            description="User is a backend engineer",
            memory_type="user",
            content="The user is a senior backend engineer with Python expertise."
        )
        assert filename.endswith(".md")

        entry = self.mm.get_memory(filename)
        assert entry is not None
        assert entry.name == "Test User Role"
        assert entry.type == "user"
        assert "backend engineer" in entry.content

    def test_save_updates_index(self):
        self.mm.save_memory("My Note", "A note", "project", "Some content")
        index = self.mm.get_index_content()
        assert "My Note" in index

    def test_delete_memory(self):
        filename = self.mm.save_memory("ToDelete", "temp", "feedback", "will be deleted")
        assert self.mm.delete_memory(filename)
        assert self.mm.get_memory(filename) is None
        # Should be removed from index
        assert filename not in self.mm.get_index_content()

    def test_delete_nonexistent(self):
        assert not self.mm.delete_memory("nonexistent.md")

    def test_list_memories(self):
        self.mm.save_memory("Mem1", "First", "user", "content 1")
        self.mm.save_memory("Mem2", "Second", "project", "content 2")
        memories = self.mm.list_memories()
        assert len(memories) == 2
        names = {m.name for m in memories}
        assert "Mem1" in names
        assert "Mem2" in names

    def test_list_empty(self):
        assert self.mm.list_memories() == []

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid memory type"):
            self.mm.save_memory("Bad", "bad", "invalid_type", "content")

    def test_find_relevant_memories(self):
        self.mm.save_memory("Python Style", "Python coding preferences", "feedback", "Use type hints always")
        self.mm.save_memory("Deploy Process", "How to deploy to prod", "project", "Run deploy.sh")
        self.mm.save_memory("User Role", "User is a developer", "user", "Senior Python developer")

        results = self.mm.find_relevant_memories("python coding style")
        assert len(results) > 0
        # Should find the Python Style memory
        names = [r.name for r in results]
        assert "Python Style" in names

    def test_find_relevant_no_match(self):
        self.mm.save_memory("Unrelated", "About cats", "project", "Cats are great")
        results = self.mm.find_relevant_memories("kubernetes deployment")
        # Might find 0 or low-relevance results
        assert isinstance(results, list)

    def test_build_memory_prompt_empty(self):
        assert self.mm.build_memory_prompt() == ""

    def test_build_memory_prompt_with_content(self):
        self.mm.save_memory("Test", "test memory", "user", "content")
        prompt = self.mm.build_memory_prompt()
        assert "Memory" in prompt
        assert "Test" in prompt

    def test_index_truncation(self):
        # Create more than MAX_INDEX_LINES entries
        for i in range(250):
            self.mm.save_memory(f"Mem{i}", f"desc{i}", "project", f"content{i}")
        index = self.mm.get_index_content()
        assert "WARNING" in index or "Truncated" in index.lower() or len(index.split("\n")) <= 202

    def test_custom_filename(self):
        filename = self.mm.save_memory("Test", "desc", "user", "content", filename="custom_file.md")
        assert filename == "custom_file.md"
        assert (self.test_dir / "custom_file.md").exists()

    def test_memory_entry_to_frontmatter(self):
        entry = MemoryEntry(
            name="Test",
            description="A test",
            type="user",
            content="Hello world",
            filename="test.md",
        )
        fm = entry.to_frontmatter()
        assert "---" in fm
        assert "name: Test" in fm
        assert "Hello world" in fm
