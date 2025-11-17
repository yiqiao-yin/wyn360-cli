# WYN360-CLI Browser Use Roadmap

## Overview

This roadmap outlines the implementation of direct website fetching and DOM extraction capabilities for WYN360-CLI. This addresses the limitation where WebSearchTool searches for keywords instead of directly fetching specific URLs provided by users.

**Problem Statement:**
When users provide a specific URL like `https://github.com/user/repo`, the current WebSearchTool searches for keywords and returns top 5 search results, which may not include the exact URL requested.

**Solution:**
Implement direct URL fetching using crawl4ai (LLM-optimized web crawler) with smart caching and content management.

---

## Technical Architecture

### Core Technologies

1. **crawl4ai** - LLM-focused web crawler
   - Built on Playwright for modern browser automation
   - Automatic HTML → Markdown conversion
   - Async architecture for performance
   - Handles JavaScript-heavy sites

2. **Storage Strategy**
   - In-memory: Agent conversation context
   - TTL Cache: ~/.wyn360/cache/fetched_sites/
   - Persistent: User-controlled long-term storage

3. **Content Management**
   - Smart truncation with configurable max tokens
   - Gzip compression for cached files
   - Automatic cleanup with TTL (30 minutes default)

---

## Implementation Phases

### Phase 1: MVP - Basic Website Fetching (v0.3.24)

**Goal:** Add direct URL fetching capability with in-memory storage

#### Tasks:
- [x] Research browser automation solutions
- [x] Create ROADMAP_BROWSERUSE.md
- [x] Add crawl4ai dependency to pyproject.toml
- [x] Implement `fetch_website(url)` tool in agent.py
- [x] Add URL detection logic in system prompt
- [x] Implement smart content truncation
- [x] Store fetched content in agent context (in-memory)
- [x] Update documentation (README.md, SYSTEM.md, USE_CASES.md)
- [x] Add error handling for failed fetches
- [x] Test with various URL types (GitHub, docs, blogs)

#### Features:
```python
@tool
async def fetch_website(url: str) -> str:
    """
    Fetch and extract content from a specific URL.

    Args:
        url: Direct URL to fetch (e.g., https://github.com/user/repo)

    Returns:
        Markdown-formatted content from the website (truncated if needed)
    """
```

#### System Prompt Logic:
```
When user provides direct URL:
  - "Read https://example.com" → fetch_website()
  - "What's on github.com/user/repo" → fetch_website()

When user asks general question:
  - "Find ML repos" → WebSearchTool
  - "What's the weather?" → WebSearchTool
```

#### Configuration:
```yaml
# ~/.wyn360/config.yaml
browser_use:
  max_tokens: 50000  # Max tokens per fetched site (configurable)
  truncate_strategy: "smart"  # smart, head, tail
```

**Version:** v0.3.24
**Status:** In Progress
**ETA:** Current session

---

### Phase 2: TTL-Based Caching (v0.3.25)

**Goal:** Add persistent caching with automatic cleanup

#### Tasks:
- [x] Create cache directory structure (~/.wyn360/cache/fetched_sites/)
- [x] Implement TTL-based cache system
- [x] Add cache key generation (URL hash)
- [x] Store cached content as gzipped markdown
- [x] Implement automatic cleanup on cache read
- [x] Add cache statistics tracking
- [ ] Implement cache warming (prefetch common URLs) - FUTURE
- [ ] Add cache hit/miss metrics - FUTURE (basic tracking exists)
- [x] Update config with cache settings

#### Features:
```python
class WebsiteCache:
    """TTL-based cache for fetched websites"""

    def __init__(self, cache_dir: Path, ttl: int = 1800):
        self.cache_dir = cache_dir
        self.ttl = ttl  # 30 minutes default

    async def get(self, url: str) -> Optional[str]:
        """Get cached content if not expired"""

    async def set(self, url: str, content: str):
        """Cache content with TTL"""

    async def cleanup_expired(self):
        """Remove expired cache entries"""
```

#### Configuration:
```yaml
# ~/.wyn360/config.yaml
browser_use:
  cache:
    enabled: true
    ttl: 1800  # 30 minutes (configurable)
    max_size_mb: 100  # Max total cache size
    auto_cleanup: true
```

#### Cache File Format:
```
~/.wyn360/cache/fetched_sites/
  ├── a3f2c1b9.md.gz  # Gzipped markdown (URL hash)
  ├── d8e4b2a1.md.gz
  └── cache_index.json  # Metadata (URL, timestamp, size)
```

**Version:** v0.3.24 (completed in same release as Phase 1)
**Status:** ✅ Complete (except 2 optional future enhancements)
**Completed:** Current session

---

### Phase 3: User-Controlled Storage (v0.3.26)

**Goal:** Give users control over cache persistence and management

#### Tasks:
- [ ] Implement user prompt for cache preferences - FUTURE
- [x] Add persistent storage option (cache persists with TTL)
- [ ] Create `/clear-cache` CLI command - FUTURE (agent tool exists)
- [ ] Create `/show-cache` CLI command - FUTURE (agent tool exists)
- [ ] Add cache preference persistence - FUTURE
- [x] Implement selective cache clearing (via agent tool)
- [ ] Add cache export feature - FUTURE
- [x] Create cache viewer tool (show_cache_stats agent tool)
- [x] Implement agent tools: show_cache_stats(), clear_website_cache()
- [ ] Update CLI with slash commands - FUTURE

#### Features:

**User Prompts:**
```
After fetching site:
"Would you like me to cache this content?
- Yes → Keep for 30 minutes
- No → Discard after conversation
- Always → Keep until manually cleared
- Never → Don't ask again for this session"
```

**CLI Commands:**
```bash
# Show cache statistics
wyn360 cache stats

# Clear all cache
wyn360 cache clear

# Clear specific URL
wyn360 cache clear --url https://example.com

# List cached sites
wyn360 cache list

# Export cached content
wyn360 cache export --output cache_backup.tar.gz
```

**Agent Tools:**
```python
@tool
def clear_cache(url: Optional[str] = None):
    """Clear cached website content"""

@tool
def show_cache_stats() -> Dict[str, Any]:
    """Show cache statistics and cached URLs"""
```

#### Configuration:
```yaml
# ~/.wyn360/config.yaml
browser_use:
  cache:
    user_control: true
    ask_before_cache: true
    default_action: "temp"  # temp, persist, never
    persistent_urls:
      - "https://docs.python.org/*"  # Always cache docs
      - "https://github.com/*/README.md"
```

**Version:** v0.3.24 (core features completed)
**Status:** ⚠️ Partially Complete
**Completed:** Core agent tools (show_cache_stats, clear_website_cache) implemented
**Remaining:** CLI slash commands, user prompts, cache export (future enhancements)

---

### Phase 4: Authenticated Browsing (v0.3.40)

**Goal:** Enable automated login to websites with secure credential storage

#### Tasks:
- [x] Phase 4.1: Implement secure credential storage
  - [x] Create CredentialManager with AES-256-GCM encryption
  - [x] Implement encrypted vault storage (~/.wyn360/credentials/)
  - [x] Add audit logging (no sensitive data)
  - [x] Write unit tests for credential management (21/21 passing)
  - [x] Set strict file permissions (0600)

- [x] Phase 4.2: Implement browser authentication
  - [x] Phase 4.2.1: SessionManager for session cookies
    - [x] Create SessionManager class with TTL-based expiration
    - [x] Implement session save/load/clear operations
    - [x] Add session validation and cleanup
    - [x] Write unit tests (16/16 passing)
  - [x] Phase 4.2.2: BrowserAuth for automated login
    - [x] Create BrowserAuth class using Playwright
    - [x] Implement form detection (username, password, submit)
    - [x] Add CAPTCHA detection
    - [x] Add 2FA detection
    - [x] Implement login flow with error handling
    - [x] Write unit tests (11/11 passing)
  - [x] Phase 4.2.3: Agent integration
    - [x] Add login_to_website tool to agent
    - [x] Integrate CredentialManager, SessionManager, BrowserAuth
    - [x] Update system prompt with authentication guidelines
  - [x] Phase 4.2.4: Configuration and documentation
    - [x] Update .gitignore (.wyn360/ directory)
    - [x] Update .env.example with credential format
  - [x] Phase 4.2.5: Documentation
    - [x] Update ROADMAP_BROWSERUSE.md
  - [x] Phase 4.2.6: Testing
    - [x] Run all unit tests (27/27 passing)
  - [x] Phase 4.2.7: Version release
    - [x] Commit and document changes for v0.3.40

