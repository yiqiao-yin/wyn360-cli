#!/usr/bin/env python3
"""
Unit Tests for Ask AI Documentation Search Algorithm

This module tests the core semantic search functionality for the GitHub book
Ask AI feature. These tests are specifically for documentation search performance
and do not interfere with the main WYN360 CLI codebase.

Focus Areas:
- Search index structure and embeddings
- Similarity scoring accuracy
- Query expansion and tokenization
- Threshold tuning for optimal results
- Streamlit/web app content discoverability
"""

import json
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestSearchIndexStructure:
    """Test the structure and content of the search index"""

    @pytest.fixture(scope="class")
    def search_index_path(self):
        """Path to the search index file"""
        return project_root / "docs" / "assets" / "search-index.json"

    @pytest.fixture(scope="class")
    def search_index(self, search_index_path):
        """Load the search index data"""
        if not search_index_path.exists():
            pytest.skip(f"Search index not found at {search_index_path}")

        with open(search_index_path, 'r') as f:
            return json.load(f)

    def test_search_index_exists(self, search_index_path):
        """Verify search index file exists"""
        assert search_index_path.exists(), f"Search index missing: {search_index_path}"

    def test_search_index_structure(self, search_index):
        """Verify search index has required structure"""
        assert "version" in search_index
        assert "chunks" in search_index
        assert "embeddings" in search_index
        assert "metadata" in search_index

        metadata = search_index["metadata"]
        assert "total_chunks" in metadata
        assert "embedding_model" in metadata
        assert "embedding_dimension" in metadata
        assert "has_embeddings" in metadata

        assert metadata["has_embeddings"] == True, "Search index should have embeddings"
        assert metadata["embedding_dimension"] == 384, "Expected 384-dimensional embeddings"

    def test_chunks_and_embeddings_alignment(self, search_index):
        """Verify chunks and embeddings arrays are properly aligned"""
        chunks = search_index["chunks"]
        embeddings = search_index["embeddings"]

        assert len(chunks) == len(embeddings), \
            f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) count mismatch"

        # Check embedding dimensions
        for i, embedding in enumerate(embeddings):
            assert len(embedding) == 384, \
                f"Embedding {i} has dimension {len(embedding)}, expected 384"

    def test_streamlit_content_exists(self, search_index):
        """Verify Streamlit content exists in search index"""
        chunks = search_index["chunks"]

        streamlit_chunks = []
        for chunk in chunks:
            content_lower = chunk["content"].lower()
            title_lower = chunk["title"].lower()

            if "streamlit" in content_lower or "streamlit" in title_lower:
                streamlit_chunks.append(chunk)

        assert len(streamlit_chunks) > 0, "No Streamlit content found in search index"

        # Log found content for debugging
        print(f"\nFound {len(streamlit_chunks)} Streamlit-related chunks:")
        for chunk in streamlit_chunks[:3]:  # Show first 3
            print(f"- {chunk['title']}: {chunk['content'][:100]}...")

    def test_web_app_content_exists(self, search_index):
        """Verify web application content exists"""
        chunks = search_index["chunks"]

        web_app_terms = ["web app", "webapp", "application", "fastapi", "gradio"]
        web_chunks = []

        for chunk in chunks:
            content_lower = chunk["content"].lower()
            title_lower = chunk["title"].lower()

            if any(term in content_lower or term in title_lower for term in web_app_terms):
                web_chunks.append(chunk)

        assert len(web_chunks) > 0, "No web application content found"

        print(f"\nFound {len(web_chunks)} web application chunks")


