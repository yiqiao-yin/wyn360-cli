"""
Unit tests for ChunkCache class (Phase 13.1)

Tests cover:
- Cache initialization
- Saving and loading chunks
- TTL-based expiration
- Cache clearing (all and specific)
- Cache statistics
- File hashing
- Size management and cleanup
"""

import pytest
import tempfile
import time
from pathlib import Path
from wyn360_cli.document_readers import ChunkCache, ChunkMetadata, DocumentMetadata


class TestChunkCache:
    """Test ChunkCache functionality."""

    def test_cache_initialization(self):
        """Test cache initializes with correct parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir, ttl=3600, max_size_mb=100)

            assert cache.cache_dir == cache_dir
            assert cache.ttl == 3600
            assert cache.max_size_mb == 100
            assert cache.cache_dir.exists()

    def test_cache_default_directory(self):
        """Test cache uses default directory if not specified."""
        cache = ChunkCache()

        expected_dir = Path.home() / ".wyn360" / "cache" / "documents"
        assert cache.cache_dir == expected_dir
        assert cache.cache_dir.exists()

    def test_get_file_hash_consistent(self):
        """Test that same file produces same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Test content")

            hash1 = cache.get_file_hash(str(test_file))
            hash2 = cache.get_file_hash(str(test_file))

            assert hash1 == hash2

    def test_get_file_hash_changes_on_modification(self):
        """Test that hash changes when file is modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("Original content")

            hash1 = cache.get_file_hash(str(test_file))

            # Modify file
            time.sleep(0.1)  # Ensure mtime changes
            test_file.write_text("Modified content")

            hash2 = cache.get_file_hash(str(test_file))

            assert hash1 != hash2

    def test_save_and_load_chunks(self):
        """Test saving and loading chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir, ttl=3600)

            test_file = Path(tmpdir) / "test.xlsx"
            test_file.write_text("Dummy content")

            # Create metadata
            metadata = DocumentMetadata(
                file_path=str(test_file),
                file_hash="test_hash",
                file_size=1000,
                total_tokens=5000,
                chunk_count=5,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="excel"
            )

            # Create chunks
            chunks = [
                ChunkMetadata(
                    chunk_id="001",
                    position={"start": 0, "end": 1000},
                    summary="Summary of chunk 1",
                    tags=["tag1", "tag2", "tag3"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=10,
                    sheet_name="Sheet1"
                ),
                ChunkMetadata(
                    chunk_id="002",
                    position={"start": 1000, "end": 2000},
                    summary="Summary of chunk 2",
                    tags=["tag4", "tag5"],
                    token_count=1000,
                    summary_tokens=95,
                    tag_tokens=8,
                    sheet_name="Sheet1"
                )
            ]

            # Save
            success = cache.save_chunks(str(test_file), metadata, chunks)
            assert success is True

            # Load
            loaded = cache.load_chunks(str(test_file))
            assert loaded is not None
            assert "metadata" in loaded
            assert "chunks" in loaded
            assert len(loaded["chunks"]) == 2
            assert loaded["chunks"][0]["chunk_id"] == "001"
            assert loaded["chunks"][0]["summary"] == "Summary of chunk 1"
            assert loaded["chunks"][1]["chunk_id"] == "002"

    def test_load_chunks_cache_miss(self):
        """Test loading chunks when no cache exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            test_file = Path(tmpdir) / "nonexistent.xlsx"

            loaded = cache.load_chunks(str(test_file))
            assert loaded is None

    def test_cache_ttl_expiration(self):
        """Test that cache expires after TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir, ttl=1)  # 1 second TTL

            test_file = Path(tmpdir) / "test.xlsx"
            test_file.write_text("Content")

            metadata = DocumentMetadata(
                file_path=str(test_file),
                file_hash="hash",
                file_size=100,
                total_tokens=1000,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=1,
                doc_type="excel"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="001",
                    position={"start": 0, "end": 1000},
                    summary="Summary",
                    tags=["tag"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=5
                )
            ]

            # Save
            cache.save_chunks(str(test_file), metadata, chunks)

            # Immediately load - should work
            loaded = cache.load_chunks(str(test_file))
            assert loaded is not None

            # Wait for expiration
            time.sleep(2)

            # Load again - should be expired
            loaded = cache.load_chunks(str(test_file))
            assert loaded is None

    def test_clear_cache_specific_file(self):
        """Test clearing cache for specific file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            file1 = Path(tmpdir) / "file1.xlsx"
            file2 = Path(tmpdir) / "file2.xlsx"
            file1.write_text("Content 1")
            file2.write_text("Content 2")

            metadata = DocumentMetadata(
                file_path="",
                file_hash="hash",
                file_size=100,
                total_tokens=1000,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="excel"
            )

            chunks = [ChunkMetadata(
                chunk_id="001",
                position={},
                summary="Summary",
                tags=["tag"],
                token_count=1000,
                summary_tokens=100,
                tag_tokens=5
            )]

            # Save both
            metadata.file_path = str(file1)
            cache.save_chunks(str(file1), metadata, chunks)
            metadata.file_path = str(file2)
            cache.save_chunks(str(file2), metadata, chunks)

            # Clear file1
            count = cache.clear_cache(str(file1))
            assert count == 1

            # file1 should be gone
            assert cache.load_chunks(str(file1)) is None
            # file2 should still exist
            assert cache.load_chunks(str(file2)) is not None

    def test_clear_cache_all(self):
        """Test clearing all cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create multiple cached files
            for i in range(3):
                test_file = Path(tmpdir) / f"file{i}.xlsx"
                test_file.write_text(f"Content {i}")

                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=f"hash{i}",
                    file_size=100,
                    total_tokens=1000,
                    chunk_count=1,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="excel"
                )

                chunks = [ChunkMetadata(
                    chunk_id="001",
                    position={},
                    summary=f"Summary {i}",
                    tags=["tag"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=5
                )]

                cache.save_chunks(str(test_file), metadata, chunks)

            # Clear all
            count = cache.clear_cache()
            assert count == 3

            # All should be gone
            for i in range(3):
                test_file = Path(tmpdir) / f"file{i}.xlsx"
                assert cache.load_chunks(str(test_file)) is None

    def test_get_stats_empty_cache(self):
        """Test statistics for empty cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            stats = cache.get_stats()

            assert stats["total_files"] == 0
            assert stats["total_chunks"] == 0
            assert stats["total_size_mb"] == 0
            assert stats["oldest_cache"] == "N/A"
            assert stats["newest_cache"] == "N/A"
            assert len(stats["cache_entries"]) == 0

    def test_get_stats_with_cached_files(self):
        """Test statistics with cached files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Add cached files
            for i in range(2):
                test_file = Path(tmpdir) / f"file{i}.xlsx"
                test_file.write_text(f"Content {i}")

                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=f"hash{i}",
                    file_size=100,
                    total_tokens=1000,
                    chunk_count=5,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="excel"
                )

                chunks = [
                    ChunkMetadata(
                        chunk_id=f"00{j}",
                        position={},
                        summary=f"Summary {j}",
                        tags=["tag"],
                        token_count=1000,
                        summary_tokens=100,
                        tag_tokens=5
                    )
                    for j in range(5)
                ]

                cache.save_chunks(str(test_file), metadata, chunks)

            stats = cache.get_stats()

            assert stats["total_files"] == 2
            assert stats["total_chunks"] == 10  # 2 files × 5 chunks
            assert stats["total_size_mb"] > 0
            assert stats["oldest_cache"] != "N/A"
            assert stats["newest_cache"] != "N/A"
            assert len(stats["cache_entries"]) == 2

    def test_format_age(self):
        """Test age formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Test different time ranges
            assert "sec ago" in cache._format_age(30)
            assert "min ago" in cache._format_age(120)
            assert "hours ago" in cache._format_age(7200)
            assert "days ago" in cache._format_age(172800)

    def test_cache_survives_multiple_operations(self):
        """Test that cache works correctly across multiple save/load cycles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            test_file = Path(tmpdir) / "test.xlsx"
            test_file.write_text("Content")

            metadata = DocumentMetadata(
                file_path=str(test_file),
                file_hash="hash",
                file_size=100,
                total_tokens=2000,
                chunk_count=2,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="excel"
            )

            chunks_v1 = [
                ChunkMetadata(
                    chunk_id="001",
                    position={},
                    summary="Version 1",
                    tags=["v1"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=5
                )
            ]

            # Save v1
            cache.save_chunks(str(test_file), metadata, chunks_v1)

            # Load v1
            loaded = cache.load_chunks(str(test_file))
            assert loaded["chunks"][0]["summary"] == "Version 1"

            # Modify file to trigger new hash
            time.sleep(0.1)
            test_file.write_text("Modified content")

            chunks_v2 = [
                ChunkMetadata(
                    chunk_id="001",
                    position={},
                    summary="Version 2",
                    tags=["v2"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=5
                )
            ]

            # Save v2 (should be different cache)
            metadata.created_at = time.time()
            cache.save_chunks(str(test_file), metadata, chunks_v2)

            # Load v2
            loaded = cache.load_chunks(str(test_file))
            assert loaded["chunks"][0]["summary"] == "Version 2"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
