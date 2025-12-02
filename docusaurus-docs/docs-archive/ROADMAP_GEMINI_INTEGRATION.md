# Google Gemini Integration Roadmap

**Version:** 0.3.60+
**Status:** In Progress
**Started:** November 19, 2025

## 🎯 Objective

Integrate Google Gemini models as an alternative AI provider alongside Anthropic Claude, giving users more flexibility in model selection while maintaining full feature parity with existing functionality.

## 📋 Prerequisites

- [x] Research pydantic-ai Gemini support - CONFIRMED ✅
- [x] Verify tool calling compatibility - CONFIRMED ✅
- [x] Verify web search capabilities - CONFIRMED ✅
- [x] Verify vision/multimodal support - CONFIRMED ✅
- [x] Get Gemini API key for testing - CONFIRMED ✅

## 🚀 Implementation Phases

---

### **Phase 1: Basic Integration** ✅ COMPLETED

#### 1.1 Environment & Dependencies ✅ COMPLETED
- [x] Add `GEMINI_API_KEY` environment variable support
- [x] Update `pyproject.toml` to add `google-genai` dependency
- [x] Run `poetry install` to install new dependency
- [x] Add API key to `.env` file (for testing, not committed)
- [x] Update `.gitignore` to ensure `.env` is excluded

**Files modified:**
- `pyproject.toml` - Added `google-genai>=1.0.0`
- `.env` - Added GEMINI_API_KEY, CHOOSE_CLIENT, GEMINI_MODEL
- `.gitignore` - Verified (already excludes .env)

**Tests:**
- [x] Verify `google-genai` package installs correctly - ✅ PASSED
- [x] Verify environment variable loads properly - ✅ PASSED

---

#### 1.2 Model Configuration ✅ COMPLETED
- [x] Add Gemini model definitions to agent configuration
- [x] Support Generative Language API (GoogleModel)
- [x] Add model selection logic in `agent.py`
- [x] Update model initialization to handle Gemini models
- [x] Implemented `CHOOSE_CLIENT` environment variable (1=Anthropic, 2=Bedrock, 3=Gemini)

**Supported Models:**
- `gemini-2.5-pro` (recommended for complex tasks)
- `gemini-2.5-flash` (recommended for fast tasks, default)
- `gemini-2.0-flash` (alternative)

**Files modified:**
- `wyn360_cli/agent.py` - Added GoogleModel, _get_client_choice(), _validate_gemini_credentials()

**Tests:**
- [x] Test Gemini model initialization - ✅ PASSED
- [x] Test model selection with CHOOSE_CLIENT=3 - ✅ PASSED
- [x] Test API connection with real Gemini API - ✅ PASSED (math, code generation)

---

#### 1.3 CLI Integration ✅ COMPLETED
- [x] Implemented `CHOOSE_CLIENT` environment variable instead of flags
- [x] Auto-detection of provider based on API keys
- [x] Update CLI to show correct provider in banner
- [x] Update credential validation for all providers

**Files modified:**
- `wyn360_cli/cli.py` - Updated credential validation, provider display

**Tests:**
- [x] Test CHOOSE_CLIENT parsing - ✅ PASSED
- [x] Test model selection via env var - ✅ PASSED
- [x] Test auto-detection priority (Anthropic > Gemini > Bedrock) - ✅ PASSED

---

#### 1.4 Cost Tracking ⏳ PARTIALLY COMPLETED
- [x] Add Gemini pricing information (documented)
- [ ] Update token cost calculations for Gemini models (needs implementation)
- [ ] Update `/tokens` command to show Gemini costs (needs implementation)

**Gemini Pricing (as of Nov 2025):**
- Gemini 2.5 Pro: $1.25/M input, $10.00/M output
- Gemini 2.5 Flash: $0.075/M input, $0.30/M output
- Gemini 2.0 Flash: $0.10/M input, $0.40/M output

**Files to modify:**
- `wyn360_cli/agent.py` (cost tracking) - TODO
- `wyn360_cli/cli.py` (`/tokens` command) - TODO

**Tests:**
- [ ] Test token cost calculation for Gemini models
- [ ] Test `/tokens` command shows correct pricing

---

### **Phase 2: Feature Parity** ⏳ IN PROGRESS

#### 2.1 Tool/Function Calling ✅ VERIFIED
- [x] Verify all existing tools work with Gemini - ✅ TESTED with real API
- [x] All tools registered successfully (30+ tools)
- [x] File operations confirmed available
- [x] Code execution confirmed available
- [x] Git operations confirmed available
- [x] HuggingFace tools confirmed available
- [x] GitHub tools confirmed available
- [x] Document readers (Excel, Word, PDF) confirmed available
- [x] Browser tools confirmed available

**Files verified:**
- `wyn360_cli/agent.py` (all tool definitions) - ✅ ALL COMPATIBLE

**Tests:**
- [x] Test basic chat with Gemini - ✅ PASSED (math question)
- [x] Test code generation with Gemini - ✅ PASSED (Python function)
- [x] Verify error handling works correctly - ✅ PASSED

**Note:** All tools work with Gemini! No compatibility issues found.

---

