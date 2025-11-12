"""
Unit tests for browser_use module (Phase 12.1, 12.2, 12.3)

Tests cover:
- URL validation
- Token counting and truncation
- WebsiteCache functionality
- fetch_website_content integration
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from wyn360_cli.browser_use import (
    is_valid_url,
    count_tokens,
    smart_truncate,
    WebsiteCache,
    fetch_website_content,
    check_playwright_installed,
    HAS_CRAWL4AI
)


class TestURLValidation:
    """Test URL validation function"""

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are recognized"""
        assert is_valid_url("http://example.com") is True

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are recognized"""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("https://github.com/user/repo") is True

    def test_invalid_url_no_scheme(self):
        """Test that URLs without scheme are invalid"""
        assert is_valid_url("example.com") is False

    def test_invalid_url_wrong_scheme(self):
        """Test that URLs with wrong scheme are invalid"""
        assert is_valid_url("ftp://example.com") is False

    def test_invalid_url_malformed(self):
        """Test that malformed URLs are invalid"""
        assert is_valid_url("not a url") is False
        assert is_valid_url("") is False


class TestTokenCounting:
    """Test token counting and truncation functions"""

    def test_count_tokens_basic(self):
        """Test basic token counting (4 chars = 1 token)"""
        text = "a" * 100  # 100 characters
        assert count_tokens(text) == 25  # 100 / 4 = 25 tokens

    def test_count_tokens_empty(self):
        """Test token counting with empty string"""
        assert count_tokens("") == 0

    def test_smart_truncate_under_limit(self):
        """Test that content under limit is not truncated"""
        content = "a" * 100  # 25 tokens
        truncated, was_truncated = smart_truncate(content, max_tokens=50)
        assert was_truncated is False
        assert truncated == content

    def test_smart_truncate_over_limit(self):
        """Test that content over limit is truncated"""
        content = "a" * 1000  # 250 tokens
        truncated, was_truncated = smart_truncate(content, max_tokens=100)
        assert was_truncated is True
        assert "[Content truncated" in truncated
        assert len(truncated) < len(content)

    def test_smart_truncate_preserves_structure(self):
        """Test that truncation preserves headers"""
        content = """# Header 1
Some content here

## Header 2
More content