#### Features:

**CredentialManager:**
```python
class CredentialManager:
    """Securely manage login credentials with AES-256-GCM encryption"""

    def save_credential(self, domain: str, username: str, password: str) -> bool:
        """Encrypt and save credentials"""

    def get_credential(self, domain: str) -> Optional[Dict[str, str]]:
        """Decrypt and retrieve credentials"""

    def list_stored_sites(self) -> List[Dict[str, str]]:
        """List sites with stored credentials"""

    def delete_credential(self, domain: str) -> bool:
        """Remove stored credentials"""
```

**SessionManager:**
```python
class SessionManager:
    """Manage authenticated sessions and cookies per website"""

    def save_session(self, domain: str, cookies: List[Dict], ttl: int = 1800):
        """Save session cookies with TTL (default: 30 minutes)"""

    def get_session(self, domain: str) -> Optional[Dict]:
        """Retrieve active session if not expired"""

    def is_session_valid(self, domain: str) -> bool:
        """Check if valid session exists"""

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
```

**BrowserAuth:**
```python
class BrowserAuth:
    """Automated browser authentication using Playwright"""

    async def login(self, url: str, username: str, password: str) -> Dict:
        """
        Attempt to login to a website
        Returns: {success, message, cookies, requires_2fa, has_captcha}
        """

    async def verify_session(self, url: str, cookies: List[Dict]) -> bool:
        """Verify if session cookies are still valid"""

    async def fetch_authenticated_content(self, url: str, cookies: List[Dict]) -> str:
        """Fetch content from authenticated page"""
```

**Agent Tool:**
```python
@tool
async def login_to_website(
    url: str,
    username: str,
    password: str,
    save_credentials: bool = True
) -> str:
    """
    Login to a website using browser automation.

    - Detects login forms automatically
    - Handles CAPTCHA detection (notifies user)
    - Handles 2FA detection (notifies user)
    - Saves session cookies (30 min TTL)
    - Optionally encrypts and saves credentials
    """
```

#### Security Features:
- **Encryption**: AES-256-GCM for credential storage
- **Key Management**: Per-user encryption key from system entropy
- **File Permissions**: 0600 (user read/write only)
- **Session TTL**: 30-minute default (configurable)
- **Audit Logging**: Access tracking without sensitive data
- **No Plain Text**: Credentials only decrypted when needed

#### Storage Structure:
```
~/.wyn360/
  ├── credentials/
  │   ├── .keyfile          # Encryption key (0600)
  │   └── vault.enc         # Encrypted credentials
  ├── sessions/
  │   ├── example_com.session.json
  │   └── github_com.session.json
  └── logs/
      └── auth_audit.log    # Audit log (no sensitive data)
```

#### Usage Example:
```python
# Login to website
result = await login_to_website(
    url="https://example-site.com/login",
    username="demo_user",
    password="SecurePass123!"
)

# Subsequent requests use saved session
content = await fetch_website("https://example-site.com/profile")
```

#### Limitations:
- **CAPTCHA**: Requires manual completion (tool detects and notifies)
- **2FA/MFA**: Requires manual verification (tool detects and notifies)
- **Complex Auth**: OAuth, SAML, etc. may require manual login
- **Headless Mode**: Some sites detect headless browsers

#### Configuration:
```yaml
# ~/.wyn360/config.yaml (future enhancement)
authentication:
  session_ttl: 1800  # 30 minutes
  save_credentials: true
  headless: true
  timeout: 30000  # 30 seconds
```

**Version:** v0.3.40
**Status:** ✅ Complete
**Completed:** Current session
**Test Coverage:** 27/27 tests passing (SessionManager: 16/16, BrowserAuth: 11/11)

---

### Phase 4.3: Authenticated Fetch Integration (v0.3.41)

**Goal:** Seamlessly integrate authenticated sessions with fetch_website for automatic authenticated browsing

#### Tasks:
- [x] Modify fetch_website_content to accept cookies parameter
- [x] Update AsyncWebCrawler to inject cookies into browser context
- [x] Add automatic session detection in agent's fetch_website tool
- [x] Extract domain from URL and check for saved sessions
- [x] Pass session cookies to fetch_website_content automatically
- [x] Add authentication indicator in fetch response
- [x] Update fetch_website docstring with authentication info
- [x] Update system prompt with seamless integration details
- [x] Update ROADMAP_BROWSERUSE.md

#### Features:

**Seamless Authenticated Browsing:**
- fetch_website automatically detects and uses saved session cookies
- No manual cookie management required
- Domain-based session matching
- Visual indicator (🔐) when fetching authenticated content

**Implementation:**
```python
# In agent.py fetch_website method
domain = urlparse(url).netloc
session = self.session_manager.get_session(domain)
if session:
    cookies = session['cookies']
    authenticated = True

# Pass cookies to browser
success, content = await fetch_website_content(
    url=url,
    cookies=cookies  # Automatically injected
)
```

**User Experience:**
```python
# Step 1: Login once
login_to_website(
    url="https://example-site.com/login",
    username="demo_user",
    password="SecurePass123!"
)

# Step 2: All subsequent fetches are automatically authenticated!
fetch_website("https://example-site.com/profile")  # 🔐 authenticated
fetch_website("https://example-site.com/dashboard")  # 🔐 authenticated
fetch_website("https://example-site.com/settings")  # 🔐 authenticated
```

**Benefits:**
- Zero friction authenticated browsing
- Session cookies automatically used when available
- Clear visual feedback (🔐 indicator)
- 30-minute session TTL for security
- No manual token/cookie management

**Technical Changes:**
- `browser_use.py`: Added `cookies` parameter to `fetch_website_content`
- `browser_use.py`: Modified `AsyncWebCrawler` initialization with `browser_config`
- `agent.py`: Added session detection in `fetch_website` tool
- `agent.py`: Updated system prompt with Phase 4.3 integration details

**Version:** v0.3.41
**Status:** ✅ Complete
**Completed:** Current session

---

### Phase 4.4: Enhanced Form Detection (v0.3.42-0.3.43)

**Status:** ✅ Complete
**Priority:** HIGH
**Completed:** 2025-11-13
**Documentation:** v0.3.43

**Context:**
Real-world testing revealed form detection limitations. The system failed to login to `wyn360search.com` due to inability to detect non-standard login forms.

**Improvements Implemented:**

- [x] **4.4.1: Intelligent URL Discovery**
  - Tries 12 common login URLs (`/login`, `/signin`, `/auth`, `/account/login`, etc.)
  - Follows "Login" links on homepage automatically
  - Validates each URL for login form presence before selecting

- [x] **4.4.2: Dynamic Content Waiting**
  - Waits up to 10 seconds for form elements to appear
  - Handles JavaScript frameworks (React/Vue/Angular)
  - Additional 1-second settle time for dynamic content
  - Continues gracefully if timeout occurs

- [x] **4.4.3: Enhanced Form Detection with Fuzzy Matching**
  - Analyzes ALL input elements on page (not just predefined selectors)
  - Fuzzy matches on 7 attributes: type, name, id, placeholder, class, autocomplete, aria-label
  - Confidence scoring for username field candidates
  - Falls back to traditional detection if enhanced detection succeeds

- [x] **4.4.4: Debug Mode with Screenshots**
  - Environment variable: `export WYN360_BROWSER_DEBUG=true`
  - Saves timestamped screenshots at each step (8 screenshots per login attempt)
  - Dumps full HTML content for analysis
  - Exports detected elements to JSON with confidence scores
  - Stores in `~/.wyn360/debug/browser_auth/{timestamp}_*.png|html|json`
  - Provides clear error messages with debug file locations

- [x] **4.4.5: Manual Selector Override**
  - New agent tool: `login_with_manual_selectors()`
  - Accepts custom CSS selectors for username, password, submit fields
  - Bypasses automatic form detection entirely
  - Example: "Login with selectors #user, #pass, #submit-btn"
  - Saves debug screenshots when enabled

**Files Modified:**
- `wyn360_cli/browser_auth.py`: +300 lines (Phase 4.4 methods)
- `wyn360_cli/agent.py`: +100 lines (new tool + debug support)
- `pyproject.toml`: Version updated to 0.3.42

