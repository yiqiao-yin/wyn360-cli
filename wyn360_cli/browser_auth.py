"""
Browser Authentication Module for WYN360-CLI (Phase 4.2.2)

Handles automated login to websites using Playwright.

Features:
- Automatic form detection (username, password, submit)
- Multi-step login flow support
- CAPTCHA detection (informs user)
- 2FA detection (prompts user for code)
- Session cookie extraction
- Login state verification

Dependencies:
- playwright (installed via pip)
- Requires: playwright install chromium (one-time setup)
"""

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from typing import Dict, Optional, List, Tuple
import asyncio
import re


class BrowserAuth:
    """Automated browser authentication using Playwright."""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize Browser Authentication.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Page load timeout in milliseconds (default: 30000 = 30s)
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def _detect_login_form(self, page: Page) -> Dict[str, Optional[str]]:
        """
        Detect login form elements on the page.

        Args:
            page: Playwright page object

        Returns:
            Dictionary with selectors: {
                'username': selector or None,
                'password': selector or None,
                'submit': selector or None
            }
        """
        form_elements = {
            'username': None,
            'password': None,
            'submit': None
        }

        try:
            # Detect username field (email, text, or username input)
            username_selectors = [
                'input[type="email"]',
                'input[type="text"][name*="user"]',
                'input[type="text"][name*="email"]',
                'input[type="text"][id*="user"]',
                'input[type="text"][id*="email"]',
                'input[name="username"]',
                'input[name="email"]',
                'input[id="username"]',
                'input[id="email"]',
                'input[placeholder*="username" i]',
                'input[placeholder*="email" i]'
            ]

            for selector in username_selectors:
                if await page.locator(selector).count() > 0:
                    form_elements['username'] = selector
                    break

            # Detect password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]'
            ]

            for selector in password_selectors:
                if await page.locator(selector).count() > 0:
                    form_elements['password'] = selector
                    break

            # Detect submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("log in")',
                'button:has-text("sign in")',
                'button:has-text("login")',
                'input[value="log in" i]',
                'input[value="sign in" i]',
                'input[value="login" i]'
            ]

            for selector in submit_selectors:
                if await page.locator(selector).count() > 0:
                    form_elements['submit'] = selector
                    break

        except Exception as e:
            print(f"Error detecting form elements: {e}")

        return form_elements

    async def _detect_captcha(self, page: Page) -> bool:
        """
        Detect if CAPTCHA is present on the page.

        Args:
            page: Playwright page object

        Returns:
            True if CAPTCHA detected, False otherwise
        """
        captcha_indicators = [
            'div[class*="captcha" i]',
            'div[class*="recaptcha" i]',
            'iframe[src*="recaptcha"]',
            'iframe[src*="captcha"]'
        ]

        for selector in captcha_indicators:
            if await page.locator(selector).count() > 0:
                return True

        return False

    async def _detect_2fa(self, page: Page) -> bool:
        """
        Detect if 2FA/MFA code is required.

        Args:
            page: Playwright page object

        Returns:
            True if 2FA detected, False otherwise
        """
        twofa_indicators = [
            'input[name*="code" i]',
            'input[name*="otp" i]',
            'input[name*="2fa" i]',
            'input[placeholder*="code" i]',
            'text="verification code"',
            'text="authentication code"',
            'text="two-factor"'
        ]

        for selector in twofa_indicators:
            if await page.locator(selector).count() > 0:
                return True

        return False

    async def login(
        self,
        url: str,
        username: str,
        password: str
    ) -> Dict[str, any]:
        """
        Attempt to login to a website.

        Args:
            url: Website URL
            username: Login username/email
            password: Login password

        Returns:
            Dictionary with:
            {
                'success': bool,
                'message': str,
                'cookies': List[Dict] or None,
                'requires_2fa': bool,
                'has_captcha': bool
            }
        """
        result = {
            'success': False,
            'message': '',
            'cookies': None,
            'requires_2fa': False,
            'has_captcha': False
        }

        try:
            # Launch browser
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=self.headless)
                self.page = await self.browser.new_page()

                # Navigate to URL
                try:
                    await self.page.goto(url, timeout=self.timeout)
                except PlaywrightTimeout:
                    result['message'] = f"Timeout loading {url}"
                    return result

                # Check for CAPTCHA
                if await self._detect_captcha(self.page):
                    result['has_captcha'] = True
                    result['message'] = "CAPTCHA detected. Please complete CAPTCHA manually."
                    return result

                # Detect login form
                form = await self._detect_login_form(self.page)

                if not form['username'] or not form['password']:
                    result['message'] = "Could not detect login form. Please check the URL."
                    return result

                # Fill username
                await self.page.fill(form['username'], username)

                # Fill password
                await self.page.fill(form['password'], password)

                # Click submit button (or press Enter if no button found)
                if form['submit']:
                    await self.page.click(form['submit'])
                else:
                    # Press Enter on password field
                    await self.page.press(form['password'], 'Enter')

                # Wait for navigation or form submission
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeout:
                    pass  # Some pages don't fully load, continue anyway

                # Check for 2FA
                if await self._detect_2fa(self.page):
                    result['requires_2fa'] = True
                    result['message'] = "2FA required. Please enter verification code manually."
                    # Get cookies even for 2FA (partial authentication)
                    result['cookies'] = await self.page.context.cookies()
                    return result

                # Check if login was successful
                # (Heuristic: if we're still on login page, login failed)
                current_url = self.page.url

                # Look for error messages
                error_indicators = [
                    'text="incorrect password" i',
                    'text="invalid credentials" i',
                    'text="login failed" i',
                    'text="username or password" i',
                    'div[class*="error"]',
                    'div[class*="alert"]'
                ]

                has_error = False
                for selector in error_indicators:
                    if await self.page.locator(selector).count() > 0:
                        has_error = True
                        break

                if has_error:
                    result['message'] = "Login failed. Incorrect username or password."
                    return result

                # If we're redirected away from login page, assume success
                if current_url != url and not has_error:
                    result['success'] = True
                    result['message'] = f"Login successful! Redirected to {current_url}"
                    result['cookies'] = await self.page.context.cookies()
                else:
                    # Try to verify by looking for logout/account elements
                    success_indicators = [
                        'text="logout" i',
                        'text="sign out" i',
                        'text="my account" i',
                        'a[href*="logout"]'
                    ]

                    for selector in success_indicators:
                        if await self.page.locator(selector).count() > 0:
                            result['success'] = True
                            result['message'] = "Login successful!"
                            result['cookies'] = await self.page.context.cookies()
                            break

                    if not result['success']:
                        result['message'] = "Login status unclear. Please verify manually."

        except Exception as e:
            result['message'] = f"Error during login: {str(e)}"

        finally:
            if self.browser:
                await self.browser.close()

        return result

    async def verify_session(self, url: str, cookies: List[Dict]) -> bool:
        """
        Verify if session cookies are still valid.

        Args:
            url: Website URL to check
            cookies: List of cookie dictionaries

        Returns:
            True if session is valid, False otherwise
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()

                # Add cookies to context
                await context.add_cookies(cookies)

                page = await context.new_page()

                # Navigate to URL
                await page.goto(url, timeout=self.timeout)

                # Check for logout button (indicates logged in)
                logout_selectors = [
                    'text="logout" i',
                    'text="sign out" i',
                    'a[href*="logout"]'
                ]

                for selector in logout_selectors:
                    if await page.locator(selector).count() > 0:
                        await browser.close()
                        return True

                await browser.close()
                return False

        except Exception as e:
            print(f"Error verifying session: {e}")
            return False

    async def fetch_authenticated_content(
        self,
        url: str,
        cookies: List[Dict]
    ) -> Optional[str]:
        """
        Fetch content from an authenticated page using session cookies.

        Args:
            url: URL to fetch
            cookies: Session cookies

        Returns:
            Page content as string, or None if failed
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context()

                # Add cookies
                await context.add_cookies(cookies)

                page = await context.new_page()

                # Navigate to URL
                await page.goto(url, timeout=self.timeout)

                # Get page content
                content = await page.content()

                await browser.close()

                return content

        except Exception as e:
            print(f"Error fetching authenticated content: {e}")
            return None