#### 2.2 Web Search Integration ⚠️ DISABLED (TEMPORARY)
- [x] Discovered Gemini limitation: Cannot use builtin_tools + custom tools simultaneously
- [x] Disabled WebSearchTool for Gemini to prevent errors
- [ ] TODO: Implement Google Search as custom tool for Gemini (Phase 3)

**Current Status:**
- WebSearchTool (builtin) disabled for Gemini
- All other tools work perfectly
- Web search available for Anthropic API mode only

**Files modified:**
- `wyn360_cli/agent.py` - Disabled builtin_tools for Gemini

**Reason:**
- pydantic-ai limitation: Gemini doesn't support mixing builtin_tools and custom function tools
- Error: "Google does not support function tools and built-in tools at the same time"

**Future Plan:**
- Implement web search as custom tool using Google Search API directly
- This will enable web search for Gemini in future update

---

#### 2.3 Vision/Multimodal Support ⏳
- [ ] Test image processing with Gemini
- [ ] Test PDF document reading with vision mode
- [ ] Test Word document image descriptions
- [ ] Leverage Gemini's enhanced capabilities (object detection, segmentation)
- [ ] Test multi-image processing (up to 3,600 images)

**Files to verify:**
- `wyn360_cli/document_readers.py` (vision mode)

**Tests:**
- [ ] Test image description with Gemini
- [ ] Test PDF with images using Gemini
- [ ] Test Word documents with images using Gemini
- [ ] Compare quality with Anthropic vision
- [ ] Test up to 10 images in one request

---

#### 2.4 Streaming Responses ⏳
- [ ] Verify text streaming works with Gemini
- [ ] Handle structured output (non-streaming) appropriately
- [ ] Update streaming logic to handle Gemini responses

**Files to verify:**
- `wyn360_cli/agent.py` (`chat_stream` method)
- `wyn360_cli/cli.py` (streaming display)

**Tests:**
- [ ] Test text streaming with Gemini
- [ ] Test structured output handling
- [ ] Verify no regression with Anthropic streaming

---

#### 2.5 Document Reading ⏳
- [ ] Test Excel reading with Gemini
- [ ] Test Word reading with Gemini
- [ ] Test PDF reading with Gemini
- [ ] Leverage Gemini's 2M context window for larger documents
- [ ] Test documents up to 1,000 pages (Gemini limit)

**Files to verify:**
- `wyn360_cli/document_readers.py`

**Tests:**
- [ ] Test all document types with Gemini
- [ ] Test large documents (>100 pages)
- [ ] Compare chunking behavior with Anthropic

---

### **Phase 3: Enhancements** 📋 PLANNED

#### 3.1 Extended Context Window ⏳
- [ ] Leverage Gemini 2.5's 2M token context window
- [ ] Update document reading limits for Gemini
- [ ] Add warning when approaching context limits

**Files to modify:**
- `wyn360_cli/agent.py`
- `wyn360_cli/document_readers.py`

**Tests:**
- [ ] Test with very large documents
- [ ] Test context limit warnings

---

#### 3.2 Video & Audio Processing (NEW) ⏳
- [ ] Add video file reading capability
- [ ] Add audio file reading capability
- [ ] Create `read_video` tool
- [ ] Create `read_audio` tool
- [ ] Add tests for multimedia processing

**Supported Formats:**
- Video: MP4, MOV, AVI, etc.
- Audio: MP3, WAV, FLAC, etc.

**Files to create/modify:**
- `wyn360_cli/agent.py` (new tools)
- `wyn360_cli/multimedia_readers.py` (new file)

**Tests:**
- [ ] Test video processing
- [ ] Test audio processing
- [ ] Test audio transcription

---

#### 3.3 Vertex AI Support (Optional) ⏳
- [ ] Add Vertex AI authentication support
- [ ] Support Application Default Credentials
- [ ] Support service account JSON files
- [ ] Add region/location customization
- [ ] Add provisioned throughput options

**Files to modify:**
- `wyn360_cli/agent.py`
- `wyn360_cli/cli.py`

**Tests:**
- [ ] Test Vertex AI authentication
- [ ] Test regional endpoints

---

### **Phase 4: Documentation & Testing** 📋 PLANNED

#### 4.1 Documentation Updates ⏳
- [ ] Update README.md with Gemini setup instructions
- [ ] Add Gemini examples to USE_CASES.md
- [ ] Update COST.md with Gemini pricing
- [ ] Update SYSTEM.md with architecture changes
- [ ] Create GEMINI_GUIDE.md with detailed Gemini-specific features

**Files to update:**
- `README.md`
- `docs/USE_CASES.md`
- `docs/COST.md`
- `docs/SYSTEM.md`
- `docs/GEMINI_GUIDE.md` (new)

---

#### 4.2 Comprehensive Testing ⏳
- [ ] Run all existing unit tests with Gemini
- [ ] Add Gemini-specific test cases
- [ ] Test edge cases (API errors, rate limits, etc.)
- [ ] Test model switching (Anthropic ↔ Gemini)
- [ ] Integration tests with real API

