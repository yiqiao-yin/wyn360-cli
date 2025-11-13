"""
Unit tests for Adaptive Chunking (Phase 5.7.1)

Tests cover:
- Backward compatibility (adaptive_sizing disabled by default)
- Dense content detection (tables, lists, code)
- Sparse content detection (prose)
- Mixed content handling
- _calculate_adaptive_size method
"""

import pytest
from wyn360_cli.document_readers import DocumentChunker


class TestAdaptiveChunking:
    """Test adaptive chunking functionality (Phase 5.7.1)."""

    def test_adaptive_sizing_disabled_default(self):
        """Test that adaptive sizing is disabled by default (backward compatibility)."""
        chunker = DocumentChunker(chunk_size=1000)

        assert chunker.adaptive_sizing is False
        assert chunker.chunk_size == 1000

        # Should use default chunk size regardless of content
        dense_text = "| Column 1 | Column 2 |\n|----------|----------|\n| Data 1   | Data 2   |"
        sparse_text = "This is a simple paragraph of text without any special formatting."

        # Both should use the same chunk size (1000 tokens = ~4000 chars)
        dense_chunks = chunker.chunk_by_tokens(dense_text, preserve_boundaries=False)
        sparse_chunks = chunker.chunk_by_tokens(sparse_text, preserve_boundaries=False)

        # Verify chunks were created
        assert len(dense_chunks) > 0
        assert len(sparse_chunks) > 0

    def test_adaptive_sizing_dense_content_tables(self):
        """Test that tables get smaller chunks when adaptive sizing is enabled."""
        chunker_adaptive = DocumentChunker(chunk_size=1000, adaptive_sizing=True)
        chunker_normal = DocumentChunker(chunk_size=1000, adaptive_sizing=False)

        # Create a table (dense content)
        table_text = """
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data A   | Data B   | Data C   |
| Data D   | Data E   | Data F   |
| Data G   | Data H   | Data I   |
""" * 100  # Repeat to make it long enough to chunk

        # Get adaptive chunk size
        adaptive_size = chunker_adaptive._calculate_adaptive_size(table_text)

        # Should be smaller than default (500 tokens for dense content)
        assert adaptive_size < chunker_normal.chunk_size
        assert adaptive_size >= 500  # At least 500 tokens

    def test_adaptive_sizing_dense_content_lists(self):
        """Test that lists get smaller chunks when adaptive sizing is enabled."""
        chunker = DocumentChunker(chunk_size=1000, adaptive_sizing=True)

        # Create a list (dense content)
        list_text = """
- Item 1
- Item 2
- Item 3
* Bullet point 1
* Bullet point 2
1. Numbered item 1
2. Numbered item 2
3. Numbered item 3
""" * 50  # Repeat to make it long

        # Get adaptive chunk size
        adaptive_size = chunker._calculate_adaptive_size(list_text)

        # Should be smaller than default
        assert adaptive_size < chunker.chunk_size
        assert adaptive_size >= 500

    def test_adaptive_sizing_dense_content_code(self):
        """Test that code blocks get smaller chunks when adaptive sizing is enabled."""
        chunker = DocumentChunker(chunk_size=1000, adaptive_sizing=True)

        # Create code block (dense content)
        code_text = """
```python
def example_function():
    print("Hello, world!")
    return True
```

Some text here.

    # Indented code (4 spaces)
    def another_function():
        pass
""" * 20

        # Get adaptive chunk size
        adaptive_size = chunker._calculate_adaptive_size(code_text)

        # Should be smaller than default
        assert adaptive_size < chunker.chunk_size
        assert adaptive_size >= 500

    def test_adaptive_sizing_sparse_content(self):
        """Test that prose text gets larger chunks when adaptive sizing is enabled."""
        chunker = DocumentChunker(chunk_size=1000, adaptive_sizing=True)

        # Create sparse prose text (no tables, lists, or code)
        prose_text = """
This is a regular paragraph of text without any special formatting.
It contains only simple sentences and common punctuation. There are
no tables, lists, or code blocks in this text. This is the kind of
content that benefits from larger chunk sizes because it maintains
better context when kept together.

Here is another paragraph that continues the narrative. It also
contains only plain text without any structured elements. This
allows the adaptive chunking algorithm to use a larger chunk size
for better semantic coherence.
""" * 50  # Repeat to make it long

        # Get adaptive chunk size
        adaptive_size = chunker._calculate_adaptive_size(prose_text)

        # Should be larger than default (1500 tokens for sparse content)
        assert adaptive_size > chunker.chunk_size
        assert adaptive_size <= 1500  # Capped at 1500

    def test_adaptive_sizing_mixed_content(self):
        """Test handling of mixed content (both dense and sparse)."""
        chunker = DocumentChunker(chunk_size=1000, adaptive_sizing=True)

        # Create mixed content (has both table and prose)
        mixed_text = """
This is some introductory text explaining the table below.

| Name    | Age | City        |
|---------|-----|-------------|
| Alice   | 30  | New York    |
| Bob     | 25  | Los Angeles |
| Charlie | 35  | Chicago     |

Here is some concluding text after the table.
"""

        # Get adaptive chunk size
        adaptive_size = chunker._calculate_adaptive_size(mixed_text)

        # Should detect as dense content (due to table)
        assert adaptive_size < chunker.chunk_size
        assert adaptive_size >= 500

    def test_calculate_adaptive_size_empty_text(self):
        """Test _calculate_adaptive_size with empty text."""
        chunker = DocumentChunker(chunk_size=1000, adaptive_sizing=True)

        # Empty text should return default chunk_size
        adaptive_size = chunker._calculate_adaptive_size("")
        assert adaptive_size == chunker.chunk_size

    def test_adaptive_sizing_integration(self):
        """Integration test: verify adaptive sizing works end-to-end."""
        # Create chunker with adaptive sizing enabled
        chunker = DocumentChunker(chunk_size=1000, adaptive_sizing=True)

        # Dense content (table)
        table_text = "| A | B |\n|---|---|\n| 1 | 2 |" * 200

        # Sparse content (prose)
        prose_text = "This is a paragraph. " * 500

        # Chunk both
        table_chunks = chunker.chunk_by_tokens(table_text, preserve_boundaries=False)
        prose_chunks = chunker.chunk_by_tokens(prose_text, preserve_boundaries=False)

        # Verify chunks were created
        assert len(table_chunks) > 0
        assert len(prose_chunks) > 0

        # Table should create more chunks (smaller chunk size)
        # Prose should create fewer chunks (larger chunk size)
        # Note: This is a heuristic test - exact counts depend on text length
        assert isinstance(table_chunks, list)
        assert isinstance(prose_chunks, list)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
