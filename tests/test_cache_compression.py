"""
Unit tests for Cache Compression (Phase 5.6.2)

Tests cover:
- Compressed cache save/load
- Backward compatibility with uncompressed cache
- Storage size reduction verification
- Migration from uncompressed to compressed
"""

import pytest
import gzip
import json
import tempfile
import time
from pathlib import Path
from wyn360_cli.document_readers import ChunkCache, DocumentMetadata, ChunkMetadata


class TestCacheCompression:
    """Test cache compression functionality (Phase 5.6.2)."""

    def test_save_compressed_cache(self):
        """Test that cache files are saved with gzip compression."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            # Create test metadata and chunks
            metadata = DocumentMetadata(
                file_path="test.txt",
                file_hash="test_hash",
                file_size=1000,
                total_tokens=250,
                chunk_count=2,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 100},
                    summary="Summary 1",
                    tags=["tag1"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                ),
                ChunkMetadata(
                    chunk_id="chunk_1",
                    position={"start": 100, "end": 250},
                    summary="Summary 2",
                    tags=["tag2"],
                    token_count=150,
                    summary_tokens=15,
                    tag_tokens=5
                )
            ]

            # Save chunks
            success = cache.save_chunks("test.txt", metadata, chunks)
            assert success

            # Verify compressed files exist
            file_hash = cache.get_file_hash("test.txt")
            cache_path = cache.get_cache_path(file_hash)

            metadata_file_gz = cache_path / "metadata.json.gz"
            chunks_file_gz = cache_path / "chunks_index.json.gz"

            assert metadata_file_gz.exists()
            assert chunks_file_gz.exists()

            # Verify files are actually compressed (can be read with gzip)
            with gzip.open(metadata_file_gz, 'rt', encoding='utf-8') as f:
                loaded_metadata = json.load(f)
                assert loaded_metadata["file_path"] == "test.txt"

            with gzip.open(chunks_file_gz, 'rt', encoding='utf-8') as f:
                loaded_chunks = json.load(f)
                assert len(loaded_chunks["chunks"]) == 2

    def test_load_compressed_cache(self):
        """Test loading compressed cache files."""
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
                    tags=["tag1", "tag2"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                )
            ]

            # Save and load
            cache.save_chunks("test.txt", metadata, chunks)
            loaded = cache.load_chunks("test.txt")

            # Verify loaded data
            assert loaded is not None
            assert loaded["metadata"]["file_path"] == "test.txt"
            assert len(loaded["chunks"]) == 1
            assert loaded["chunks"][0]["summary"] == "Test summary"

    def test_backward_compatibility_load_uncompressed(self):
        """Test that uncompressed cache files can still be loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            # Manually create uncompressed cache files (old format)
            file_hash = cache.get_file_hash("test.txt")
            cache_path = cache.get_cache_path(file_hash)
            cache_path.mkdir(parents=True, exist_ok=True)

            metadata_file = cache_path / "metadata.json"
            chunks_file = cache_path / "chunks_index.json"

            # Write uncompressed metadata
            metadata_data = {
                "file_path": "test.txt",
                "file_hash": "old_hash",
                "file_size": 1000,
                "total_tokens": 100,
                "chunk_count": 1,
                "chunk_size": 1000,
                "created_at": time.time(),
                "ttl": 3600,
                "doc_type": "text"
            }
            with open(metadata_file, 'w') as f:
                json.dump(metadata_data, f)

            # Write uncompressed chunks
            chunks_data = {
                "chunks": [{
                    "chunk_id": "chunk_0",
                    "position": {"start": 0, "end": 100},
                    "summary": "Old format summary",
                    "tags": ["old"],
                    "token_count": 100,
                    "summary_tokens": 10,
                    "tag_tokens": 5
                }]
            }
            with open(chunks_file, 'w') as f:
                json.dump(chunks_data, f)

            # Load using cache (should work with uncompressed files)
            loaded = cache.load_chunks("test.txt")

            assert loaded is not None
            assert loaded["metadata"]["file_path"] == "test.txt"
            assert loaded["chunks"][0]["summary"] == "Old format summary"

    def test_migration_removes_uncompressed_files(self):
        """Test that saving compressed cache removes old uncompressed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            # Create uncompressed files first
            file_hash = cache.get_file_hash("test.txt")
            cache_path = cache.get_cache_path(file_hash)
            cache_path.mkdir(parents=True, exist_ok=True)

            old_metadata = cache_path / "metadata.json"
            old_chunks = cache_path / "chunks_index.json"

            with open(old_metadata, 'w') as f:
                json.dump({"test": "data"}, f)
            with open(old_chunks, 'w') as f:
                json.dump({"test": "data"}, f)

            assert old_metadata.exists()
            assert old_chunks.exists()

            # Save compressed cache
            metadata = DocumentMetadata(
                file_path="test.txt",
                file_hash="new_hash",
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
                    summary="Test",
                    tags=["test"],
                    token_count=100,
                    summary_tokens=10,
                    tag_tokens=5
                )
            ]

            cache.save_chunks("test.txt", metadata, chunks)

            # Verify old files are removed
            assert not old_metadata.exists()
            assert not old_chunks.exists()

            # Verify compressed files exist
            assert (cache_path / "metadata.json.gz").exists()
            assert (cache_path / "chunks_index.json.gz").exists()

    def test_compression_reduces_storage_size(self):
        """Test that compression significantly reduces storage size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a chunk with repetitive summary (compresses well)
            large_summary = "This is repetitive test summary content. " * 1000

            metadata = DocumentMetadata(
                file_path="test.txt",
                file_hash="test_hash",
                file_size=10000,
                total_tokens=5000,
                chunk_count=1,
                chunk_size=10000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 10000},
                    summary=large_summary,
                    tags=["tag1", "tag2", "tag3"],
                    token_count=5000,
                    summary_tokens=1000,
                    tag_tokens=10
                )
            ]

            # Calculate uncompressed size
            uncompressed_data = json.dumps({
                "chunks": [
                    {
                        "chunk_id": "chunk_0",
                        "position": {"start": 0, "end": 10000},
                        "summary": large_summary,
                        "tags": ["tag1", "tag2", "tag3"],
                        "token_count": 5000,
                        "summary_tokens": 1000,
                        "tag_tokens": 10,
                        "sheet_name": None,
                        "section_title": None,
                        "page_range": None,
                        "embedding": None
                    }
                ]
            }, indent=2)
            uncompressed_size = len(uncompressed_data.encode('utf-8'))

            # Save with compression
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)
            cache.save_chunks("test.txt", metadata, chunks)

            # Get compressed file size
            file_hash = cache.get_file_hash("test.txt")
            cache_path = cache.get_cache_path(file_hash)
            chunks_file_gz = cache_path / "chunks_index.json.gz"

            compressed_size = chunks_file_gz.stat().st_size

            # Verify significant compression (at least 50% reduction)
            compression_ratio = compressed_size / uncompressed_size
            assert compression_ratio < 0.5, f"Compression ratio {compression_ratio:.2%} is not sufficient"

    def test_empty_chunks_compression(self):
        """Test compression with empty chunks list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            metadata = DocumentMetadata(
                file_path="test.txt",
                file_hash="test_hash",
                file_size=0,
                total_tokens=0,
                chunk_count=0,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            # Save with empty chunks
            success = cache.save_chunks("test.txt", metadata, [])
            assert success

            # Load and verify
            loaded = cache.load_chunks("test.txt")
            assert loaded is not None
            assert len(loaded["chunks"]) == 0

    def test_large_chunks_compression(self):
        """Test compression with many large chunks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            # Create 50 chunks with substantial content
            chunks = []
            for i in range(50):
                chunks.append(
                    ChunkMetadata(
                        chunk_id=f"chunk_{i}",
                        position={"start": i * 100, "end": (i + 1) * 100},
                        summary=f"Summary {i}",
                        tags=[f"tag{i}", f"category{i % 5}"],
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=10
                    )
                )

            metadata = DocumentMetadata(
                file_path="large.txt",
                file_hash="large_hash",
                file_size=50000,
                total_tokens=25000,
                chunk_count=50,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            # Save and load
            success = cache.save_chunks("large.txt", metadata, chunks)
            assert success

            loaded = cache.load_chunks("large.txt")
            assert loaded is not None
            assert len(loaded["chunks"]) == 50
            assert loaded["chunks"][25]["summary"] == "Summary 25"

    def test_compression_with_special_characters(self):
        """Test compression with special characters and unicode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            chunks = [
                ChunkMetadata(
                    chunk_id="chunk_0",
                    position={"start": 0, "end": 100},
                    summary="Unicode summary: ñ ü ö ä 中文 日本語 한글",
                    tags=["emoji_😀", "symbols_©®™"],
                    token_count=100,
                    summary_tokens=20,
                    tag_tokens=5
                )
            ]

            metadata = DocumentMetadata(
                file_path="unicode.txt",
                file_hash="unicode_hash",
                file_size=1000,
                total_tokens=100,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            # Save and load
            cache.save_chunks("unicode.txt", metadata, chunks)
            loaded = cache.load_chunks("unicode.txt")

            assert loaded is not None
            assert "中文 日本語 한글" in loaded["chunks"][0]["summary"]
            assert "ñ ü ö ä" in loaded["chunks"][0]["summary"]

    def test_preferring_compressed_over_uncompressed(self):
        """Test that compressed files are preferred when both exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ChunkCache(cache_dir=Path(tmpdir), ttl=3600)

            file_hash = cache.get_file_hash("test.txt")
            cache_path = cache.get_cache_path(file_hash)
            cache_path.mkdir(parents=True, exist_ok=True)

            # Create both compressed and uncompressed files
            # Compressed has "new" content
            current_time = time.time()
            metadata_gz = {
                "file_path": "test.txt",
                "file_hash": "new_hash",
                "file_size": 1000,
                "total_tokens": 100,
                "chunk_count": 1,
                "chunk_size": 1000,
                "created_at": current_time,
                "ttl": 3600,
                "doc_type": "text"
            }
            chunks_gz = {
                "chunks": [{
                    "chunk_id": "chunk_0",
                    "position": {"start": 0, "end": 100},
                    "summary": "New compressed summary",
                    "tags": ["new"],
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
                json.dump(metadata_gz, f)
            with gzip.open(cache_path / "chunks_index.json.gz", 'wt', encoding='utf-8') as f:
                json.dump(chunks_gz, f)

            # Uncompressed has "old" content
            metadata_old = metadata_gz.copy()
            chunks_old = {
                "chunks": [{
                    "chunk_id": "chunk_0",
                    "position": {"start": 0, "end": 100},
                    "summary": "Old uncompressed summary",
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

            with open(cache_path / "metadata.json", 'w') as f:
                json.dump(metadata_old, f)
            with open(cache_path / "chunks_index.json", 'w') as f:
                json.dump(chunks_old, f)

            # Load - should prefer compressed
            loaded = cache.load_chunks("test.txt")

            assert loaded is not None
            assert loaded["chunks"][0]["summary"] == "New compressed summary"
            assert loaded["chunks"][0]["tags"] == ["new"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
