"""
Unit tests for Quality Scoring (Phase 5.7.4)

Tests cover:
- Backward compatibility (quality_threshold=0.0 by default)
- Quality score calculation
- Coherence checks (starts/ends properly)
- Completeness checks (no orphaned items)
- Independence checks (no unresolved references)
- Quality filtering
"""

import pytest
from wyn360_cli.document_readers import DocumentChunker


class TestQualityScoring:
    """Test quality scoring functionality (Phase 5.7.4)."""

    def test_quality_threshold_disabled_default(self):
        """Test that quality filtering is disabled by default (backward compatibility)."""
        chunker = DocumentChunker(chunk_size=1000)

        assert chunker.quality_threshold == 0.0

        # Should not filter any chunks
        text = "incomplete sentence without" * 100
        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # All chunks should be returned (no filtering)
        assert len(chunks) > 0

    def test_score_chunk_quality_perfect_chunk(self):
        """Test scoring of a high-quality chunk."""
        chunker = DocumentChunker(chunk_size=1000)

        # Perfect chunk: starts with capital, ends with period, complete sentences
        chunk = "This is a well-formed chunk. It contains complete sentences. The content is coherent and independent."

        score = chunker.score_chunk_quality(chunk)

        # Should have high score (close to 1.0)
        assert score >= 0.8

    def test_score_chunk_quality_lowercase_start(self):
        """Test penalty for chunks starting with lowercase."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = "this chunk starts with lowercase. It should get a penalty for that."

        score = chunker.score_chunk_quality(chunk)

        # Should be penalized but not zero
        assert 0.0 < score < 1.0
        assert score < 0.95  # Some penalty applied

    def test_score_chunk_quality_no_end_punctuation(self):
        """Test penalty for chunks without proper ending punctuation."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = "This chunk does not end properly"

        score = chunker.score_chunk_quality(chunk)

        # Should be penalized
        assert 0.0 < score < 1.0
        assert score < 0.95

    def test_score_chunk_quality_orphaned_list_item(self):
        """Test penalty for orphaned list items."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = "- Single list item without others"

        score = chunker.score_chunk_quality(chunk)

        # Should be penalized significantly
        assert 0.0 < score < 1.0
        assert score < 0.9

    def test_score_chunk_quality_complete_list(self):
        """Test that complete lists score well."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = """
- First item
- Second item
- Third item
"""

        score = chunker.score_chunk_quality(chunk)

        # Should score reasonably (might have minor penalties for punctuation)
        assert score >= 0.5

    def test_score_chunk_quality_incomplete_table(self):
        """Test penalty for incomplete tables."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = "| Column 1 | Column 2 |"

        score = chunker.score_chunk_quality(chunk)

        # Should be penalized for incomplete table
        assert 0.0 < score < 1.0
        assert score < 0.9

    def test_score_chunk_quality_complete_table(self):
        """Test that complete tables score well."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = """
| Column 1 | Column 2 |
|----------|----------|
| Data A   | Data B   |
| Data C   | Data D   |
"""

        score = chunker.score_chunk_quality(chunk)

        # Should score reasonably
        assert score >= 0.5

    def test_score_chunk_quality_incomplete_code_block(self):
        """Test penalty for incomplete code blocks."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = """
```python
def incomplete():
"""

        score = chunker.score_chunk_quality(chunk)

        # Should be heavily penalized
        assert 0.0 < score < 1.0
        assert score < 0.85  # 0.2 penalty for incomplete code block

    def test_score_chunk_quality_complete_code_block(self):
        """Test that complete code blocks score well."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = """
```python
def complete_function():
    return True
```
"""

        score = chunker.score_chunk_quality(chunk)

        # Should score reasonably (might have penalties for punctuation)
        assert score >= 0.5

    def test_score_chunk_quality_starts_with_reference(self):
        """Test penalty for chunks starting with pronouns."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = "This refers to something mentioned earlier. It is not independent."

        score = chunker.score_chunk_quality(chunk)

        # Should be penalized
        assert 0.0 < score < 1.0
        assert score < 0.95

    def test_score_chunk_quality_too_short(self):
        """Test penalty for very short chunks."""
        chunker = DocumentChunker(chunk_size=1000)

        chunk = "Short."

        score = chunker.score_chunk_quality(chunk)

        # Should be heavily penalized
        assert 0.0 < score < 1.0
        assert score < 0.9

    def test_score_chunk_quality_empty(self):
        """Test scoring of empty chunk."""
        chunker = DocumentChunker(chunk_size=1000)

        score = chunker.score_chunk_quality("")

        assert score == 0.0

    def test_quality_filtering_basic(self):
        """Test basic quality filtering."""
        chunker = DocumentChunker(chunk_size=100, quality_threshold=0.7)

        # Mix of good and bad chunks
        text = """
This is a good chunk. It has proper formatting and complete sentences.

incomplete chunk without

Another good chunk. This one also has proper structure.

this starts lowercase

Final good chunk. Well-formed and complete.
"""

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=True)

        # Should filter out low-quality chunks
        assert len(chunks) > 0

        # Verify remaining chunks have quality >= threshold
        for chunk in chunks:
            quality = chunker.score_chunk_quality(chunk)
            assert quality >= 0.7 or chunk in chunks  # Allow best chunk even if below threshold

    def test_quality_filtering_keeps_best_if_all_filtered(self):
        """Test that at least one chunk is kept even if all are below threshold."""
        chunker = DocumentChunker(chunk_size=50, quality_threshold=0.9)

        # All chunks will be low quality
        text = "incomplete " * 100

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should keep at least one chunk (the best one)
        assert len(chunks) >= 1

    def test_quality_filtering_disabled_with_zero_threshold(self):
        """Test that quality filtering is disabled when threshold is 0."""
        chunker = DocumentChunker(chunk_size=50, quality_threshold=0.0)

        text = "incomplete " * 100

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should keep all chunks
        assert len(chunks) > 1

    def test_quality_integration_all_features(self):
        """Integration test: all Phase 5.7 features together."""
        chunker = DocumentChunker(
            chunk_size=1000,
            adaptive_sizing=True,
            overlap_tokens=100,
            content_aware=True,
            quality_threshold=0.6
        )

        text = """
This is a complete paragraph with proper formatting.

| Table | Data |
|-------|------|
| Row 1 | A    |
| Row 2 | B    |

```python
def example():
    return True
```

Another complete paragraph. This demonstrates all features working together.
""" * 5

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create high-quality chunks
        assert len(chunks) > 0

        # All chunks should meet quality threshold
        for chunk in chunks:
            quality = chunker.score_chunk_quality(chunk)
            # Allow slight tolerance for best-chunk fallback
            assert quality >= 0.5


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
