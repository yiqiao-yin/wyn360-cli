# WYN360 CLI - OCR Support Implementation Roadmap

**Status:** 📋 Phase 5.3 - Planning Complete, Ready for Implementation
**Priority:** Medium
**Target Version:** v0.3.33-v0.3.34
**Estimated Completion:** 2-3 weeks

---

## 📋 Executive Summary

This roadmap outlines the implementation of **OCR Support** for scanned PDFs - enabling text extraction from image-based PDF documents. This is a medium-priority enhancement in Phase 5.3.

### Key Value Proposition

**Current State:** Scanned PDFs (images of pages) cannot be read. Text extraction only works on text-based PDFs.

**With OCR:** Scanned PDFs are automatically detected and processed with OCR to extract text, making them searchable and analyzable.

### Business Impact

- **Scanned document support** - Process legacy documents, forms, receipts
- **Universal PDF handling** - Works with any PDF regardless of type
- **Cost awareness** - Clear warnings about OCR processing time
- **Quality assessment** - Confidence scores for OCR results

---

## 🎯 Implementation Plan Overview

### Phase 5.3.1: OCR Infrastructure (v0.3.33)
- Add Tesseract OCR dependency (or pytesseract wrapper)
- Create OCRProcessor class for text extraction
- Implement scanned PDF detection logic
- Basic text extraction from images

### Phase 5.3.2: Integration with PDFReader (v0.3.33)
- Update PDFReader to detect scanned pages
- Process scanned pages with OCR
- Combine OCR text with existing text (hybrid PDFs)
- Add OCR confidence scores to chunks

### Phase 5.3.3: Quality & Optimization (v0.3.34)
- Language detection (English, Spanish, etc.)
- OCR preprocessing (deskew, denoise)
- Quality assessment and warnings
- Performance optimization for large scans

### Phase 5.3.4: Testing & Documentation (v0.3.34)
- Comprehensive OCR tests
- Documentation and examples
- Cost/performance benchmarks

---

## 🔧 Detailed Implementation

### Phase 5.3.1: OCR Infrastructure

**Dependencies:**
```toml
dependencies = [
    # ... existing ...
    "pytesseract>=0.3.10",  # Python wrapper for Tesseract
    "pdf2image>=1.16.0",    # Convert PDF pages to images
    "Pillow>=10.0.0",       # Image processing (already present)
]
```

**OCRProcessor Class:**
```python
class OCRProcessor:
    """Extract text from images using Tesseract OCR."""

    def __init__(self, language: str = "eng"):
        """
        Initialize OCR processor.

        Args:
            language: Tesseract language code (eng, spa, fra, etc.)
        """
        self.language = language
        self._check_tesseract()

    def _check_tesseract(self):
        """Verify Tesseract is installed."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            raise RuntimeError(
                "Tesseract OCR not installed. "
                "Install: apt-get install tesseract-ocr (Linux) "
                "or brew install tesseract (Mac)"
            )

    def extract_text(
        self,
        image: Image.Image,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from image using OCR.

        Args:
            image: PIL Image object
            preprocess: Apply preprocessing (deskew, denoise)

        Returns:
            {
                "text": str,
                "confidence": float (0-100),
                "word_count": int
            }
        """
        import pytesseract

        if preprocess:
            image = self._preprocess_image(image)

        # Extract text with confidence
        data = pytesseract.image_to_data(
            image,
            lang=self.language,
            output_type=pytesseract.Output.DICT
        )

        # Calculate average confidence
        confidences = [c for c in data['conf'] if c != -1]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Extract text
        text = pytesseract.image_to_string(image, lang=self.language)

        return {
            "text": text.strip(),
            "confidence": avg_confidence,
            "word_count": len(text.split())
        }

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        image = image.convert('L')

        # Increase contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        return image

    def is_scanned_page(
        self,
        page_image: Image.Image,
        text_from_pdf: str
    ) -> bool:
        """
        Detect if PDF page is scanned (image-based).

        Args:
            page_image: Page rendered as image
            text_from_pdf: Text extracted directly from PDF

        Returns:
            True if page appears to be scanned
        """
        # If PDF has very little text but page has visual content, likely scanned
        if len(text_from_pdf.strip()) < 10:
            # Try quick OCR to see if there's text
            result = self.extract_text(page_image, preprocess=False)
            return result["word_count"] > 20

        return False
```

**Scanned PDF Detection Logic:**
```python
# In PDFReader._read_with_pymupdf()

async def _read_with_pymupdf(self, page_range: Optional[Tuple[int, int]] = None):
    """Read PDF with PyMuPDF, detecting and processing scanned pages."""

    ocr_processor = None
    if self.enable_ocr:  # NEW parameter
        try:
            ocr_processor = OCRProcessor()
        except RuntimeError:
            # Tesseract not installed, skip OCR
            pass

    for page_num in range(start_page, end_page):
        page = doc[page_num]

        # Extract text normally
        text = page.get_text()

        # Check if page is scanned
        if ocr_processor and len(text.strip()) < 50:
            # Render page as image
            pix = page.get_pixmap(dpi=300)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Check if truly scanned
            if ocr_processor.is_scanned_page(image, text):
                # Extract text with OCR
                ocr_result = ocr_processor.extract_text(image)
                text = ocr_result["text"]

                # Add OCR metadata
                page_data["ocr_used"] = True
                page_data["ocr_confidence"] = ocr_result["confidence"]

        # ... rest of processing ...
```

