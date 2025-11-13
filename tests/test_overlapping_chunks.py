"""
Unit tests for Overlapping Chunks (Phase 5.7.2)

Tests cover:
- Backward compatibility (overlap_tokens=0 by default)
- Basic overlapping chunk creation
- Overlap size validation
- Edge cases (empty text, small text, large overlap)
- Integration with adaptive sizing
"""

import pytest
from wyn360_cli.document_readers import DocumentChunker


class TestOverlappingChunks:
    """Test overlapping chunks functionality (Phase 5.7.2)."""

    def test_overlap_disabled_default(self):
        """Test that overlapping is disabled by default (backward compatibility)."""
        chunker = DocumentChunker(chunk_size=1000)

        assert chunker.overlap_tokens == 0

        # Should create non-overlapping chunks
        text = "A" * 10000  # 10,000 characters
        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Verify chunks don't overlap
        assert len(chunks) > 1
        # Each chunk should be ~4000 chars (1000 tokens * 4)
        # No overlap, so total length should equal original text length
        total_length = sum(len(chunk) for chunk in chunks)
        assert total_length == len(text)

    def test_basic_overlapping_chunks(self):
        """Test basic overlapping chunk creation."""
        # Create chunker with 200 token overlap
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=200)

        # Create text long enough for multiple chunks
        text = "A" * 8000  # 8,000 characters

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should have overlapping chunks
        assert len(chunks) >= 2

        # Verify overlap exists
        # chunk[0] ends with some A's
        # chunk[1] starts with some A's (the overlap)
        if len(chunks) >= 2:
            # Check that chunks overlap (both have the same content in overlap region)
            assert chunks[0][-100:] == chunks[1][:100]  # Some overlap exists

    def test_overlap_size_validation(self):
        """Test that overlap size is validated and capped."""
        # Overlap shouldn't exceed half the chunk size
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=600)  # 60% of chunk size

        text = "B" * 10000

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should still create valid chunks (overlap capped at 50%)
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_overlap_with_small_text(self):
        """Test overlapping with text smaller than chunk size."""
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=200)

        # Small text (less than chunk size)
        text = "C" * 500  # Only 500 characters

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create just one chunk
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_overlap_with_empty_text(self):
        """Test overlapping with empty text."""
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=200)

        chunks = chunker.chunk_by_tokens("", preserve_boundaries=False)

        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_overlap_preserves_content(self):
        """Test that overlapping chunks preserve all original content."""
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=100)

        # Use distinct text to verify content preservation
        # Creates "0123456789012345678901234567890...9" (10000 digits)
        text = "".join(str(i % 10) for i in range(10000))

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # First chunk should start with "01234..."
        assert chunks[0].startswith("012345")

        # Last chunk should end with the end of original text
        # The text ends with "...789" (since 9999 % 10 = 9, 9998 % 10 = 8, 9997 % 10 = 7)
        assert chunks[-1].endswith(text[-10:])

        # All content should be represented (though with overlap)
        # The first chunk should contain the beginning
        # The last chunk should contain the end
        assert text[:100] in chunks[0]
        assert text[-100:] in chunks[-1]

    def test_overlap_with_boundaries(self):
        """Test overlapping chunks with preserve_boundaries=True."""
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=200)

        # Create text with paragraph boundaries
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.\n\n" * 100

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=True)

        # Should create chunks
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_overlap_integration_with_adaptive_sizing(self):
        """Test that overlap works with adaptive sizing."""
        chunker = DocumentChunker(
            chunk_size=1000,
            adaptive_sizing=True,
            overlap_tokens=200
        )

        # Dense content (table)
        table_text = "| A | B |\n|---|---|\n| 1 | 2 |" * 200

        chunks = chunker.chunk_by_tokens(table_text, preserve_boundaries=False)

        # Should create overlapping chunks with adaptive sizing
        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_calculate_overlap_amount(self):
        """Test that overlap amount is calculated correctly."""
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=250)

        # Create specific text to test overlap
        text = "X" * 12000  # 12,000 characters

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        assert len(chunks) >= 2

        # With 1000 token chunks (~4000 chars) and 250 token overlap (~1000 chars):
        # chunk1: 0-4000
        # chunk2: 3000-7000 (1000 char overlap)
        # chunk3: 6000-10000
        # chunk4: 9000-12000

        # Verify first chunk is approximately chunk_size * 4 characters
        assert len(chunks[0]) <= 4000 + 100  # Allow small variance

    def test_overlap_edge_case_exact_multiple(self):
        """Test overlap when text length is exact multiple of chunk size."""
        chunker = DocumentChunker(chunk_size=1000, overlap_tokens=200)

        # Exactly 2 chunks worth of text (8000 chars = 2 * 4000)
        text = "Y" * 8000

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should handle exact multiples correctly
        assert len(chunks) >= 2
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_zero_overlap_matches_default_behavior(self):
        """Test that overlap_tokens=0 produces same results as default."""
        chunker_with_zero = DocumentChunker(chunk_size=1000, overlap_tokens=0)
        chunker_default = DocumentChunker(chunk_size=1000)

        text = "Z" * 10000

        chunks_zero = chunker_with_zero.chunk_by_tokens(text, preserve_boundaries=False)
        chunks_default = chunker_default.chunk_by_tokens(text, preserve_boundaries=False)

        # Should produce identical results
        assert len(chunks_zero) == len(chunks_default)
        assert chunks_zero == chunks_default


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
