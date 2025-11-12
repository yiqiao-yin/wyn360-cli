"""
Unit tests for OCRProcessor class (Phase 5.3.1)

Tests cover:
- OCRProcessor initialization
- Tesseract availability checking
- Text extraction from images
- Confidence scoring
- Image preprocessing
- Scanned page detection
- Quality assessment
- Error handling (Tesseract not installed)
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
import numpy as np

# Mock pytesseract and pdf2image before importing
sys.modules['pytesseract'] = MagicMock()
sys.modules['pdf2image'] = MagicMock()

from wyn360_cli.document_readers import OCRProcessor, HAS_PYTESSERACT


class TestOCRProcessor:
    """Test OCRProcessor functionality."""

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_processor_initialization(self, mock_pytesseract):
        """Test processor initializes with correct language."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor(language="eng")

        assert processor.language == "eng"
        mock_pytesseract.get_tesseract_version.assert_called_once()

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_processor_custom_language(self, mock_pytesseract):
        """Test processor with custom language."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor(language="spa")

        assert processor.language == "spa"

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', False)
    def test_initialization_without_pytesseract(self):
        """Test error when pytesseract not installed."""
        with pytest.raises(RuntimeError) as exc_info:
            OCRProcessor()

        assert "Tesseract OCR not installed" in str(exc_info.value)
        assert "pip install pytesseract" in str(exc_info.value)

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_tesseract_binary_not_found(self, mock_pytesseract):
        """Test error when Tesseract binary not accessible."""
        mock_pytesseract.get_tesseract_version.side_effect = Exception("Binary not found")

        with pytest.raises(RuntimeError) as exc_info:
            OCRProcessor()

        assert "Tesseract binary not found" in str(exc_info.value)

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_extract_text_basic(self, mock_pytesseract):
        """Test basic text extraction."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        # Mock OCR results
        mock_pytesseract.image_to_data.return_value = {
            'conf': [95, 90, 85, 92, -1],  # -1 should be ignored
            'text': ['Hello', 'World', 'Test', 'OCR', '']
        }
        mock_pytesseract.image_to_string.return_value = "Hello World Test OCR"
        mock_pytesseract.Output.DICT = 'dict'

        processor = OCRProcessor()

        # Create dummy image
        image = Image.new('RGB', (100, 100), color='white')

        result = processor.extract_text(image, preprocess=False)

        # Verify results
        assert result["text"] == "Hello World Test OCR"
        assert result["confidence"] == pytest.approx(90.5, abs=0.1)  # (95+90+85+92)/4
        assert result["word_count"] == 4

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_extract_text_with_preprocessing(self, mock_pytesseract):
        """Test text extraction with preprocessing enabled."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_data.return_value = {
            'conf': [85],
            'text': ['Test']
        }
        mock_pytesseract.image_to_string.return_value = "Test"
        mock_pytesseract.Output.DICT = 'dict'

        processor = OCRProcessor()
        image = Image.new('RGB', (100, 100), color='white')

        result = processor.extract_text(image, preprocess=True)

        # Should call preprocessing
        assert "text" in result
        assert "confidence" in result

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_extract_text_empty_result(self, mock_pytesseract):
        """Test extraction with no text found."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_data.return_value = {
            'conf': [],
            'text': []
        }
        mock_pytesseract.image_to_string.return_value = ""
        mock_pytesseract.Output.DICT = 'dict'

        processor = OCRProcessor()
        image = Image.new('RGB', (100, 100), color='white')

        result = processor.extract_text(image, preprocess=False)

        assert result["text"] == ""
        assert result["confidence"] == 0
        assert result["word_count"] == 0

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_is_scanned_page_true(self, mock_pytesseract):
        """Test detection of scanned page."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_data.return_value = {
            'conf': [90] * 30,  # 30 words
            'text': ['word'] * 30
        }
        mock_pytesseract.image_to_string.return_value = " ".join(['word'] * 30)
        mock_pytesseract.Output.DICT = 'dict'

        processor = OCRProcessor()
        image = Image.new('RGB', (100, 100), color='white')

        # PDF has little text, but image has lots of text -> scanned
        is_scanned = processor.is_scanned_page(image, text_from_pdf="", min_words_threshold=20)

        assert is_scanned is True

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_is_scanned_page_false(self, mock_pytesseract):
        """Test detection of non-scanned page."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor()
        image = Image.new('RGB', (100, 100), color='white')

        # PDF has lots of text -> not scanned
        is_scanned = processor.is_scanned_page(
            image,
            text_from_pdf="This is a text-based PDF with lots of content",
            min_words_threshold=20
        )

        assert is_scanned is False

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_assess_quality_excellent(self, mock_pytesseract):
        """Test quality assessment for excellent OCR."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor()

        ocr_result = {"confidence": 95, "text": "Test", "word_count": 10}
        quality = processor.assess_quality(ocr_result)

        assert quality == "excellent"

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_assess_quality_good(self, mock_pytesseract):
        """Test quality assessment for good OCR."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor()

        ocr_result = {"confidence": 80, "text": "Test", "word_count": 10}
        quality = processor.assess_quality(ocr_result)

        assert quality == "good"

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_assess_quality_fair(self, mock_pytesseract):
        """Test quality assessment for fair OCR."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor()

        ocr_result = {"confidence": 65, "text": "Test", "word_count": 10}
        quality = processor.assess_quality(ocr_result)

        assert quality == "fair"

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_assess_quality_poor(self, mock_pytesseract):
        """Test quality assessment for poor OCR."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor()

        ocr_result = {"confidence": 45, "text": "Test", "word_count": 10}
        quality = processor.assess_quality(ocr_result)

        assert quality == "poor"

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_preprocess_image(self, mock_pytesseract):
        """Test image preprocessing."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        processor = OCRProcessor()

        # Create RGB image
        image = Image.new('RGB', (100, 100), color=(128, 128, 128))

        processed = processor._preprocess_image(image)

        # Should be grayscale
        assert processed.mode == 'L'

    @patch('wyn360_cli.document_readers.HAS_PYTESSERACT', True)
    @patch('wyn360_cli.document_readers.pytesseract')
    def test_extract_text_with_special_characters(self, mock_pytesseract):
        """Test text extraction with special characters."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_data.return_value = {
            'conf': [88],
            'text': ['Hello!']
        }
        mock_pytesseract.image_to_string.return_value = "Hello! @#$%"
        mock_pytesseract.Output.DICT = 'dict'

        processor = OCRProcessor()
        image = Image.new('RGB', (100, 100), color='white')

        result = processor.extract_text(image, preprocess=False)

        assert "Hello!" in result["text"]
        assert result["word_count"] == 2  # "Hello!" and "@#$%"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
