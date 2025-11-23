# WYN360 CLI - Vision Mode Implementation Roadmap

**Status:** ✅ Phase 5.1 - Implementation Complete (Documentation in Progress)
**Priority:** High (Phase 5.1)
**Start Date:** November 2025
**Completion Date:** January 2026

---

## 📋 Executive Summary

This roadmap outlines the implementation of **Vision Mode** - a feature that enables intelligent image processing in Word and PDF documents using Claude's Vision API. This is the highest priority enhancement in Phase 5 of the Document Readers feature set.

### Key Value Proposition

**Current State:** Documents with images show only placeholders like `[Image]` or are completely skipped, losing valuable information from charts, diagrams, and visual content.

**With Vision Mode:** Images are automatically sent to Claude Vision API for intelligent description, extracting insights from:
- 📊 Charts and graphs (data visualizations)
- 📐 Diagrams and flowcharts (process flows, architectures)
- 🖥️ Screenshots (UI mockups, interfaces)
- 📷 Photos and illustrations (visual documentation)

### Business Impact

- **Better comprehension** of visual-heavy documents (reports, presentations, technical docs)
- **Accessibility** for users who can't see images
- **Searchability** - image content becomes text-searchable through summaries
- **Cost transparency** - separate tracking of vision API costs vs. text processing

---

## 🎯 Goals and Non-Goals

### Goals

1. ✅ Extract images from Word (.docx) and PDF documents
2. ✅ Send images to Claude Vision API for intelligent description
3. ✅ Support three image handling modes:
   - `skip` - Ignore images (current default, no API calls)
   - `describe` - Extract alt text/captions only (no API calls)
   - `vision` - Full Vision API processing (requires API calls, costs money)
4. ✅ Track vision API costs separately from text summarization
5. ✅ Provide clear cost warnings to users before processing
6. ✅ Support batch processing for efficiency
7. ✅ Integrate seamlessly with existing chunking/caching system
8. ✅ Maintain backward compatibility (no breaking changes)

### Non-Goals

1. ❌ OCR for scanned PDFs (saved for Phase 5.2)
2. ❌ Image editing or manipulation
3. ❌ Video or animation processing
4. ❌ Chart data extraction (just descriptions)
5. ❌ Local image processing (all processing via Claude Vision API)

---

## 🏗️ Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WYN360 Agent                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  read_word() / read_pdf()                          │     │
│  │  - Check image_handling_mode                       │     │
│  │  - Warn user about costs if vision mode           │     │
│  │  - Track vision tokens separately                 │     │
│  └────────────────┬───────────────────────────────────┘     │
└────────────────────┼──────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼─────────┐      ┌────────▼────────┐
│  WordReader     │      │  PDFReader      │
│  ┌───────────┐  │      │  ┌───────────┐  │
│  │ Extract   │  │      │  │ Extract   │  │
│  │ images    │  │      │  │ images    │  │
│  │ from docx │  │      │  │ from PDF  │  │
│  └─────┬─────┘  │      │  └─────┬─────┘  │
└────────┼────────┘      └────────┼────────┘
         │                        │
         └────────┬───────────────┘
                  │
         ┌────────▼─────────┐
         │ ImageProcessor   │
         │ ┌──────────────┐ │
         │ │ Vision API   │ │
         │ │ Integration  │ │
         │ └──────────────┘ │
         │ ┌──────────────┐ │
         │ │ Image Format │ │
         │ │ Detection    │ │
         │ └──────────────┘ │
         │ ┌──────────────┐ │
         │ │ Type         │ │
         │ │ Detection    │ │
         │ └──────────────┘ │
         └──────────────────┘
                  │
         ┌────────▼─────────┐
         │ Claude Vision    │
         │ API              │
         │ (Sonnet 4.5)     │
         └──────────────────┘
```

### Data Flow

```
User: "Read presentation.docx with vision mode"
  ↓
Agent: check image_handling_mode = "vision"
  ↓
Agent: Warn user about vision API costs
  ↓
WordReader: read document
  ↓
WordReader: extract_images() → List[ImageData]
  ↓
ImageProcessor: describe_images_batch()
  ↓
Claude Vision API: process each image
  ↓
ImageProcessor: return descriptions
  ↓
WordReader: insert descriptions into markdown
  ↓
ChunkSummarizer: summarize chunks (including image descriptions)
  ↓
ChunkCache: cache results
  ↓
Agent: format output, track costs
  ↓
