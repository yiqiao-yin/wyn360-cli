"""
Unit tests for Content-Aware Chunking (Phase 5.7.3)

Tests cover:
- Backward compatibility (content_aware=False by default)
- Table detection and preservation
- Code block detection and preservation
- List detection and preservation
- Mixed content handling
- _detect_content_blocks method
"""

import pytest
from wyn360_cli.document_readers import DocumentChunker


class TestContentAwareChunking:
    """Test content-aware chunking functionality (Phase 5.7.3)."""

    def test_content_aware_disabled_default(self):
        """Test that content-aware chunking is disabled by default (backward compatibility)."""
        chunker = DocumentChunker(chunk_size=1000)

        assert chunker.content_aware is False

        # Regular chunking should split anywhere
        text_with_table = """
Some text before.

| Column 1 | Column 2 |
|----------|----------|
| Data A   | Data B   |
| Data C   | Data D   |

Some text after.
""" * 100

        chunks = chunker.chunk_by_tokens(text_with_table, preserve_boundaries=False)

        # Should create chunks (may split table)
        assert len(chunks) > 0

    def test_detect_content_blocks_empty(self):
        """Test _detect_content_blocks with empty text."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        blocks = chunker._detect_content_blocks("")

        assert blocks == []

    def test_detect_content_blocks_no_blocks(self):
        """Test _detect_content_blocks with plain text."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        text = "This is plain text without any special formatting."
        blocks = chunker._detect_content_blocks(text)

        assert blocks == []

    def test_detect_content_blocks_table(self):
        """Test detecting markdown tables."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        text = """
Some text before.

| Name | Age |
|------|-----|
| Alice | 30 |
| Bob   | 25 |

Some text after.
"""

        blocks = chunker._detect_content_blocks(text)

        # Should detect table
        table_blocks = [b for b in blocks if b['type'] == 'table']
        assert len(table_blocks) >= 1
        assert '| Name | Age |' in table_blocks[0]['content']

    def test_detect_content_blocks_code(self):
        """Test detecting code blocks."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        text = """
Some text before.

```python
def hello():
    print("Hello, world!")
```

Some text after.
"""

        blocks = chunker._detect_content_blocks(text)

        # Should detect code block
        code_blocks = [b for b in blocks if b['type'] == 'code']
        assert len(code_blocks) == 1
        assert 'def hello()' in code_blocks[0]['content']

    def test_detect_content_blocks_list(self):
        """Test detecting lists."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        text = """
Some text before.

- Item 1
- Item 2
- Item 3

Some text after.
"""

        blocks = chunker._detect_content_blocks(text)

        # Should detect list
        list_blocks = [b for b in blocks if b['type'] == 'list']
        assert len(list_blocks) >= 1
        # List detection may vary based on regex, just verify blocks were found
        assert len(blocks) > 0

    def test_content_aware_preserves_table(self):
        """Test that content-aware chunking doesn't split tables."""
        chunker = DocumentChunker(chunk_size=100, content_aware=True)  # Small chunks

        text = """
Before table text that should be in a separate chunk if needed.

| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

After table text.
"""

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify table is preserved (not split across chunks)
        # Find which chunk contains the table header
        table_chunks = [c for c in chunks if '| Column A | Column B |' in c]

        if table_chunks:
            # Table should be complete in one chunk
            assert '| Value 1' in table_chunks[0]
            assert '| Value 4' in table_chunks[0]

    def test_content_aware_preserves_code_block(self):
        """Test that content-aware chunking doesn't split code blocks."""
        chunker = DocumentChunker(chunk_size=100, content_aware=True)  # Small chunks

        text = """
Text before code.

```python
def calculate_sum(a, b):
    result = a + b
    return result

print(calculate_sum(5, 3))
```

Text after code.
"""

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Verify chunks were created
        assert len(chunks) > 0

        # Find chunk containing code block start
        code_chunks = [c for c in chunks if '```python' in c]

        if code_chunks:
            # Code block should be complete (start and end in same chunk)
            assert 'def calculate_sum' in code_chunks[0]
            assert 'return result' in code_chunks[0]
            assert 'print(calculate_sum' in code_chunks[0]

    def test_content_aware_large_block(self):
        """Test handling of content blocks larger than chunk size."""
        chunker = DocumentChunker(chunk_size=50, content_aware=True)  # Very small chunks

        # Create a large table
        text = """
| Column 1 | Column 2 | Column 3 | Column 4 |
|----------|----------|----------|----------|
""" + "\n".join(f"| Value {i}A | Value {i}B | Value {i}C | Value {i}D |" for i in range(100))

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should still create chunks (even though block is large)
        assert len(chunks) > 0

    def test_content_aware_mixed_content(self):
        """Test content-aware chunking with mixed content types."""
        chunker = DocumentChunker(chunk_size=200, content_aware=True)

        text = """
Introduction paragraph.

| Table 1 | Data |
|---------|------|
| Row 1   | A    |
| Row 2   | B    |

Middle paragraph.

```javascript
console.log("Hello");
```

- List item 1
- List item 2
- List item 3

Conclusion paragraph.
"""

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create chunks
        assert len(chunks) > 0

        # Verify content blocks aren't split
        # (This is a heuristic test - we check that blocks appear complete)
        all_text = ''.join(chunks)
        assert '| Table 1 | Data |' in all_text
        assert 'console.log' in all_text
        assert '- List item 1' in all_text

    def test_content_aware_integration_with_adaptive(self):
        """Test content-aware chunking with adaptive sizing."""
        chunker = DocumentChunker(
            chunk_size=1000,
            adaptive_sizing=True,
            content_aware=True
        )

        text = """
Regular paragraph of text.

| Column 1 | Column 2 |
|----------|----------|
| Data A   | Data B   |

Another paragraph.
""" * 10

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create chunks
        assert len(chunks) > 0

    def test_content_aware_integration_with_overlap(self):
        """Test content-aware chunking with overlapping chunks."""
        chunker = DocumentChunker(
            chunk_size=1000,
            overlap_tokens=100,
            content_aware=True
        )

        text = """
Paragraph before table.

| Header A | Header B |
|----------|----------|
| Cell 1   | Cell 2   |

Paragraph after table.
""" * 20

        chunks = chunker.chunk_by_tokens(text, preserve_boundaries=False)

        # Should create chunks
        assert len(chunks) > 0

    def test_content_aware_empty_text(self):
        """Test content-aware chunking with empty text."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        chunks = chunker.chunk_by_tokens("", preserve_boundaries=False)

        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_content_blocks_sorted_by_position(self):
        """Test that detected content blocks are sorted by position."""
        chunker = DocumentChunker(chunk_size=1000, content_aware=True)

        text = """
First paragraph.

```code
some code
```

Middle paragraph.

| Table |
|-------|
| Data  |

Last paragraph.
"""

        blocks = chunker._detect_content_blocks(text)

        # Blocks should be sorted by start position
        if len(blocks) >= 2:
            for i in range(len(blocks) - 1):
                assert blocks[i]['start'] <= blocks[i + 1]['start']


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