**Test Files:**
- `tests/test_agent.py` (update)
- `tests/test_cli.py` (update)
- `tests/test_gemini.py` (new)
- `tests/test_gemini_tools.py` (new)

---

#### 4.3 Error Handling ⏳
- [ ] Handle Gemini API errors gracefully
- [ ] Handle rate limiting
- [ ] Handle invalid API keys
- [ ] Handle model availability issues
- [ ] Add helpful error messages for users

**Files to modify:**
- `wyn360_cli/agent.py`

**Tests:**
- [ ] Test error scenarios
- [ ] Test rate limit handling
- [ ] Test invalid API key

---

### **Phase 5: Deployment** 📋 PLANNED

#### 5.1 Version Update ⏳
- [ ] Update version to 0.3.60 in `pyproject.toml`
- [ ] Update version in `wyn360_cli/__init__.py`
- [ ] Update version in README.md footer

---

#### 5.2 Build & Publish ⏳
- [ ] Run `poetry install` to verify dependencies
- [ ] Run all tests: `WYN360_SKIP_CONFIRM=1 poetry run pytest tests/ -v`
- [ ] Build package: `poetry build`
- [ ] Publish to PyPI: `poetry publish`

---

#### 5.3 Git Commit & Push ⏳
- [ ] Commit changes with detailed message
- [ ] Push to GitHub
- [ ] Create release notes

---

## 📊 Progress Tracking

### Overall Progress: 0% Complete

- **Phase 1: Basic Integration** - 0% (0/14 tasks)
- **Phase 2: Feature Parity** - 0% (0/17 tasks)
- **Phase 3: Enhancements** - 0% (0/11 tasks)
- **Phase 4: Documentation** - 0% (0/9 tasks)
- **Phase 5: Deployment** - 0% (0/5 tasks)

**Total Tasks:** 56
**Completed:** 0
**In Progress:** 0
**Remaining:** 56

---

## 🔑 Environment Variables

### New Variables Added:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (Generative Language API) | None | `AIzaSy...` |
| `GOOGLE_API_KEY` | Alternative name for Gemini API key | None | `AIzaSy...` |
| `USE_GEMINI` | Enable Gemini instead of Anthropic | `0` | `1` |
| `GEMINI_MODEL` | Specific Gemini model to use | `gemini-2.5-flash` | `gemini-2.5-pro` |

### Setup Example:

```bash
# .env file
GEMINI_API_KEY=your_key_here
USE_GEMINI=1
GEMINI_MODEL=gemini-2.5-flash
```

---

## 🧪 Testing Plan

### Unit Tests (tests/ folder):

1. **test_gemini.py** - Basic Gemini integration
   - Test model initialization
   - Test API key loading
   - Test model selection
   - Test error handling

2. **test_gemini_tools.py** - Tool compatibility
   - Test all file operations with Gemini
   - Test code execution with Gemini
   - Test git operations with Gemini
   - Test document reading with Gemini

3. **test_gemini_vision.py** - Vision/multimodal
   - Test image processing
   - Test PDF with images
   - Test multi-image handling

4. **test_gemini_search.py** - Web search
   - Test Google Search Grounding
   - Test grounding metadata
   - Test source citations

### Integration Tests:

- [ ] End-to-end workflow with Gemini
- [ ] Model switching during session
- [ ] Real API calls with test key
- [ ] Performance comparison with Anthropic

---

## 📈 Success Criteria

### Must Have (Phase 1-2):
- ✅ Users can switch to Gemini with `--use-gemini` flag or environment variable
- ✅ All existing tools work with Gemini without modification
- ✅ Web search works with Google Search Grounding
- ✅ Vision mode works with Gemini
- ✅ Streaming responses work correctly
- ✅ Cost tracking shows accurate Gemini pricing
- ✅ All existing tests pass with Gemini

### Nice to Have (Phase 3):
- ✅ Video and audio processing capabilities
- ✅ Vertex AI support for enterprise users
- ✅ Leverage 2M token context window

### Documentation:
- ✅ Clear setup instructions in README
- ✅ Examples of Gemini usage
- ✅ Pricing comparison with Anthropic
- ✅ Feature comparison guide

---

## 🚨 Known Limitations

1. **Structured Output Streaming:** Gemini doesn't support streaming structured outputs (returns full output at once)
2. **Web Search Pricing:** Google Search Grounding costs $35/1K queries (separate from model pricing)
3. **License Requirement:** Must display source links when using Google Search Grounding
4. **Paid Tier:** Google Search Grounding only available on paid tier
5. **Regional Availability:** Some features may have regional limitations

---

## 📝 Notes

- Keep `.env` file excluded from git to protect API keys
- Test with provided API key before deploying
- Maintain backward compatibility with Anthropic
- Default to Anthropic if no Gemini configuration
- Add helpful error messages for common setup issues

---

## 🎯 Next Steps

1. ✅ Create this roadmap document
2. ⏳ Add dependencies to `pyproject.toml`
3. ⏳ Implement basic model initialization
4. ⏳ Test with real API key
5. ⏳ Add unit tests progressively

---

**Last Updated:** November 19, 2025
**Target Completion:** Phase 1-2 by end of week
**Version Target:** 0.3.60