User: receives document with image descriptions
```

---

## 📊 Current Implementation Status

### ✅ Completed (Lines 122-349 in document_readers.py)

**ImageProcessor Class:**
- ✅ Vision API integration (line 157-243)
- ✅ Image format detection (line 272-293)
- ✅ Context-aware prompts (line 295-319)
- ✅ Image type detection (line 321-334)
- ✅ Markdown formatting (line 336-349)
- ✅ Batch processing support (line 245-270)
- ✅ Error handling with fallbacks
- ✅ Token tracking

**Dependencies Added:**
- ✅ `base64` - Image encoding
- ✅ `io` - BytesIO for image handling
- ✅ `PIL/Pillow` - Optional, for format detection (HAS_PIL flag)

**Phase 5.1.1 - WordReader Enhancement:**
- ✅ `_extract_images()` method (lines 1633-1679)
- ✅ `_process_images_with_vision()` method (lines 1681-1720)
- ✅ Updated `read()` to async with vision support (line 1428)
- ✅ 5 new tests added to test_word_reader.py
- ✅ All 336 tests passing

**Phase 5.1.2 - PDFReader Enhancement:**
- ✅ Added `image_handling` parameter to PDFReader.__init__()
- ✅ Updated `read()` to async with image_processor parameter
- ✅ `_extract_images_pymupdf()` method (lines 2137-2177)
- ✅ `_extract_images_pdfplumber()` method (lines 2179-2216)
- ✅ `_process_images_with_vision()` method (lines 2218-2260)
- ✅ Updated `_read_with_pymupdf()` to async with image extraction
- ✅ Updated `_read_with_pdfplumber()` to async with image extraction
- ✅ All 8 PDFReader tests updated to async
- ✅ All 336 tests passing

**Phase 5.1.3 - Agent Integration (v0.3.30):**
- ✅ Added vision token tracking fields to Agent.__init__() (lines 99-102)
- ✅ Added ImageProcessor import to agent.py
- ✅ Created track_vision_processing() method (lines 2931-2942)
- ✅ Updated read_word() to use ImageProcessor when vision mode enabled (lines 2284-2301)
- ✅ Updated read_pdf() with image_handling parameter (line 2421)
- ✅ Updated read_pdf() to use ImageProcessor (lines 2553-2570)
- ✅ Updated get_token_stats() to calculate and return vision costs (lines 3001-3035)
- ✅ Updated /tokens command in cli.py to display vision API stats (lines 274-284)
- ✅ All existing tests continue to pass

**Phase 5.1.4 - Testing (v0.3.30):**
- ✅ Created test_image_processor.py with 23 comprehensive tests
- ✅ Tests cover format detection (PNG, JPEG, GIF, WebP, unknown)
- ✅ Tests cover image type detection (chart, diagram, screenshot, photo, other)
- ✅ Tests cover prompt building with/without context
- ✅ Tests cover markdown formatting for all image types
- ✅ Tests cover Vision API integration (success, error handling, batch processing)
- ✅ All 359 tests passing (336 existing + 23 new)

### 🚧 Remaining Work

1. **Phase 5.1.5 - Documentation** (~50 lines) - IN PROGRESS
   - Update README.md with vision mode examples
   - Update COST.md with vision pricing
   - Update ROADMAP_DOCUMENTS.md with Phase 5.1 completion
   - Add cost calculator examples
   - Update USE_CASES.md
   - Update version numbers to 0.3.30

---

## 🔧 Detailed Implementation Plan

### Phase 5.1.1: WordReader Image Extraction (v0.3.30)

**Goal:** Extract images from Word documents and integrate with vision mode

#### Implementation Steps

**Step 1: Add Image Extraction Method to WordReader**

Location: `wyn360_cli/document_readers.py` (after line 1327, in WordReader class)

```python
def _extract_images(self, doc) -> List[Dict[str, Any]]:
    """
    Extract all images from Word document.

    Returns:
        List of image dicts with {
            "data": bytes,
            "format": "png"|"jpeg"|"gif",
            "context": {"section": "...", "index": N}
        }
    """
    images = []

    # Method 1: Inline shapes (document.inline_shapes)
    for idx, shape in enumerate(doc.inline_shapes):
        try:
            # Get image bytes
            image_bytes = shape._inline.graphic.graphicData.pic.blipFill.blip.embed
            image_part = doc.part.related_parts[image_bytes]
            image_data = image_part.blob

            # Detect format from content type
            content_type = image_part.content_type  # 'image/png', 'image/jpeg', etc.
            image_format = content_type.split('/')[-1] if '/' in content_type else 'png'

            images.append({
                "data": image_data,
                "format": image_format,
                "context": {
                    "doc_type": "word",
                    "index": idx,
                    "shape_type": "inline"
                }
            })
        except Exception as e:
            # Skip images that can't be extracted
            continue

    return images
