"""
Integration tests for Excel reading with semantic embeddings (Phase 5.2)

Tests cover:
- ChunkMetadata has embedding field
- ChunkSummarizer with enable_embeddings=True adds embeddings
- Embeddings are correct format (list of floats)
- Embedding dimensions match model (384 for all-MiniLM-L6-v2)
- Fallback when embeddings disabled
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from dataclasses import asdict

# Mock sentence_transformers before importing
sys.modules['sentence_transformers'] = MagicMock()

from wyn360_cli.document_readers import (
    ChunkSummarizer,
    ChunkMetadata,
    EmbeddingModel
)


class TestExcelEmbeddingIntegration:
    """Test Excel reading with semantic embeddings."""

    def test_chunk_metadata_has_embedding_field(self):
        """Test that ChunkMetadata has embedding field."""
        chunk = ChunkMetadata(
            chunk_id="chunk-1",
            position={"start": 0, "end": 100},
            summary="Test summary",
            tags=["test"],
            token_count=50,
            summary_tokens=10,
            tag_tokens=5,
            embedding=[0.1, 0.2, 0.3]  # Phase 5.2
        )

        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert isinstance(chunk.embedding, list)

    def test_chunk_metadata_embedding_optional(self):
        """Test that embedding field is optional."""
        chunk = ChunkMetadata(
            chunk_id="chunk-1",
            position={"start": 0, "end": 100},
            summary="Test summary",
            tags=["test"],
            token_count=50,
            summary_tokens=10,
            tag_tokens=5
        )

        assert chunk.embedding is None

    def test_chunk_summarizer_with_embeddings_enabled(self):
        """Test ChunkSummarizer initializes with embeddings enabled."""
        with patch('wyn360_cli.document_readers.EmbeddingModel') as MockEmbedding:
            mock_embedding_instance = Mock()
            MockEmbedding.return_value = mock_embedding_instance

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=True
            )

            assert summarizer.enable_embeddings is True
            assert summarizer.embedding_model is not None

    def test_chunk_summarizer_with_embeddings_disabled(self):
        """Test ChunkSummarizer with embeddings disabled."""
        summarizer = ChunkSummarizer(
            api_key="test-key",
            enable_embeddings=False
        )

        assert summarizer.enable_embeddings is False
        assert summarizer.embedding_model is None

    def test_add_embeddings_to_chunks_success(self):
        """Test adding embeddings to chunks."""
        with patch('wyn360_cli.document_readers.EmbeddingModel') as MockEmbedding:
            # Mock embedding model
            mock_embedding_instance = Mock()
            mock_embeddings = np.array([
                [0.1, 0.2, 0.3, 0.4],  # Chunk 1 embedding
                [0.5, 0.6, 0.7, 0.8],  # Chunk 2 embedding
            ])
            mock_embedding_instance.encode.return_value = mock_embeddings
            MockEmbedding.return_value = mock_embedding_instance

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=True
            )

            # Create test chunks
            chunks = [
                {
                    "summary": "First chunk summary",
                    "tags": ["tag1", "tag2"],
                    "chunk_id": "chunk-1"
                },
                {
                    "summary": "Second chunk summary",
                    "tags": ["tag3", "tag4"],
                    "chunk_id": "chunk-2"
                }
            ]

            # Add embeddings
            chunks_with_embeddings = summarizer.add_embeddings_to_chunks(chunks)

            # Verify embeddings were added
            assert len(chunks_with_embeddings) == 2
            assert "embedding" in chunks_with_embeddings[0]
            assert "embedding" in chunks_with_embeddings[1]

            # Verify embeddings are lists (converted from numpy)
            assert isinstance(chunks_with_embeddings[0]["embedding"], list)
            assert isinstance(chunks_with_embeddings[1]["embedding"], list)

            # Verify embedding dimensions (4 in mock)
            assert len(chunks_with_embeddings[0]["embedding"]) == 4
            assert len(chunks_with_embeddings[1]["embedding"]) == 4

    def test_add_embeddings_to_chunks_disabled(self):
        """Test add_embeddings_to_chunks when embeddings disabled."""
        summarizer = ChunkSummarizer(
            api_key="test-key",
            enable_embeddings=False
        )

        chunks = [
            {
                "summary": "Test summary",
                "tags": ["tag1"],
                "chunk_id": "chunk-1"
            }
        ]

        # Should return chunks unchanged
        result = summarizer.add_embeddings_to_chunks(chunks)
        assert result == chunks
        assert "embedding" not in result[0]

    def test_add_embeddings_combines_summary_and_tags(self):
        """Test that embeddings are generated from summary + tags."""
        with patch('wyn360_cli.document_readers.EmbeddingModel') as MockEmbedding:
            mock_embedding_instance = Mock()
            mock_embeddings = np.array([[0.1, 0.2, 0.3]])
            mock_embedding_instance.encode.return_value = mock_embeddings
            MockEmbedding.return_value = mock_embedding_instance

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=True
            )

            chunks = [
                {
                    "summary": "Test summary",
                    "tags": ["tag1", "tag2"],
                    "chunk_id": "chunk-1"
                }
            ]

            summarizer.add_embeddings_to_chunks(chunks)

            # Verify encode was called with combined text
            mock_embedding_instance.encode.assert_called_once()
            call_args = mock_embedding_instance.encode.call_args[0][0]
            assert call_args == ["Test summary | tag1, tag2"]

    def test_embedding_model_initialization_failure(self):
        """Test graceful handling when embedding model fails to initialize."""
        with patch('wyn360_cli.document_readers.EmbeddingModel', side_effect=ImportError("No module")):
            # Should not raise, just disable embeddings
            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=True
            )

            # Embeddings should be disabled after failure
            assert summarizer.enable_embeddings is False
            assert summarizer.embedding_model is None

    def test_embedding_model_custom_provider(self):
        """Test ChunkSummarizer with custom embedding provider."""
        with patch('wyn360_cli.document_readers.EmbeddingModel') as MockEmbedding:
            mock_embedding_instance = Mock()
            MockEmbedding.return_value = mock_embedding_instance

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=True,
                embedding_provider="local",
                embedding_model="all-mpnet-base-v2"
            )

            # Verify EmbeddingModel was called with correct parameters
            MockEmbedding.assert_called_once_with(
                provider="local",
                model_name="all-mpnet-base-v2",
                api_key=None
            )

    def test_embedding_preserves_other_chunk_fields(self):
        """Test that adding embeddings preserves other chunk fields."""
        with patch('wyn360_cli.document_readers.EmbeddingModel') as MockEmbedding:
            mock_embedding_instance = Mock()
            mock_embeddings = np.array([[0.1, 0.2]])
            mock_embedding_instance.encode.return_value = mock_embeddings
            MockEmbedding.return_value = mock_embedding_instance

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=True
            )

            chunks = [
                {
                    "chunk_id": "chunk-1",
                    "summary": "Test",
                    "tags": ["tag1"],
                    "token_count": 50,
                    "position": {"start": 0},
                    "sheet_name": "Sheet1"
                }
            ]

            result = summarizer.add_embeddings_to_chunks(chunks)

            # All original fields should be preserved
            assert result[0]["chunk_id"] == "chunk-1"
            assert result[0]["summary"] == "Test"
            assert result[0]["tags"] == ["tag1"]
            assert result[0]["token_count"] == 50
            assert result[0]["position"] == {"start": 0}
            assert result[0]["sheet_name"] == "Sheet1"
            # Plus new embedding field
            assert "embedding" in result[0]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
