"""
Unit tests for Unified Browser Manager

Tests the unified browser management system that coordinates Playwright
instances across all automation approaches (DOM, Stagehand, Vision).
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.wyn360.tools.browser.browser_manager import UnifiedBrowserManager, browser_manager


class TestUnifiedBrowserManager:
    """Test unified browser manager functionality"""

    def setup_method(self):
        """Reset browser manager state before each test"""
        # Create a fresh instance for testing
        self.manager = UnifiedBrowserManager()
        # Reset any existing state
        self.manager.browser = None
        self.manager.playwright = None
        self.manager.contexts = {}
        self.manager.pages = {}

    def test_singleton_pattern(self):
        """Test that UnifiedBrowserManager follows singleton pattern"""
        manager1 = UnifiedBrowserManager()
        manager2 = UnifiedBrowserManager()

        assert manager1 is manager2
        assert id(manager1) == id(manager2)

    @pytest.mark.asyncio
    async def test_initialize_browser_settings(self):
        """Test browser initialization with various settings"""
        # Test that initialization sets the correct internal state
        with patch.object(self.manager, 'playwright', None):
            with patch.object(self.manager, 'browser', None):
                # Mock the async playwright and browser initialization
                with patch('src.wyn360.tools.browser.browser_manager.async_playwright') as mock_pw:
                    mock_playwright_instance = AsyncMock()
                    mock_browser = AsyncMock()
                    mock_pw.return_value.start = AsyncMock(return_value=mock_playwright_instance)
                    mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

                    await self.manager.initialize(headless=True, viewport={'width': 1024, 'height': 768})

                    assert self.manager.headless is True
                    assert self.manager.viewport == {'width': 1024, 'height': 768}

    def test_is_initialized_false(self):
        """Test is_initialized returns False when browser not initialized"""
        assert self.manager.is_initialized() is False

    def test_is_initialized_true(self):
        """Test is_initialized returns True when browser is ready"""
        mock_browser = Mock()
        mock_browser.is_closed = False
        self.manager.browser = mock_browser

        assert self.manager.is_initialized() is True

    def test_is_initialized_false_when_closed(self):
        """Test is_initialized returns False when browser is closed"""
        mock_browser = Mock()
        mock_browser.is_closed = True
        self.manager.browser = mock_browser

        assert self.manager.is_initialized() is False

    @pytest.mark.asyncio
    async def test_get_browser_info(self):
        """Test getting browser state information"""
        # Set up some state
        self.manager.headless = True
        self.manager.viewport = {'width': 1024, 'height': 768}
        self.manager.contexts['test'] = Mock()
        self.manager.pages['test:page1'] = Mock()
        self.manager.pages['test:page2'] = Mock()

        info = await self.manager.get_browser_info()

        assert info['headless'] is True
        assert info['viewport'] == {'width': 1024, 'height': 768}
        assert info['contexts'] == ['test']
        assert 'test:page1' in info['pages']
        assert 'test:page2' in info['pages']
        assert info['contexts_count'] == 1
        assert info['pages_count'] == 2

    @pytest.mark.asyncio
    async def test_close_page(self):
        """Test closing a specific page"""
        mock_page = AsyncMock()
        self.manager.pages['default:test'] = mock_page

        await self.manager.close_page("test", "default")

        # Verify page was closed and removed
        mock_page.close.assert_called_once()
        assert 'default:test' not in self.manager.pages

    @pytest.mark.asyncio
    async def test_close_context(self):
        """Test closing a specific context and its pages"""
        mock_context = AsyncMock()
        mock_page1 = AsyncMock()
        mock_page2 = AsyncMock()

        self.manager.contexts['test'] = mock_context
        self.manager.pages['test:page1'] = mock_page1
        self.manager.pages['test:page2'] = mock_page2
        self.manager.pages['other:page'] = AsyncMock()  # Different context

        await self.manager.close_context("test")

        # Verify pages in the context were closed
        mock_page1.close.assert_called_once()
        mock_page2.close.assert_called_once()

        # Verify context was closed
        mock_context.close.assert_called_once()

        # Verify cleanup
        assert 'test' not in self.manager.contexts
        assert 'test:page1' not in self.manager.pages
        assert 'test:page2' not in self.manager.pages
        assert 'other:page' in self.manager.pages  # Other context unaffected

    @pytest.mark.asyncio
    async def test_close_all_resources(self):
        """Test closing all browser resources"""
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        mock_page = AsyncMock()
        mock_context = AsyncMock()

        self.manager.browser = mock_browser
        self.manager.playwright = mock_playwright
        self.manager.pages['test:page'] = mock_page
        self.manager.contexts['test'] = mock_context

        await self.manager.close()

        # Verify all resources were cleaned up
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()

        # Verify state was reset
        assert self.manager.browser is None
        assert self.manager.playwright is None
        assert len(self.manager.pages) == 0
        assert len(self.manager.contexts) == 0

    def test_browser_manager_global_instance(self):
        """Test that the global browser_manager is accessible"""
        from src.wyn360.tools.browser.browser_manager import browser_manager

        assert browser_manager is not None
        assert isinstance(browser_manager, UnifiedBrowserManager)

    @pytest.mark.asyncio
    async def test_get_context_with_mocked_browser(self):
        """Test get_context with mocked browser"""
        # Set up a mock browser
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context

        self.manager.browser = mock_browser

        context = await self.manager.get_context("test")

        assert context == mock_context
        assert 'test' in self.manager.contexts
        mock_browser.new_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_page_with_mocked_context(self):
        """Test get_page with mocked context"""
        # Set up mocks
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context

        self.manager.browser = mock_browser

        page = await self.manager.get_page("test_page", "test_context")

        assert page == mock_page
        assert 'test_context:test_page' in self.manager.pages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])