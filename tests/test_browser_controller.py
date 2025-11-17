"""Tests for BrowserController class."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from wyn360_cli.browser_controller import BrowserController, BrowserControllerError


class TestBrowserControllerInitialization:
    """Test browser initialization and cleanup."""

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_initialize_success(self, mock_playwright):
        """Test successful browser initialization."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        # Test
        controller = BrowserController()
        await controller.initialize(headless=True, viewport_size=(1024, 768))

        # Verify
        assert controller._initialized is True
        assert controller.browser is not None
        assert controller.page is not None
        mock_pw_instance.chromium.launch.assert_called_once()
        mock_page.set_default_timeout.assert_called_once_with(30000)

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_initialize_already_initialized(self, mock_playwright):
        """Test initialization when already initialized."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Call initialize again
        await controller.initialize()

        # Should only launch once
        assert mock_pw_instance.chromium.launch.call_count == 1

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_cleanup(self, mock_playwright):
        """Test browser cleanup."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Cleanup
        await controller.cleanup()

        # Verify
        assert controller._initialized is False
        assert controller.page is None
        assert controller.browser is None
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_pw_instance.stop.assert_called_once()

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_context_manager(self, mock_playwright):
        """Test async context manager."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        # Test context manager
        async with BrowserController() as controller:
            assert controller._initialized is True

        # Verify cleanup was called
        mock_page.close.assert_called_once()


class TestBrowserNavigation:
    """Test browser navigation."""

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_navigate_success(self, mock_playwright):
        """Test successful navigation."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()
        mock_page.goto = AsyncMock()

        controller = BrowserController()
        await controller.initialize()

        # Navigate
        await controller.navigate("https://example.com")

        # Verify
        mock_page.goto.assert_called_once_with("https://example.com", wait_until='networkidle')

    @pytest.mark.asyncio
    async def test_navigate_not_initialized(self):
        """Test navigation without initialization."""
        controller = BrowserController()

        with pytest.raises(BrowserControllerError, match="not initialized"):
            await controller.navigate("https://example.com")


class TestBrowserActions:
    """Test browser action execution."""

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_action_click(self, mock_playwright):
        """Test click action."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()
        mock_page.click = AsyncMock()

        controller = BrowserController()
        await controller.initialize()

        # Execute click action
        result = await controller.execute_action({
            'type': 'click',
            'selector': '#submit-btn'
        })

        # Verify
        assert result['success'] is True
        assert result['action'] == 'click'
        mock_page.click.assert_called_once_with('#submit-btn', timeout=5000)

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_action_type(self, mock_playwright):
        """Test type action."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()
        mock_page.fill = AsyncMock()
        mock_page.type = AsyncMock()

        controller = BrowserController()
        await controller.initialize()

        # Execute type action
        result = await controller.execute_action({
            'type': 'type',
            'selector': '#search',
            'text': 'test query'
        })

        # Verify
        assert result['success'] is True
        assert result['action'] == 'type'
        mock_page.fill.assert_called_once_with('#search', '')  # Clear first
        mock_page.type.assert_called_once_with('#search', 'test query', delay=50)

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_action_scroll(self, mock_playwright):
        """Test scroll action."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()
        mock_page.evaluate = AsyncMock()

        controller = BrowserController()
        await controller.initialize()

        # Execute scroll action
        result = await controller.execute_action({
            'type': 'scroll',
            'direction': 'down',
            'amount': 500
        })

        # Verify
        assert result['success'] is True
        assert result['action'] == 'scroll'
        mock_page.evaluate.assert_called_once_with("window.scrollBy(0, 500)")

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_action_extract(self, mock_playwright):
        """Test extract action."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text = AsyncMock(return_value="Test Text")

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()
        mock_page.query_selector_all = AsyncMock(return_value=[mock_element])

        controller = BrowserController()
        await controller.initialize()

        # Execute extract action
        result = await controller.execute_action({
            'type': 'extract',
            'selector': '.product-price'
        })

        # Verify
        assert result['success'] is True
        assert result['action'] == 'extract'
        assert len(result['data']) == 1
        assert result['data'][0] == "Test Text"

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_action_wait(self, mock_playwright):
        """Test wait action."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Execute wait action
        result = await controller.execute_action({
            'type': 'wait',
            'seconds': 1
        })

        # Verify
        assert result['success'] is True
        assert result['action'] == 'wait'

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_action_unknown(self, mock_playwright):
        """Test unknown action type."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Execute unknown action
        result = await controller.execute_action({
            'type': 'unknown_action'
        })

        # Verify error is returned in result
        assert result['success'] is False
        assert 'error' in result


class TestBrowserScreenshot:
    """Test screenshot capture."""

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_take_screenshot(self, mock_playwright):
        """Test screenshot capture."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b'fake_screenshot_data')

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Take screenshot
        screenshot = await controller.take_screenshot()

        # Verify
        assert screenshot == b'fake_screenshot_data'
        mock_page.screenshot.assert_called_once_with(type='png', full_page=False)

    @pytest.mark.asyncio
    async def test_take_screenshot_not_initialized(self):
        """Test screenshot without initialization."""
        controller = BrowserController()

        with pytest.raises(BrowserControllerError, match="not initialized"):
            await controller.take_screenshot()


class TestBrowserPageState:
    """Test page state extraction."""

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_get_page_state(self, mock_playwright):
        """Test page state extraction."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Example Page")
        mock_page.evaluate = AsyncMock(return_value="complete")

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Get page state
        state = await controller.get_page_state()

        # Verify
        assert state['url'] == "https://example.com"
        assert state['title'] == "Example Page"
        assert state['ready_state'] == "complete"
        assert state['loaded'] is True


class TestBrowserElementFinding:
    """Test element finding strategies."""

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_find_element_by_selector(self, mock_playwright):
        """Test finding element by CSS selector."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_element = Mock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Find element
        element = await controller.find_element('selector', '#test-element')

        # Verify
        assert element == mock_element
        mock_page.query_selector.assert_called_once_with('#test-element')

    @pytest.mark.asyncio
    @patch('wyn360_cli.browser_controller.HAS_PLAYWRIGHT', True)
    @patch('wyn360_cli.browser_controller.async_playwright')
    async def test_find_element_by_xpath(self, mock_playwright):
        """Test finding element by XPath."""
        # Setup mocks
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_element = Mock()
        mock_page.query_selector_all = AsyncMock(return_value=[mock_element])

        mock_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.set_default_timeout = Mock()

        controller = BrowserController()
        await controller.initialize()

        # Find element
        element = await controller.find_element('xpath', '//div[@id="test"]')

        # Verify
        assert element == mock_element
        mock_page.query_selector_all.assert_called_once_with('xpath=//div[@id="test"]')
