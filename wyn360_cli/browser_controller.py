"""
Browser Controller for autonomous browser automation.

This module provides pure browser automation using Playwright (no AI).
Responsible for: browser lifecycle, action execution, screenshot capture.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Import configuration system
from .config import load_config, get_progressive_timeout, get_site_profile

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


class BrowserConfig:
    """
    Configuration for browser automation with enhanced configuration system.

    Provides both legacy static configuration and new dynamic configuration support.
    Maintains full backward compatibility while adding advanced features.
    """

    # Legacy static settings (for backward compatibility)
    DEFAULT_TIMEOUT = 30000      # Optimized: 30s (reduced from 45s)
    NAVIGATION_TIMEOUT = 45000   # Optimized: 45s (reduced from 90s)
    ACTION_TIMEOUT = 15000       # Optimized: 15s (reduced from 20s)
    MAX_RETRIES = 2              # Optimized: 2 (reduced from 3)
    RETRY_DELAY = 1.5            # Optimized: 1.5s (reduced from 2s)
    WAIT_AFTER_NAVIGATION = 2.0  # Optimized: 2s (reduced from 3s)
    WAIT_AFTER_ACTION = 1.0      # Optimized: 1s (reduced from 1.5s)

    @classmethod
    def get_config(cls):
        """Get current configuration"""
        try:
            return load_config()
        except Exception:
            # Return None if config loading fails
            return None

    @classmethod
    def get_timeout(cls, timeout_type: str, url: str = "", attempt: int = 0) -> int:
        """
        Get timeout value with dynamic configuration and site-specific optimization.

        Args:
            timeout_type: 'navigation', 'action', or 'default'
            url: URL for site-specific optimization
            attempt: Retry attempt number (0-based) for progressive timeouts

        Returns:
            Timeout in milliseconds
        """
        config = cls.get_config()

        if not config:
            # Fallback to static configuration
            if timeout_type == 'navigation':
                return cls.NAVIGATION_TIMEOUT
            elif timeout_type == 'action':
                return cls.ACTION_TIMEOUT
            else:
                return cls.DEFAULT_TIMEOUT

        # Get base timeout from config
        if timeout_type == 'navigation':
            base_timeout = config.browser_navigation_timeout
        elif timeout_type == 'action':
            base_timeout = config.browser_action_timeout
        else:
            base_timeout = config.browser_default_timeout

        # Apply site-specific optimization
        if url:
            site_overrides = get_site_profile(url, config.browser_auto_site_detection)
            timeout_key = f"browser_{timeout_type}_timeout"
            if timeout_key in site_overrides:
                base_timeout = site_overrides[timeout_key]

        # Apply progressive timeout strategy
        return get_progressive_timeout(base_timeout, attempt, config.browser_timeout_strategy)

    @classmethod
    def get_retries(cls, url: str = "") -> int:
        """Get max retries with site-specific optimization"""
        config = cls.get_config()

        if not config:
            return cls.MAX_RETRIES

        # Check for site-specific settings
        if url:
            site_overrides = get_site_profile(url, config.browser_auto_site_detection)
            if "browser_max_retries" in site_overrides:
                return site_overrides["browser_max_retries"]

        return config.browser_max_retries

    @classmethod
    def get_retry_delay(cls, url: str = "") -> float:
        """Get retry delay with site-specific optimization"""
        config = cls.get_config()

        if not config:
            return cls.RETRY_DELAY

        return config.browser_retry_delay

    @classmethod
    def get_wait_after_navigation(cls, url: str = "") -> float:
        """Get wait time after navigation with site-specific optimization"""
        config = cls.get_config()

        if not config:
            return cls.WAIT_AFTER_NAVIGATION

        # Check for site-specific settings
        if url:
            site_overrides = get_site_profile(url, config.browser_auto_site_detection)
            if "browser_wait_after_navigation" in site_overrides:
                return site_overrides["browser_wait_after_navigation"]

        return config.browser_wait_after_navigation

    @classmethod
    def get_wait_after_action(cls, url: str = "") -> float:
        """Get wait time after action"""
        config = cls.get_config()

        if not config:
            return cls.WAIT_AFTER_ACTION

        return config.browser_wait_after_action

    @classmethod
    def get_wait_strategy(cls, url: str = "") -> str:
        """Get page load wait strategy"""
        config = cls.get_config()

        if not config:
            return 'networkidle'  # Legacy default

        # Check for site-specific settings
        if url:
            site_overrides = get_site_profile(url, config.browser_auto_site_detection)
            if "browser_wait_strategy" in site_overrides:
                return site_overrides["browser_wait_strategy"]

        return config.browser_wait_strategy


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

            # Launch Chromium browser with enhanced anti-detection
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',  # Avoid detection
                    '--no-sandbox',  # Required for some environments
                    '--disable-web-security',  # Reduce security restrictions
                    '--disable-features=VizDisplayCompositor',  # Improve performance
                    '--disable-extensions-http-throttling',  # Reduce throttling
                    '--no-first-run',  # Skip first-run experience
                    '--disable-default-apps',  # Don't load default apps
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ]
            )

            # Create browser context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': viewport_size[0], 'height': viewport_size[1]},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

            # Create new page
            self.page = await self.context.new_page()

            # Set default timeout from config (Phase 5.4)
            self.page.set_default_timeout(BrowserConfig.DEFAULT_TIMEOUT)

            # Add stealth JavaScript to avoid detection
            await self.page.add_init_script("""
                // Remove automation indicators
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Override permissions query
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            """)

            self._initialized = True
            logger.info("Browser initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.cleanup()
            raise BrowserControllerError(f"Browser initialization failed: {e}")

    async def navigate(self, url: str, wait_until: str = None, attempt: int = 0) -> None:
        """
        Navigate to URL with smart waiting and dynamic configuration.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
                       ('load', 'domcontentloaded', 'networkidle', 'commit')
                       If None, uses dynamic configuration default
            attempt: Retry attempt number for progressive timeouts

        Raises:
            BrowserControllerError: If navigation fails
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        # Get dynamic configuration
        if wait_until is None:
            wait_until = BrowserConfig.get_wait_strategy(url)

        # Get dynamic timeout with progressive strategy
        navigation_timeout = BrowserConfig.get_timeout('navigation', url, attempt)
        wait_after_nav = BrowserConfig.get_wait_after_navigation(url)

        try:
            logger.info(f"Navigating to: {url} (timeout: {navigation_timeout}ms, wait_until: {wait_until}, attempt: {attempt + 1})")

            # Use dynamic timeout with site-specific and progressive optimization
            await self.page.goto(
                url,
                wait_until=wait_until,
                timeout=navigation_timeout
            )

            # Additional wait for JavaScript rendering (configurable)
            await asyncio.sleep(wait_after_nav)

            # Check for common blocking patterns
            await self._check_for_blocking_patterns(url)

            logger.info(f"Navigation complete: {url}")

        except PlaywrightTimeoutError as e:
            logger.warning(f"Navigation timeout ({navigation_timeout}ms): {url}")
            # Try fallback: wait for 'load' instead of 'networkidle'
            if wait_until == 'networkidle':
                logger.info("Retrying with 'load' wait strategy...")
                try:
                    await self.page.goto(url, wait_until='load', timeout=30000)
                    logger.info("Fallback navigation succeeded")
                except Exception:
                    raise BrowserControllerError(f"Navigation timeout: {url}")
            else:
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

    async def execute_action(self, action: Dict[str, Any], retry: bool = True) -> Dict[str, Any]:
        """
        Execute browser action from parsed decision (Phase 5.4: with retry logic).

        Supported actions:
          - click: {type: 'click', selector: '#btn', text: 'Submit'}
          - type: {type: 'type', selector: '#search', text: 'sneakers'}
          - scroll: {type: 'scroll', direction: 'down', amount: 500}
          - navigate: {type: 'navigate', url: 'https://...'}
          - extract: {type: 'extract', selector: '.price'}
          - wait: {type: 'wait', seconds: 2}

        Args:
            action: Action dictionary with type and parameters
            retry: Enable retry on failure (default: True, Phase 5.4)

        Returns:
            Result dictionary with success status and data

        Raises:
            BrowserControllerError: If action execution fails after retries
        """
        if not self._initialized:
            raise BrowserControllerError("Browser not initialized. Call initialize() first.")

        action_type = action.get('type')
        max_attempts = BrowserConfig.MAX_RETRIES + 1 if retry else 1

        last_error = None

        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    logger.info(f"Retrying action {action_type} (attempt {attempt + 1}/{max_attempts})")
                    await asyncio.sleep(BrowserConfig.RETRY_DELAY)

                # Execute action
                if action_type == 'click':
                    result = await self._action_click(action)
                elif action_type == 'type':
                    result = await self._action_type(action)
                elif action_type == 'scroll':
                    result = await self._action_scroll(action)
                elif action_type == 'navigate':
                    result = await self._action_navigate(action)
                elif action_type == 'extract':
                    result = await self._action_extract(action)
                elif action_type == 'wait':
                    result = await self._action_wait(action)
                else:
                    raise BrowserControllerError(f"Unknown action type: {action_type}")

                # Wait for page updates after action (Phase 5.4)
                await asyncio.sleep(BrowserConfig.WAIT_AFTER_ACTION)

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Action {action_type} failed (attempt {attempt + 1}/{max_attempts}): {e}")

                # Don't retry certain errors
                if isinstance(e, BrowserControllerError) and "Unknown action type" in str(e):
                    break  # Don't retry unknown action types

        # All attempts failed
        logger.error(f"Action execution failed after {max_attempts} attempts: {action_type}")
        return {
            'success': False,
            'error': str(last_error),
            'action': action,
            'attempts': max_attempts
        }

    def _convert_selector(self, selector: str) -> tuple[str, str]:
        """
        Convert invalid selectors to proper Playwright selectors.

        Returns:
            tuple: (selector_type, converted_selector)
                   selector_type can be 'css', 'text', or 'xpath'
        """
        if not selector:
            return 'css', selector

        # Handle :contains() pseudo-selector (not valid CSS)
        import re
        contains_match = re.search(r'([^:]+):contains\(["\']([^"\']+)["\']\)', selector)
        if contains_match:
            element_type = contains_match.group(1)
            text_content = contains_match.group(2)
            # Convert to text-based selector
            return 'text', text_content

        # Handle other jQuery/invalid selectors that might appear
        if ':contains(' in selector:
            # Extract text from contains
            text_match = re.search(r':contains\(["\']([^"\']+)["\']\)', selector)
            if text_match:
                return 'text', text_match.group(1)

        # Valid CSS selector
        return 'css', selector

    async def _action_click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute click action (Phase 5.4: configurable timeout)."""
        selector = action.get('selector')
        text = action.get('text')

        try:
            if selector:
                # Convert and validate selector
                selector_type, converted_selector = self._convert_selector(selector)

                if selector_type == 'text':
                    # Use text-based selection
                    await self.page.get_by_text(converted_selector).first.click(timeout=BrowserConfig.ACTION_TIMEOUT)
                    logger.info(f"Clicked element with text: {converted_selector}")
                    target = f"text:{converted_selector}"
                elif selector_type == 'css':
                    # Use CSS selector
                    await self.page.click(converted_selector, timeout=BrowserConfig.ACTION_TIMEOUT)
                    logger.info(f"Clicked element: {converted_selector}")
                    target = converted_selector
                else:
                    raise ValueError(f"Unsupported selector type: {selector_type}")

            elif text:
                # Click by text directly
                await self.page.get_by_text(text).first.click(timeout=BrowserConfig.ACTION_TIMEOUT)
                logger.info(f"Clicked element with text: {text}")
                target = f"text:{text}"
            else:
                raise ValueError("Click action requires 'selector' or 'text'")

            return {'success': True, 'action': 'click', 'target': target}

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

    async def _check_for_blocking_patterns(self, url: str) -> None:
        """
        Check for common e-commerce blocking patterns and handle them.

        Detects:
        - CAPTCHA challenges
        - Bot detection messages
        - Access denied pages
        - Rate limiting messages

        Args:
            url: The current page URL

        Raises:
            BrowserControllerError: If site is blocking automated access
        """
        try:
            # Get page title and content for analysis
            title = await self.page.title()
            page_text = await self.page.inner_text('body') if await self.page.query_selector('body') else ""

            # Common blocking patterns (case insensitive)
            blocking_patterns = [
                'robot or computer',
                'captcha',
                'not a robot',
                'verify you are human',
                'access denied',
                'blocked',
                'suspicious activity',
                'automated traffic',
                'try again later',
                'rate limit',
                'security check'
            ]

            page_text_lower = page_text.lower()
            title_lower = title.lower()

            # Check for blocking patterns
            detected_patterns = []
            for pattern in blocking_patterns:
                if pattern in page_text_lower or pattern in title_lower:
                    detected_patterns.append(pattern)

            if detected_patterns:
                logger.warning(f"Anti-bot detection triggered on {url}")
                logger.warning(f"Detected patterns: {detected_patterns}")
                logger.warning(f"Page title: {title}")

                # Try to handle some common cases automatically
                await self._handle_blocking_patterns(detected_patterns)

        except Exception as e:
            logger.debug(f"Could not check for blocking patterns: {e}")
            # Don't raise - this is just a check, not critical

    async def _handle_blocking_patterns(self, patterns: List[str]) -> None:
        """
        Attempt to automatically handle detected blocking patterns.

        Args:
            patterns: List of detected blocking pattern keywords
        """
        try:
            # Look for and close cookie banners/modal dialogs first
            common_close_selectors = [
                'button[aria-label*="close"]',
                'button[aria-label*="dismiss"]',
                '.close',
                '#close',
                'button:has-text("Accept")',
                'button:has-text("Got it")',
                'button:has-text("OK")',
                '[data-dismiss="modal"]'
            ]

            for selector in common_close_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Found potential close button: {selector}")
                        await elements[0].click(timeout=5000)
                        await asyncio.sleep(1)
                        break
                except:
                    continue

            # If CAPTCHA or security check detected, wait longer and suggest manual intervention
            if any('captcha' in p or 'security' in p for p in patterns):
                logger.warning("CAPTCHA or security check detected - automated browsing may not work")
                logger.warning("Consider using the tool on simpler websites or enabling headless=False to solve manually")

        except Exception as e:
            logger.debug(f"Could not handle blocking patterns: {e}")

    async def cleanup(self) -> None:
        """
        Close browser and cleanup resources.

        This method is safe to call multiple times.
        """
        logger.info("Cleaning up browser resources")

        try:
            # Force close operations with timeout to prevent hanging
            import asyncio

            async def force_close(coro, name, timeout=5):
                try:
                    await asyncio.wait_for(coro, timeout=timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout closing {name}, continuing anyway")
                except Exception as e:
                    logger.error(f"Error closing {name}: {e}")

            if self.page:
                await force_close(self.page.close(), "page")
                self.page = None

            if self.context:
                await force_close(self.context.close(), "context")
                self.context = None

            if self.browser:
                await force_close(self.browser.close(), "browser")
                self.browser = None

            if self.playwright:
                await force_close(self.playwright.stop(), "playwright")
                self.playwright = None

            self._initialized = False
            logger.info("Browser cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Force reset state even if cleanup failed
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