---

### Phase 5.3.2: Integration with PDFReader

**Update PDFReader.__init__():**
```python
def __init__(
    self,
    file_path: str,
    chunk_size: int = 1000,
    engine: str = "pymupdf",
    pages_per_chunk: int = 3,
    image_handling: str = "skip",
    enable_ocr: bool = False,  # NEW PARAMETER
    ocr_language: str = "eng"  # NEW PARAMETER
):
    """
    Initialize PDF reader.

    Args:
        enable_ocr: Enable OCR for scanned PDFs
        ocr_language: Tesseract language code
    """
    # ... existing init ...
    self.enable_ocr = enable_ocr
    self.ocr_language = ocr_language
```

**Combine OCR with Vision Mode:**

For hybrid PDFs with both text and images:
- Extract text normally
- Extract images with Vision API (if enabled)
- Use OCR for scanned pages
- Combine all sources into coherent content

---

### Phase 5.3.3: Quality & Optimization

**Language Detection:**
```python
def detect_language(self, image: Image.Image) -> str:
    """
    Detect language of text in image.

    Returns:
        Tesseract language code (eng, spa, fra, etc.)
    """
    import pytesseract
    from langdetect import detect

    # Quick OCR in English
    text = pytesseract.image_to_string(image, lang="eng")

    # Detect language
    try:
        lang_code = detect(text)
        # Map to Tesseract codes
        lang_map = {"en": "eng", "es": "spa", "fr": "fra", "de": "deu"}
        return lang_map.get(lang_code, "eng")
    except:
        return "eng"
```

**Quality Assessment:**
```python
def assess_ocr_quality(self, ocr_result: Dict) -> str:
    """
    Assess OCR quality and provide user feedback.

    Returns:
        Quality rating: "excellent", "good", "fair", "poor"
    """
    confidence = ocr_result["confidence"]

    if confidence > 90:
        return "excellent"
    elif confidence > 75:
        return "good"
    elif confidence > 60:
        return "fair"
    else:
        return "poor"
```

---

### Phase 5.3.4: Testing & Documentation

**Tests:**
- `test_ocr_processor.py` (15 tests)
  - OCR text extraction
  - Confidence scoring
  - Scanned page detection
  - Preprocessing effects
  - Language detection
  - Error handling (Tesseract not installed)

- `test_pdf_ocr_integration.py` (10 tests)
  - Scanned PDF reading
  - Hybrid PDF handling
  - OCR + Vision mode combined
  - Performance with large scans

**Documentation:**
- Update README.md with OCR examples
- Add OCR costs and performance notes to COST.md
- Document Tesseract installation instructions

---

## 💰 Cost Analysis

### Computational Costs

**OCR Processing:**
- Speed: ~1-2 seconds per page (300 DPI)
- Memory: ~50MB per page during processing
- No API costs (runs locally)

**Storage:**
- No additional cache size (OCR text replaces non-existent text)

**Performance Impact:**
- 10-page scanned PDF: ~10-20 seconds additional processing
- Acceptable for occasional use, not real-time

---

## ✅ Success Criteria

### Functional Requirements
- ✅ Detect scanned PDF pages accurately
- ✅ Extract text from scanned pages with >75% accuracy
- ✅ Handle hybrid PDFs (mix of text and scanned pages)
- ✅ Provide confidence scores and quality warnings
- ✅ Language detection for multi-lingual documents

### Quality Requirements
- ✅ OCR accuracy >80% on clear scans
- ✅ Processing time <2s per page
- ✅ Graceful fallback if Tesseract not installed
- ✅ All existing tests continue to pass

---

## 🗓️ Implementation Timeline

### Week 1: OCR Infrastructure (5.3.1)
- Days 1-2: Add dependencies, create OCRProcessor
- Days 3-4: Implement scanned page detection
- Day 5: Basic OCR testing

### Week 2: Integration (5.3.2-5.3.3)
- Days 1-2: Integrate with PDFReader
- Days 3-4: Quality improvements and language detection
- Day 5: Performance optimization

### Week 3: Testing & Documentation (5.3.4)
- Days 1-2: Comprehensive testing
- Days 3-4: Documentation updates
- Day 5: Release prep

**Total: 3 weeks**

---

**Last Updated:** January 2026
**Document Version:** 1.0
**Maintained by:** Yiqiao Yin (yiqiao.yin@wyn-associates.com)