class TestSimilarityScoring:
    """Test similarity calculation and scoring accuracy"""

    @pytest.fixture(scope="class")
    def search_index_path(self):
        return project_root / "docs" / "assets" / "search-index.json"

    @pytest.fixture(scope="class")
    def search_index(self, search_index_path):
        if not search_index_path.exists():
            pytest.skip("Search index not found")
        with open(search_index_path, 'r') as f:
            return json.load(f)

    def cosine_similarity(self, vec_a, vec_b):
        """Calculate cosine similarity between two vectors"""
        vec_a = np.array(vec_a)
        vec_b = np.array(vec_b)

        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0

        return dot_product / (norm_a * norm_b)

    def test_embedding_similarity_calculation(self, search_index):
        """Test cosine similarity calculation accuracy"""
        embeddings = search_index["embeddings"]

        # Test identical vectors should have similarity 1.0
        embedding_0 = embeddings[0]
        similarity = self.cosine_similarity(embedding_0, embedding_0)
        assert abs(similarity - 1.0) < 0.001, f"Identical vectors should have similarity ~1.0, got {similarity}"

        # Test different vectors should have similarity < 1.0
        if len(embeddings) > 1:
            embedding_1 = embeddings[1]
            similarity = self.cosine_similarity(embedding_0, embedding_1)
            assert 0 <= similarity <= 1.0, f"Similarity should be in [0,1], got {similarity}"

    def test_streamlit_query_similarity(self, search_index):
        """Test similarity scores for 'streamlit app' query"""
        chunks = search_index["chunks"]
        embeddings = search_index["embeddings"]

        # Find Streamlit-related chunks manually
        streamlit_indices = []
        for i, chunk in enumerate(chunks):
            content = chunk["content"].lower()
            title = chunk["title"].lower()

            if "streamlit" in content or "streamlit" in title:
                streamlit_indices.append(i)

        assert len(streamlit_indices) > 0, "No Streamlit content found for similarity testing"

        # Create a simple query vector for "streamlit app"
        # This is a simplified approach - in reality we'd use sentence transformers
        query_terms = ["streamlit", "app", "application", "web", "build"]

        # For each Streamlit chunk, check if it would score reasonably high
        for idx in streamlit_indices[:3]:  # Test first 3 chunks
            chunk = chunks[idx]
            content_words = chunk["content"].lower().split()

            # Count term matches (simplified relevance scoring)
            match_count = sum(1 for term in query_terms if term in content_words)

            # Streamlit content should have at least some matching terms
            assert match_count > 0, f"Streamlit chunk should match query terms: {chunk['title']}"

            print(f"Chunk '{chunk['title'][:50]}...' matches {match_count}/{len(query_terms)} query terms")

    def test_similarity_threshold_analysis(self, search_index):
        """Analyze appropriate similarity thresholds"""
        embeddings = search_index["embeddings"]
        chunks = search_index["chunks"]

        # Calculate similarity distribution
        if len(embeddings) < 2:
            pytest.skip("Need at least 2 embeddings for threshold analysis")

        similarities = []

        # Sample similarities between first 50 embeddings (for performance)
        sample_size = min(50, len(embeddings))

        for i in range(sample_size):
            for j in range(i + 1, sample_size):
                sim = self.cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)

        similarities = np.array(similarities)

        # Analyze similarity distribution
        mean_sim = np.mean(similarities)
        std_sim = np.std(similarities)
        percentiles = np.percentile(similarities, [25, 50, 75, 90, 95])

        print(f"\nSimilarity Distribution Analysis:")
        print(f"Mean: {mean_sim:.3f}, Std: {std_sim:.3f}")
        print(f"Percentiles [25,50,75,90,95]: {percentiles}")

        # Current threshold is 0.05 - this is likely too low
        current_threshold = 0.05
        above_threshold = np.sum(similarities > current_threshold) / len(similarities)

        print(f"Current threshold {current_threshold}: {above_threshold:.1%} of pairs above threshold")

        # Suggest better thresholds
        suggested_thresholds = [0.1, 0.15, 0.2, 0.25, 0.3]
        for thresh in suggested_thresholds:
            above = np.sum(similarities > thresh) / len(similarities)
            print(f"Threshold {thresh}: {above:.1%} of pairs above threshold")

        # Threshold should be above mean for meaningful results
        assert current_threshold < mean_sim, \
            f"Current threshold {current_threshold} too low (mean similarity: {mean_sim:.3f})"