**New Methods:**
- `BrowserAuth._find_login_page()`: Intelligent URL discovery
- `BrowserAuth._has_login_form()`: Quick form presence check
- `BrowserAuth._wait_for_form_load()`: Dynamic content waiting
- `BrowserAuth._detect_login_form_enhanced()`: Fuzzy matching detection
- `BrowserAuth._save_debug_screenshot()`: Debug screenshot helper
- `BrowserAuth._save_debug_html()`: Debug HTML dump helper
- `BrowserAuth._save_debug_info()`: Debug JSON export helper
- `BrowserAuth.login_with_selectors()`: Manual selector override
- `Agent.login_with_manual_selectors()`: Agent tool for manual login

**Success Metrics (Expected):**
- Login success rate: 60% → 90%+ (testing in progress)
- Form detection rate: 70% → 95%+ (enhanced detection added)
- Average login time: ~15s (with discovery and waiting)
- Debug information: Comprehensive (screenshots + HTML + JSON)

**Usage:**

Enable debug mode:
```bash
export WYN360_BROWSER_DEBUG=true
wyn360 "login to http://wyn360search.com with your_username/your_password"
```

Use manual selectors:
```bash
wyn360 "login to http://example.com with user/pass using selectors #username, #password, #submit"
```

**Next Steps:**
- Real-world testing with wyn360search.com
- Test with diverse website types
- Gather metrics on success rates
- Consider Phase 4.5 (LLM-powered form analysis) if needed

---

### Phase 4.5: LLM-Powered Form Analysis (v0.3.43 - PLANNED)

**Status:** 📋 Planned
**Priority:** MEDIUM
**Estimated Effort:** 4-6 hours

**Approach:**
When automatic form detection fails, use Claude API to analyze page HTML and suggest selectors.

**Implementation:**

- [ ] **4.5.1: HTML Analysis Tool**
  - Extract relevant HTML (forms, inputs, buttons)
  - Truncate to fit in prompt (~50k chars)
  - Call Claude API with analysis task

- [ ] **4.5.2: Selector Suggestion**
  - LLM returns JSON with suggested selectors
  - Include confidence score (0-100)
  - Provide reasoning for suggestions
  - Fall back to manual mode if confidence <70

- [ ] **4.5.3: Adaptive Learning**
  - Cache successful selector patterns per domain
  - Build domain-specific form detection rules
  - Share patterns across users (privacy-safe)

**Example:**
```python
async def _analyze_page_with_llm(self, page: Page) -> Dict:
    html_content = await page.content()
    prompt = f"Analyze this HTML and identify login form elements: {html_content[:50000]}"
    # Call Claude API
    analysis = await claude_analyze(prompt)
    return analysis['selectors']
```

**Benefits:**
- Handle truly unique/custom forms
- Improve over time with learning
- Reduce manual intervention

---

### Phase 4.6: Interactive Browser Mode (v0.3.44 - PLANNED)

**Status:** 📋 Planned
**Priority:** LOW
**Estimated Effort:** 3-4 hours

**Feature:**
Launch non-headless browser, let user login manually, capture session cookies when complete.

**Implementation:**

- [ ] **4.6.1: Interactive Login Method**
  - New method: `interactive_login(url)`
  - Launch browser with `headless=False`
  - Display instructions to user
  - Wait for user confirmation (press ENTER)
  - Capture cookies and close browser

- [ ] **4.6.2: Session Import/Export**
  - Export cookies to JSON file
  - Import cookies from browser extensions
  - Support Chrome/Firefox cookie formats
  - Manual cookie entry via UI

**Use Cases:**
- Complex authentication (OAuth, SAML, SSO)
- CAPTCHA/2FA that can't be automated
- Sites with strong bot detection
- User wants full control

**Example:**
```bash
You: Help me login to wyn360search.com interactively

WYN360: 🌐 Opening browser for manual login...
        📝 Please login manually in the browser window
        ✅ Press ENTER when you're logged in

[Browser window opens]
[User logs in manually]
[User presses ENTER]

WYN360: ✅ Session captured! You can now fetch authenticated pages.
```

---

## Technical Considerations

### 1. Content Truncation Strategy

**Smart Truncation:**
- Preserve headers and structure
- Keep first N tokens + last M tokens
- Summarize middle section if needed

**Implementation:**
```python
def smart_truncate(markdown: str, max_tokens: int) -> str:
    """
    Intelligently truncate markdown content.

    Strategy:
    1. Keep full content if under max_tokens
    2. Preserve document structure (headers)
    3. Keep first 70% and last 30% of tokens
    4. Add truncation marker
    """
```

### 2. Browser Management

**Resource Management:**
- Use browser context pooling
- Close browser after each fetch
- Implement connection timeout (30s default)
- Handle network failures gracefully

**Memory Usage:**
- ~50-100MB per browser instance
- Close immediately after content extraction
- No persistent browser sessions

### 3. Security Considerations

**URL Validation:**
- Whitelist allowed protocols (http, https)
- Validate URL format before fetching
- Implement rate limiting (max 10 fetches/minute)
- Block potentially dangerous URLs

**Content Safety:**
- Sanitize markdown output
- Remove script tags and potentially harmful content
- Implement content size limits

### 4. Error Handling

**Common Scenarios:**
```python
# Timeout
if fetch_time > 30:
    return "⚠️ Website took too long to load (timeout: 30s)"

# 404 / 403 / 500 errors
if status_code >= 400:
    return f"❌ Failed to fetch: HTTP {status_code}"

# Network errors
except NetworkError:
    return "❌ Network error: Unable to connect"

# JavaScript errors
except JavaScriptError:
    return "⚠️ Page loaded but JavaScript failed"
```

---

## Performance Metrics

### Target Performance:
- Fetch time: < 5 seconds (average)
- Cache hit rate: > 80% (for repeated URLs)
- Memory overhead: < 200MB (including browser)
- Cache size: < 100MB total

### Monitoring:
```python
class BrowserUseMetrics:
    fetch_count: int
    cache_hits: int
    cache_misses: int
    avg_fetch_time: float
    total_bytes_fetched: int
    failed_fetches: int
```

---

## Dependencies

### New Dependencies:
```toml
[tool.poetry.dependencies]
crawl4ai = "^0.7.6"  # LLM-optimized web crawler
# Note: crawl4ai includes playwright as dependency
```

### Browser Binaries:
```bash
# Installed automatically during package installation
playwright install chromium
# Size: ~200MB (Chromium only)
```

---

## Documentation Updates

### README.md:
- Add "Browser Use" section
- Document fetch_website usage
- Show examples with real URLs

### SYSTEM.md:
- Document Phase 12.1, 12.2, 12.3
- Add architecture diagram
- Document cache system

### USE_CASES.md:
- Add Use Case 18: "Direct Website Fetching"
- Add examples with GitHub, docs, blogs
- Document cache management

### COST.md:
- Document token usage for fetched content
- Show cache savings
- Cost comparison: fetch vs search

---

## Testing Strategy

### Test Cases:

**1. Basic URL Fetching:**
```python
# GitHub repository
url = "https://github.com/user/repo"
content = await fetch_website(url)
assert "README" in content

# Documentation site
url = "https://docs.python.org/3/library/asyncio.html"
content = await fetch_website(url)
assert "asyncio" in content
```

**2. Cache System:**
```python
# First fetch (miss)
content1 = await fetch_website(url)
assert cache_stats.misses == 1

# Second fetch (hit)
content2 = await fetch_website(url)
assert cache_stats.hits == 1
assert content1 == content2
```

**3. Truncation:**
```python
# Large page
url = "https://example.com/large-page"
content = await fetch_website(url)
assert count_tokens(content) <= MAX_TOKENS
assert "[Content truncated]" in content
```

**4. Error Handling:**
```python
# 404 error
content = await fetch_website("https://example.com/404")
assert "404" in content or "not found" in content.lower()

# Timeout
content = await fetch_website("https://slow-site.com")
assert "timeout" in content.lower()
```

---

## Migration Path

### For Existing Users:

**Version 0.3.23 → 0.3.24:**
- New dependency: crawl4ai
- Browser binaries installed automatically
- No breaking changes to existing features
- WebSearchTool remains unchanged

**Configuration Migration:**
```bash
# Automatic migration on first run
wyn360 migrate-config

# Adds new browser_use section to config
# Preserves existing settings
```

---