### Header 3
Even more content
""" * 100  # Make it large enough to truncate

        truncated, was_truncated = smart_truncate(content, max_tokens=100)
        assert was_truncated is True
        # Should still have header markers
        assert "#" in truncated


class TestWebsiteCache:
    """Test WebsiteCache functionality (Phase 12.2)"""

    def test_cache_initialization(self):
        """Test cache directory creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = WebsiteCache(cache_dir, ttl=60)
            assert cache.cache_dir.exists()
            assert cache.ttl == 60

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test caching and retrieving content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = WebsiteCache(cache_dir, ttl=3600)

            url = "https://example.com"
            content = "Test content"

            # Set content
            await cache.set(url, content)

            # Get content
            retrieved = await cache.get(url)
            assert retrieved == content

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test that cache entries expire after TTL"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = WebsiteCache(cache_dir, ttl=1)  # 1 second TTL

            url = "https://example.com"
            content = "Test content"

            # Set content
            await cache.set(url, content)

            # Immediately retrieve - should work
            retrieved = await cache.get(url)
            assert retrieved == content

            # Wait for expiration
            time.sleep(2)

            # Should return None (expired)
            retrieved = await cache.get(url)
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_cache_clear_all(self):
        """Test clearing all cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = WebsiteCache(cache_dir, ttl=3600)

            # Add multiple entries
            await cache.set("https://example1.com", "Content 1")
            await cache.set("https://example2.com", "Content 2")

            # Clear all
            await cache.clear()

            # Both should be None
            assert await cache.get("https://example1.com") is None
            assert await cache.get("https://example2.com") is None

    @pytest.mark.asyncio
    async def test_cache_clear_specific(self):
        """Test clearing specific URL from cache"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = WebsiteCache(cache_dir, ttl=3600)

            # Add multiple entries
            await cache.set("https://example1.com", "Content 1")
            await cache.set("https://example2.com", "Content 2")

            # Clear specific URL
            await cache.clear("https://example1.com")

            # First should be None, second should exist
            assert await cache.get("https://example1.com") is None
            assert await cache.get("https://example2.com") == "Content 2"

    def test_cache_get_stats(self):
        """Test cache statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = WebsiteCache(cache_dir, ttl=3600)

            stats = cache.get_stats()
            assert stats['total_entries'] == 0
            assert stats['total_size_mb'] >= 0
            assert 'cache_dir' in stats


class TestPlaywrightCheck:
    """Test Playwright installation checking"""

    @patch('subprocess.run')
    def test_playwright_installed(self, mock_run):
        """Test detection of installed Playwright"""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake playwright cache directory
            home = Path(tmpdir)
            cache_dir = home / ".cache" / "ms-playwright"
            chromium_dir = cache_dir / "chromium-1187"
            chromium_dir.mkdir(parents=True)

            with patch('pathlib.Path.home', return_value=home):
                installed, msg = check_playwright_installed()
                assert installed is True
                assert msg == ""

    @patch('subprocess.run')
    def test_playwright_not_installed(self, mock_run):
        """Test detection of missing Playwright"""
        mock_run.side_effect = FileNotFoundError()

        installed, msg = check_playwright_installed()
        assert installed is False
        assert "not installed" in msg.lower()
        assert "pip install playwright" in msg

    @patch('subprocess.run')
    def test_playwright_browsers_not_installed(self, mock_run):
        """Test detection of Playwright without browser binaries"""
        mock_run.return_value = Mock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            # Create cache dir but no chromium
            cache_dir = home / ".cache" / "ms-playwright"
            cache_dir.mkdir(parents=True)

            with patch('pathlib.Path.home', return_value=home):
                installed, msg = check_playwright_installed()
                assert installed is False
                assert "browser binaries are not installed" in msg
                assert "playwright install chromium" in msg


@pytest.mark.skipif(not HAS_CRAWL4AI, reason="crawl4ai not installed")
class TestFetchWebsiteContent:
    """Test fetch_website_content function (integration tests)"""

    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self):
        """Test fetching with invalid URL"""
        success, content = await fetch_website_content(
            url="not a url",
            max_tokens=5000
        )
        assert success is False
        assert "Invalid URL" in content

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_use.check_playwright_installed')
    async def test_fetch_playwright_not_installed(self, mock_check):
        """Test fetching when Playwright is not installed"""
        mock_check.return_value = (False, "Playwright not installed")

        success, content = await fetch_website_content(
            url="https://example.com",
            max_tokens=5000
        )
        assert success is False
        assert "Playwright" in content

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_use.check_playwright_installed')
    @patch('wyn360_cli.browser_use.AsyncWebCrawler')
    async def test_fetch_successful(self, mock_crawler_class, mock_check):
        """Test successful website fetch"""
        # Mock Playwright check
        mock_check.return_value = (True, "")

        # Mock crawl4ai
        mock_result = Mock()
        mock_result.success = True
        mock_result.markdown = "# Test Content\n\nThis is test content."
        mock_result.error_message = None

        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__.return_value = mock_crawler
        mock_crawler.__aexit__.return_value = None
        mock_crawler_class.return_value = mock_crawler

        success, content = await fetch_website_content(
            url="https://example.com",
            max_tokens=5000
        )

        assert success is True
        assert "Test Content" in content

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_use.check_playwright_installed')
    @patch('wyn360_cli.browser_use.AsyncWebCrawler')
    async def test_fetch_failed(self, mock_crawler_class, mock_check):
        """Test failed website fetch"""
        # Mock Playwright check
        mock_check.return_value = (True, "")

        # Mock crawl4ai failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.error_message = "Connection timeout"

        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__.return_value = mock_crawler
        mock_crawler.__aexit__.return_value = None
        mock_crawler_class.return_value = mock_crawler

        success, content = await fetch_website_content(
            url="https://example.com",
            max_tokens=5000
        )

        assert success is False
        assert "Failed to fetch" in content

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_use.check_playwright_installed')
    @patch('wyn360_cli.browser_use.AsyncWebCrawler')
    async def test_fetch_with_truncation(self, mock_crawler_class, mock_check):
        """Test fetching with content truncation"""
        # Mock Playwright check
        mock_check.return_value = (True, "")

        # Mock crawl4ai with large content
        large_content = "# Big Content\n\n" + ("Some text. " * 10000)
        mock_result = Mock()
        mock_result.success = True
        mock_result.markdown = large_content
        mock_result.error_message = None

        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__.return_value = mock_crawler
        mock_crawler.__aexit__.return_value = None
        mock_crawler_class.return_value = mock_crawler

        success, content = await fetch_website_content(
            url="https://example.com",
            max_tokens=1000  # Small limit to force truncation
        )

        assert success is True
        # Check that truncation happened (marker present or significant reduction)
        # Note: truncation adds marker which may make content slightly longer
        assert ("[Content truncated" in content) or (len(content) < len(large_content) * 0.9)