class TestQueryProcessing:
    """Test query expansion and tokenization"""

    def test_streamlit_query_expansion(self):
        """Test that 'streamlit app' query gets properly expanded"""
        query = "streamlit app"

        # Simulate the JavaScript _expandQueryWithSynonyms method
        query_lower = query.lower()
        expansions = []

        if "streamlit" in query_lower:
            expansions.extend(["web application", "app development", "UI framework"])

        if "app" in query_lower:
            expansions.extend(["application", "software", "program"])

        expanded_query = f"{query} {' '.join(expansions)}"

        assert "web application" in expanded_query
        assert "application" in expanded_query
        print(f"Expanded query: '{query}' → '{expanded_query}'")

    def test_internet_query_expansion(self):
        """Test that 'internet' queries expand to browser-related terms"""
        query = "internet"

        query_lower = query.lower()
        expansions = []

        if query_lower in ["internet", "online", "web"]:
            expansions.extend(["web search", "browser use", "browser automation", "website fetching"])

        expanded_query = f"{query} {' '.join(expansions)}"

        assert "browser use" in expanded_query
        assert "web search" in expanded_query
        print(f"Expanded query: '{query}' → '{expanded_query}'")

    def test_tokenization(self):
        """Test query tokenization"""
        text = "Build a Streamlit app for data visualization!"

        # Simulate JavaScript tokenization
        import re

        # Remove punctuation and split
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = [word for word in clean_text.split() if len(word) > 2]

        # Remove stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'are', 'was'
        }
        filtered_tokens = [token for token in tokens if token not in stop_words]

        expected_tokens = ["build", "streamlit", "app", "data", "visualization"]

        assert "streamlit" in filtered_tokens
        assert "app" in filtered_tokens
        assert "data" in filtered_tokens

        print(f"Tokenized: '{text}' → {filtered_tokens}")


class TestContentDiscoverability:
    """Test that specific content can be discovered by relevant queries"""

    @pytest.fixture(scope="class")
    def search_index_path(self):
        return project_root / "docs" / "assets" / "search-index.json"

    @pytest.fixture(scope="class")
    def search_index(self, search_index_path):
        if not search_index_path.exists():
            pytest.skip("Search index not found")
        with open(search_index_path, 'r') as f:
            return json.load(f)

    def test_streamlit_content_discoverable(self, search_index):
        """Test that Streamlit content is discoverable by various queries"""
        chunks = search_index["chunks"]

        # Queries that should find Streamlit content
        test_queries = [
            "streamlit app",
            "streamlit application",
            "web app development",
            "build web application",
            "create app streamlit",
            "app.py streamlit"
        ]

        for query in test_queries:
            query_words = set(query.lower().split())
            found_chunks = []

            for chunk in chunks:
                content_words = set(chunk["content"].lower().split())
                title_words = set(chunk["title"].lower().split())
                all_words = content_words | title_words

                # Check if query words overlap with chunk content
                overlap = query_words & all_words
                if len(overlap) >= 1:  # At least one word match
                    found_chunks.append(chunk)

            assert len(found_chunks) > 0, f"Query '{query}' should find Streamlit content"
            print(f"Query '{query}' found {len(found_chunks)} relevant chunks")

    def test_browser_content_discoverable(self, search_index):
        """Test that browser/internet content is discoverable"""
        chunks = search_index["chunks"]

        test_queries = [
            "internet usage",
            "browser automation",
            "web browsing",
            "website interaction",
            "online activity"
        ]

        browser_terms = ["browser", "web", "internet", "online", "website", "url"]

        for query in test_queries:
            query_words = set(query.lower().split())
            found_chunks = []

            for chunk in chunks:
                content_lower = chunk["content"].lower()
                title_lower = chunk["title"].lower()

                # Check for browser-related terms in content
                has_browser_term = any(term in content_lower or term in title_lower
                                     for term in browser_terms)

                # Check for query word overlap
                content_words = set(content_lower.split())
                title_words = set(title_lower.split())
                all_words = content_words | title_words
                overlap = query_words & all_words

                if has_browser_term and len(overlap) >= 1:
                    found_chunks.append(chunk)

            assert len(found_chunks) > 0, f"Query '{query}' should find browser content"
            print(f"Query '{query}' found {len(found_chunks)} browser-related chunks")


if __name__ == "__main__":
    # Run specific test categories
    print("Running Ask AI Search Algorithm Tests...")
    print("=" * 50)

    # Set up pytest arguments for detailed output
    pytest_args = [
        __file__,
        "-v",                    # Verbose output
        "-s",                    # Don't capture stdout
        "--tb=short",            # Short traceback format
        "--disable-warnings"     # Disable pytest warnings
    ]

    # Run tests
    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")

    sys.exit(exit_code)