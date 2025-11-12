"""Browser use functionality for WYN360 CLI.

This module provides website fetching and caching capabilities using crawl4ai.
Phase 12.1: Basic fetching with smart truncation
Phase 12.2: TTL-based caching
Phase 12.3: User-controlled persistent storage
"""

import hashlib
import gzip
import json
import time
import re
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

# crawl4ai is optional - only available if installed
try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False
    AsyncWebCrawler = None


class WebsiteCache:
    """TTL-based cache for fetched websites (Phase 12.2)."""

    def __init__(self, cache_dir: Path, ttl: int = 1800, max_size_mb: int = 100):
        """
        Initialize the website cache.

        Args:
            cache_dir: Directory to store cached content
            ttl: Time to live in seconds (default 30 minutes)
            max_size_mb: Maximum cache size in MB
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.max_size_mb = max_size_mb
        self.index_file = cache_dir / "cache_index.json"

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load or create index
        self.index = self._load_index()

    def _load_index(self) -> dict:
        """Load the cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_index(self):
        """Save the cache index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache index: {e}")

    def _get_cache_key(self, url: str) -> str:
        """Generate a cache key from URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry is expired."""
        return (time.time() - timestamp) > self.ttl

    async def get(self, url: str) -> Optional[str]:
        """
        Get cached content if available and not expired.

        Args:
            url: URL to fetch from cache

        Returns:
            Cached markdown content, or None if not found/expired
        """
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.md.gz"

        # Check if cached
        if cache_key not in self.index:
            return None

        entry = self.index[cache_key]

        # Check if expired
        if self._is_expired(entry['timestamp']):
            # Remove expired entry
            self._remove_entry(cache_key)
            return None

        # Read cached content
        try:
            if cache_file.exists():
                with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Warning: Failed to read cache: {e}")
            self._remove_entry(cache_key)

        return None

    async def set(self, url: str, content: str):
        """
        Cache content with TTL.

        Args:
            url: URL being cached
            content: Markdown content to cache
        """
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.md.gz"

        # Check cache size before adding
        await self._cleanup_if_needed()

        # Write compressed content
        try:
            with gzip.open(cache_file, 'wt', encoding='utf-8') as f:
                f.write(content)

            # Update index
            self.index[cache_key] = {
                'url': url,
                'timestamp': time.time(),
                'size': cache_file.stat().st_size
            }
            self._save_index()

        except Exception as e:
            print(f"Warning: Failed to cache content: {e}")

    def _remove_entry(self, cache_key: str):
        """Remove a cache entry."""
        cache_file = self.cache_dir / f"{cache_key}.md.gz"
        if cache_file.exists():
            cache_file.unlink()
        if cache_key in self.index:
            del self.index[cache_key]
            self._save_index()

    async def _cleanup_if_needed(self):
        """Clean up cache if it exceeds max size."""
        # Calculate total cache size
        total_size_bytes = sum(entry['size'] for entry in self.index.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size_bytes > max_size_bytes:
            # Remove oldest entries until under limit
            sorted_entries = sorted(
                self.index.items(),
                key=lambda x: x[1]['timestamp']
            )

            for cache_key, _ in sorted_entries:
                if total_size_bytes <= max_size_bytes:
                    break
                entry = self.index[cache_key]
                total_size_bytes -= entry['size']
                self._remove_entry(cache_key)

    async def cleanup_expired(self):
        """Remove all expired cache entries."""
        expired_keys = [
            key for key, entry in self.index.items()
            if self._is_expired(entry['timestamp'])
        ]

        for key in expired_keys:
            self._remove_entry(key)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_size_bytes = sum(entry['size'] for entry in self.index.values())
        total_entries = len(self.index)
        expired_count = sum(
            1 for entry in self.index.values()
            if self._is_expired(entry['timestamp'])
        )

        return {
            'total_entries': total_entries,
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2),
            'expired_entries': expired_count,
            'cache_dir': str(self.cache_dir)
        }

    async def clear(self, url: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            url: Specific URL to clear, or None to clear all
        """
        if url:
            # Clear specific URL
            cache_key = self._get_cache_key(url)
            self._remove_entry(cache_key)
        else:
            # Clear all
            for cache_key in list(self.index.keys()):
                self._remove_entry(cache_key)


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.

    Args:
        url: String to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception:
        return False


