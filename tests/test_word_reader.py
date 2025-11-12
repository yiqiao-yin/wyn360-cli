"""
Unit tests for WordReader class (Phase 13.3)

Tests cover:
- Word file reading with python-docx
- Section extraction with headings
- Table extraction and markdown conversion
- Structure-aware chunking (full sections and partial)
- Error handling (file not found, python-docx not installed)
- Edge cases (no sections, large sections, empty document)
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from wyn360_cli.document_readers import WordReader, count_tokens


class TestWordReader:
    """Test WordReader functionality."""

    def test_reader_initialization(self):
        """Test reader initializes with correct parameters."""
        reader = WordReader(file_path="test.docx", chunk_size=1000)

        assert reader.file_path == Path("test.docx")
        assert reader.chunk_size == 1000
        assert reader.image_handling == "describe"

    def test_reader_initialization_with_image_handling(self):
        """Test reader initializes with custom image handling."""
        reader = WordReader(
            file_path="test.docx",
            chunk_size=500,
            image_handling="skip"
        )

        assert reader.image_handling == "skip"
        assert reader.chunk_size == 500

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', False)
    def test_read_without_python_docx(self):
        """Test error when python-docx not installed."""
        with tempfile.NamedTemporaryFile(suffix=".docx") as tmpfile:
            reader = WordReader(file_path=tmpfile.name)

            with pytest.raises(ImportError) as exc_info:
                reader.read()

            assert "python-docx not installed" in str(exc_info.value)

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', True)
    @patch('wyn360_cli.document_readers.Document')
    def test_read_nonexistent_file(self, mock_document):
        """Test error when file doesn't exist."""
        reader = WordReader(file_path="/nonexistent/file.docx")

        with pytest.raises(FileNotFoundError):
            reader.read()

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', True)
    @patch('wyn360_cli.document_readers.Document')
    def test_read_simple_document(self, mock_document):
        """Test reading a simple Word document with sections."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock document
            mock_doc = MagicMock()

            # Create mock paragraphs
            heading_para = Mock()
            heading_para.style.name = "Heading 1"
            heading_para.text = "Introduction"
            heading_para._element = Mock()

            content_para = Mock()
            content_para.style.name = "Normal"
            content_para.text = "This is the introduction content."
            content_para._element = Mock()

            mock_doc.paragraphs = [heading_para, content_para]

            # Mock document structure
            heading_element = Mock()
            heading_element.tag = "w:p"
            content_element = Mock()
            content_element.tag = "w:p"

            mock_doc.element.body = [heading_element, content_element]
            mock_doc.tables = []

            # Map elements to paragraphs
            heading_para._element = heading_element
            content_para._element = content_element

            mock_document.return_value = mock_doc

            # Read document
            reader = WordReader(file_path=tmpfile_path)
            result = reader.read()

            # Verify results
            assert result["total_sections"] == 1
            assert len(result["sections"]) == 1
            assert result["sections"][0]["title"] == "Introduction"
            assert result["sections"][0]["level"] == 1
            assert "introduction content" in result["sections"][0]["content"].lower()

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', True)
    @patch('wyn360_cli.document_readers.Document')
    def test_extract_multiple_sections(self, mock_document):
        """Test extracting multiple sections with different heading levels."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_doc = MagicMock()

            # Create sections
            h1_para = Mock()
            h1_para.style.name = "Heading 1"
            h1_para.text = "Chapter 1"
            h1_para._element = Mock()

            p1_para = Mock()
            p1_para.style.name = "Normal"
            p1_para.text = "Content of chapter 1."
            p1_para._element = Mock()

            h2_para = Mock()
            h2_para.style.name = "Heading 2"
            h2_para.text = "Section 1.1"
            h2_para._element = Mock()

            p2_para = Mock()
            p2_para.style.name = "Normal"
            p2_para.text = "Content of section 1.1."
            p2_para._element = Mock()

            mock_doc.paragraphs = [h1_para, p1_para, h2_para, p2_para]

            # Mock elements
            elements = [Mock() for _ in range(4)]
            for elem in elements:
                elem.tag = "w:p"

            h1_para._element = elements[0]
            p1_para._element = elements[1]
            h2_para._element = elements[2]
            p2_para._element = elements[3]

            mock_doc.element.body = elements
            mock_doc.tables = []

            mock_document.return_value = mock_doc

            reader = WordReader(file_path=tmpfile_path)
            result = reader.read()

            # Verify multiple sections
            assert result["total_sections"] == 2
            assert result["sections"][0]["title"] == "Chapter 1"
            assert result["sections"][0]["level"] == 1
            assert result["sections"][1]["title"] == "Section 1.1"
            assert result["sections"][1]["level"] == 2

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', True)
    @patch('wyn360_cli.document_readers.Document')
    def test_extract_table(self, mock_document):
        """Test table extraction and markdown conversion."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_doc = MagicMock()

            # Create heading
            heading_para = Mock()
            heading_para.style.name = "Heading 1"
            heading_para.text = "Data Table"
            heading_para._element = Mock()

            mock_doc.paragraphs = [heading_para]

            # Create table
            mock_table = Mock()
            row1 = Mock()
            row1.cells = [Mock(text="Name"), Mock(text="Age")]
            row2 = Mock()
            row2.cells = [Mock(text="Alice"), Mock(text="30")]
            row3 = Mock()
            row3.cells = [Mock(text="Bob"), Mock(text="25")]

            mock_table.rows = [row1, row2, row3]
            mock_table._element = Mock()

            mock_doc.tables = [mock_table]

            # Mock elements
            heading_elem = Mock()
            heading_elem.tag = "w:p"
            table_elem = Mock()
            table_elem.tag = "w:tbl"

            heading_para._element = heading_elem
            mock_table._element = table_elem

            mock_doc.element.body = [heading_elem, table_elem]

            mock_document.return_value = mock_doc

            reader = WordReader(file_path=tmpfile_path)
            result = reader.read()

            # Verify table was extracted
            assert result["total_sections"] == 1
            assert result["sections"][0]["has_tables"] is True
            content = result["sections"][0]["content"]
            assert "| Name | Age |" in content
            assert "| --- | --- |" in content
            assert "| Alice | 30 |" in content
            assert "| Bob | 25 |" in content

        finally:
            Path(tmpfile_path).unlink()

    def test_table_to_markdown(self):
        """Test table to markdown conversion."""
        reader = WordReader(file_path="test.docx")

        # Mock table
        mock_table = Mock()
        row1 = Mock()
        row1.cells = [Mock(text="Header1"), Mock(text="Header2")]
        row2 = Mock()
        row2.cells = [Mock(text="Data1"), Mock(text="Data2")]
        row3 = Mock()
        row3.cells = [Mock(text="Data3"), Mock(text="Data4")]

        mock_table.rows = [row1, row2, row3]

        markdown = reader._table_to_markdown(mock_table)

        # Verify markdown structure
        assert "| Header1 | Header2 |" in markdown
        assert "| --- | --- |" in markdown
        assert "| Data1 | Data2 |" in markdown
        assert "| Data3 | Data4 |" in markdown

    def test_table_to_markdown_with_pipes(self):
        """Test that pipe characters in cells are escaped."""
        reader = WordReader(file_path="test.docx")

        mock_table = Mock()
        row1 = Mock()
        row1.cells = [Mock(text="Header")]
        row2 = Mock()
        row2.cells = [Mock(text="Value|With|Pipes")]

        mock_table.rows = [row1, row2]

        markdown = reader._table_to_markdown(mock_table)

        # Pipe should be escaped
        assert "Value\\|With\\|Pipes" in markdown

    def test_chunk_sections_single_small_section(self):
        """Test chunking a single small section."""
        reader = WordReader(file_path="test.docx", chunk_size=1000)

        sections = [
            {
                "level": 1,
                "title": "Introduction",
                "content": "This is a short introduction." * 5,
                "tokens": 50
            }
        ]

        chunks = reader.chunk_sections(sections)

        # Single small section should be one chunk
        assert len(chunks) == 1
        assert chunks[0]["section_title"] == "Introduction"
        assert chunks[0]["tokens"] == 50
        assert chunks[0]["position"]["chunk_type"] == "full_section"

    def test_chunk_sections_multiple_small_sections(self):
        """Test chunking multiple small sections."""
        reader = WordReader(file_path="test.docx", chunk_size=1000)

        sections = [
            {"level": 1, "title": "Section 1", "content": "Content 1" * 20, "tokens": 100},
            {"level": 1, "title": "Section 2", "content": "Content 2" * 20, "tokens": 100},
            {"level": 1, "title": "Section 3", "content": "Content 3" * 20, "tokens": 100}
        ]

        chunks = reader.chunk_sections(sections)

        # Each section should be its own chunk
        assert len(chunks) == 3
        assert all(c["position"]["chunk_type"] == "full_section" for c in chunks)

    def test_chunk_sections_large_section(self):
        """Test chunking a large section that exceeds chunk_size."""
        reader = WordReader(file_path="test.docx", chunk_size=200)

        # Create large section with multiple paragraphs
        content = "\n\n".join([f"Paragraph {i} with some content." * 10 for i in range(20)])

        sections = [
            {
                "level": 1,
                "title": "Large Section",
                "content": content,
                "tokens": count_tokens(content)
            }
        ]

        chunks = reader.chunk_sections(sections)

        # Large section should be split into multiple chunks
        assert len(chunks) > 1
        assert all(c["section_title"] == "Large Section" for c in chunks)
        # At least one chunk should be marked as partial
        assert any(c["position"]["chunk_type"] == "partial" for c in chunks)

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', True)
    @patch('wyn360_cli.document_readers.Document')
    def test_document_without_headings(self, mock_document):
        """Test document with no headings (all paragraphs)."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_doc = MagicMock()

            # Only normal paragraphs, no headings
            p1 = Mock()
            p1.style.name = "Normal"
            p1.text = "First paragraph."
            p1._element = Mock()

            p2 = Mock()
            p2.style.name = "Normal"
            p2.text = "Second paragraph."
            p2._element = Mock()

            mock_doc.paragraphs = [p1, p2]

            elements = [Mock(), Mock()]
            for elem in elements:
                elem.tag = "w:p"

            p1._element = elements[0]
            p2._element = elements[1]

            mock_doc.element.body = elements
            mock_doc.tables = []

            mock_document.return_value = mock_doc

            reader = WordReader(file_path=tmpfile_path)
            result = reader.read()

            # Should create a single "Document" section
            assert result["total_sections"] == 1
            assert result["sections"][0]["title"] == "Document"
            assert "First paragraph" in result["sections"][0]["content"]
            assert "Second paragraph" in result["sections"][0]["content"]

        finally:
            Path(tmpfile_path).unlink()

    @patch('wyn360_cli.document_readers.HAS_PYTHON_DOCX', True)
    @patch('wyn360_cli.document_readers.Document')
    def test_empty_document(self, mock_document):
        """Test empty document with no content."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            mock_doc = MagicMock()
            mock_doc.paragraphs = []
            mock_doc.element.body = []
            mock_doc.tables = []

            mock_document.return_value = mock_doc

            reader = WordReader(file_path=tmpfile_path)
            result = reader.read()

            # Empty document should return no sections
            assert result["total_sections"] == 0
            assert len(result["sections"]) == 0
            assert result["total_tokens"] == 0

        finally:
            Path(tmpfile_path).unlink()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