```

**Step 2: Integrate Vision Processing in _extract_sections()**

Modify `_extract_sections()` to detect images and process them if vision mode enabled:

```python
# In _extract_sections(), after line 1289 (paragraph processing)
# Add image detection:

# Check for images in paragraph
if para.runs:
    for run in para.runs:
        if run._element.xpath('.//w:drawing'):
            # Image found in paragraph
            if current_section:
                current_section["has_images"] = True
```

**Step 3: Add Vision Processing Method**

```python
async def _process_images_with_vision(
    self,
    images: List[Dict[str, Any]],
    image_processor: 'ImageProcessor',
    section_context: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Process images with vision API.

    Args:
        images: List of image data dicts
        image_processor: ImageProcessor instance
        section_context: Context about current section

    Returns:
        List of image description dicts
    """
    if not images:
        return []

    # Add section context to each image
    for img in images:
        img["context"].update(section_context)

    # Batch process images
    descriptions = await image_processor.describe_images_batch(images)

    return descriptions
```

**Step 4: Update read() Method Signature**

```python
async def read(self, image_processor: Optional['ImageProcessor'] = None) -> Dict[str, Any]:
    """
    Read Word file and return structured data.

    Args:
        image_processor: Optional ImageProcessor for vision mode

    Returns:
        {
            "sections": [...],
            "images": [...],  # NEW: list of image descriptions if vision mode
            "vision_tokens_used": 0  # NEW: tokens used for vision API
        }
    """
```

#### Files Modified
- `wyn360_cli/document_readers.py` - WordReader class (~150 new lines)

#### Tests Required
- `test_word_reader.py`:
  - `test_extract_images_from_docx()` - Mock docx with images
  - `test_image_extraction_with_vision_mode()` - Mock ImageProcessor
  - `test_image_extraction_skip_mode()` - Verify images skipped
  - `test_image_extraction_describe_mode()` - Extract alt text only
  - `test_image_context_preserved()` - Verify section context

---

### Phase 5.1.2: PDFReader Image Extraction (v0.3.31)

**Goal:** Extract images from PDF documents

#### Implementation Steps

**Step 1: Add Image Extraction for PyMuPDF**

Location: `wyn360_cli/document_readers.py` (in PDFReader class)

```python
def _extract_images_pymupdf(self, page, page_num: int) -> List[Dict[str, Any]]:
    """
    Extract images from PDF page using PyMuPDF.

    Args:
        page: PyMuPDF page object
        page_num: Page number (1-indexed)

    Returns:
        List of image dicts
    """
    images = []

    try:
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]  # image xref
            base_image = page.parent.extract_image(xref)

            image_data = base_image["image"]
            image_ext = base_image["ext"]  # png, jpeg, etc.

            images.append({
                "data": image_data,
                "format": image_ext,
                "context": {
                    "doc_type": "pdf",
                    "page_number": page_num,
                    "index": img_index
                }
            })
    except Exception as e:
        # Skip if image extraction fails
        pass

    return images
```

**Step 2: Add Image Extraction for pdfplumber**

```python
def _extract_images_pdfplumber(self, page, page_num: int) -> List[Dict[str, Any]]:
    """
    Extract images from PDF page using pdfplumber.

    Note: pdfplumber doesn't have direct image extraction,
    so we'll need to work with page.images metadata
    """
    images = []

    try:
        # pdfplumber provides image objects but not raw data directly
        # We'll need to use page.to_image() and crop
        page_images = page.images

        for idx, img_info in enumerate(page_images):
            # This is a simplified approach
            # Full implementation would require cropping page image
            images.append({
                "data": None,  # Would need cropping logic
                "format": "png",
                "context": {
                    "doc_type": "pdf",
                    "page_number": page_num,
                    "index": idx,
                    "note": "pdfplumber image extraction limited"
                }
            })
    except Exception:
        pass

    return images
```

**Step 3: Update read() Methods**

Modify `_read_with_pymupdf()` and `_read_with_pdfplumber()` to:
- Extract images from each page
- Store images with page data
- Track image count

#### Files Modified
- `wyn360_cli/document_readers.py` - PDFReader class (~200 new lines)

#### Tests Required
- `test_pdf_reader.py`:
  - `test_extract_images_pymupdf()` - Mock pymupdf image extraction
  - `test_extract_images_pdfplumber()` - Mock pdfplumber
  - `test_image_extraction_with_vision()` - End-to-end vision mode
  - `test_image_context_in_pdf()` - Verify page context
  - `test_pdf_without_images()` - Handle PDFs with no images

---

### Phase 5.1.3: Agent Integration (v0.3.32)

**Goal:** Integrate vision mode into agent tools

#### Implementation Steps

**Step 1: Update Agent Initialization**

Location: `wyn360_cli/agent.py` (around line 100-110)

```python
# Add to __init__
self.vision_tokens_used = 0  # Track vision API tokens separately
self.vision_enabled = False  # Can be toggled
```

**Step 2: Update read_word() Method**

Location: `wyn360_cli/agent.py` (around line 2178)

```python
async def read_word(
    self,
    ctx: RunContext[None],
    file_path: str,
    max_tokens: Optional[int] = None,
    use_chunking: bool = True,
    image_handling: Optional[str] = None,
    regenerate_cache: bool = False,
    query: Optional[str] = None
) -> str:
    """..."""

    # Get image_handling mode
    if image_handling is None:
        image_handling = self.image_handling_mode

    # Warn user about vision costs
    if image_handling == "vision":
        # Count estimated cost
        response = "⚠️ **Vision Mode Enabled**\n\n"
        response += "This will use Claude Vision API to process images.\n"
        response += "**Estimated cost:** ~$0.01-0.05 per image\n"
        response += "Do you want to proceed?\n\n"
        # In actual implementation, might want user confirmation

    # Create ImageProcessor if vision mode
    image_processor = None
    if image_handling == "vision":
        from .document_readers import ImageProcessor
        image_processor = ImageProcessor(
            api_key=self.api_key,
            model="claude-3-5-sonnet-20241022"
        )

    # Pass image_processor to reader
    reader = WordReader(
        file_path=str(file_path_obj),
        chunk_size=1000,
        image_handling=image_handling
    )

    # Read with vision processing
    result = await reader.read(image_processor=image_processor)

    # Track vision tokens
    if "vision_tokens_used" in result:
        self.vision_tokens_used += result["vision_tokens_used"]

    # ... rest of method
```

**Step 3: Update read_pdf() Similarly**

**Step 4: Update /tokens Command**

Location: `wyn360_cli/cli.py` (tokens command)

```python
# Add vision tokens to display
if agent.vision_tokens_used > 0:
    console.print(f"Vision API Tokens: {agent.vision_tokens_used:,}")
    # Calculate vision cost (different pricing)
    # Sonnet 4.5 vision: ~$3/MTok input, ~$15/MTok output
```

#### Files Modified
- `wyn360_cli/agent.py` - read_word(), read_pdf() methods (~100 lines)
- `wyn360_cli/cli.py` - /tokens command (~20 lines)

---

### Phase 5.1.4: Testing (v0.3.33)

**Goal:** Comprehensive test coverage

#### Test Files to Create/Update

**1. test_image_processor.py (NEW)**

20 tests covering:
- Image format detection
- Vision API calls (mocked)
- Error handling
- Batch processing
- Context prompt building
- Image type detection
- Markdown formatting
- Cost tracking

**2. test_word_reader.py (UPDATE)**

Add 5 tests:
- Image extraction from docx
- Vision mode integration
- Skip/describe/vision modes
- Image context preservation
- Error handling for corrupted images

**3. test_pdf_reader.py (UPDATE)**

Add 5 tests:
- Image extraction from PDF (pymupdf)
- Image extraction from PDF (pdfplumber)
- Vision mode end-to-end
- Page context in images
- PDFs without images

**4. Integration Tests (NEW)**

Test complete workflows:
- Read Word doc with vision mode
- Read PDF with vision mode
- Cost tracking accuracy
- Cache with vision descriptions
- Query retrieval with image content

#### Total Test Count
- Current: 120 tests
- New: ~30 tests
- **Total: ~150 tests**

---

### Phase 5.1.5: Documentation (v0.3.34)

**Goal:** Complete user-facing documentation

#### Documents to Update

**1. README.md**

Add section: **Vision Mode for Images**

```markdown
### 🖼️ Vision Mode for Images

WYN360 can intelligently describe images in Word and PDF documents using Claude Vision API.

#### Usage

wyn360 read presentation.docx --image-mode vision


#### Image Handling Modes

- **skip** (default): Ignore images entirely
- **describe**: Extract alt text and captions only (no API calls)
- **vision**: Use Claude Vision API for intelligent descriptions (costs apply)

#### Cost Considerations

Vision mode uses Claude's Vision API with the following pricing:
- ~$0.01-0.05 per image
- Separate from text processing costs
- Track costs with `/tokens` command

#### Example Output

📊 **[Image 1]:** A bar chart showing quarterly revenue growth from Q1 to Q4,
with Q4 showing the highest revenue at approximately $2.5M.

📐 **[Image 2]:** System architecture diagram depicting three layers: frontend
(React), API layer (FastAPI), and database (PostgreSQL).
```

**2. ROADMAP_DOCUMENTS.md**

Update Phase 5.1 status:
- Mark all tasks as completed
- Add "IMPLEMENTED" badges
- Update version history table

**3. USE_CASES.md**

Add new use case:

```markdown
### Use Case 18: Analyzing Presentation with Charts

**Scenario:** User needs to understand a PowerPoint presentation converted to Word with multiple charts.

**Commands:**
wyn360 read quarterly_report.docx --image-mode vision

**Output:** Full document summary with intelligent descriptions of all charts, graphs, and diagrams.

**Value:** Extract insights from visual data without manually describing each chart.
```

**4. COST.md (NEW or UPDATE)**

Create cost guide:

```markdown
### Vision API Costs

#### Pricing
- Input tokens (image + text): $3.00 per million tokens
- Output tokens (descriptions): $15.00 per million tokens

#### Typical Costs
- Simple chart: ~$0.01 (300 input tokens, 100 output tokens)
- Complex diagram: ~$0.03 (500 input tokens, 200 output tokens)
- Photo: ~$0.02 (400 input tokens, 150 output tokens)

#### Example: 20-Page Report
- 10 images average
- Total cost: ~$0.10-0.30
- Plus text summarization: ~$0.05
- **Total: ~$0.15-0.35**

#### Cost Control
- Use `skip` mode for documents without important images
- Use `describe` mode for simple images with alt text
- Reserve `vision` mode for critical visual content
```

---

## 💰 Cost Analysis

### Vision API Pricing (Claude Sonnet 4.5)

| Component | Price per MTok | Typical Usage | Cost per Image |
|-----------|---------------|---------------|----------------|
| Input (image + text) | $3.00 | 300-500 tokens | $0.0009-0.0015 |
| Output (description) | $15.00 | 100-200 tokens | $0.0015-0.0030 |
| **Total per image** | - | - | **$0.01-0.05** |

### Example Scenarios

**Scenario 1: Research Paper (15 pages, 5 diagrams)**
- Text summarization: ~$0.02 (Haiku)
- Vision processing: ~$0.05 (5 diagrams)
- **Total: ~$0.07**

**Scenario 2: Financial Report (50 pages, 20 charts)**
- Text summarization: ~$0.08 (Haiku)
- Vision processing: ~$0.20-0.40 (20 charts)
- **Total: ~$0.28-0.48**

**Scenario 3: Presentation (30 slides, 30 images)**
- Text summarization: ~$0.05 (Haiku)
- Vision processing: ~$0.30-0.60 (30 images)
- **Total: ~$0.35-0.65**

### Cost Mitigation Strategies

1. **Smart Defaults**: Default to `skip` mode, require explicit `--vision` flag
2. **User Warnings**: Show estimated cost before processing
3. **Batch Limits**: Limit to 50 images per document by default
4. **Caching**: Cache vision results for 1 hour (same as text)
5. **Selective Processing**: Allow users to specify image indices to process

---

## ✅ Success Criteria

### Functional Requirements

- ✅ Extract images from Word documents with 95%+ success rate
- ✅ Extract images from PDFs (PyMuPDF) with 90%+ success rate
- ✅ Vision API calls return descriptions within 3 seconds per image
- ✅ Support skip/describe/vision modes seamlessly
- ✅ Zero breaking changes to existing API
- ✅ All existing tests continue to pass
- ✅ New features have 90%+ test coverage

### Quality Requirements

- ✅ Image descriptions are accurate and concise (100-300 tokens)
- ✅ Cost tracking is accurate to within 1%
- ✅ Error handling gracefully handles corrupted images
- ✅ Performance: process 10-image document in <30 seconds
- ✅ Memory: handle documents with 50+ images without OOM

### Documentation Requirements

- ✅ README.md updated with vision mode examples
- ✅ Cost guide with clear pricing examples
- ✅ USE_CASES.md with vision mode scenarios
- ✅ All slash commands documented
- ✅ API reference updated

---

## 🗓️ Implementation Timeline

### Sprint 1: Core Image Extraction (Week 1)
- **Days 1-2:** WordReader image extraction
- **Days 3-4:** PDFReader image extraction (PyMuPDF)
- **Day 5:** Testing image extraction

**Deliverable:** Images can be extracted from both Word and PDF

### Sprint 2: Vision API Integration (Week 2)
- **Days 1-2:** Agent integration (read_word, read_pdf)
- **Days 3-4:** Cost tracking and warnings
- **Day 5:** Integration testing

**Deliverable:** Vision mode working end-to-end

### Sprint 3: Testing & Documentation (Week 3)
- **Days 1-2:** Comprehensive unit tests
- **Days 3-4:** Documentation updates
- **Day 5:** Code review and polish

**Deliverable:** Production-ready vision mode

### Total Estimate: 3 weeks (15 development days)

---

## 🧪 Testing Strategy

### Unit Tests (~30 new tests)

**ImageProcessor (20 tests):**
- Format detection (4 tests)
- Vision API calls (4 tests)
- Error handling (4 tests)
- Batch processing (3 tests)
- Type detection (3 tests)
- Markdown formatting (2 tests)

**WordReader (5 tests):**
- Image extraction
- Vision mode integration
- Skip/describe/vision modes
- Context preservation
- Error handling

**PDFReader (5 tests):**
- PyMuPDF image extraction
- pdfplumber image extraction
- Vision mode end-to-end
- Page context
- No images handling

### Integration Tests (~5 tests)

- End-to-end Word document with vision
- End-to-end PDF with vision
- Cost tracking validation
- Cache with vision results
- Query retrieval with image content

### Performance Tests

- Large document (50+ images) processing time
- Memory usage with many images
- Concurrent vision API calls
- Cache hit rate with vision mode

---

## 🔒 Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Vision API rate limits | Medium | High | Implement retry logic, batch throttling |
| Large image handling | Medium | Medium | Resize images before sending, set size limits |
| Cost overruns | High | High | Clear warnings, user confirmation, batch limits |
| python-docx image extraction failures | Medium | Medium | Graceful fallbacks, error handling |
| PyMuPDF vs pdfplumber incompatibility | Low | Medium | Test both engines, document limitations |

### User Experience Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Unexpected high costs | High | High | Prominent cost warnings, require explicit --vision flag |
| Slow processing | Medium | Medium | Progress indicators, async processing |
| Inaccurate descriptions | Low | Medium | Include confidence scores, allow user feedback |
| Breaking changes | Low | High | Comprehensive backward compatibility testing |

---

## 📚 References

### API Documentation
- [Claude Vision API](https://docs.anthropic.com/en/docs/vision)
- [python-docx](https://python-docx.readthedocs.io/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [pdfplumber](https://github.com/jsvine/pdfplumber)

### Related Files
- `wyn360_cli/document_readers.py` - Core implementation
- `wyn360_cli/agent.py` - Agent integration
- `docs/ROADMAP_DOCUMENTS.md` - Parent roadmap
- `docs/USE_CASES.md` - Use cases

---

## 🎯 Next Steps

### Immediate Actions (To Begin Implementation)

1. ✅ Create this roadmap document
2. ⏳ User review and approval of plan
3. ⏳ Begin Sprint 1: WordReader image extraction
4. ⏳ Daily standup updates on progress
5. ⏳ Continuous testing as features are added

### Decision Points

**Before starting implementation, confirm:**
- ✅ Cost structure acceptable to users
- ✅ Vision API access available
- ✅ Three-week timeline acceptable
- ✅ Approach aligns with project goals

---

## 📞 Feedback & Questions

**Questions? Concerns? Suggestions?**

This is a comprehensive plan designed to implement vision mode without breaking existing functionality. The implementation is broken into logical phases, each with clear deliverables and test requirements.

**Key Design Decisions:**
1. **Default to skip mode** - Avoid surprise costs
2. **Separate cost tracking** - Transparency on vision vs text costs
3. **Three image modes** - Flexibility for different use cases
4. **Batch processing** - Efficiency for multi-image documents
5. **Cache vision results** - Avoid re-processing same images

---

**Last Updated:** November 2025
**Document Version:** 1.0
**Maintained by:** Yiqiao Yin (yiqiao.yin@wyn-associates.com)