def count_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses rough approximation: 1 token ≈ 4 characters.

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def smart_truncate(markdown: str, max_tokens: int) -> Tuple[str, bool]:
    """
    Intelligently truncate markdown content.

    Strategy:
    1. Keep full content if under max_tokens
    2. Preserve document structure (headers)
    3. Keep first 70% and last 30% of tokens
    4. Add truncation marker

    Args:
        markdown: Markdown content to truncate
        max_tokens: Maximum tokens to keep

    Returns:
        Tuple of (truncated_content, was_truncated)
    """
    current_tokens = count_tokens(markdown)

    if current_tokens <= max_tokens:
        return markdown, False

    # Split into lines
    lines = markdown.split('\n')

    # Calculate how many chars we can keep
    max_chars = max_tokens * 4

    # Keep first 70% and last 30%
    first_chars = int(max_chars * 0.7)
    last_chars = int(max_chars * 0.3)

    # Find good breaking points (preferably at headers or paragraphs)
    def find_break_point(text: str, target_pos: int, direction: str = 'forward') -> int:
        """Find a good place to break text (at header or paragraph)."""
        # Look for headers first
        header_pattern = r'\n#{1,6}\s'
        matches = list(re.finditer(header_pattern, text))

        if direction == 'forward':
            # Find first header after target
            for match in matches:
                if match.start() >= target_pos:
                    return match.start()
        else:
            # Find last header before target
            for match in reversed(matches):
                if match.start() <= target_pos:
                    return match.start()

        # If no header found, look for paragraph break
        para_pattern = r'\n\n'
        matches = list(re.finditer(para_pattern, text))

        if direction == 'forward':
            for match in matches:
                if match.start() >= target_pos:
                    return match.start()
        else:
            for match in reversed(matches):
                if match.start() <= target_pos:
                    return match.start()

        # If nothing found, use target position
        return target_pos

    # Find breaking points
    first_break = find_break_point(markdown, first_chars, 'forward')
    last_break = find_break_point(markdown, len(markdown) - last_chars, 'backward')

    # Extract sections
    first_section = markdown[:first_break].rstrip()
    last_section = markdown[last_break:].lstrip()

    # Combine with truncation marker
    truncation_marker = f"\n\n---\n**[Content truncated - Original: {current_tokens:,} tokens, Showing: ~{max_tokens:,} tokens]**\n---\n\n"

    truncated = first_section + truncation_marker + last_section

    return truncated, True


async def fetch_website_content(
    url: str,
    max_tokens: int = 50000,
    truncate_strategy: str = "smart"
) -> Tuple[bool, str]:
    """
    Fetch website content and convert to markdown.

    Args:
        url: URL to fetch
        max_tokens: Maximum tokens to return
        truncate_strategy: How to truncate (smart, head, tail)

    Returns:
        Tuple of (success, content_or_error_message)
    """
    if not HAS_CRAWL4AI:
        return False, "❌ crawl4ai is not installed. Install with: pip install crawl4ai"

    if not is_valid_url(url):
        return False, f"❌ Invalid URL: {url}"

    try:
        # Fetch website using crawl4ai
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url)

            if not result.success:
                return False, f"❌ Failed to fetch website: {result.error_message or 'Unknown error'}"

            # Get markdown content
            markdown = result.markdown

            if not markdown or markdown.strip() == "":
                return False, "❌ No content extracted from website"

            # Apply truncation
            if truncate_strategy == "smart":
                truncated, was_truncated = smart_truncate(markdown, max_tokens)
            elif truncate_strategy == "head":
                # Keep first N tokens
                max_chars = max_tokens * 4
                truncated = markdown[:max_chars]
                was_truncated = len(markdown) > max_chars
                if was_truncated:
                    truncated += f"\n\n---\n**[Content truncated]**\n---\n"
            elif truncate_strategy == "tail":
                # Keep last N tokens
                max_chars = max_tokens * 4
                truncated = markdown[-max_chars:]
                was_truncated = len(markdown) > max_chars
                if was_truncated:
                    truncated = f"---\n**[Content truncated]**\n---\n\n" + truncated
            else:
                # No truncation
                truncated = markdown
                was_truncated = False

            return True, truncated

    except Exception as e:
        return False, f"❌ Error fetching website: {str(e)}"
