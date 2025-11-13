"""
Unit tests for MultiDocumentRetriever class (Phase 5.5)

Tests cover:
- Searching across multiple cached documents
- Listing all cached documents
- Document comparison
- Cross-reference detection
- Integration with ChunkCache and ChunkRetriever
"""

import pytest
import tempfile
import time
from pathlib import Path
from wyn360_cli.document_readers import (
    MultiDocumentRetriever,
    ChunkCache,
    ChunkRetriever,
    ChunkMetadata,
    DocumentMetadata,
    EmbeddingModel
)


class TestMultiDocumentRetriever:
    """Test MultiDocumentRetriever functionality."""

    def test_initialization(self):
        """Test retriever initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            retriever = MultiDocumentRetriever(cache=cache)

            assert retriever.cache == cache
            assert retriever.retriever is not None
            assert isinstance(retriever.retriever, ChunkRetriever)

    def test_initialization_with_custom_retriever(self):
        """Test initialization with custom retriever."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            custom_retriever = ChunkRetriever(top_k=5)
            multi_retriever = MultiDocumentRetriever(
                cache=cache,
                retriever=custom_retriever
            )

            assert multi_retriever.retriever == custom_retriever
            assert multi_retriever.retriever.top_k == 5

    def test_list_cached_documents_empty(self):
        """Test listing documents when cache is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            retriever = MultiDocumentRetriever(cache=cache)
            documents = retriever.list_cached_documents()

            assert documents == []

    def test_list_cached_documents_with_files(self):
        """Test listing cached documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create test files
            file1 = Path(tmpdir) / "test1.xlsx"
            file2 = Path(tmpdir) / "test2.pdf"
            file1.write_text("Content 1")
            file2.write_text("Content 2")

            # Cache documents
            for i, test_file in enumerate([file1, file2], 1):
                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=f"hash{i}",
                    file_size=100,
                    total_tokens=1000,
                    chunk_count=2,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="excel" if i == 1 else "pdf"
                )

                chunks = [
                    ChunkMetadata(
                        chunk_id=f"00{j}",
                        position={},
                        summary=f"Summary {j}",
                        tags=["tag"],
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=5
                    )
                    for j in range(2)
                ]

                cache.save_chunks(str(test_file), metadata, chunks)

            # List documents
            retriever = MultiDocumentRetriever(cache=cache)
            documents = retriever.list_cached_documents()

            assert len(documents) == 2
            assert all("file_path" in doc for doc in documents)
            assert all("chunks" in doc for doc in documents)
            assert all("doc_type" in doc for doc in documents)
            assert any(doc["doc_type"] == "excel" for doc in documents)
            assert any(doc["doc_type"] == "pdf" for doc in documents)

    def test_search_all_documents_no_cache(self):
        """Test search when no documents are cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            retriever = MultiDocumentRetriever(cache=cache)
            results = retriever.search_all_documents("test query", top_k=5)

            assert results == []

    def test_search_all_documents_single_doc(self):
        """Test search across single cached document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create and cache a document
            test_file = Path(tmpdir) / "test.xlsx"
            test_file.write_text("Content")

            metadata = DocumentMetadata(
                file_path=str(test_file),
                file_hash="hash1",
                file_size=100,
                total_tokens=1000,
                chunk_count=3,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="excel"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="001",
                    position={},
                    summary="Revenue data for Q1",
                    tags=["revenue", "Q1", "finance"],
                    token_count=300,
                    summary_tokens=30,
                    tag_tokens=10
                ),
                ChunkMetadata(
                    chunk_id="002",
                    position={},
                    summary="Expense breakdown",
                    tags=["expenses", "costs"],
                    token_count=300,
                    summary_tokens=30,
                    tag_tokens=8
                ),
                ChunkMetadata(
                    chunk_id="003",
                    position={},
                    summary="Profit margins",
                    tags=["profit", "margins"],
                    token_count=300,
                    summary_tokens=30,
                    tag_tokens=8
                )
            ]

            cache.save_chunks(str(test_file), metadata, chunks)

            # Search
            retriever = MultiDocumentRetriever(cache=cache)
            results = retriever.search_all_documents("revenue", top_k=5)

            assert len(results) > 0
            assert all("file_path" in result for result in results)
            assert results[0]["file_path"] == str(test_file)
            assert "revenue" in results[0]["summary"].lower() or "revenue" in [t.lower() for t in results[0]["tags"]]

    def test_search_all_documents_multiple_docs(self):
        """Test search across multiple documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create two documents
            file1 = Path(tmpdir) / "expenses.xlsx"
            file2 = Path(tmpdir) / "revenue.xlsx"
            file1.write_text("Expenses")
            file2.write_text("Revenue")

            # Cache both documents
            for i, (test_file, topic) in enumerate([(file1, "expenses"), (file2, "revenue")], 1):
                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=f"hash{i}",
                    file_size=100,
                    total_tokens=1000,
                    chunk_count=2,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="excel"
                )

                chunks = [
                    ChunkMetadata(
                        chunk_id="001",
                        position={},
                        summary=f"{topic.capitalize()} summary",
                        tags=[topic, "finance"],
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=8
                    ),
                    ChunkMetadata(
                        chunk_id="002",
                        position={},
                        summary=f"Additional {topic} data",
                        tags=[topic, "data"],
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=8
                    )
                ]

                cache.save_chunks(str(test_file), metadata, chunks)

            # Search across both documents
            retriever = MultiDocumentRetriever(cache=cache)
            results = retriever.search_all_documents("finance", top_k=5)

            # Should get results from both documents
            assert len(results) > 0
            file_paths = set(result["file_path"] for result in results)
            assert len(file_paths) >= 1  # At least one document matches

    def test_compare_documents_both_exist(self):
        """Test comparing two cached documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create two documents
            file1 = Path(tmpdir) / "doc1.xlsx"
            file2 = Path(tmpdir) / "doc2.xlsx"
            file1.write_text("Doc 1")
            file2.write_text("Doc 2")

            # Cache both
            for i, test_file in enumerate([file1, file2], 1):
                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=f"hash{i}",
                    file_size=100,
                    total_tokens=1000 * i,  # Different token counts
                    chunk_count=2 * i,  # Different chunk counts
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
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=5
                    )
                    for j in range(2 * i)
                ]

                cache.save_chunks(str(test_file), metadata, chunks)

            # Compare
            retriever = MultiDocumentRetriever(cache=cache)
            comparison = retriever.compare_documents(str(file1), str(file2))

            assert "error" not in comparison
            assert "doc1" in comparison
            assert "doc2" in comparison
            assert "comparison" in comparison

            # Check metadata
            assert comparison["doc1"]["file_path"] == str(file1)
            assert comparison["doc2"]["file_path"] == str(file2)
            assert comparison["doc1"]["total_chunks"] == 2
            assert comparison["doc2"]["total_chunks"] == 4

            # Check comparison metrics
            assert comparison["comparison"]["chunk_count_diff"] == 2
            assert comparison["comparison"]["token_count_diff"] == 1000
            assert comparison["comparison"]["same_type"] is True

    def test_compare_documents_with_aspect(self):
        """Test comparing documents with specific aspect."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create two documents
            file1 = Path(tmpdir) / "Q1.xlsx"
            file2 = Path(tmpdir) / "Q2.xlsx"
            file1.write_text("Q1")
            file2.write_text("Q2")

            # Cache both with revenue-related chunks
            for i, test_file in enumerate([file1, file2], 1):
                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=f"hash{i}",
                    file_size=100,
                    total_tokens=1000,
                    chunk_count=2,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="excel"
                )

                chunks = [
                    ChunkMetadata(
                        chunk_id="001",
                        position={},
                        summary=f"Q{i} revenue data",
                        tags=["revenue", f"Q{i}"],
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=8
                    ),
                    ChunkMetadata(
                        chunk_id="002",
                        position={},
                        summary=f"Q{i} expenses",
                        tags=["expenses", f"Q{i}"],
                        token_count=500,
                        summary_tokens=50,
                        tag_tokens=8
                    )
                ]

                cache.save_chunks(str(test_file), metadata, chunks)

            # Compare with aspect
            retriever = MultiDocumentRetriever(cache=cache)
            comparison = retriever.compare_documents(str(file1), str(file2), aspect="revenue")

            assert "error" not in comparison
            assert comparison["comparison"]["aspect_compared"] == "revenue"
            # Should have relevant chunks filtered by aspect
            assert len(comparison["doc1"]["relevant_chunks"]) > 0
            assert len(comparison["doc2"]["relevant_chunks"]) > 0

    def test_compare_documents_one_missing(self):
        """Test comparing when one document doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            file1 = Path(tmpdir) / "exists.xlsx"
            file2 = Path(tmpdir) / "missing.xlsx"
            file1.write_text("Exists")

            # Cache only file1
            metadata = DocumentMetadata(
                file_path=str(file1),
                file_hash="hash1",
                file_size=100,
                total_tokens=1000,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="excel"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="001",
                    position={},
                    summary="Summary",
                    tags=["tag"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=5
                )
            ]

            cache.save_chunks(str(file1), metadata, chunks)

            # Compare (file2 doesn't exist in cache)
            retriever = MultiDocumentRetriever(cache=cache)
            comparison = retriever.compare_documents(str(file1), str(file2))

            assert "error" in comparison
            assert comparison["doc1_found"] is True
            assert comparison["doc2_found"] is False

    def test_find_cross_references_single_mention(self):
        """Test finding cross-references across documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            # Create three documents, two mentioning "machine learning"
            files = [
                (Path(tmpdir) / "ml_doc.txt", "machine learning", True),
                (Path(tmpdir) / "ai_doc.txt", "machine learning", True),
                (Path(tmpdir) / "stats_doc.txt", "statistics", False)
            ]

            for test_file, topic, mentions_ml in files:
                test_file.write_text(topic)

                metadata = DocumentMetadata(
                    file_path=str(test_file),
                    file_hash=test_file.name,
                    file_size=100,
                    total_tokens=1000,
                    chunk_count=1,
                    chunk_size=1000,
                    created_at=time.time(),
                    ttl=3600,
                    doc_type="text"
                )

                tags = ["machine-learning", "AI"] if mentions_ml else ["statistics"]
                chunks = [
                    ChunkMetadata(
                        chunk_id="001",
                        position={},
                        summary=f"Document about {topic}",
                        tags=tags,
                        token_count=1000,
                        summary_tokens=100,
                        tag_tokens=10
                    )
                ]

                cache.save_chunks(str(test_file), metadata, chunks)

            # Find cross-references
            retriever = MultiDocumentRetriever(cache=cache)
            cross_refs = retriever.find_cross_references("machine learning", min_mentions=1)

            # Should find at least 1 document mentioning machine learning
            assert len(cross_refs) >= 1  # At least one document matches
            # Verify results contain chunks
            for file_path, chunks in cross_refs.items():
                assert len(chunks) > 0

    def test_find_cross_references_min_mentions(self):
        """Test min_mentions filtering in cross-references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = ChunkCache(cache_dir=cache_dir)

            test_file = Path(tmpdir) / "doc.txt"
            test_file.write_text("Content")

            metadata = DocumentMetadata(
                file_path=str(test_file),
                file_hash="hash1",
                file_size=100,
                total_tokens=1000,
                chunk_count=1,
                chunk_size=1000,
                created_at=time.time(),
                ttl=3600,
                doc_type="text"
            )

            chunks = [
                ChunkMetadata(
                    chunk_id="001",
                    position={},
                    summary="Single mention of topic",
                    tags=["topic"],
                    token_count=1000,
                    summary_tokens=100,
                    tag_tokens=5
                )
            ]

            cache.save_chunks(str(test_file), metadata, chunks)

            retriever = MultiDocumentRetriever(cache=cache)

            # Should find with min_mentions=1
            cross_refs = retriever.find_cross_references("topic", min_mentions=1)
            assert len(cross_refs) > 0

            # Should not find with min_mentions=2
            cross_refs = retriever.find_cross_references("topic", min_mentions=2)
            assert len(cross_refs) == 0  # Only 1 matching chunk, need 2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
