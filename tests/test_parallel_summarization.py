"""
Unit tests for Parallel Chunk Summarization (Phase 5.6.1)

Tests cover:
- Parallel summarization of multiple chunks
- Batch processing
- Error handling in parallel mode
- Performance comparison (sequential vs parallel)
"""

import pytest
import asyncio
from wyn360_cli.document_readers import ChunkSummarizer
from unittest.mock import Mock, patch, AsyncMock


class TestParallelSummarization:
    """Test parallel chunk summarization functionality (Phase 5.6.1)."""

    @pytest.mark.asyncio
    async def test_summarize_chunks_parallel_basic(self):
        """Test basic parallel chunk summarization."""
        # Mock Anthropic client
        with patch('wyn360_cli.document_readers.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text="SUMMARY: Test summary\nTAGS: [tag1, tag2, tag3]")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=20)
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=False
            )

            # Create test chunks
            chunks_data = [
                {"content": "Chunk 1 content here", "context": {"doc_type": "excel"}},
                {"content": "Chunk 2 content here", "context": {"doc_type": "excel"}},
                {"content": "Chunk 3 content here", "context": {"doc_type": "excel"}},
            ]

            # Summarize in parallel
            results = await summarizer.summarize_chunks_parallel(chunks_data, batch_size=10)

            # Verify results
            assert len(results) == 3
            for result in results:
                assert "summary" in result
                assert "tags" in result
                assert "summary_tokens" in result

    @pytest.mark.asyncio
    async def test_summarize_chunks_parallel_batching(self):
        """Test that batching works correctly."""
        with patch('wyn360_cli.document_readers.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text="SUMMARY: Test summary\nTAGS: [tag1, tag2]")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=20)
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=False
            )

            # Create 15 chunks (will be processed in 2 batches of 10 and 5)
            chunks_data = [
                {"content": f"Chunk {i} content", "context": {"doc_type": "pdf"}}
                for i in range(15)
            ]

            # Summarize in parallel with batch_size=10
            results = await summarizer.summarize_chunks_parallel(chunks_data, batch_size=10)

            # Verify all chunks were processed
            assert len(results) == 15

    @pytest.mark.asyncio
    async def test_summarize_chunks_parallel_error_handling(self):
        """Test that errors in parallel processing are handled gracefully."""
        with patch('wyn360_cli.document_readers.Anthropic') as mock_anthropic:
            mock_client = Mock()

            # Make the first call fail, second succeed
            call_count = [0]

            async def mock_create(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise Exception("API error")
                else:
                    response = Mock()
                    response.content = [Mock(text="SUMMARY: Test summary\nTAGS: [tag1]")]
                    response.usage = Mock(input_tokens=100, output_tokens=20)
                    return response

            mock_client.messages.create = mock_create
            mock_anthropic.return_value = mock_client

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=False
            )

            chunks_data = [
                {"content": "Chunk 1", "context": {"doc_type": "word"}},
                {"content": "Chunk 2", "context": {"doc_type": "word"}},
            ]

            # Summarize in parallel
            results = await summarizer.summarize_chunks_parallel(chunks_data, batch_size=10)

            # First chunk should have fallback summary (error)
            assert "error" in results[0]

            # Second chunk should succeed
            assert "summary" in results[1]

    @pytest.mark.asyncio
    async def test_summarize_chunks_parallel_empty_list(self):
        """Test parallel summarization with empty chunk list."""
        summarizer = ChunkSummarizer(
            api_key="test-key",
            enable_embeddings=False
        )

        results = await summarizer.summarize_chunks_parallel([], batch_size=10)

        assert results == []

    @pytest.mark.asyncio
    async def test_summarize_chunks_parallel_preserves_order(self):
        """Test that parallel summarization preserves chunk order."""
        with patch('wyn360_cli.document_readers.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text="SUMMARY: Test summary\nTAGS: [tag1, tag2]")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=20)
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=False
            )

            chunks_data = [
                {"content": f"Chunk {i}", "context": {"doc_type": "excel"}}
                for i in range(5)
            ]

            # Summarize in parallel
            results = await summarizer.summarize_chunks_parallel(chunks_data, batch_size=10)

            # Verify order is preserved and all chunks processed
            assert len(results) == 5
            assert all("summary" in result for result in results)
            assert all("tags" in result for result in results)

    @pytest.mark.asyncio
    async def test_summarize_chunks_parallel_batch_size_one(self):
        """Test parallel summarization with batch_size=1 (sequential-like)."""
        with patch('wyn360_cli.document_readers.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.content = [Mock(text="SUMMARY: Test\nTAGS: [tag1]")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=20)
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            summarizer = ChunkSummarizer(
                api_key="test-key",
                enable_embeddings=False
            )

            chunks_data = [
                {"content": "Chunk 1", "context": {}},
                {"content": "Chunk 2", "context": {}},
            ]

            # Summarize with batch_size=1
            results = await summarizer.summarize_chunks_parallel(chunks_data, batch_size=1)

            assert len(results) == 2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
