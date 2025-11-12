"""
Unit tests for PDFReader class (Phase 13.4)

Tests cover:
- PDF file reading with pymupdf and pdfplumber
- Page extraction with page ranges
- Table detection and markdown conversion
- Page-aware chunking (3-5 pages per chunk)
- Error handling (file not found, libraries not installed)
- Engine switching (pymupdf vs pdfplumber)
- Edge cases (empty PDFs, single page, large documents)
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call, AsyncMock
from wyn360_cli.document_readers import PDFReader, count_tokens


class TestPDFReader:
    """Test PDFReader functionality."""

    def test_reader_initialization(self):
        """Test reader initializes with correct parameters."""
        reader = PDFReader(file_path="test.pdf", chunk_size=1000, engine="pymupdf")

        assert reader.file_path == Path("test.pdf")
        assert reader.chunk_size == 1000
        assert reader.engine == "pymupdf"
        assert reader.pages_per_chunk == 3

    def test_reader_initialization_with_custom_pages_per_chunk(self):
        """Test reader initializes with custom pages_per_chunk."""
        reader = PDFReader(
            file_path="test.pdf",
            chunk_size=500,
            engine="pdfplumber",
            pages_per_chunk=5
        )

        assert reader.engine == "pdfplumber"
        assert reader.chunk_size == 500
        assert reader.pages_per_chunk == 5

    def test_reader_invalid_engine(self):
        """Test error when invalid engine specified."""
        with pytest.raises(ValueError) as exc_info:
            PDFReader(file_path="test.pdf", engine="invalid")

        assert "Unknown PDF engine" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', False)
    async def test_read_without_pymupdf(self):
        """Test error when pymupdf not installed."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmpfile:
            reader = PDFReader(file_path=tmpfile.name, engine="pymupdf")

            with pytest.raises(ImportError) as exc_info:
                await reader.read()

            assert "pymupdf not installed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PDFPLUMBER', False)
    async def test_read_without_pdfplumber(self):
        """Test error when pdfplumber not installed."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmpfile:
            reader = PDFReader(file_path=tmpfile.name, engine="pdfplumber")

            with pytest.raises(ImportError) as exc_info:
                await reader.read()

            assert "pdfplumber not installed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    @patch('wyn360_cli.document_readers.pymupdf')
    async def test_read_nonexistent_file(self, mock_pymupdf):
        """Test error when file doesn't exist."""
        reader = PDFReader(file_path="/nonexistent/file.pdf", engine="pymupdf")

        with pytest.raises(FileNotFoundError):
            await reader.read()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    async def test_read_simple_pdf_pymupdf(self):
        """Test reading a simple PDF with PyMuPDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock pymupdf
            with patch('wyn360_cli.document_readers.pymupdf') as mock_pymupdf:
                # Mock document
                mock_doc = MagicMock()
                mock_doc.__len__.return_value = 3  # 3 pages

                # Mock pages
                page1 = Mock()
                page1.get_text.return_value = "Page 1 content with some text."
                page1.find_tables.return_value = Mock(tables=[])
                page1.get_images.return_value = []  # No images

                page2 = Mock()
                page2.get_text.return_value = "Page 2 content with more text."
                page2.find_tables.return_value = Mock(tables=[])
                page2.get_images.return_value = []  # No images

                page3 = Mock()
                page3.get_text.return_value = "Page 3 final content."
                page3.find_tables.return_value = Mock(tables=[])
                page3.get_images.return_value = []  # No images

                mock_doc.__getitem__.side_effect = [page1, page2, page3]
                mock_pymupdf.open.return_value = mock_doc

                # Read PDF
                reader = PDFReader(file_path=tmpfile_path, engine="pymupdf")
                result = await reader.read()

                # Verify results
                assert result["total_pages"] == 3
                assert len(result["pages"]) == 3
                assert result["page_range_read"] == (1, 3)
                assert result["pages"][0]["page_number"] == 1
                assert result["pages"][1]["page_number"] == 2
                assert result["pages"][2]["page_number"] == 3
                assert "Page 1 content" in result["pages"][0]["content"]

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PDFPLUMBER', True)
    async def test_read_simple_pdf_pdfplumber(self):
        """Test reading a simple PDF with pdfplumber."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock pdfplumber
            with patch('wyn360_cli.document_readers.pdfplumber') as mock_pdfplumber:
                # Mock pages
                page1 = Mock()
                page1.extract_text.return_value = "Page 1 content."
                page1.extract_tables.return_value = []
                page1.images = []  # No images

                page2 = Mock()
                page2.extract_text.return_value = "Page 2 content."
                page2.extract_tables.return_value = []
                page2.images = []  # No images

                # Mock PDF
                mock_pdf = MagicMock()
                mock_pdf.__enter__.return_value = mock_pdf
                mock_pdf.pages = [page1, page2]
                mock_pdfplumber.open.return_value = mock_pdf

                # Read PDF
                reader = PDFReader(file_path=tmpfile_path, engine="pdfplumber")
                result = await reader.read()

                # Verify results
                assert result["total_pages"] == 2
                assert len(result["pages"]) == 2
                assert result["page_range_read"] == (1, 2)
                assert "Page 1 content" in result["pages"][0]["content"]

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    async def test_read_with_page_range(self):
        """Test reading specific page range."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            with patch('wyn360_cli.document_readers.pymupdf') as mock_pymupdf:
                # Mock document with 10 pages
                mock_doc = MagicMock()
                mock_doc.__len__.return_value = 10

                # Mock pages 3-5 only (what we request)
                mock_pages = []
                for i in range(3, 6):  # Pages 3, 4, 5 (0-indexed: 2, 3, 4)
                    page = Mock()
                    page.get_text.return_value = f"Page {i} content."
                    page.find_tables.return_value = Mock(tables=[])
                    page.get_images.return_value = []  # No images
                    mock_pages.append(page)

                mock_doc.__getitem__.side_effect = mock_pages
                mock_pymupdf.open.return_value = mock_doc

                # Read pages 3-5
                reader = PDFReader(file_path=tmpfile_path, engine="pymupdf")
                result = await reader.read(page_range=(3, 5))

                # Verify only requested pages read
                assert result["total_pages"] == 10
                assert len(result["pages"]) == 3
                assert result["page_range_read"] == (3, 5)
                assert result["pages"][0]["page_number"] == 3
                assert result["pages"][2]["page_number"] == 5

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    async def test_read_with_tables_pymupdf(self):
        """Test table extraction with PyMuPDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            with patch('wyn360_cli.document_readers.pymupdf') as mock_pymupdf:
                # Mock document
                mock_doc = MagicMock()
                mock_doc.__len__.return_value = 1

                # Mock page with table
                page = Mock()
                page.get_text.return_value = "Page with table."
                page.get_images.return_value = []  # No images

                # Mock table
                mock_table = Mock()
                mock_table.extract.return_value = [
                    ["Name", "Age"],
                    ["Alice", "30"],
                    ["Bob", "25"]
                ]

                page_tables = Mock()
                page_tables.tables = [mock_table]
                page.find_tables.return_value = page_tables

                mock_doc.__getitem__.return_value = page
                mock_pymupdf.open.return_value = mock_doc

                # Read PDF
                reader = PDFReader(file_path=tmpfile_path, engine="pymupdf")
                result = await reader.read()

                # Verify table detected
                assert result["has_tables"] is True
                assert result["pages"][0]["has_tables"] is True
                assert "| Name | Age |" in result["pages"][0]["content"]
                assert "| Alice | 30 |" in result["pages"][0]["content"]

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PDFPLUMBER', True)
    async def test_read_with_tables_pdfplumber(self):
        """Test table extraction with pdfplumber."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            with patch('wyn360_cli.document_readers.pdfplumber') as mock_pdfplumber:
                # Mock page with table
                page = Mock()
                page.extract_text.return_value = "Page with table."
                page.extract_tables.return_value = [
                    [
                        ["Header1", "Header2"],
                        ["Data1", "Data2"],
                        ["Data3", "Data4"]
                    ]
                ]
                page.images = []  # No images

                # Mock PDF
                mock_pdf = MagicMock()
                mock_pdf.__enter__.return_value = mock_pdf
                mock_pdf.pages = [page]
                mock_pdfplumber.open.return_value = mock_pdf

                # Read PDF
                reader = PDFReader(file_path=tmpfile_path, engine="pdfplumber")
                result = await reader.read()

                # Verify table detected
                assert result["has_tables"] is True
                assert "| Header1 | Header2 |" in result["pages"][0]["content"]
                assert "| Data1 | Data2 |" in result["pages"][0]["content"]

        finally:
            Path(tmpfile_path).unlink()

    def test_table_to_markdown_with_pipes(self):
        """Test that pipe characters in cells are escaped."""
        reader = PDFReader(file_path="test.pdf")

        table_data = [
            ["Header"],
            ["Value|With|Pipes"]
        ]

        markdown = reader._table_to_markdown_pymupdf(table_data)

        # Pipe should be escaped
        assert "Value\\|With\\|Pipes" in markdown

    def test_chunk_pages_single_small_page(self):
        """Test chunking a single small page."""
        reader = PDFReader(file_path="test.pdf", chunk_size=1000)

        pages = [
            {
                "page_number": 1,
                "content": "Short page content." * 10,
                "tokens": 50,
                "has_tables": False
            }
        ]

        chunks = reader.chunk_pages(pages)

        # Single small page should be one chunk
        assert len(chunks) == 1
        assert chunks[0]["page_range"] == (1, 1)
        assert chunks[0]["tokens"] == 50
        assert chunks[0]["position"]["chunk_type"] == "page_range"

    def test_chunk_pages_multiple_small_pages(self):
        """Test chunking multiple small pages."""
        reader = PDFReader(file_path="test.pdf", chunk_size=1000, pages_per_chunk=3)

        pages = [
            {"page_number": 1, "content": "Page 1" * 20, "tokens": 100, "has_tables": False},
            {"page_number": 2, "content": "Page 2" * 20, "tokens": 100, "has_tables": False},
            {"page_number": 3, "content": "Page 3" * 20, "tokens": 100, "has_tables": False},
            {"page_number": 4, "content": "Page 4" * 20, "tokens": 100, "has_tables": False},
            {"page_number": 5, "content": "Page 5" * 20, "tokens": 100, "has_tables": False}
        ]

        chunks = reader.chunk_pages(pages)

        # Should create chunks of 3 pages each
        assert len(chunks) == 2
        assert chunks[0]["page_range"] == (1, 3)
        assert chunks[1]["page_range"] == (4, 5)
        assert "[Page 1]" in chunks[0]["content"]
        assert "[Page 3]" in chunks[0]["content"]

    def test_chunk_pages_respects_token_limit(self):
        """Test that chunking respects token limit."""
        reader = PDFReader(file_path="test.pdf", chunk_size=200, pages_per_chunk=5)

        # Create pages that would exceed limit if combined
        pages = [
            {"page_number": 1, "content": "P1" * 50, "tokens": 150, "has_tables": False},
            {"page_number": 2, "content": "P2" * 50, "tokens": 150, "has_tables": False},
            {"page_number": 3, "content": "P3" * 50, "tokens": 150, "has_tables": False}
        ]

        chunks = reader.chunk_pages(pages)

        # Each page should be its own chunk (exceeds limit when combined)
        assert len(chunks) == 3
        assert all(c["page_range"][0] == c["page_range"][1] for c in chunks)

    def test_chunk_pages_preserves_page_markers(self):
        """Test that page markers are preserved in chunk content."""
        reader = PDFReader(file_path="test.pdf", chunk_size=1000)

        pages = [
            {"page_number": 10, "content": "Content from page 10", "tokens": 50, "has_tables": False},
            {"page_number": 11, "content": "Content from page 11", "tokens": 50, "has_tables": False}
        ]

        chunks = reader.chunk_pages(pages)

        # Verify page markers
        assert "[Page 10]" in chunks[0]["content"]
        assert "[Page 11]" in chunks[0]["content"]

    def test_chunk_pages_with_tables(self):
        """Test chunking preserves table information."""
        reader = PDFReader(file_path="test.pdf", chunk_size=1000)

        pages = [
            {"page_number": 1, "content": "Page 1", "tokens": 50, "has_tables": False},
            {"page_number": 2, "content": "| A | B |\n| C | D |", "tokens": 60, "has_tables": True},
            {"page_number": 3, "content": "Page 3", "tokens": 50, "has_tables": False}
        ]

        chunks = reader.chunk_pages(pages)

        # Should be one chunk with has_tables=True
        assert len(chunks) == 1
        assert chunks[0]["has_tables"] is True

    def test_chunk_pages_empty(self):
        """Test chunking with no pages."""
        reader = PDFReader(file_path="test.pdf")

        chunks = reader.chunk_pages([])

        assert chunks == []


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
