"""
Unit tests for ChunkSummarizer class (Phase 13.1)

Tests cover:
- Chunk summarization with mocked Claude API
- Tag generation
- Error handling and fallbacks
- Context formatting
- Token tracking
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from wyn360_cli.document_readers import ChunkSummarizer


class TestChunkSummarizer:
    """Test ChunkSummarizer functionality."""

    def test_summarizer_initialization(self):
        """Test summarizer initializes with correct parameters."""
        summarizer = ChunkSummarizer(api_key="test-key", model="claude-3-5-haiku-20241022")

        assert summarizer.api_key == "test-key"
        assert summarizer.model == "claude-3-5-haiku-20241022"
        assert summarizer.summary_tokens == 100
        assert summarizer.tag_count == 8

    def test_format_context_excel(self):
        """Test context formatting for Excel documents."""
        summarizer = ChunkSummarizer(api_key="test-key")
        context = {
            "doc_type": "excel",
            "sheet_name": "Q1_Expenses"
        }

        context_str = summarizer._format_context(context)

        assert "excel" in context_str.lower()
        assert "Q1_Expenses" in context_str

    def test_format_context_word(self):
        """Test context formatting for Word documents."""
        summarizer = ChunkSummarizer(api_key="test-key")
        context = {
            "doc_type": "word",
            "section_title": "Chapter 1: Introduction"
        }

        context_str = summarizer._format_context(context)

        assert "word" in context_str.lower()
        assert "Chapter 1" in context_str

    def test_format_context_pdf(self):
        """Test context formatting for PDF documents."""
        summarizer = ChunkSummarizer(api_key="test-key")
        context = {
            "doc_type": "pdf",
            "page_range": (1, 5)
        }

        context_str = summarizer._format_context(context)

        assert "pdf" in context_str.lower()
        assert "1-5" in context_str

    def test_format_context_empty(self):
        """Test context formatting with no context."""
        summarizer = ChunkSummarizer(api_key="test-key")
        context = {}

        context_str = summarizer._format_context(context)

        assert context_str == "No context"

    def test_parse_summary_response_valid(self):
        """Test parsing valid summary response."""
        summarizer = ChunkSummarizer(api_key="test-key")
        response = """SUMMARY: This chunk discusses Q1 expenses totaling $5,240 across various categories.
TAGS: [expenses, Q1, budget, financial, spending, categories, analysis, report]"""

        summary, tags = summarizer._parse_summary_response(response)

        assert "Q1 expenses" in summary
        assert "$5,240" in summary
        assert len(tags) <= 8
        assert "expenses" in tags
        assert "Q1" in tags

    def test_parse_summary_response_missing_tags(self):
        """Test parsing response with missing tags."""
        summarizer = ChunkSummarizer(api_key="test-key")
        response = "SUMMARY: This is the summary without tags."

        summary, tags = summarizer._parse_summary_response(response)

        assert "This is the summary" in summary
        # Should fallback to keyword extraction
        assert len(tags) > 0

    def test_parse_summary_response_missing_summary(self):
        """Test parsing response with missing summary."""
        summarizer = ChunkSummarizer(api_key="test-key")
        response = "TAGS: [tag1, tag2, tag3]"

        summary, tags = summarizer._parse_summary_response(response)

        # Should use first part of content as summary
        assert len(summary) > 0
        assert "tag1" in tags
        assert "tag2" in tags

    def test_parse_summary_response_no_labels(self):
        """Test parsing response without SUMMARY/TAGS labels."""
        summarizer = ChunkSummarizer(api_key="test-key")
        response = "Just some text without proper formatting."

        summary, tags = summarizer._parse_summary_response(response)

        # Should extract what it can
        assert len(summary) > 0
        assert len(tags) > 0

    def test_extract_keywords(self):
        """Test keyword extraction fallback."""
        summarizer = ChunkSummarizer(api_key="test-key")
        text = "The financial report shows quarterly expenses totaling five thousand dollars for various categories."

        keywords = summarizer._extract_keywords(text)

        assert len(keywords) <= 8
        # Should extract meaningful words (4+ chars)
        assert all(len(word) >= 4 for word in keywords)
        # Common words like "the", "for" should be filtered
        assert "financial" in keywords
        assert "expenses" in keywords

    def test_extract_keywords_short_text(self):
        """Test keyword extraction from short text."""
        summarizer = ChunkSummarizer(api_key="test-key")
        text = "Test document."

        keywords = summarizer._extract_keywords(text)

        assert "test" in keywords
        assert "document" in keywords

    def test_extract_keywords_deduplication(self):
        """Test that extracted keywords are unique."""
        summarizer = ChunkSummarizer(api_key="test-key")
        text = "testing testing testing document document"

        keywords = summarizer._extract_keywords(text)

        # Should only have unique words
        assert len(keywords) == len(set(keywords))
        assert "testing" in keywords
        assert "document" in keywords

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_summarize_chunk_success(self, mock_anthropic_class):
        """Test successful chunk summarization."""
        # Mock the API client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="""SUMMARY: Q1 expenses total $5,240 across food, gas, and utilities categories.
