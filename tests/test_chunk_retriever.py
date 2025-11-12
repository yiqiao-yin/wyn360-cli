"""
Unit tests for ChunkRetriever class (Phase 13.1)

Tests cover:
- Query tokenization
- Chunk scoring (tag matching, summary matching)
- Top-K retrieval
- Edge cases (empty queries, no matches, etc.)
"""

import pytest
from wyn360_cli.document_readers import ChunkRetriever


class TestChunkRetriever:
    """Test ChunkRetriever functionality."""

    def test_retriever_initialization(self):
        """Test retriever initializes with correct top_k."""
        retriever = ChunkRetriever(top_k=5)
        assert retriever.top_k == 5

    def test_retriever_default_top_k(self):
        """Test retriever uses default top_k if not specified."""
        retriever = ChunkRetriever()
        assert retriever.top_k == 3

    def test_tokenize_query_basic(self):
        """Test basic query tokenization."""
        retriever = ChunkRetriever()
        query = "What were the April expenses?"

        terms = retriever._tokenize_query(query)

        assert "what" in terms
        assert "were" in terms
        assert "april" in terms
        assert "expenses" in terms

    def test_tokenize_query_lowercase(self):
        """Test that query terms are lowercased."""
        retriever = ChunkRetriever()
        query = "APRIL EXPENSES Budget"

        terms = retriever._tokenize_query(query)

        assert all(term.islower() for term in terms)
        assert "april" in terms
        assert "expenses" in terms
        assert "budget" in terms

    def test_tokenize_query_filters_short_words(self):
        """Test that very short words are filtered out."""
        retriever = ChunkRetriever()
        query = "What is a test of the system?"

        terms = retriever._tokenize_query(query)

        # 3+ character words only
        assert all(len(term) >= 3 for term in terms)
        assert "what" in terms
        assert "test" in terms
        assert "system" in terms

    def test_tokenize_query_empty(self):
        """Test tokenizing empty query."""
        retriever = ChunkRetriever()
        terms = retriever._tokenize_query("")

        assert len(terms) == 0

    def test_score_chunk_exact_tag_match(self):
        """Test scoring with exact tag match."""
        retriever = ChunkRetriever()
        query_terms = ["expenses", "april"]
        chunk = {
            "tags": ["expenses", "april", "q2", "budget"],
            "summary": "Some summary about stuff."
        }

        score = retriever._score_chunk(query_terms, chunk)

        # 2 exact tag matches × 3 points each = 6
        assert score == 6.0

    def test_score_chunk_partial_tag_match(self):
        """Test scoring with partial tag match."""
        retriever = ChunkRetriever()
        query_terms = ["expense"]  # Singular
        chunk = {
            "tags": ["expenses", "quarterly", "budget"],  # Plural
            "summary": "Summary text."
        }

        score = retriever._score_chunk(query_terms, chunk)

        # "expense" partially matches "expenses" = 1 point
        assert score >= 1.0

    def test_score_chunk_summary_match(self):
        """Test scoring with summary match."""
        retriever = ChunkRetriever()
        query_terms = ["budget", "analysis"]
        chunk = {
            "tags": ["other", "tags"],
            "summary": "This is a budget analysis for Q1 expenses."
        }

        score = retriever._score_chunk(query_terms, chunk)

        # 2 summary matches × 0.5 points each = 1.0
        assert score == 1.0

    def test_score_chunk_combined_matches(self):
        """Test scoring with both tag and summary matches."""
        retriever = ChunkRetriever()
        query_terms = ["expenses", "april"]
        chunk = {
            "tags": ["expenses", "q2", "budget"],
            "summary": "April spending analysis shows increased costs."
        }

        score = retriever._score_chunk(query_terms, chunk)

        # "expenses" exact tag match = 3
        # "april" summary match = 0.5
        # Total = 3.5
        assert score == 3.5

    def test_score_chunk_no_matches(self):
        """Test scoring with no matches."""
        retriever = ChunkRetriever()
        query_terms = ["unrelated", "terms"]
        chunk = {
            "tags": ["expenses", "budget"],
            "summary": "Financial summary for Q1."
        }

        score = retriever._score_chunk(query_terms, chunk)

        assert score == 0.0

    def test_match_query_single_result(self):
        """Test query matching with single best result."""
        retriever = ChunkRetriever(top_k=3)
        query = "April expenses"
        chunks = [
            {
                "chunk_id": "001",
                "tags": ["january", "expenses"],
                "summary": "January data"
            },
            {
                "chunk_id": "002",
                "tags": ["april", "expenses", "q2"],
                "summary": "April spending details"
            },
            {
                "chunk_id": "003",
                "tags": ["budget", "forecast"],
                "summary": "Budget planning"
            }
        ]

        results = retriever.match_query(query, chunks)

        # Should return chunk 002 first (best match)
        assert len(results) <= 3
        assert results[0]["chunk_id"] == "002"

    def test_match_query_top_k_limit(self):
        """Test that only top-K results are returned."""
        retriever = ChunkRetriever(top_k=2)
        query = "expenses"
        chunks = [
            {"chunk_id": f"{i:03d}", "tags": ["expenses"], "summary": f"Summary {i}"}
            for i in range(10)
        ]

        results = retriever.match_query(query, chunks)

        # Should return only top 2
        assert len(results) == 2

    def test_match_query_sorted_by_relevance(self):
        """Test that results are sorted by relevance score."""
        retriever = ChunkRetriever(top_k=5)
        query = "april budget expenses"
        chunks = [
            {
                "chunk_id": "001",
                "tags": ["january"],
                "summary": "January data"
            },
            {
                "chunk_id": "002",
                "tags": ["april", "budget", "expenses"],
                "summary": "April budget and expenses"
            },
            {
                "chunk_id": "003",
                "tags": ["april"],
                "summary": "April summary"
            },
            {
                "chunk_id": "004",
                "tags": ["budget"],
                "summary": "Budget only"
            }
        ]

        results = retriever.match_query(query, chunks)

        # Chunk 002 should be first (matches all 3 terms)
        assert results[0]["chunk_id"] == "002"
        # Chunk 003 and 004 should follow (match 1 term each)
        assert results[1]["chunk_id"] in ["003", "004"]

    def test_match_query_empty_query(self):
        """Test matching with empty query."""
        retriever = ChunkRetriever()
        chunks = [
            {"chunk_id": "001", "tags": ["tag1"], "summary": "Summary 1"},
            {"chunk_id": "002", "tags": ["tag2"], "summary": "Summary 2"}
        ]

        results = retriever.match_query("", chunks)

        # With empty query, all scores are 0, order is undefined
        # but should still return top_k chunks
        assert len(results) <= retriever.top_k

    def test_match_query_no_matching_chunks(self):
        """Test matching when no chunks match."""
        retriever = ChunkRetriever()
        query = "completely unrelated query terms"
        chunks = [
            {"chunk_id": "001", "tags": ["expenses"], "summary": "Financial data"},
            {"chunk_id": "002", "tags": ["budget"], "summary": "Budget info"}
        ]

        results = retriever.match_query(query, chunks)

        # Should still return some chunks (highest scores, even if 0)
        assert len(results) > 0
        assert len(results) <= retriever.top_k

    def test_get_relevant_chunks_with_query(self):
        """Test get_relevant_chunks filters by query."""
        retriever = ChunkRetriever(top_k=2)
        query = "expenses"
        chunks = [
            {"chunk_id": "001", "tags": ["expenses"], "summary": "Data 1"},
            {"chunk_id": "002", "tags": ["budget"], "summary": "Data 2"},
            {"chunk_id": "003", "tags": ["expenses"], "summary": "Data 3"}
        ]

        results = retriever.get_relevant_chunks(query, chunks)

        # Should return filtered and sorted results
        assert len(results) <= 2
        assert all("expenses" in r["tags"] for r in results)

    def test_get_relevant_chunks_without_query(self):
        """Test get_relevant_chunks returns all when no query."""
        retriever = ChunkRetriever(top_k=2)
        chunks = [
            {"chunk_id": "001", "tags": ["tag1"], "summary": "Summary 1"},
            {"chunk_id": "002", "tags": ["tag2"], "summary": "Summary 2"},
            {"chunk_id": "003", "tags": ["tag3"], "summary": "Summary 3"}
        ]

        results = retriever.get_relevant_chunks(None, chunks)

        # Without query, should return all chunks
        assert len(results) == 3

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        retriever = ChunkRetriever()
        query = "APRIL EXPENSES"
        chunks = [
            {
                "chunk_id": "001",
                "tags": ["April", "Expenses", "Q2"],
                "summary": "april expenses data"
            }
        ]

        results = retriever.match_query(query, chunks)

        # Should match despite case differences
        assert len(results) > 0
        assert results[0]["chunk_id"] == "001"

    def test_retrieval_with_missing_fields(self):
        """Test retrieval handles chunks with missing fields gracefully."""
        retriever = ChunkRetriever()
        query = "test"
        chunks = [
            {"chunk_id": "001"},  # Missing tags and summary
            {"chunk_id": "002", "tags": []},  # Empty tags
            {"chunk_id": "003", "tags": ["test"], "summary": ""}  # Empty summary
        ]

        # Should not crash
        results = retriever.match_query(query, chunks)
        assert len(results) > 0

    def test_numerical_terms_in_query(self):
        """Test that numerical terms are handled correctly."""
        retriever = ChunkRetriever()
        query = "Q1 2024 expenses"

        terms = retriever._tokenize_query(query)

        # Should include alphanumeric terms
        assert "2024" in terms
        assert "expenses" in terms

    def test_special_characters_filtered(self):
        """Test that special characters are filtered from query."""
        retriever = ChunkRetriever()
        query = "What's the $$ cost?"

        terms = retriever._tokenize_query(query)

        # Should extract words, filter special chars
        assert "what" in terms
        assert "cost" in terms
        # Special chars should not appear
        assert "$" not in " ".join(terms)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
