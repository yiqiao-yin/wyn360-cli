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
- [ ] Add crawl4ai dependency to pyproject.toml
- [ ] Implement `fetch_website(url)` tool in agent.py
- [ ] Add URL detection logic in system prompt
- [ ] Implement smart content truncation
- [ ] Store fetched content in agent context (in-memory)
- [ ] Update documentation (README.md, SYSTEM.md, USE_CASES.md)
- [ ] Add error handling for failed fetches
- [ ] Test with various URL types (GitHub, docs, blogs)

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
- [ ] Create cache directory structure (~/.wyn360/cache/fetched_sites/)
- [ ] Implement TTL-based cache system
- [ ] Add cache key generation (URL hash)
- [ ] Store cached content as gzipped markdown
- [ ] Implement automatic cleanup on cache read
- [ ] Add cache statistics tracking
- [ ] Implement cache warming (prefetch common URLs)
- [ ] Add cache hit/miss metrics
- [ ] Update config with cache settings

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

**Version:** v0.3.25
**Status:** Planned
**ETA:** Next session

---

### Phase 3: User-Controlled Storage (v0.3.26)

**Goal:** Give users control over cache persistence and management

#### Tasks:
- [ ] Implement user prompt for cache preferences
- [ ] Add persistent storage option
- [ ] Create `/clear-cache` command
- [ ] Create `/show-cache` command (statistics)
- [ ] Add cache preference persistence
- [ ] Implement selective cache clearing
- [ ] Add cache export feature
- [ ] Create cache viewer tool
- [ ] Update CLI with cache management commands

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

**Version:** v0.3.26
**Status:** Planned
**ETA:** Future session

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
| v0.3.24 | Phase 1 | In Progress | TBD |
| v0.3.25 | Phase 2 | Planned | TBD |
| v0.3.26 | Phase 3 | Planned | TBD |
| v0.3.27+ | Phase 4-6 | Future | TBD |

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
4. Should we support authentication (login)? (Future)

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