TAGS: [expenses, Q1, food, gas, utilities, budget, financial, quarterly]""")]
        mock_response.usage = Mock(input_tokens=1000, output_tokens=120)

        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic_class.return_value = mock_client

        summarizer = ChunkSummarizer(api_key="test-key")

        chunk_text = "Detailed expense data here..." * 100
        context = {"doc_type": "excel", "sheet_name": "Q1_Expenses"}

        result = await summarizer.summarize_chunk(chunk_text, context)

        # Verify result structure
        assert "summary" in result
        assert "tags" in result
        assert "summary_tokens" in result
        assert "tag_tokens" in result
        assert "api_tokens" in result

        # Verify content
        assert "Q1 expenses" in result["summary"]
        assert "expenses" in result["tags"]
        assert len(result["tags"]) <= 8

        # Verify API was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["model"] == "claude-3-5-haiku-20241022"
        assert call_args[1]["max_tokens"] == 200

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_summarize_chunk_api_failure(self, mock_anthropic_class):
        """Test summarization with API failure (fallback)."""
        # Mock API failure
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client

        summarizer = ChunkSummarizer(api_key="test-key")

        chunk_text = "This is test content about expenses and budgets."
        context = {"doc_type": "excel"}

        result = await summarizer.summarize_chunk(chunk_text, context)

        # Should use fallback
        assert "summary" in result
        assert "tags" in result
        assert "error" in result
        assert "API call failed" in result["error"]

        # Fallback summary should be first ~100 tokens
        assert len(result["summary"]) > 0
        # Fallback should extract keywords
        assert len(result["tags"]) > 0

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.Anthropic')
    async def test_summarize_chunk_token_tracking(self, mock_anthropic_class):
        """Test that token usage is tracked correctly."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="SUMMARY: Test summary.\nTAGS: [tag1, tag2]")]
        mock_response.usage = Mock(input_tokens=1234, output_tokens=56)

        mock_client.messages.create = Mock(return_value=mock_response)
        mock_anthropic_class.return_value = mock_client

        summarizer = ChunkSummarizer(api_key="test-key")

        result = await summarizer.summarize_chunk("Test content", {})

        # Verify API token tracking
        assert result["api_tokens"]["input"] == 1234
        assert result["api_tokens"]["output"] == 56

    def test_fallback_summary(self):
        """Test fallback summary generation."""
        summarizer = ChunkSummarizer(api_key="test-key")

        chunk_text = "This is a long chunk of text about financial expenses and budget tracking."
        error_msg = "API timeout"

        result = summarizer._fallback_summary(chunk_text, error_msg)

        assert "summary" in result
        assert "tags" in result
        assert "error" in result
        assert error_msg in result["error"]

        # Summary should be truncated
        assert len(result["summary"]) <= 400 + 3  # +3 for "..."

        # Tags should be extracted
        assert "financial" in result["tags"]
        assert "expenses" in result["tags"]

    def test_fallback_summary_very_short_text(self):
        """Test fallback with very short text."""
        summarizer = ChunkSummarizer(api_key="test-key")

        chunk_text = "Short text."
        result = summarizer._fallback_summary(chunk_text, "error")

        assert result["summary"] == chunk_text + "..."
        assert len(result["tags"]) > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
