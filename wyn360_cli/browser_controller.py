"""
Browser Controller for autonomous browser automation.

This module provides pure browser automation using Playwright (no AI).
Responsible for: browser lifecycle, action execution, screenshot capture.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, ElementHandle, TimeoutError as PlaywrightTimeoutError
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    # Playwright types for type hints (will be None if not installed)
    Browser = Any
    BrowserContext = Any
    Page = Any
    ElementHandle = Any
    PlaywrightTimeoutError = TimeoutError


logger = logging.getLogger(__name__)


class BrowserControllerError(Exception):
    """Base exception for BrowserController errors."""
    pass


class BrowserController:
    """
    Pure browser automation using Playwright (no AI).

    Responsible for:
    - Browser lifecycle management (launch, navigate, close)
    - Action execution (click, type, scroll, navigate, wait)
    - Screenshot capture (optimized for Claude Vision API)
    - Element location (CSS selectors, XPath, text-based, fuzzy matching)
    - Error handling and retry logic
    - Resource cleanup and timeout management
    """

    def __init__(self):
        """Initialize BrowserController."""
        if not HAS_PLAYWRIGHT:
            raise ImportError(
                "Playwright is required for browser automation.\n"
                "Install with: playwright install chromium"
            )

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False

    async def initialize(
        self,
        headless: bool = False,
        viewport_size: Tuple[int, int] = (1024, 768)
    ) -> None:
        """
        Launch browser with optimal settings for vision analysis.

        Args:
            headless: Run browser in headless mode (default: False for visibility)
            viewport_size: Browser viewport dimensions (default: 1024x768 XGA - optimal for vision API)

        Raises:
            BrowserControllerError: If browser initialization fails
        """
        if self._initialized:
            logger.warning("Browser already initialized")
            return

        try:
            logger.info(f"Initializing browser (headless={headless}, viewport={viewport_size})")

            # Launch Playwright
            self.playwright = await async_playwright().start()

            # Launch Chromium browser
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',  # Avoid detection
                    '--no-sandbox',  # Required for some environments
                ]
            )

            # Create browser context
            self.context = await self.browser.new_context(
                viewport={'width': viewport_size[0], 'height': viewport_size[1]},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            )

            # Create new page
            self.page = await self.context.new_page()

            # Set default timeout (30 seconds)
            self.page.set_default_timeout(30000)

            self._initialized = True
            logger.info("Browser initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.cleanup()
            raise BrowserControllerError(f"Browser initialization failed: {e}")

    async def navigate(self, url: str, wait_until: str = 'networkidle') -> None:
        """
        Navigate to URL with smart waiting.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
                       ('load', 'domcontentloaded', 'networkidle', 'commit')

        Raises:
            BrowserControllerError: If navigation fails
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until)

            # Additional wait for JavaScript rendering
            await asyncio.sleep(1)

            logger.info(f"Navigation complete: {url}")

        except PlaywrightTimeoutError:
            raise BrowserControllerError(f"Navigation timeout: {url}")
        except Exception as e:
            raise BrowserControllerError(f"Navigation failed: {e}")

    async def take_screenshot(self, optimize_for_vision: bool = True) -> bytes:
        """
        Capture screenshot optimized for Claude Vision.

        Args:
            optimize_for_vision: Optimize screenshot for vision API (default: True)
                                - Resolution: 1024x768 (XGA - optimal for vision API)
                                - Format: PNG
                                - Compression: Balanced for quality vs size

        Returns:
            Screenshot as bytes (PNG format)

        Raises:
            BrowserControllerError: If screenshot capture fails
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        try:
            logger.debug("Capturing screenshot")

            screenshot_bytes = await self.page.screenshot(
                type='png',
                full_page=False  # Only visible viewport (better for vision analysis)
            )

            logger.debug(f"Screenshot captured ({len(screenshot_bytes)} bytes)")
            return screenshot_bytes

        except Exception as e:
            raise BrowserControllerError(f"Screenshot capture failed: {e}")

    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute browser action from parsed decision.

        Supported actions:
          - click: {type: 'click', selector: '#btn', text: 'Submit'}
          - type: {type: 'type', selector: '#search', text: 'sneakers'}
          - scroll: {type: 'scroll', direction: 'down', amount: 500}
          - navigate: {type: 'navigate', url: 'https://...'}
          - extract: {type: 'extract', selector: '.price'}
          - wait: {type: 'wait', seconds: 2}

        Args:
            action: Action dictionary with type and parameters

        Returns:
            Result dictionary with success status and data

        Raises:
            BrowserControllerError: If action execution fails
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        action_type = action.get('type')

        try:
            if action_type == 'click':
                return await self._action_click(action)

            elif action_type == 'type':
                return await self._action_type(action)

            elif action_type == 'scroll':
                return await self._action_scroll(action)

            elif action_type == 'navigate':
                return await self._action_navigate(action)

            elif action_type == 'extract':
                return await self._action_extract(action)

            elif action_type == 'wait':
                return await self._action_wait(action)

            else:
                raise BrowserControllerError(f"Unknown action type: {action_type}")

        except Exception as e:
            logger.error(f"Action execution failed: {action_type} - {e}")
            return {
                'success': False,
                'error': str(e),
                'action': action
            }

    async def _action_click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute click action."""
        selector = action.get('selector')
        text = action.get('text')

        try:
            if selector:
                # Click by selector
                await self.page.click(selector, timeout=5000)
                logger.info(f"Clicked element: {selector}")
            elif text:
                # Click by text
                element = await self.page.get_by_text(text).first.click(timeout=5000)
                logger.info(f"Clicked element with text: {text}")
            else:
                raise ValueError("Click action requires 'selector' or 'text'")

            # Wait for any resulting navigation/changes
            await asyncio.sleep(1)

            return {'success': True, 'action': 'click', 'target': selector or text}

        except PlaywrightTimeoutError:
            raise BrowserControllerError(f"Click timeout: {selector or text}")

    async def _action_type(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute type action."""
        selector = action.get('selector')
        text = action.get('text', '')
        clear_first = action.get('clear', True)

        try:
            if not selector:
                raise ValueError("Type action requires 'selector'")

            if clear_first:
                # Clear existing text first
                await self.page.fill(selector, '')

            # Type text
            await self.page.type(selector, text, delay=50)  # Realistic typing speed
            logger.info(f"Typed into {selector}: {text}")

            # Small delay for any auto-complete/suggestions
            await asyncio.sleep(0.5)

            return {'success': True, 'action': 'type', 'selector': selector, 'text': text}

        except PlaywrightTimeoutError:
            raise BrowserControllerError(f"Type timeout: {selector}")

    async def _action_scroll(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scroll action."""
        direction = action.get('direction', 'down')
        amount = action.get('amount', 500)

        try:
            if direction == 'down':
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == 'up':
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == 'top':
                await self.page.evaluate("window.scrollTo(0, 0)")
            elif direction == 'bottom':
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            logger.info(f"Scrolled {direction} by {amount}px")

            # Wait for any lazy-loaded content
            await asyncio.sleep(1)

            return {'success': True, 'action': 'scroll', 'direction': direction, 'amount': amount}

        except Exception as e:
            raise BrowserControllerError(f"Scroll failed: {e}")

    async def _action_navigate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute navigate action."""
        url = action.get('url')

        if not url:
            raise ValueError("Navigate action requires 'url'")

        await self.navigate(url)
        return {'success': True, 'action': 'navigate', 'url': url}

    async def _action_extract(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute extract action to get text from elements."""
        selector = action.get('selector')

        try:
            if not selector:
                raise ValueError("Extract action requires 'selector'")

            # Get all matching elements
            elements = await self.page.query_selector_all(selector)

            # Extract text from each element
            extracted_data = []
            for element in elements[:10]:  # Limit to first 10 elements
                text = await element.inner_text()
                extracted_data.append(text.strip())

            logger.info(f"Extracted {len(extracted_data)} items from {selector}")

            return {
                'success': True,
                'action': 'extract',
                'selector': selector,
                'data': extracted_data
            }

        except PlaywrightTimeoutError:
            raise BrowserControllerError(f"Extract timeout: {selector}")

    async def _action_wait(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wait action."""
        seconds = action.get('seconds', 1)

        await asyncio.sleep(seconds)
        logger.info(f"Waited {seconds} seconds")

        return {'success': True, 'action': 'wait', 'seconds': seconds}

    async def find_element(
        self,
        strategy: str,
        value: str
    ) -> Optional[ElementHandle]:
        """
        Find element using various strategies.

        Args:
            strategy: Search strategy ('selector', 'xpath', 'text', 'fuzzy')
            value: Search value (selector, xpath expression, or text)

        Returns:
            ElementHandle if found, None otherwise

        Raises:
            BrowserControllerError: If search fails
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        try:
            if strategy == 'selector':
                # CSS selector
                return await self.page.query_selector(value)

            elif strategy == 'xpath':
                # XPath expression
                elements = await self.page.query_selector_all(f"xpath={value}")
                return elements[0] if elements else None

            elif strategy == 'text':
                # Exact text match
                element = self.page.get_by_text(value, exact=True)
                return await element.element_handle() if await element.count() > 0 else None

            elif strategy == 'fuzzy':
                # Partial text match
                element = self.page.get_by_text(value, exact=False)
                return await element.element_handle() if await element.count() > 0 else None

            else:
                raise ValueError(f"Unknown search strategy: {strategy}")

        except Exception as e:
            logger.error(f"Element search failed ({strategy}={value}): {e}")
            return None

    async def get_page_state(self) -> Dict[str, Any]:
        """
        Extract current page metadata.

        Returns:
            Dictionary with page state information

        Raises:
            BrowserControllerError: If page state extraction fails
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        try:
            url = self.page.url
            title = await self.page.title()

            # Check if page is loaded
            ready_state = await self.page.evaluate("document.readyState")

            return {
                'url': url,
                'title': title,
                'ready_state': ready_state,
                'loaded': ready_state == 'complete'
            }

        except Exception as e:
            raise BrowserControllerError(f"Failed to get page state: {e}")

    async def cleanup(self) -> None:
        """
        Close browser and cleanup resources.

        This method is safe to call multiple times.
        """
        logger.info("Cleaning up browser resources")

        try:
            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self._initialized = False
            logger.info("Browser cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