## Future Enhancements (Post v0.3.43)

---

### Phase 5: Autonomous Vision-Based Browser Automation (v0.3.50-0.3.55) - OPTION A

**Status:** 📋 Planned (Primary Implementation Path)
**Priority:** HIGH
**Architecture:** Custom pydantic-ai + Anthropic Vision + Playwright
**Estimated Effort:** 2-3 weeks

**Goal:** Enable autonomous multi-step browser task execution using Claude Vision to analyze screenshots and make intelligent navigation decisions.

**Design Philosophy:**
- **Single Agent Framework**: Everything stays within pydantic-ai infrastructure
- **Unified Billing**: All AI decisions (vision + language) through ANTHROPIC_API_KEY
- **Tight Integration**: Seamlessly works with existing WYN360 tools (WebSearch, auth, file tools, etc.)
- **Full Control**: Custom implementation for maximum flexibility and context sharing
- **Anthropic API Only**: Gracefully disabled in Bedrock mode (vision not well-supported)

**Key Use Cases (Ranked by Priority):**
1. **Open-Ended Exploration** (Priority 1): "Browse Amazon electronics and tell me what's trending"
2. **Integrated Workflows** (Priority 2): "Search web for best shoe stores, browse top result, find best deal"
3. **Structured Shopping** (Priority 3): "Find the cheapest sneaker with 2-day shipping on Amazon"

---

#### Phase 5.1: Core Infrastructure (v0.3.52)

**Goal:** Build foundational browser control and vision analysis infrastructure

**Status:** ✅ COMPLETE (2025-11-17)

**Tasks:**
- [x] **5.1.1: BrowserController Class** ✅
  - Create `wyn360_cli/browser_controller.py`
  - Implement Playwright-based browser automation (visible browser by default)
  - Browser lifecycle management (launch, navigate, close)
  - Action execution (click, type, scroll, navigate, wait)
  - Screenshot capture (with quality optimization for vision API)
  - Element locator strategies (CSS selectors, XPath, text-based, fuzzy matching)
  - Error handling and retry logic
  - Resource cleanup and timeout management
  - **Tests:** 17/17 passing (tests/test_browser_controller.py)

- [x] **5.1.2: Vision Decision Engine** ✅
  - Create `wyn360_cli/vision_engine.py`
  - Integrate with Anthropic Vision API via pydantic-ai
  - Screenshot analysis prompt engineering
  - Action decision parsing (structured output)
  - Context management (task goal, action history, page state)
  - Confidence scoring for decisions
  - Fallback strategies for low-confidence scenarios
  - **Tests:** 23/23 passing (tests/test_vision_engine.py)

- [x] **5.1.3: Action Parser** ✅
  - Parse Claude's natural language decisions into Playwright actions
  - Support action types: click, type, scroll, navigate, extract, complete
  - Handle coordinates, selectors, text targets
  - Validate actions before execution
  - Error recovery suggestions
  - **Integrated into:** VisionDecisionEngine (_parse_decision, _validate_action methods)

**Implementation Details:**

```python
# wyn360_cli/browser_controller.py
class BrowserController:
    """
    Pure browser automation using Playwright (no AI).
    Responsible for: browser lifecycle, action execution, screenshot capture.
    """

    async def initialize(self, headless: bool = False, viewport_size: tuple = (1024, 768)):
        """Launch browser with optimal settings for vision analysis."""

    async def navigate(self, url: str):
        """Navigate to URL with smart waiting."""

    async def take_screenshot(self, optimize_for_vision: bool = True) -> bytes:
        """
        Capture screenshot optimized for Claude Vision.
        - Resolution: 1024x768 (XGA - optimal for vision API)
        - Format: PNG
        - Compression: Balanced for quality vs size
        """

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute browser action from parsed decision.

        Actions:
          - click: {type: 'click', selector: '#btn', text: 'Submit'}
          - type: {type: 'type', selector: '#search', text: 'sneakers'}
          - scroll: {type: 'scroll', direction: 'down', amount: 500}
          - navigate: {type: 'navigate', url: 'https://...'}
          - extract: {type: 'extract', selector: '.price'}
          - wait: {type: 'wait', seconds: 2}
        """

    async def find_element(self, strategy: str, value: str) -> Optional[ElementHandle]:
        """
        Find element using various strategies:
        - selector: CSS selector
        - xpath: XPath expression
        - text: Visible text content
        - fuzzy: Fuzzy text matching
        """

    async def get_page_state(self) -> Dict[str, Any]:
        """Extract current page metadata (URL, title, loaded state)."""

    async def cleanup(self):
        """Close browser and cleanup resources."""


# wyn360_cli/vision_engine.py
class VisionDecisionEngine:
    """
    Uses Anthropic Claude Vision (via pydantic-ai) to analyze screenshots.
    Responsible for: vision analysis, decision making, action planning.
    """

    def __init__(self, agent: Agent):
        """Initialize with WYN360Agent (pydantic-ai)."""
        self.agent = agent

    async def analyze_and_decide(
        self,
        screenshot: bytes,
        goal: str,
        history: List[Dict],
        page_state: Dict
    ) -> Dict[str, Any]:
        """
        Analyze screenshot and decide next action.

        Returns:
          {
            'status': 'continue' | 'complete' | 'stuck',
            'action': {...},  # Next action to execute
            'reasoning': str,  # Claude's reasoning
            'confidence': float,  # 0-100
            'extracted_data': {...},  # If status='complete'
          }
        """
        from pydantic_ai import BinaryContent

        # Build analysis prompt
        prompt = self._build_analysis_prompt(goal, history, page_state)

        # Call agent with vision (all through pydantic-ai!)
        result = await self.agent.run(
            user_prompt=[
                prompt,
                BinaryContent(data=screenshot, media_type='image/png'),
            ]
        )

        # Parse decision
        return self._parse_decision(result.data)

    def _build_analysis_prompt(self, goal: str, history: List, state: Dict) -> str:
        """
        Build comprehensive vision analysis prompt.

        Includes:
        - Task goal
        - Current page state
        - Action history (what we've tried)
        - Available actions
        - Success criteria
        - Instructions for structured output
        """

    def _parse_decision(self, response: Any) -> Dict:
        """Parse Claude's response into structured action."""
```

**Features:**
- XGA resolution (1024x768) for optimal vision API performance
- Visible browser (headless=False) so user can watch
- Smart element location (CSS, XPath, text, fuzzy)
- Comprehensive error handling
- Resource cleanup

**Dependencies:**
```toml
# Already have playwright via crawl4ai, no new deps needed
```

**Version:** v0.3.52
**Status:** ✅ COMPLETE
**Completed:** 2025-11-17

---

#### Phase 5.2: Task Executor Loop (v0.3.51)

**Goal:** Implement the core screenshot → analyze → decide → act → repeat loop

**Tasks:**
- [ ] **5.2.1: BrowserTaskExecutor Class**
  - Create `wyn360_cli/browser_task_executor.py`
  - Implement main execution loop
  - Task state management (goal, progress, history)
  - Step limiting (max_steps to prevent infinite loops)
  - Success detection (task completion criteria)
  - Stuck detection (repeated failed actions)
  - Progress reporting to user
  - Execution metrics tracking

- [ ] **5.2.2: Loop Orchestration**
  - Initialize browser and vision engine
  - Main loop: screenshot → analyze → execute → validate
  - State persistence across steps
  - Error recovery and retries
  - Graceful degradation
  - User interruption handling

