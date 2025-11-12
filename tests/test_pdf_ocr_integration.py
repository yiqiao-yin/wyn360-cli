"""
Integration tests for PDFReader with OCR support (Phase 5.3.2)

Tests cover:
- PDFReader initialization with enable_ocr parameter
- OCR integration with pymupdf engine
- OCR integration with pdfplumber engine
- OCR metadata in page data
- Scanned page detection
- Graceful fallback when Tesseract not available
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import sys

# Mock dependencies
sys.modules['pytesseract'] = MagicMock()
sys.modules['pdf2image'] = MagicMock()
sys.modules['pymupdf'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()

from wyn360_cli.document_readers import PDFReader, OCRProcessor


class TestPDFOCRIntegration:
    """Test PDFReader with OCR integration."""

    def test_reader_initialization_with_ocr(self):
        """Test reader initializes with OCR parameters."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmpfile:
            reader = PDFReader(
                file_path=tmpfile.name,
                enable_ocr=True,
                ocr_language="eng"
            )

            assert reader.enable_ocr is True
            assert reader.ocr_language == "eng"

    def test_reader_initialization_with_custom_language(self):
        """Test reader with custom OCR language."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmpfile:
            reader = PDFReader(
                file_path=tmpfile.name,
                enable_ocr=True,
                ocr_language="spa"
            )

            assert reader.ocr_language == "spa"

    def test_reader_initialization_ocr_disabled(self):
        """Test reader with OCR disabled (default)."""
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmpfile:
            reader = PDFReader(file_path=tmpfile.name)

            assert reader.enable_ocr is False

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pymupdf')
    @patch('wyn360_cli.document_readers.OCRProcessor')
    async def test_read_with_ocr_enabled_pymupdf(self, mock_ocr_class, mock_pymupdf):
        """Test reading PDF with OCR enabled (pymupdf)."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock PDF document
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_page = MagicMock()
            mock_page.get_text.return_value = ""  # Empty text - scanned page
            mock_page.find_tables.return_value = MagicMock(tables=[])

            # Mock pixmap for image rendering
            mock_pix = MagicMock()
            mock_pix.width = 100
            mock_pix.height = 100
            mock_pix.samples = b'\x00' * (100 * 100 * 3)
            mock_page.get_pixmap.return_value = mock_pix

            mock_doc.__getitem__.return_value = mock_page
            mock_pymupdf.open.return_value = mock_doc

            # Mock OCR processor
            mock_ocr = MagicMock()
            mock_ocr.is_scanned_page.return_value = True
            mock_ocr.extract_text.return_value = {
                "text": "OCR extracted text",
                "confidence": 85.5,
                "word_count": 3
            }
            mock_ocr_class.return_value = mock_ocr

            # Read PDF with OCR
            reader = PDFReader(file_path=tmpfile_path, enable_ocr=True)
            result = await reader.read()

            # Verify OCR was used
            assert len(result["pages"]) == 1
            assert result["pages"][0]["content"] == "OCR extracted text"
            assert result["pages"][0].get("ocr_used") is True
            assert result["pages"][0].get("ocr_confidence") == 85.5

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pymupdf')
    @patch('wyn360_cli.document_readers.OCRProcessor')
    async def test_read_text_based_pdf_no_ocr(self, mock_ocr_class, mock_pymupdf):
        """Test that text-based PDFs don't trigger OCR."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock PDF with actual text content
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_page = MagicMock()
            mock_page.get_text.return_value = "This is a text-based PDF with actual content"
            mock_page.find_tables.return_value = MagicMock(tables=[])
            mock_doc.__getitem__.return_value = mock_page
            mock_pymupdf.open.return_value = mock_doc

            mock_ocr = MagicMock()
            mock_ocr_class.return_value = mock_ocr

            # Read PDF with OCR enabled
            reader = PDFReader(file_path=tmpfile_path, enable_ocr=True)
            result = await reader.read()

            # OCR should not be used for text-based PDF
            assert len(result["pages"]) == 1
            assert "This is a text-based PDF" in result["pages"][0]["content"]
            assert result["pages"][0].get("ocr_used") is not True

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PDFPLUMBER', True)
    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.HAS_PDF2IMAGE', True)
    @patch('wyn360_cli.document_readers.pdfplumber')
    @patch('wyn360_cli.document_readers.OCRProcessor')
    async def test_read_with_ocr_pdfplumber(self, mock_ocr_class, mock_pdfplumber):
        """Test reading PDF with OCR enabled (pdfplumber engine)."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock pdfplumber PDF
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""  # Empty text
            mock_page.extract_tables.return_value = []

            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__.return_value = mock_pdf
            mock_pdfplumber.open.return_value = mock_pdf

            # Mock pdf2image
            with patch('wyn360_cli.document_readers.convert_from_path') as mock_convert:
                mock_image = MagicMock()
                mock_convert.return_value = [mock_image]

                # Mock OCR processor
                mock_ocr = MagicMock()
                mock_ocr.is_scanned_page.return_value = True
                mock_ocr.extract_text.return_value = {
                    "text": "OCR text from pdfplumber",
                    "confidence": 90.0,
                    "word_count": 4
                }
                mock_ocr_class.return_value = mock_ocr

                # Read PDF with OCR
                reader = PDFReader(
                    file_path=tmpfile_path,
                    engine="pdfplumber",
                    enable_ocr=True
                )
                result = await reader.read()

                # Verify OCR was used
                assert len(result["pages"]) == 1
                assert result["pages"][0]["content"] == "OCR text from pdfplumber"
                assert result["pages"][0].get("ocr_used") is True
                assert result["pages"][0].get("ocr_confidence") == 90.0

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', False)
    @patch('wyn360_cli.document_readers.pymupdf')
    async def test_ocr_graceful_fallback_no_tesseract(self, mock_pymupdf):
        """Test graceful fallback when Tesseract not installed."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock PDF
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_page = MagicMock()
            mock_page.get_text.return_value = ""  # Empty text
            mock_page.find_tables.return_value = MagicMock(tables=[])
            mock_doc.__getitem__.return_value = mock_page
            mock_pymupdf.open.return_value = mock_doc

            # Read PDF with OCR enabled but Tesseract not available
            reader = PDFReader(file_path=tmpfile_path, enable_ocr=True)
            result = await reader.read()

            # Should not crash, just skip OCR
            assert len(result["pages"]) == 1
            assert result["pages"][0].get("ocr_used") is not True

        finally:
            Path(tmpfile_path).unlink()

    @pytest.mark.asyncio
    @patch('wyn360_cli.document_readers.HAS_PYMUPDF', True)
    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pymupdf')
    @patch('wyn360_cli.document_readers.OCRProcessor')
    async def test_hybrid_pdf_mixed_pages(self, mock_ocr_class, mock_pymupdf):
        """Test hybrid PDF with both scanned and text-based pages."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name

        try:
            # Mock PDF with 2 pages: one text-based, one scanned
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 2

            # Page 1: text-based
            mock_page1 = MagicMock()
            mock_page1.get_text.return_value = "Regular text content"
            mock_page1.find_tables.return_value = MagicMock(tables=[])

            # Page 2: scanned
            mock_page2 = MagicMock()
            mock_page2.get_text.return_value = ""
            mock_page2.find_tables.return_value = MagicMock(tables=[])
            mock_pix = MagicMock()
            mock_pix.width = 100
            mock_pix.height = 100
            mock_pix.samples = b'\x00' * (100 * 100 * 3)
            mock_page2.get_pixmap.return_value = mock_pix

            mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
            mock_pymupdf.open.return_value = mock_doc

            # Mock OCR
            mock_ocr = MagicMock()
            mock_ocr.is_scanned_page.return_value = True
            mock_ocr.extract_text.return_value = {
                "text": "Scanned page text",
                "confidence": 88.0,
                "word_count": 3
            }
            mock_ocr_class.return_value = mock_ocr

            # Read hybrid PDF
            reader = PDFReader(file_path=tmpfile_path, enable_ocr=True)
            result = await reader.read()

            # Verify mixed pages
            assert len(result["pages"]) == 2
            # Page 1 should not use OCR
            assert "Regular text content" in result["pages"][0]["content"]
            assert result["pages"][0].get("ocr_used") is not True
            # Page 2 should use OCR
            assert result["pages"][1]["content"] == "Scanned page text"
            assert result["pages"][1].get("ocr_used") is True

        finally:
            Path(tmpfile_path).unlink()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
