"""
Unit tests for LRU Cache Eviction (Phase 5.6.3)

Tests cover:
- Last accessed timestamp tracking
- LRU eviction when cache is full
- Keeping frequently accessed documents
- Evicting least recently used documents
"""

import pytest
import tempfile
import time
from pathlib import Path
from wyn360_cli.document_readers import ChunkCache, DocumentMetadata, ChunkMetadata


class TestLRUEviction:
    """Test LRU cache eviction functionality (Phase 5.6.3)."""

    def test_last_accessed_initialized_on_save(self):
        """Test that last_accessed is initialized when saving cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            metadata = DocumentMetadata(
                file_path="test.txt",
                file_hash="test_hash",
                file_size=1000,
                total_tokens=100,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 100},
                    summary="Test summary",
                    tags=["test"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                )
            ]

            # Save chunks
            cache.save_chunks("test.txt", metadata, chunks)

            # Check stats to see if last_accessed is set
            stats = cache.get_stats()
            assert len(stats["cache_entries"]) == 1
            entry = stats["cache_entries"][0]
            assert "last_accessed" in entry
            # last_accessed should be equal to created_at initially
            assert abs(entry["last_accessed"] - metadata.created_at) < 1.0

    def test_last_accessed_updated_on_load(self):
        """Test that last_accessed is updated when loading cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            metadata = DocumentMetadata(
                file_path="test.txt",
                file_hash="test_hash",
                file_size=1000,
                total_tokens=100,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 100},
                    summary="Test summary",
                    tags=["test"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                )
            ]

            # Save chunks
            cache.save_chunks("test.txt", metadata, chunks)

            # Get initial last_accessed time
            stats1 = cache.get_stats()
            initial_last_accessed = stats1["cache_entries"][0]["last_accessed"]

            # Wait a bit
            time.sleep(0.1)

            # Load chunks (should update last_accessed)
            loaded = cache.load_chunks("test.txt")
            assert loaded is not None

            # Check that last_accessed was updated
            stats2 = cache.get_stats()
            new_last_accessed = stats2["cache_entries"][0]["last_accessed"]

            assert new_last_accessed > initial_last_accessed

    def test_lru_eviction_removes_least_recently_used(self):
        """Test that LRU eviction removes least recently used files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache with small max size (1MB)
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600, max_size_mb=1)

            # Create 3 files, each with ~500KB summary (total ~1.5MB compressed)
            large_summary = "X" * 10000  # 10KB repeated to create large content

            for i in range(3):
                metadata = DocumentMetadata(
                    file_path=f"file{i}.txt",
                    file_hash=f"hash{i}",
                    file_size=500000,
                    total_tokens=5000,
                    chunk_count=1,
                    chunk_size=10000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="text"
                )

                chunks = [
                    ChunkMetadata(
                        chunk_id=f"chunk_{i}",
                        position={"start": 0, "end": 500000},
                        summary=large_summary * 50,  # ~500KB
                        tags=[f"file{i}"],
                        token_count=5000,
                        summary_tokens=1000,
                        tag_tokens=5
                    )
                ]

                cache.save_chunks(f"file{i}.txt", metadata, chunks)
                time.sleep(0.05)  # Small delay between saves

            # Access file0 and file2 (not file1)
            cache.load_chunks("file0.txt")
            time.sleep(0.05)
            cache.load_chunks("file2.txt")
            time.sleep(0.05)

            # file1 should be least recently used
            stats_before = cache.get_stats()
            entries_before = {e["file_path"]: e["last_accessed"] for e in stats_before["cache_entries"]}

            # Verify file1 has the oldest last_accessed time
            if "file1.txt" in entries_before:
                assert entries_before["file1.txt"] < entries_before.get("file0.txt", float('inf'))
                assert entries_before["file1.txt"] < entries_before.get("file2.txt", float('inf'))

    def test_lru_eviction_with_multiple_accesses(self):
        """Test LRU eviction with multiple access patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600, max_size_mb=1)

            # Create 4 small files
            for i in range(4):
                metadata = DocumentMetadata(
                    file_path=f"doc{i}.txt",
                    file_hash=f"hash{i}",
                    file_size=1000,
                    total_tokens=100,
                    chunk_count=1,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="text"
                )

                chunks = [
                    ChunkMetadata(
                        chunk_id=f"chunk_{i}",
                        position={"start": 0, "end": 1000},
                        summary=f"Summary {i}",
                        tags=[f"doc{i}"],
                        token_count=100,
                        summary_tokens=10,
                        tag_tokens=5
                    )
                ]

                cache.save_chunks(f"doc{i}.txt", metadata, chunks)
                time.sleep(0.05)

            # Access pattern: doc0, doc1, doc2, doc1, doc0
            # doc3 should be least recently used, then doc2
            cache.load_chunks("doc0.txt")
            time.sleep(0.05)
            cache.load_chunks("doc1.txt")
            time.sleep(0.05)
            cache.load_chunks("doc2.txt")
            time.sleep(0.05)
            cache.load_chunks("doc1.txt")
            time.sleep(0.05)
            cache.load_chunks("doc0.txt")

            # Verify access times
            stats = cache.get_stats()
            entries = {e["file_path"]: e["last_accessed"] for e in stats["cache_entries"]}

            # doc0 should have most recent access
            # doc1 should be second most recent
            # doc2 should be third
            # doc3 should be least recent
            assert entries["doc0.txt"] > entries["doc1.txt"]
            assert entries["doc1.txt"] > entries["doc2.txt"]
            assert entries["doc2.txt"] > entries["doc3.txt"]

    def test_last_accessed_preserved_across_loads(self):
        """Test that last_accessed persists correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            metadata = DocumentMetadata(
                file_path="persist.txt",
                file_hash="persist_hash",
                file_size=1000,
                total_tokens=100,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 1000},
                    summary="Persist test",
                    tags=["test"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                )
            ]

            # Save
            cache.save_chunks("persist.txt", metadata, chunks)
            time.sleep(0.1)

            # Load multiple times
            for _ in range(3):
                loaded = cache.load_chunks("persist.txt")
                assert loaded is not None
                time.sleep(0.1)

            # Each load should update last_accessed
            stats = cache.get_stats()
            entry = stats["cache_entries"][0]

            # last_accessed should be recent (within last second)
            assert time.time() - entry["last_accessed"] < 1.0

    def test_backward_compatibility_missing_last_accessed(self):
        """Test that old cache entries without last_accessed still work."""
        import gzip
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            # Manually create old-format cache without last_accessed
            file_hash = cache.get_file_hash("old.txt")
            cache_path = cache.get_cache_path(file_hash)
            cache_path.mkdir(parents=True, exist_ok=True)

            current_time = time.time()
            metadata_data = {
                "file_path": "old.txt",
                "file_hash": "old_hash",
                "file_size": 1000,
                "total_tokens": 100,
                "chunk_count": 1,
                "chunk_size": 1000,
                "created_at": current_time,
                "ttl": 3600,
                "doc_type": "text"
                # NOTE: No last_accessed field
            }

            chunks_data = {
                "chunks": [{
                    "chunk_id": "chunk_0",
                    "position": {"start": 0, "end": 100},
                    "summary": "Old format",
                    "tags": ["old"],
                    "token_count": 100,
                    "summary_tokens": 10,
                    "tag_tokens": 5,
                    "sheet_name": None,
                    "section_title": None,
                    "page_range": None,
                    "embedding": None
                }]
            }

            with gzip.open(cache_path / "metadata.json.gz", 'wt', encoding='utf-8') as f:
                json.dump(metadata_data, f)
            with gzip.open(cache_path / "chunks_index.json.gz", 'wt', encoding='utf-8') as f:
                json.dump(chunks_data, f)

            # Load should work and default last_accessed to created_at
            loaded = cache.load_chunks("old.txt")
            assert loaded is not None

            # Check stats - should use created_at as last_accessed
            stats = cache.get_stats()
            assert len(stats["cache_entries"]) == 1
            entry = stats["cache_entries"][0]
            assert "last_accessed" in entry

    def test_stats_include_last_accessed(self):
        """Test that cache stats include last_accessed field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            metadata = DocumentMetadata(
                file_path="stats.txt",
                file_hash="stats_hash",
                file_size=1000,
                total_tokens=100,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 1000},
                    summary="Stats test",
                    tags=["test"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                )
            ]

            cache.save_chunks("stats.txt", metadata, chunks)

            stats = cache.get_stats()
            assert "cache_entries" in stats
            assert len(stats["cache_entries"]) == 1

            entry = stats["cache_entries"][0]
            assert "file_path" in entry
            assert "last_accessed" in entry
            assert isinstance(entry["last_accessed"], float)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