- [ ] **5.2.3: Context Management**
  - Track action history (what worked, what didn't)
  - Maintain page state changes
  - Store extracted information
  - Build comprehensive final report
  - Memory-efficient history (avoid token bloat)

**Implementation:**

```python
# wyn360_cli/browser_task_executor.py
class BrowserTaskExecutor:
    """
    Orchestrates autonomous browser tasks using vision-based decision making.
    Coordinates BrowserController (automation) + VisionDecisionEngine (AI).
    """

    def __init__(self, agent: Agent):
        """Initialize with WYN360Agent (pydantic-ai)."""
        self.agent = agent
        self.controller = BrowserController()
        self.vision_engine = VisionDecisionEngine(agent)

    async def execute_task(
        self,
        task: str,
        url: str,
        max_steps: int = 20,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        Execute multi-step browser task autonomously.

        Args:
          task: Natural language task description
          url: Starting URL
          max_steps: Maximum browser actions (default: 20)
          headless: Run browser in headless mode (default: False for user visibility)

        Returns:
          {
            'status': 'success' | 'partial' | 'failed',
            'result': {...},  # Extracted data
            'steps_taken': int,
            'history': [...],  # Action history
            'reasoning': str,  # Final summary
          }
        """

        # Initialize
        await self.controller.initialize(headless=headless)
        await self.controller.navigate(url)

        history = []
        stuck_count = 0
        last_action = None

        try:
            for step in range(max_steps):
                # 1. Capture current state
                screenshot = await self.controller.take_screenshot()
                page_state = await self.controller.get_page_state()

                # 2. Analyze and decide (ALL AI via pydantic-ai + Anthropic Vision)
                decision = await self.vision_engine.analyze_and_decide(
                    screenshot=screenshot,
                    goal=task,
                    history=history,
                    page_state=page_state
                )

                # 3. Check if task complete
                if decision['status'] == 'complete':
                    return {
                        'status': 'success',
                        'result': decision['extracted_data'],
                        'steps_taken': step + 1,
                        'history': history,
                        'reasoning': decision['reasoning']
                    }

                # 4. Check if stuck (repeated failures)
                if decision['status'] == 'stuck' or decision['action'] == last_action:
                    stuck_count += 1
                    if stuck_count >= 3:
                        return self._handle_stuck_state(task, history, step)
                else:
                    stuck_count = 0

                # 5. Execute action
                action_result = await self.controller.execute_action(decision['action'])

                # 6. Record history
                history.append({
                    'step': step + 1,
                    'action': decision['action'],
                    'reasoning': decision['reasoning'],
                    'confidence': decision['confidence'],
                    'result': action_result,
                    'page_url': page_state['url']
                })

                last_action = decision['action']

                # 7. Small delay for page updates
                await asyncio.sleep(1)

        finally:
            await self.controller.cleanup()

        # Max steps reached
        return {
            'status': 'partial',
            'result': None,
            'steps_taken': max_steps,
            'history': history,
            'reasoning': f"Reached maximum steps ({max_steps}) without completion"
        }

    def _handle_stuck_state(self, task: str, history: List, step: int) -> Dict:
        """Handle case where agent is stuck/repeating actions."""
        return {
            'status': 'failed',
            'result': None,
            'steps_taken': step,
            'history': history,
            'reasoning': "Agent appears stuck. Last 3 actions failed or repeated."
        }
```

**Features:**
- Smart stuck detection (repeated failed actions)
- Progress visibility (user can watch browser)
- Comprehensive history tracking
- Graceful failure handling
- Resource cleanup guaranteed (try/finally)

**Version:** v0.3.51
**Estimated Time:** 4-6 days

---

#### Phase 5.3: Agent Tool Integration (v0.3.52)

**Goal:** Add `browse_and_find` tool to WYN360Agent

**Tasks:**
- [ ] **5.3.1: New Agent Tool**
  - Add `browse_and_find()` tool to `wyn360_cli/agent.py`
  - Integrate BrowserTaskExecutor
  - Format results for agent consumption
  - Error handling and user-friendly messages
  - Bedrock mode check (vision required)

- [ ] **5.3.2: System Prompt Update**
  - Add Phase 5 autonomous browsing section
  - Usage guidelines for the tool
  - Example scenarios
  - Limitations and best practices

- [ ] **5.3.3: Tool Chaining Support**
  - Enable seamless use with WebSearchTool
  - Enable use with authenticated browsing (login_to_website)
  - Context sharing across tools
  - Multi-tool workflow examples

**Implementation:**

```python
# In wyn360_cli/agent.py (WYN360Agent class)

@self.agent.tool
async def browse_and_find(
    ctx: RunContext[None],
    task: str,
    url: str,
    max_steps: int = 20,
    headless: bool = False
) -> str:
    """
    Autonomously browse a website to complete a multi-step task using vision.

    **How it works:**
    1. Opens browser (visible by default so you can watch)
    2. Takes screenshots and analyzes with Claude Vision
    3. Makes intelligent decisions about what to click/type/navigate
    4. Continues until task is complete or max_steps reached
    5. Returns extracted information

    **Examples:**
    - "Find the cheapest sneaker with 2-day shipping on Amazon"
    - "Browse electronics section and tell me what's trending"
    - "Search for 'laptop', sort by best rating, get first result's price"
    - "Go to my Amazon wishlist and find the most expensive item"

    **Args:**
        task: Natural language description of what to accomplish
        url: Starting URL (e.g., "https://amazon.com")
        max_steps: Maximum browser actions to attempt (default: 20)
        headless: Run browser invisibly (default: False - visible)

    **Integration:**
    - Works seamlessly with login_to_website (uses saved sessions)
    - Can be chained with WebSearchTool ("search for X, then browse top result")
    - Shares context with main agent

    **IMPORTANT:**
    - Only works in Anthropic API mode (requires vision capabilities)
    - Disabled in Bedrock mode
    - Browser will be visible by default (user can watch the agent work)
    - Set headless=True to run invisibly

    **Returns:**
        Extracted information or task result as formatted text
    """

    # Check mode (vision required)
    if self.use_bedrock:
        return (
            "❌ Autonomous browsing requires vision capabilities.\n\n"
            "This feature uses Claude Vision to analyze screenshots and make "
            "intelligent navigation decisions. Vision capabilities are not "
            "available in AWS Bedrock mode.\n\n"
            "Please use Anthropic API mode to access this feature:\n"
            "  export ANTHROPIC_API_KEY=your_key_here\n"
            "  unset CLAUDE_CODE_USE_BEDROCK"
        )

    try:
        # Initialize executor
        executor = BrowserTaskExecutor(self.agent)

        # Execute task
        result = await executor.execute_task(
            task=task,
            url=url,
            max_steps=max_steps,
            headless=headless
        )

        # Format response based on status
        if result['status'] == 'success':
            return f"""✅ **Task Completed Successfully!**

**Task:** {task}
**Steps Taken:** {result['steps_taken']}

**Result:**
{self._format_extracted_data(result['result'])}

**Summary:**
{result['reasoning']}

---
*Powered by Claude Vision + Playwright*
"""

        elif result['status'] == 'partial':
            return f"""⚠️ **Task Partially Completed**

**Task:** {task}
**Steps Taken:** {result['steps_taken']} (reached maximum)

**Progress:**
{self._format_action_history(result['history'])}

**Note:** {result['reasoning']}

You may want to:
1. Increase max_steps (currently {max_steps})
2. Refine the task description
3. Try a different starting URL
"""

        else:  # failed
            return f"""❌ **Task Failed**

**Task:** {task}
**Steps Attempted:** {result['steps_taken']}

**Issue:** {result['reasoning']}

**Action History:**
{self._format_action_history(result['history'])}

**Suggestions:**
- Verify the URL is accessible
- Check if the task is achievable on this website
- Try breaking the task into smaller steps
- Consider using manual selectors if form detection failed
"""

    except Exception as e:
        logger.error(f"Autonomous browsing error: {e}")
        return f"❌ Error during autonomous browsing: {str(e)}"

def _format_extracted_data(self, data: Dict) -> str:
    """Format extracted data for display."""
    # Pretty-print extracted information

def _format_action_history(self, history: List[Dict]) -> str:
    """Format action history for display."""
    # Show step-by-step actions taken
```

**System Prompt Addition:**

```markdown
**Phase 5: Autonomous Vision-Based Browsing (Anthropic API Only)**

You have access to `browse_and_find()` which enables autonomous multi-step browser automation:

**How it works:**
- Takes screenshots of the browser
- Analyzes with Claude Vision (you see the page)
- Decides what to click, type, or navigate
- Continues until task complete

**Use it for:**
1. Open-ended exploration: "Browse Amazon electronics and tell me what's trending"
2. Multi-step tasks: "Find cheapest sneaker with 2-day shipping"
3. Integrated workflows: Can chain with WebSearchTool, login_to_website, etc.

**Integration with existing tools:**
- If user is logged in (via login_to_website), browse_and_find uses saved session
- Can combine with WebSearchTool: "search for best shoe stores, browse top result"
- Shares context with your main conversation

**Guidelines:**
- Start URL should be the most relevant page for the task
- Task description should be clear and specific
- For complex tasks, break into smaller browse_and_find calls
- Browser is visible by default (user can watch)

**NOT available in Bedrock mode** (requires vision capabilities)
```

**Version:** v0.3.52
**Estimated Time:** 3-4 days

---

#### Phase 5.4: Testing & Refinement (v0.3.53)

**Goal:** Comprehensive testing with real-world use cases

**Tasks:**
- [ ] **5.4.1: Use Case Testing**
  - Test Case 1: Amazon shopping (cheapest item with criteria)
  - Test Case 2: Open-ended exploration (trending items)
  - Test Case 3: Authenticated browsing (wishlist analysis)
  - Test Case 4: Multi-tool workflow (search → browse → extract)
  - Test Case 5: Form interactions (search, filter, sort)

- [ ] **5.4.2: Error Scenario Testing**
  - Handle timeout scenarios
  - Handle stuck navigation
  - Handle missing elements
  - Handle JavaScript-heavy sites
  - Handle popups/modals/cookie banners

- [ ] **5.4.3: Vision Prompt Optimization**
  - Refine vision analysis prompts
  - Improve action decision accuracy
  - Reduce hallucinations
  - Optimize for speed vs accuracy

- [ ] **5.4.4: Performance Optimization**
  - Screenshot compression
  - Vision API call efficiency
  - Action execution speed
  - Memory usage optimization

**Test Scenarios:**

```python
# Test Case 1: Structured shopping task
result = await browse_and_find(
    task="Find the cheapest sneaker with 2-day shipping",
    url="https://amazon.com"
)
# Expected: Successfully finds and returns cheapest sneaker with Prime

# Test Case 2: Open-ended exploration
result = await browse_and_find(
    task="Browse the electronics section and tell me what's trending",
    url="https://amazon.com",
    max_steps=30
)
# Expected: Navigates to electronics, analyzes trending items, returns insights

# Test Case 3: Authenticated browsing
await login_to_website("https://amazon.com/login", "user", "pass")
result = await browse_and_find(
    task="Find the most expensive item in my wishlist",
    url="https://amazon.com/wishlist"
)
# Expected: Uses saved session, accesses wishlist, finds most expensive item

# Test Case 4: Multi-tool workflow
search_results = await web_search("best online shoe stores")
top_url = extract_top_url(search_results)
result = await browse_and_find(
    task="Find the best deal on running shoes",
    url=top_url
)
# Expected: Seamlessly chains search → browse, returns best deal
```

**Success Metrics:**
- Task completion rate: >70% for structured tasks
- Exploration quality: >80% user satisfaction for open-ended tasks
- Integration success: 100% compatibility with existing tools
- Error recovery: >90% graceful error handling

**Version:** v0.3.53
**Estimated Time:** 5-7 days

---

#### Phase 5.5: Documentation & Polish (v0.3.54)

**Goal:** Comprehensive documentation and user-facing polish

**Tasks:**
- [ ] **5.5.1: Documentation Updates**
  - Update README.md with autonomous browsing section
  - Update SYSTEM.md with Phase 5 architecture
  - Update USE_CASES.md with 3+ new use cases
  - Update COST.md with vision API cost analysis
  - Create AUTONOMOUS_BROWSING.md guide

- [ ] **5.5.2: Code Documentation**
  - Docstrings for all new classes/methods
  - Architecture diagrams
  - Code examples
  - API reference

- [ ] **5.5.3: User Experience Polish**
  - Progress indicators during browsing
  - Better error messages
  - Helpful suggestions when stuck
  - Examples in tool help text

**Documentation Structure:**

```markdown
# docs/AUTONOMOUS_BROWSING.md

## Overview
Autonomous browsing enables Claude to interact with websites using vision...

## Architecture
[Diagram: Screenshot → Vision → Decision → Action → Loop]

## Usage Examples
### Example 1: Structured Shopping
### Example 2: Open-Ended Exploration
### Example 3: Authenticated Workflows

## Best Practices
- Start with specific URLs
- Use clear task descriptions
- Chain with other tools
- Handle authentication first

## Troubleshooting
- Task not completing → Increase max_steps
- Wrong actions → Refine task description
- Stuck in loop → Check website structure

## Cost Considerations
- Vision API costs ~$0.XX per screenshot
- Typical task: 10-15 screenshots = $X.XX
- Optimize by reducing max_steps
```

**Version:** v0.3.54
**Estimated Time:** 3-4 days

---

#### Phase 5.6: Advanced Features (v0.3.55)

**Goal:** Add advanced capabilities and optimizations

**Tasks:**
- [ ] **5.6.1: Screenshot Optimization**
  - Intelligent cropping (focus on relevant areas)
  - Element highlighting for clarity
  - Adaptive resolution based on content
  - Caching for repeated views

- [ ] **5.6.2: Multi-Page Workflows**
  - Support for "compare across multiple sites"
  - Parallel browsing (multiple tabs)
  - Cross-site data aggregation

- [ ] **5.6.3: Learning & Improvement**
  - Cache successful navigation patterns per domain
  - Learn common element selectors
  - Optimize prompts based on success rate

- [ ] **5.6.4: Advanced Error Recovery**
  - Automatic backtracking when stuck
  - Alternative path exploration
  - Human-in-the-loop for critical decisions

**Version:** v0.3.55
**Estimated Time:** 5-6 days

---

### **Phase 5 Summary (Option A)**

**Total Estimated Time:** 25-34 days (5-7 weeks)

**Deliverables:**
- ✅ Custom vision-based browser automation
- ✅ Fully integrated with pydantic-ai
- ✅ Seamless tool chaining
- ✅ Authenticated browsing support
- ✅ Anthropic API only (unified billing)
- ✅ Comprehensive documentation
- ✅ Production-ready error handling

**Architecture Benefits:**
- Single agent framework (pydantic-ai)
- All AI through Anthropic API
- Tight integration with existing tools
- Full control over behavior
- Shared context across tools

---

### Phase 6: browser-use Package Integration (v0.3.60-0.3.62) - OPTION B

**Status:** 📋 Planned (Alternative/Complementary Path)
**Priority:** MEDIUM
**Architecture:** Hybrid (pydantic-ai + browser-use sub-agent)
**Estimated Effort:** 1-2 weeks

**Goal:** Integrate browser-use package as a specialized sub-agent for structured browser automation tasks, while maintaining pydantic-ai as the main infrastructure.

**Design Philosophy:**
- **Hybrid Architecture**: pydantic-ai as main agent, browser-use as specialized sub-agent
- **Unified Billing**: Both use ANTHROPIC_API_KEY
- **Use Case Split**: Option B for structured tasks, Option A for integrated workflows
- **Graceful Coexistence**: Both options available, user/agent chooses best fit
- **Minimal Breaking Changes**: New tool only, existing code untouched

**When to Use Option B:**
- Structured, deterministic browser automation
- Battle-tested reliability is critical
- Fast development for simple tasks
- Don't need integration with other WYN360 tools

**When to Use Option A:**
- Integrated workflows (search → browse → authenticate)
- Open-ended exploration tasks
- Need shared context with main agent
- Authenticated browsing with existing sessions

---

#### Phase 6.1: Basic Integration (v0.3.60)

**Goal:** Add browser-use as an optional specialized tool

**Tasks:**
- [ ] **6.1.1: Dependency Management**
  - Add browser-use to optional dependencies
  - Handle graceful degradation if not installed
  - Update installation documentation

- [ ] **6.1.2: BrowserUseWrapper Class**
  - Create `wyn360_cli/browser_use_wrapper.py`
  - Wrap browser-use Agent with WYN360 interface
  - Ensure ANTHROPIC_API_KEY is used
  - Error handling and result formatting

- [ ] **6.1.3: New Agent Tool**
  - Add `browse_structured_task()` tool
  - Clearly distinguish from `browse_and_find()` (Option A)
  - Documentation on when to use which

**Implementation:**

```python
# wyn360_cli/browser_use_wrapper.py
from typing import Optional
try:
    from browser_use import Agent as BrowserAgent, ChatAnthropic
    HAS_BROWSER_USE = True
except ImportError:
    HAS_BROWSER_USE = False

class BrowserUseWrapper:
    """
    Wrapper for browser-use package.
    Provides structured browser automation as a specialized sub-agent.
    """

    def __init__(self, api_key: str):
        """Initialize with Anthropic API key."""
        if not HAS_BROWSER_USE:
            raise ImportError("browser-use not installed. Install with: pip install browser-use")
        self.api_key = api_key

    async def execute_task(self, task: str, url: Optional[str] = None) -> Dict:
        """
        Execute structured browser task using browser-use.

        Args:
          task: Natural language task (browser-use handles interpretation)
          url: Optional starting URL (browser-use can navigate if not provided)

        Returns:
          Browser-use result (formatted for WYN360)
        """
        # Create browser-use agent (separate from pydantic-ai agent)
        llm = ChatAnthropic(model='claude-sonnet-4-0')

        # Build task with URL if provided
        full_task = f"{task} starting at {url}" if url else task

        # Create and run browser-use agent
        browser_agent = BrowserAgent(
            task=full_task,
            llm=llm
        )

        result = await browser_agent.run()

        return {
            'success': True,
            'result': result,
            'source': 'browser-use'
        }


# In wyn360_cli/agent.py
@self.agent.tool
async def browse_structured_task(
    ctx: RunContext[None],
    task: str,
    url: Optional[str] = None
) -> str:
    """
    Execute structured browser automation using browser-use package.

    **Best for:**
    - Simple, deterministic tasks ("find cheapest X")
    - When speed/reliability > integration
    - Standalone browser tasks (no tool chaining needed)

    **NOT best for:**
    - Tasks needing authentication (use browse_and_find + login_to_website)
    - Multi-tool workflows (use browse_and_find)
    - Open-ended exploration (use browse_and_find)

    **How it differs from browse_and_find:**
    - browse_structured_task: Uses browser-use (separate sub-agent, optimized for structured tasks)
    - browse_and_find: Uses custom vision engine (integrated with main agent, better for workflows)

    **Examples:**
    - "Find the price of the top-rated laptop on Amazon"
    - "Get the download count for Python package 'requests' from PyPI"
    - "Check the current Bitcoin price on CoinMarketCap"

    **Args:**
        task: Natural language task description
        url: Optional starting URL

    **IMPORTANT:**
    - Requires browser-use package: pip install browser-use
    - Uses ANTHROPIC_API_KEY (unified billing)
    - Runs as separate sub-agent (no context sharing with main agent)
    - Only works in Anthropic API mode

    **Returns:**
        Task result as formatted text
    """

    # Check mode
    if self.use_bedrock:
        return "❌ browser-use integration only available in Anthropic API mode."

    # Check if browser-use installed
    if not HAS_BROWSER_USE:
        return (
            "❌ browser-use package not installed.\n\n"
            "Install with: pip install browser-use\n\n"
            "Alternative: Use browse_and_find() which is built-in (Option A)"
        )

    try:
        wrapper = BrowserUseWrapper(self.api_key)
        result = await wrapper.execute_task(task, url)

        return f"""✅ **Task Completed (via browser-use)**

**Task:** {task}

**Result:**
{result['result']}

---
*Powered by browser-use + Anthropic Claude*
"""

    except Exception as e:
        logger.error(f"browser-use error: {e}")
        return f"❌ Error: {str(e)}\n\nTry using browse_and_find() instead (Option A)"
```

**Dependencies:**

```toml
# pyproject.toml
[project.optional-dependencies]
browser-use = ["browser-use>=0.1.0"]

# Install with: pip install wyn360-cli[browser-use]
```

**Version:** v0.3.60
**Estimated Time:** 3-4 days

---

#### Phase 6.2: Smart Tool Selection (v0.3.61)

**Goal:** Help agent automatically choose between Option A and Option B

**Tasks:**
- [ ] **6.2.1: Decision Logic**
  - Add guidelines to system prompt
  - When to use browse_structured_task vs browse_and_find
  - Automatic fallback if one option fails

- [ ] **6.2.2: Performance Comparison**
  - Benchmark both options on common tasks
  - Document speed/accuracy trade-offs
  - Update recommendations based on data

**System Prompt Addition:**

```markdown
**Choosing Between Autonomous Browsing Options:**

You have TWO browser automation tools:

1. **browse_and_find** (Option A - Custom Vision):
   - Best for: Open-ended exploration, integrated workflows, authenticated browsing
   - Pros: Tight integration, context sharing, works with login_to_website
   - Cons: Slower (vision analysis), more API calls
   - Use when: Task needs tool chaining or exploration

2. **browse_structured_task** (Option B - browser-use):
   - Best for: Simple structured tasks, standalone automation
   - Pros: Faster, battle-tested, optimized for structured tasks
   - Cons: Separate sub-agent, no context sharing, no auth integration
   - Use when: Task is simple and deterministic

**Decision Guide:**
- "Find cheapest X" → browse_structured_task (simple, structured)
- "Browse and tell me trends" → browse_and_find (exploration)
- "Search web, then browse result" → browse_and_find (multi-tool)
- "Login and check my cart" → browse_and_find (authentication)

**Fallback Strategy:**
- Try browse_structured_task first for simple tasks (faster)
- If it fails or task is complex, use browse_and_find
- Always prefer browse_and_find for authenticated workflows
```

**Version:** v0.3.61
**Estimated Time:** 2-3 days

---

#### Phase 6.3: Documentation & Comparison (v0.3.62)

**Goal:** Comprehensive documentation comparing both options

**Tasks:**
- [ ] **6.3.1: Comparison Guide**
  - Create docs/BROWSER_AUTOMATION_COMPARISON.md
  - Side-by-side feature comparison
  - Use case decision tree
  - Performance benchmarks

- [ ] **6.3.2: Migration Path**
  - Document how to switch between options
  - Provide migration examples
  - Explain when to use each

**Documentation:**

```markdown
# docs/BROWSER_AUTOMATION_COMPARISON.md

## Overview
WYN360-CLI offers two approaches to autonomous browser automation:

### Option A: Custom Vision-Based (browse_and_find)
- **Architecture:** pydantic-ai + Anthropic Vision + Playwright
- **Best for:** Integrated workflows, exploration, authenticated browsing
- **Status:** Built-in, always available

### Option B: browser-use Integration (browse_structured_task)
- **Architecture:** browser-use package as sub-agent
- **Best for:** Simple structured tasks, standalone automation
- **Status:** Optional, requires browser-use package

## Feature Comparison

| Feature | Option A (Custom) | Option B (browser-use) |
|---------|-------------------|------------------------|
| **Integration** | Tight (same agent) | Loose (sub-agent) |
| **Context Sharing** | ✅ Yes | ❌ No |
| **Tool Chaining** | ✅ Native | ⚠️ Manual |
| **Authentication** | ✅ Seamless | ❌ Separate |
| **Open-Ended Tasks** | ✅ Excellent | ⚠️ Limited |
| **Structured Tasks** | ✅ Good | ✅ Excellent |
| **Speed** | Slower (vision) | Faster (optimized) |
| **Reliability** | Good | Excellent |
| **Setup** | Built-in | Requires install |
| **Billing** | Anthropic API | Anthropic API |

## Use Case Decision Tree

```
Is task authenticated? (needs login)
├─ YES → Option A (browse_and_find)
└─ NO
   │
   Does task need other tools? (search, fetch, files)
   ├─ YES → Option A (browse_and_find)
   └─ NO
      │
      Is task exploratory? ("tell me trends")
      ├─ YES → Option A (browse_and_find)
      └─ NO
         │
         Is task structured? ("find cheapest X")
         └─ YES → Option B (browse_structured_task)
```

## Performance Benchmarks

| Task Type | Option A | Option B |
|-----------|----------|----------|
| Simple extraction | 15-20s | 8-12s |
| Multi-step navigation | 25-35s | 18-25s |
| Open exploration | 40-60s | N/A |
| Authenticated task | 20-30s | N/A |

## Recommendation

**Start with Option A (browse_and_find):**
- More flexible
- Better integration
- Handles all use cases

**Use Option B (browse_structured_task) for:**
- Speed-critical simple tasks
- When browser-use is already installed
- Standalone automation needs

## Migration Examples

### Simple Task (Either Works)
```python
# Option A
result = browse_and_find(
    task="Find Python download count on PyPI",
    url="https://pypi.org/project/requests"
)

# Option B (faster)
result = browse_structured_task(
    task="Get download count for package requests",
    url="https://pypi.org"
)
```

### Complex Workflow (Option A Only)
```python
# Search web for stores
stores = web_search("best online shoe stores")

# Browse top result (needs context from search)
result = browse_and_find(
    task="Find best deal on running shoes",
    url=extract_url(stores)
)
# Option B can't do this - no context sharing
```
```

**Version:** v0.3.62
**Estimated Time:** 2-3 days

---

### **Phase 6 Summary (Option B)**

**Total Estimated Time:** 7-10 days (1.5-2 weeks)

**Deliverables:**
- ✅ browser-use package integration
- ✅ Clear separation from Option A
- ✅ Smart tool selection guidelines
- ✅ Comprehensive comparison docs
- ✅ Graceful coexistence with Option A

**When to Implement:**
- After Option A is complete and tested
- When users request faster structured automation
- If browser-use proves significantly more reliable for simple tasks

---

### Phase 7: Advanced Capabilities (v0.3.70+)

**Status:** 📋 Planned (Long-term Enhancements)
**Priority:** LOW-MEDIUM

**Goal:** Advanced features that build on Phase 5 & 6 foundations

#### Phase 7.1: Multi-Site Workflows
- Parallel browsing across multiple sites
- Cross-site data aggregation and comparison
- Site-to-site navigation ("find on Amazon, compare with eBay")

#### Phase 7.2: Intelligent Caching
- Cache successful navigation patterns per domain
- Learn common element selectors over time
- Share learned patterns (privacy-safe)
- Reduce redundant vision API calls

#### Phase 7.3: Advanced Error Recovery
- Automatic backtracking when stuck
- Alternative path exploration
- Human-in-the-loop for critical decisions
- Adaptive retry strategies

#### Phase 7.4: Performance Optimizations
- Screenshot compression and optimization
- Intelligent cropping (focus on relevant areas)
- Adaptive resolution based on content type
- Vision API call batching

#### Phase 7.5: Vector Database Integration
- Store browsing history in vector DB
- Semantic search over visited pages
- RAG-enhanced browsing decisions
- Long-term memory across sessions

---

### Phase 8: Production Hardening (v0.3.80+)

**Status:** 📋 Planned (Production Readiness)
**Priority:** MEDIUM

#### Phase 8.1: Monitoring & Metrics
- Detailed execution metrics (success rate, avg steps, cost per task)
- Vision API usage tracking
- Error categorization and logging
- Performance dashboards

#### Phase 8.2: Cost Optimization
- Vision API call reduction strategies
- Screenshot caching and reuse
- Intelligent step limiting
- Cost alerts and budgets

#### Phase 8.3: Security Hardening
- Rate limiting per domain
- URL validation and filtering
- Content safety checks
- Audit logging for all browser actions

#### Phase 8.4: Reliability
- Comprehensive error handling
- Automatic recovery mechanisms
- Graceful degradation
- Circuit breakers for failing sites

---

## Implementation Timeline

### Option A (Primary Path - Implement First)
| Phase | Version | Duration | Dependencies |
|-------|---------|----------|--------------|
| 5.1 - Core Infrastructure | v0.3.52 | ✅ COMPLETE (2025-11-17) | None |
| 5.2 - Task Executor | v0.3.53 | 4-6 days | Phase 5.1 |
| 5.3 - Agent Integration | v0.3.54 | 3-4 days | Phase 5.2 |
| 5.4 - Testing | v0.3.55 | 5-7 days | Phase 5.3 |
| 5.5 - Documentation | v0.3.56 | 3-4 days | Phase 5.4 |
| 5.6 - Advanced Features | v0.3.57 | 5-6 days | Phase 5.5 |
| **Total** | **v0.3.52-0.3.57** | **25-34 days** | **5-7 weeks** |

### Option B (Alternative Path - Implement After Option A)
| Phase | Version | Duration | Dependencies |
|-------|---------|----------|--------------|
| 6.1 - Basic Integration | v0.3.60 | 3-4 days | Phase 5 complete |
| 6.2 - Smart Selection | v0.3.61 | 2-3 days | Phase 6.1 |
| 6.3 - Documentation | v0.3.62 | 2-3 days | Phase 6.2 |
| **Total** | **v0.3.60-0.3.62** | **7-10 days** | **1.5-2 weeks** |

### Combined Timeline (Option A → Option B)
**Total:** 32-44 days (6.5-9 weeks)

---

## Success Metrics

### Option A (Custom Vision-Based)
- ✅ Task completion rate >70% for structured tasks
- ✅ User satisfaction >80% for open-ended exploration
- ✅ Integration success 100% with existing tools (auth, search, files)
- ✅ Error recovery >90% graceful handling
- ✅ Context sharing works seamlessly
- ✅ Vision API costs within acceptable range (<$0.50 per typical task)

### Option B (browser-use Integration)
- ✅ Installation success >95%
- ✅ Speed improvement >30% vs Option A for simple tasks
- ✅ Reliability >90% for structured tasks
- ✅ Clear user understanding when to use which option
- ✅ Graceful coexistence with Option A (no conflicts)

---

## Decision Points

### Already Resolved:
1. **Which option to implement first?** → Option A (custom vision-based)
2. **Should we support both options?** → Yes, complementary strengths
3. **Authentication integration?** → Option A only (tight integration required)
4. **Single vs multiple agent frameworks?** → Prefer single (pydantic-ai), Option B is specialized sub-agent

### To Be Resolved During Implementation:
1. Optimal max_steps default for different task types
2. Vision prompt templates for best accuracy/cost balance
3. When to automatically choose Option A vs Option B
4. Whether to implement Phase 7 features (long-term)
5. Production hardening priorities (Phase 8)

---

## Success Metrics

### Phase 1 Success:
- ✅ Users can fetch specific URLs directly
- ✅ Content is LLM-friendly (markdown)
- ✅ Smart truncation preserves key information
- ✅ No regression in existing features

### Phase 2 Success:
- ✅ Cache hit rate > 80%
- ✅ Average fetch time < 3s (with cache)
- ✅ Automatic cleanup works reliably
- ✅ Cache size stays under 100MB

### Phase 3 Success:
- ✅ Users can manage cache easily
- ✅ Preferences persist across sessions
- ✅ CLI commands work intuitively
- ✅ Export/import works correctly

---

## Version History

| Version | Phase | Status | Release Date |
|---------|-------|--------|--------------|
| v0.3.24 | Phase 1 | ✅ Complete | 2025-01-11 |
| v0.3.24 | Phase 2 | ✅ Complete (2 optional items remain) | 2025-01-11 |
| v0.3.24 | Phase 3 | ⚠️ Partially Complete (core tools done) | 2025-01-11 |
| v0.3.40 | Phase 4.1 + 4.2 | ✅ Complete (Auth + Sessions) | 2025-11-13 |
| v0.3.41 | Phase 4.3 | ✅ Complete (Authenticated Fetch) | 2025-11-13 |
| v0.3.42 | Phase 4.4 | ✅ Complete (Enhanced Form Detection) | 2025-11-13 |
| v0.3.43 | Phase 4.4 Docs | ✅ Complete (Use Case 26 + Docs) | 2025-11-13 |
| v0.3.44 | Phase 4.5 | 📋 Planned (LLM-Powered Analysis) | TBD |
| v0.3.44 | Phase 4.6 | 📋 Planned (Interactive Browser) | TBD |
| v0.3.25+ | Phase 3 (full) | Planned (CLI commands, prompts) | TBD |
| v0.3.27+ | Phase 5-6 | Future | TBD |

---

## Questions & Decisions

### Resolved:
1. **Which library?** → crawl4ai (LLM-optimized)
2. **Storage strategy?** → TTL cache (30 min)
3. **Truncation?** → Smart, configurable max tokens
4. **Dependencies?** → Acceptable (~200MB for browser)

### Open:
1. Should we support PDF extraction? (Future)
2. Should we integrate with existing vector DBs? (Future)
3. Should we support JavaScript execution? (Already supported via crawl4ai)
4. ~~Should we support authentication (login)?~~ → **Resolved: Yes, v0.3.40 (Phase 4)**

---

## Resources

### Documentation:
- crawl4ai docs: https://docs.crawl4ai.com/
- Playwright docs: https://playwright.dev/python/
- HTML to Markdown: https://pypi.org/project/markdownify/

### Examples:
- crawl4ai quickstart: https://docs.crawl4ai.com/core/quickstart/
- Playwright scraping: https://scrapfly.io/blog/posts/web-scraping-with-playwright-and-python

---

**Last Updated:** 2025-11-11
**Maintained By:** WYN360 Development Team
