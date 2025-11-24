"""
Unified Browser Manager for WYN360 CLI

This module provides a singleton browser manager that coordinates Playwright browser
instances across all automation approaches (DOM, Stagehand, Vision) to ensure
consistent behavior and efficient resource usage.

Phase 4.3: Unified Playwright browser instance management
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger(__name__)


class UnifiedBrowserManager:
    """
    Singleton browser manager for consistent Playwright instance management

    Ensures all automation approaches (DOM, Stagehand, Vision) share the same
    browser instance for better resource management and consistent behavior.
    """

    _instance: Optional['UnifiedBrowserManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'UnifiedBrowserManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.headless: bool = True
        self.viewport: Dict[str, int] = {'width': 1280, 'height': 720}
        self.user_agent: str = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        self.timeout: int = 30000
        self._initialized = True

        logger.info("UnifiedBrowserManager initialized")

    async def initialize(
        self,
        headless: bool = True,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30000
    ) -> None:
        """
        Initialize the unified browser instance

        Args:
            headless: Run browser in headless mode
            viewport: Browser viewport size
            user_agent: Custom user agent string
            timeout: Page load timeout in milliseconds
        """
        async with self._lock:
            if self.browser is not None:
                # Browser already initialized - update settings if different
                if self.headless != headless:
                    logger.info(f"Browser headless mode changing from {self.headless} to {headless}")
                    await self.close()
                else:
                    logger.info("Browser already initialized")
                    return

            self.headless = headless
            self.viewport = viewport or self.viewport
            self.user_agent = user_agent or self.user_agent
            self.timeout = timeout

            try:
                logger.info(f"Initializing unified browser (headless={headless}, viewport={self.viewport})")

                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                logger.info("Unified browser initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize unified browser: {e}")
                await self.close()
                raise

    async def get_context(
        self,
        name: str = "default",
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None
    ) -> BrowserContext:
        """
        Get or create a browser context

        Args:
            name: Context name for identification
            viewport: Custom viewport for this context
            user_agent: Custom user agent for this context

        Returns:
            Browser context
        """
        if self.browser is None:
            await self.initialize()

        if name in self.contexts and not self.contexts[name].is_closed:
            return self.contexts[name]

        try:
            context = await self.browser.new_context(
                viewport=viewport or self.viewport,
                user_agent=user_agent or self.user_agent
            )

            # Set default timeout
            context.set_default_timeout(self.timeout)

            self.contexts[name] = context
            logger.info(f"Created browser context: {name}")

            return context

        except Exception as e:
            logger.error(f"Failed to create browser context '{name}': {e}")
            raise

    async def get_page(
        self,
        name: str = "default",
        context_name: str = "default"
    ) -> Page:
        """
        Get or create a page in the specified context

        Args:
            name: Page name for identification
            context_name: Context to create the page in

        Returns:
            Page instance
        """
        page_key = f"{context_name}:{name}"

        if page_key in self.pages and not self.pages[page_key].is_closed:
            return self.pages[page_key]

        try:
            context = await self.get_context(context_name)
            page = await context.new_page()

            self.pages[page_key] = page
            logger.info(f"Created page: {page_key}")

            return page

        except Exception as e:
            logger.error(f"Failed to create page '{page_key}': {e}")
            raise

    async def close_page(self, name: str = "default", context_name: str = "default") -> None:
        """Close a specific page"""
        page_key = f"{context_name}:{name}"

        if page_key in self.pages:
            try:
                await self.pages[page_key].close()
                del self.pages[page_key]
                logger.info(f"Closed page: {page_key}")
            except Exception as e:
                logger.error(f"Error closing page '{page_key}': {e}")

    async def close_context(self, name: str = "default") -> None:
        """Close a specific context and all its pages"""
        if name in self.contexts:
            try:
                # Close all pages in this context
                pages_to_close = [k for k in self.pages.keys() if k.startswith(f"{name}:")]
                for page_key in pages_to_close:
                    try:
                        await self.pages[page_key].close()
                        del self.pages[page_key]
                    except:
                        pass

                # Close the context
                await self.contexts[name].close()
                del self.contexts[name]
                logger.info(f"Closed browser context: {name}")

            except Exception as e:
                logger.error(f"Error closing context '{name}': {e}")

    async def close(self) -> None:
        """Close all browser resources"""
        try:
            # Close all pages
            for page_name in list(self.pages.keys()):
                try:
                    await self.pages[page_name].close()
                except:
                    pass
            self.pages.clear()

            # Close all contexts
            for context_name in list(self.contexts.keys()):
                try:
                    await self.contexts[context_name].close()
                except:
                    pass
            self.contexts.clear()

            # Close browser
            if self.browser:
                await self.browser.close()
                self.browser = None
                logger.info("Browser closed")

            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                logger.info("Playwright stopped")

        except Exception as e:
            logger.error(f"Error during browser cleanup: {e}")

    def is_initialized(self) -> bool:
        """Check if browser is initialized and ready"""
        return self.browser is not None and not self.browser.is_closed

    async def get_browser_info(self) -> Dict[str, Any]:
        """Get information about the browser state"""
        return {
            'initialized': self.is_initialized(),
            'headless': self.headless,
            'viewport': self.viewport,
            'user_agent': self.user_agent,
            'timeout': self.timeout,
            'contexts': list(self.contexts.keys()),
            'pages': list(self.pages.keys()),
            'contexts_count': len(self.contexts),
            'pages_count': len(self.pages)
        }


# Global unified browser manager instance
browser_manager = UnifiedBrowserManager()