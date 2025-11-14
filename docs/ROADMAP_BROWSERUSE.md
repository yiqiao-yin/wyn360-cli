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

## Future Enhancements (Post v0.3.26)

### Phase 4: Advanced Features
- PDF extraction support
- Screenshot capture
- Interactive element detection
- Form auto-fill capabilities
- Multi-page crawling (follow links)

### Phase 5: Integration
- Integration with vector databases (for RAG)
- Semantic search over cached content
- Automatic summarization of fetched pages
- Content diff tracking (detect page changes)

### Phase 6: Performance
- Parallel fetching (multiple URLs)
- Browser instance pooling
- Pre-fetching predicted URLs
- Distributed caching

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
