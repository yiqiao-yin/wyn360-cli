"""
Unit tests for EmbeddingModel class (Phase 5.2.1)

Tests cover:
- Model initialization and lazy loading
- Single and batch text encoding
- Cosine similarity computation
- Error handling (model not installed)
- Edge cases (empty texts, special characters)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from wyn360_cli.document_readers import EmbeddingModel


class TestEmbeddingModel:
    """Test EmbeddingModel functionality."""

    def test_model_initialization(self):
        """Test model initializes with correct parameters."""
        model = EmbeddingModel(provider="local", model_name="all-MiniLM-L6-v2")

        assert model.provider == "local"
        assert model.model_name == "all-MiniLM-L6-v2"
        assert model.model is None
        assert model._initialized is False

    def test_model_lazy_loading(self):
        """Test model is loaded lazily on first use."""
        with patch('sentence_transformers.SentenceTransformer') as mock_st:
            mock_st_instance = Mock()
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel()

            # Model not loaded yet
            assert model.model is None
            assert model._initialized is False

            # Trigger lazy load
            model._lazy_load()

            # Model now loaded
            assert model.model == mock_st_instance
            assert model._initialized is True

            # Verify SentenceTransformer was called with correct model name
            mock_st.assert_called_once_with("all-MiniLM-L6-v2")

    def test_encode_single_text(self):
        """Test encoding a single text."""
        with patch('wyn360_cli.document_readers.SentenceTransformer') as mock_st:
            # Mock sentence transformer
            mock_st_instance = Mock()
            mock_embedding = np.array([[0.1, 0.2, 0.3, 0.4]])
            mock_st_instance.encode.return_value = mock_embedding
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel()
            result = model.encode("Hello world")

            # Verify result
            assert isinstance(result, np.ndarray)
            assert result.shape == (1, 4)
            np.testing.assert_array_equal(result, mock_embedding)

            # Verify encode was called with list
            mock_st_instance.encode.assert_called_once()
            call_args = mock_st_instance.encode.call_args
            assert call_args[0][0] == ["Hello world"]

    def test_encode_multiple_texts(self):
        """Test encoding multiple texts in batch."""
        with patch('wyn360_cli.document_readers.SentenceTransformer') as mock_st:
            # Mock sentence transformer
            mock_st_instance = Mock()
            mock_embeddings = np.array([
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
                [0.9, 1.0, 1.1, 1.2]
            ])
            mock_st_instance.encode.return_value = mock_embeddings
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel()
            texts = ["First text", "Second text", "Third text"]
            result = model.encode(texts)

            # Verify result
            assert isinstance(result, np.ndarray)
            assert result.shape == (3, 4)
            np.testing.assert_array_equal(result, mock_embeddings)

            # Verify encode was called with list
            mock_st_instance.encode.assert_called_once()
            call_args = mock_st_instance.encode.call_args
            assert call_args[0][0] == texts

    def test_compute_similarity_1d_query(self):
        """Test cosine similarity with 1D query embedding."""
        model = EmbeddingModel()
        model._initialized = True  # Skip lazy load for this test

        # Create sample embeddings (normalized for easier calculation)
        query_embedding = np.array([1.0, 0.0, 0.0])  # Unit vector in x direction
        chunk_embeddings = np.array([
            [1.0, 0.0, 0.0],  # Same direction (similarity = 1.0)
            [0.0, 1.0, 0.0],  # Orthogonal (similarity = 0.0)
            [0.5, 0.5, 0.0],  # 45 degrees (similarity ≈ 0.707)
        ])

        similarities = model.compute_similarity(query_embedding, chunk_embeddings)

        # Verify results
        assert isinstance(similarities, np.ndarray)
        assert similarities.shape == (3,)
        assert similarities[0] == pytest.approx(1.0, abs=0.01)
        assert similarities[1] == pytest.approx(0.0, abs=0.01)
        assert similarities[2] == pytest.approx(0.707, abs=0.01)

    def test_compute_similarity_2d_query(self):
        """Test cosine similarity with 2D query embedding (flattened automatically)."""
        model = EmbeddingModel()
        model._initialized = True

        # Query as 2D array (1, 3)
        query_embedding = np.array([[1.0, 0.0, 0.0]])
        chunk_embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ])

        similarities = model.compute_similarity(query_embedding, chunk_embeddings)

        # Verify results
        assert isinstance(similarities, np.ndarray)
        assert similarities.shape == (2,)
        assert similarities[0] == pytest.approx(1.0, abs=0.01)
        assert similarities[1] == pytest.approx(0.0, abs=0.01)

    def test_model_not_installed(self):
        """Test error handling when sentence-transformers not installed."""
        with patch('wyn360_cli.document_readers.SentenceTransformer', side_effect=ImportError("No module")):
            model = EmbeddingModel()

            with pytest.raises(ImportError) as exc_info:
                model.encode("Test text")

            assert "sentence-transformers not installed" in str(exc_info.value)
            assert "pip install sentence-transformers" in str(exc_info.value)

    def test_encode_empty_string(self):
        """Test encoding an empty string."""
        with patch('wyn360_cli.document_readers.SentenceTransformer') as mock_st:
            # Mock sentence transformer
            mock_st_instance = Mock()
            mock_embedding = np.array([[0.0, 0.0, 0.0, 0.0]])
            mock_st_instance.encode.return_value = mock_embedding
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel()
            result = model.encode("")

            # Verify it handles empty string
            assert isinstance(result, np.ndarray)
            assert result.shape == (1, 4)

    def test_encode_special_characters(self):
        """Test encoding text with special characters."""
        with patch('wyn360_cli.document_readers.SentenceTransformer') as mock_st:
            # Mock sentence transformer
            mock_st_instance = Mock()
            mock_embedding = np.array([[0.1, 0.2, 0.3, 0.4]])
            mock_st_instance.encode.return_value = mock_embedding
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel()
            text_with_special_chars = "Hello! @#$%^&*() 你好 🎉"
            result = model.encode(text_with_special_chars)

            # Verify it handles special characters
            assert isinstance(result, np.ndarray)
            mock_st_instance.encode.assert_called_once()

    def test_lazy_load_called_once(self):
        """Test lazy load is only called once even with multiple operations."""
        with patch('wyn360_cli.document_readers.SentenceTransformer') as mock_st:
            mock_st_instance = Mock()
            mock_embedding = np.array([[0.1, 0.2, 0.3, 0.4]])
            mock_st_instance.encode.return_value = mock_embedding
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel()

            # Call encode multiple times
            model.encode("First text")
            model.encode("Second text")
            model.encode("Third text")

            # SentenceTransformer should only be initialized once
            assert mock_st.call_count == 1

    def test_custom_model_name(self):
        """Test initialization with custom model name."""
        with patch('wyn360_cli.document_readers.SentenceTransformer') as mock_st:
            mock_st_instance = Mock()
            mock_st.return_value = mock_st_instance

            model = EmbeddingModel(model_name="custom-model-v1")

            # Trigger lazy load
            model._lazy_load()

            # Verify custom model name was used
            mock_st.assert_called_once_with("custom-model-v1")

    def test_compute_similarity_normalization(self):
        """Test that embeddings are properly normalized in similarity computation."""
        model = EmbeddingModel()
        model._initialized = True

        # Non-normalized embeddings
        query_embedding = np.array([2.0, 0.0, 0.0])  # Length = 2
        chunk_embeddings = np.array([
            [3.0, 0.0, 0.0],  # Length = 3, same direction
            [0.0, 4.0, 0.0],  # Length = 4, orthogonal
        ])

        similarities = model.compute_similarity(query_embedding, chunk_embeddings)

        # Despite different magnitudes, similarity should be based on direction
        assert similarities[0] == pytest.approx(1.0, abs=0.01)  # Same direction
        assert similarities[1] == pytest.approx(0.0, abs=0.01)  # Orthogonal

    def test_invalid_model_name(self):
        """Test error when using non-whitelisted model."""
        with pytest.raises(ValueError) as exc_info:
            EmbeddingModel(provider="local", model_name="arbitrary-bert-model")

        assert "not in safe model list" in str(exc_info.value)

    def test_invalid_provider(self):
        """Test error when using invalid provider."""
        with pytest.raises(ValueError) as exc_info:
            EmbeddingModel(provider="invalid")

        assert "Invalid provider" in str(exc_info.value)

    def test_claude_provider_requires_api_key(self):
        """Test that Claude provider requires API key."""
        with pytest.raises(ValueError) as exc_info:
            EmbeddingModel(provider="claude")

        assert "api_key required" in str(exc_info.value)

    def test_claude_provider_not_implemented_yet(self):
        """Test that Claude embeddings raise NotImplementedError."""
        model = EmbeddingModel(provider="claude", api_key="test-key")

        with pytest.raises(NotImplementedError) as exc_info:
            model.encode("Test text")

        assert "Claude embeddings API not yet available" in str(exc_info.value)

    def test_whitelisted_models(self):
        """Test that all whitelisted models can be initialized."""
        safe_models = [
            "all-MiniLM-L6-v2",
            "all-mpnet-base-v2",
            "paraphrase-MiniLM-L6-v2",
            "multi-qa-MiniLM-L6-cos-v1",
        ]

        for model_name in safe_models:
            # Should not raise
            model = EmbeddingModel(provider="local", model_name=model_name)
            assert model.model_name == model_name


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
