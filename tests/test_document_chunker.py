"""
Unit tests for DocumentChunker class (Phase 13.1)

Tests cover:
- Simple chunking by token count
- Boundary-preserving chunking (paragraphs)
- Structure-aware chunking (sections/headings)
- Edge cases (empty text, very small chunks, etc.)
"""

import pytest
from wyn360_cli.document_readers import DocumentChunker, count_tokens


class TestDocumentChunker:
    """Test DocumentChunker functionality."""

    def test_chunker_initialization(self):
        """Test chunker initializes with correct chunk size."""
        chunker = DocumentChunker(chunk_size=1000)
        assert chunker.chunk_size == 1000

    def test_chunker_default_size(self):
        """Test chunker uses default chunk size if not specified."""
        chunker = DocumentChunker()
        assert chunker.chunk_size == 1000

    def test_simple_chunking_single_chunk(self):
        """Test that small text returns single chunk."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "a" * 1000  # 250 tokens
        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_simple_chunking_multiple_chunks(self):
        """Test that large text is split into multiple chunks."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "a" * 10000  # 2500 tokens, should create ~3 chunks
        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        assert len(chunks) >= 2
        # Each chunk should be approximately chunk_size * 4 characters
        for chunk in chunks[:-1]:  # All but last chunk
            assert len(chunk) == 4000  # 1000 tokens * 4 chars

    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = DocumentChunker(chunk_size=1000)
        chunks = chunker.chunk_by_tokens("", preserve_boundaries=False)

        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_boundary_preserving_single_paragraph(self):
        """Test that single paragraph is kept intact."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "This is a single paragraph. " * 50  # ~200 tokens
        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=True)

        assert len(chunks) == 1
        assert chunks[0].strip() == text.strip()

    def test_boundary_preserving_multiple_paragraphs(self):
        """Test that paragraph boundaries are preserved."""
        chunker = DocumentChunker(chunk_size=500)  # Smaller chunks

        para1 = "This is the first paragraph. " * 50  # ~200 tokens
        para2 = "This is the second paragraph. " * 50  # ~200 tokens
        para3 = "This is the third paragraph. " * 50  # ~200 tokens
        text = f"{para1}\n\n{para2}\n\n{para3}"

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=True)

        # Should create chunks at paragraph boundaries
        assert len(chunks) >= 2
        # No paragraph should be split across chunks
        for chunk in chunks:
            # Check that chunk doesn't end mid-paragraph
            assert chunk.strip().endswith("paragraph.")

    def test_boundary_preserving_no_split_mid_paragraph(self):
        """Test that paragraphs are never split mid-way."""
        chunker = DocumentChunker(chunk_size=100)  # Very small chunks

        para = "Short paragraph."
        text = f"{para}\n\n{para}\n\n{para}"

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=True)

        # Each chunk should contain complete paragraphs only
        for chunk in chunks:
            # Count how many complete "Short paragraph." instances
            assert chunk.count("Short paragraph.") >= 1

    def test_structure_aware_chunking_empty_sections(self):
        """Test structure-aware chunking with empty sections list."""
        chunker = DocumentChunker(chunk_size=1000)
        sections = []

        chunks = chunker.chunk_by_structure(sections)

        assert len(chunks) == 0

    def test_structure_aware_chunking_single_section(self):
        """Test structure-aware chunking with single section."""
        chunker = DocumentChunker(chunk_size=1000)
        sections = [
            {
                "title": "Introduction",
                "content": "This is the introduction content. " * 50,
                "level": 1
            }
        ]

        chunks = chunker.chunk_by_structure(sections)

        assert len(chunks) == 1
        assert "Introduction" in chunks[0]["content"]
        assert chunks[0]["sections"] == ["Introduction"]

    def test_structure_aware_chunking_multiple_small_sections(self):
        """Test that small sections are combined into single chunk."""
        chunker = DocumentChunker(chunk_size=1000)
        sections = [
            {"title": "Section 1", "content": "Content 1. " * 20, "level": 1},
            {"title": "Section 2", "content": "Content 2. " * 20, "level": 1},
            {"title": "Section 3", "content": "Content 3. " * 20, "level": 1},
        ]

        chunks = chunker.chunk_by_structure(sections)

        # All sections should fit in one chunk
        assert len(chunks) == 1
        assert len(chunks[0]["sections"]) == 3
        assert "Section 1" in chunks[0]["content"]
        assert "Section 2" in chunks[0]["content"]
        assert "Section 3" in chunks[0]["content"]

    def test_structure_aware_chunking_large_sections(self):
        """Test that large sections create separate chunks."""
        chunker = DocumentChunker(chunk_size=500)  # Smaller chunk size
        # Make each section 600 tokens (2400 chars) - larger than chunk_size
        sections = [
            {"title": "Large Section 1", "content": "Content. " * 400, "level": 1},
            {"title": "Large Section 2", "content": "Content. " * 400, "level": 1},
        ]

        chunks = chunker.chunk_by_structure(sections)

        # Each large section should be its own chunk
        assert len(chunks) >= 2

    def test_structure_aware_chunking_preserves_structure(self):
        """Test that structure metadata is preserved in chunks."""
        chunker = DocumentChunker(chunk_size=1000)
        sections = [
            {"title": "Chapter 1", "content": "Intro content. " * 50, "level": 1},
            {"title": "Chapter 2", "content": "More content. " * 50, "level": 1},
        ]

        chunks = chunker.chunk_by_structure(sections)

        # Each chunk should have title, content, and sections list
        for chunk in chunks:
            assert "title" in chunk
            assert "content" in chunk
            assert "sections" in chunk
            assert isinstance(chunk["sections"], list)

    def test_chunk_by_tokens_preserves_whitespace(self):
        """Test that important whitespace is preserved."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "Line 1\nLine 2\n\nLine 3"

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        assert "\n" in chunks[0]

    def test_chunk_by_tokens_very_large_text(self):
        """Test chunking very large text (stress test)."""
        chunker = DocumentChunker(chunk_size=1000)
        # 100,000 characters = 25,000 tokens
        text = "x" * 100000

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create ~25 chunks
        assert len(chunks) >= 20
        assert len(chunks) <= 30

        # Total length should match original
        total_length = sum(len(chunk) for chunk in chunks)
        assert total_length == len(text)

    def test_token_counting_accuracy(self):
        """Test that token counting is consistent."""
        # Known: 4 chars ≈ 1 token
        text_100_chars = "a" * 100
        text_400_chars = "a" * 400
        text_1000_chars = "a" * 1000

        assert count_tokens(text_100_chars) == 25
        assert count_tokens(text_400_chars) == 100
        assert count_tokens(text_1000_chars) == 250

    def test_chunk_size_accuracy(self):
        """Test that chunks are approximately the target size."""
        chunker = DocumentChunker(chunk_size=1000)
        text = "a" * 8000  # Exactly 2000 tokens

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create exactly 2 chunks of 1000 tokens each
        assert len(chunks) == 2
        for chunk in chunks:
            assert count_tokens(chunk) == 1000

    def test_boundary_preservation_with_mixed_separators(self):
        """Test boundary preservation with different paragraph separators."""
        chunker = DocumentChunker(chunk_size=500)

        para1 = "Paragraph one. " * 30
        para2 = "Paragraph two. " * 30
        para3 = "Paragraph three. " * 30

        # Mix single and double newlines
        text = f"{para1}\n\n{para2}\n{para3}"

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=True)

        # Should handle both \n\n and \n correctly
        assert len(chunks) >= 1
        # Verify content is preserved
        total_content = "".join(chunks)
        assert "Paragraph one" in total_content
        assert "Paragraph two" in total_content
        assert "Paragraph three" in total_content


class TestTokenCounting:
    """Test token counting utility function."""

    def test_count_tokens_empty(self):
        """Test counting tokens in empty string."""
        assert count_tokens("") == 0

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        assert count_tokens("a" * 4) == 1
        assert count_tokens("a" * 8) == 2
        assert count_tokens("a" * 100) == 25

    def test_count_tokens_with_spaces(self):
        """Test token counting with spaces."""
        text = "Hello world this is a test"
        tokens = count_tokens(text)
        # Should count all characters including spaces
        assert tokens == len(text) // 4

    def test_count_tokens_multiline(self):
        """Test token counting with newlines."""
        text = "Line 1\nLine 2\nLine 3"
        tokens = count_tokens(text)
        # Newlines count as characters
        assert tokens == len(text) // 4


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
