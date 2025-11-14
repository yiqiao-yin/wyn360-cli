"""
Browser Authentication Module for WYN360-CLI (Phase 4.2.2 + 4.4)

Handles automated login to websites using Playwright.

Features:
- Automatic form detection (username, password, submit)
- Multi-step login flow support
- CAPTCHA detection (informs user)
- 2FA detection (prompts user for code)
- Session cookie extraction
- Login state verification

Phase 4.4 Enhancements:
- Intelligent URL discovery (tries common login paths)
- Dynamic content waiting (JavaScript frameworks)
- Enhanced form detection with fuzzy matching
- Debug mode with screenshots and HTML dumps
- Manual selector override

Dependencies:
- playwright (installed via pip)
- Requires: playwright install chromium (one-time setup)
"""

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from typing import Dict, Optional, List, Tuple, Any
from urllib.parse import urljoin, urlparse
from pathlib import Path
import asyncio
import re
import time
import json


class BrowserAuth:
    """Automated browser authentication using Playwright."""

    def __init__(self, headless: bool = True, timeout: int = 30000, debug: bool = False):
        """
        Initialize Browser Authentication.

        Args:
            headless: Run browser in headless mode (default: True)
            timeout: Page load timeout in milliseconds (default: 30000 = 30s)
            debug: Enable debug mode with screenshots and HTML dumps (default: False)
        """
        self.headless = headless
        self.timeout = timeout
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # Debug directory (Phase 4.4.4)
        if self.debug:
            self.debug_dir = Path.home() / '.wyn360' / 'debug' / 'browser_auth'
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            self.debug_timestamp = int(time.time())

    async def _save_debug_screenshot(self, page: Page, step: str):
        """Save screenshot for debugging (Phase 4.4.4)."""
        if self.debug:
            filename = f"{self.debug_timestamp}_{step}.png"
            await page.screenshot(path=str(self.debug_dir / filename))

    async def _save_debug_html(self, page: Page, step: str):
        """Save HTML content for debugging (Phase 4.4.4)."""
        if self.debug:
            filename = f"{self.debug_timestamp}_{step}.html"
            html_content = await page.content()
            with open(self.debug_dir / filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

    async def _save_debug_info(self, info: Dict[str, Any], step: str):
        """Save debug information to JSON (Phase 4.4.4)."""
        if self.debug:
            filename = f"{self.debug_timestamp}_{step}.json"
            with open(self.debug_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2)

    async def _find_login_page(self, base_url: str) -> Tuple[str, bool]:
        """
        Intelligently find login page (Phase 4.4.1).

        Tries:
        1. Common login URLs (/login, /signin, etc.)
        2. Following "Login" links on homepage
        3. Original URL as fallback

        Args:
            base_url: Base URL to search

        Returns:
            Tuple of (login_url, found_via_discovery)
        """
        # Parse base URL
        parsed = urlparse(base_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"

        # Common login paths (Phase 4.4.1)
        common_paths = [
            '/login',
            '/signin',
            '/sign-in',
            '/auth',
            '/authenticate',
            '/account/login',
            '/user/login',
            '/accounts/signin',
            '/login.php',
            '/signin.php',
            '/login.html',
            '/signin.html'
        ]

        # Try each common path
        for path in common_paths:
            test_url = urljoin(base_domain, path)
            try:
                await self.page.goto(test_url, timeout=10000, wait_until='domcontentloaded')
                await self._save_debug_screenshot(self.page, f"discovery_{path.replace('/', '_')}")

                # Check if this page has a login form
                if await self._has_login_form(self.page):
                    if self.debug:
                        print(f"[DEBUG] Found login page at: {test_url}")
                    return test_url, True

            except Exception:
                continue  # Path doesn't exist, try next

        # If no common path worked, try homepage and look for login links
        try:
            await self.page.goto(base_url, timeout=self.timeout)
            await self._save_debug_screenshot(self.page, "homepage")

            # Look for login links
            login_link_selectors = [
                'a:has-text("log in")',
                'a:has-text("sign in")',
                'a:has-text("login")',
                'a:has-text("signin")',
                'a[href*="login"]',
                'a[href*="signin"]'
            ]

            for selector in login_link_selectors:
                try:
                    link = await self.page.locator(selector).first
                    if link:
                        href = await link.get_attribute('href')
                        if href:
                            login_url = urljoin(base_url, href)
                            await self.page.goto(login_url, timeout=10000)

                            if await self._has_login_form(self.page):
                                if self.debug:
                                    print(f"[DEBUG] Found login page via link: {login_url}")
                                return login_url, True
                except Exception:
                    continue

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error during login page discovery: {e}")

        # Fallback to original URL
        return base_url, False

    async def _has_login_form(self, page: Page) -> bool:
        """
        Quick check if page has a login form (Phase 4.4.1).

        Args:
            page: Playwright page object

        Returns:
            True if login form detected, False otherwise
        """
        # Look for password field (most unique indicator)
        password_count = await page.locator('input[type="password"]').count()
        if password_count > 0:
            return True

        # Look for login-related form elements
        form_indicators = [
            'form[action*="login"]',
            'form[id*="login"]',
            'form[class*="login"]',
            'div[class*="login-form"]',
            'div[id*="login-form"]'
        ]

        for selector in form_indicators:
            if await page.locator(selector).count() > 0:
                return True

        return False

    async def _wait_for_form_load(self, page: Page, max_wait: int = 10000):
        """
        Wait for login form to appear (Phase 4.4.2).

        Handles dynamic content loaded by JavaScript frameworks.

        Args:
            page: Playwright page object
            max_wait: Maximum wait time in milliseconds
        """
        # Most unique indicator: password field
        selectors = [
            'input[type="password"]',
            'form[action*="login"]',
            'div[class*="login"]',
            'input[name*="user"]',
            'input[name*="email"]'
        ]

        try:
            # Wait for ANY of these selectors to appear
            await page.wait_for_selector(
                ', '.join(selectors),
                timeout=max_wait,
                state='visible'
            )
            if self.debug:
                print(f"[DEBUG] Form elements became visible")
        except PlaywrightTimeout:
            if self.debug:
                print(f"[DEBUG] Timeout waiting for form elements (continuing anyway)")
            pass  # Continue with detection even if timeout

        # Additional wait for JavaScript to settle
        await asyncio.sleep(1)

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

    async def _detect_login_form_enhanced(self, page: Page) -> Dict[str, Optional[str]]:
        """
        Enhanced form detection with fuzzy matching (Phase 4.4.3).

        Analyzes ALL input elements and uses fuzzy matching on attributes.

        Args:
            page: Playwright page object

        Returns:
            Dictionary with selectors or None
        """
        # First try traditional detection
        traditional = await self._detect_login_form(page)
        if traditional['username'] and traditional['password']:
            return traditional

        # Enhanced detection: analyze ALL inputs
        form_elements = {
            'username': None,
            'password': None,
            'submit': None
        }

        try:
            # Get ALL input elements
            all_inputs = await page.locator('input').all()

            username_candidates = []
            password_field = None

            for input_elem in all_inputs:
                # Get all attributes
                input_type = await input_elem.get_attribute('type') or ''
                input_name = await input_elem.get_attribute('name') or ''
                input_id = await input_elem.get_attribute('id') or ''
                input_placeholder = await input_elem.get_attribute('placeholder') or ''
                input_class = await input_elem.get_attribute('class') or ''
                input_autocomplete = await input_elem.get_attribute('autocomplete') or ''
                input_aria_label = await input_elem.get_attribute('aria-label') or ''

                # Combine all attributes for fuzzy matching
                combined = f"{input_type} {input_name} {input_id} {input_placeholder} {input_class} {input_autocomplete} {input_aria_label}".lower()

                # Password field (exact match)
                if input_type == 'password':
                    password_field = input_elem

                # Username field (fuzzy match)
                username_keywords = ['user', 'email', 'login', 'account', 'identifier', 'name']
                if input_type != 'password' and any(kw in combined for kw in username_keywords):
                    # Calculate confidence score
                    score = sum(1 for kw in username_keywords if kw in combined)
                    username_candidates.append((input_elem, score))

            # Select best username candidate
            if username_candidates:
                username_candidates.sort(key=lambda x: x[1], reverse=True)
                username_field = username_candidates[0][0]

                # Build selector for username field
                username_id = await username_field.get_attribute('id')
                username_name = await username_field.get_attribute('name')

                if username_id:
                    form_elements['username'] = f'#{username_id}'
                elif username_name:
                    form_elements['username'] = f'input[name="{username_name}"]'

            # Build selector for password field
            if password_field:
                password_id = await password_field.get_attribute('id')
                password_name = await password_field.get_attribute('name')

                if password_id:
                    form_elements['password'] = f'#{password_id}'
                elif password_name:
                    form_elements['password'] = f'input[name="{password_name}"]'
                else:
                    form_elements['password'] = 'input[type="password"]'

            # Find submit button (enhanced)
            all_buttons = await page.locator('button, input[type="submit"]').all()
            for button in all_buttons:
                button_type = await button.get_attribute('type') or ''
                button_text = await button.text_content() or ''
                button_value = await button.get_attribute('value') or ''
                button_class = await button.get_attribute('class') or ''

                combined = f"{button_type} {button_text} {button_value} {button_class}".lower()

                # Look for submit/login keywords
                if any(kw in combined for kw in ['submit', 'login', 'sign in', 'log in', 'enter']):
                    button_id = await button.get_attribute('id')
                    button_name = await button.get_attribute('name')

                    if button_id:
                        form_elements['submit'] = f'#{button_id}'
                    elif button_name:
                        form_elements['submit'] = f'[name="{button_name}"]'
                    elif button_type == 'submit':
                        form_elements['submit'] = 'button[type="submit"], input[type="submit"]'
                    break

            # Debug: Save detected elements
            if self.debug:
                debug_info = {
                    'username_selector': form_elements['username'],
                    'password_selector': form_elements['password'],
                    'submit_selector': form_elements['submit'],
                    'username_candidates_count': len(username_candidates),
                    'password_found': password_field is not None
                }
                await self._save_debug_info(debug_info, 'form_detection')

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Error in enhanced form detection: {e}")

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

                # Phase 4.4.1: Intelligent URL Discovery
                login_url, found_via_discovery = await self._find_login_page(url)
                if found_via_discovery and self.debug:
                    print(f"[DEBUG] Discovered login page: {login_url}")

                # Navigate to login URL
                try:
                    await self.page.goto(login_url, timeout=self.timeout)
                    await self._save_debug_screenshot(self.page, "1_initial_page")
                except PlaywrightTimeout:
                    result['message'] = f"Timeout loading {login_url}"
                    if self.debug:
                        result['message'] += f"\n\nDebug files saved to: {self.debug_dir}"
                    return result

                # Phase 4.4.2: Wait for dynamic content
                await self._wait_for_form_load(self.page)
                await self._save_debug_screenshot(self.page, "2_after_wait")
                await self._save_debug_html(self.page, "page_content")

                # Check for CAPTCHA
                if await self._detect_captcha(self.page):
                    result['has_captcha'] = True
                    result['message'] = "CAPTCHA detected. Please complete CAPTCHA manually."
                    await self._save_debug_screenshot(self.page, "captcha_detected")
                    return result

                # Phase 4.4.3: Enhanced form detection with fuzzy matching
                form = await self._detect_login_form_enhanced(self.page)

                if not form['username'] or not form['password']:
                    # Save debug info for troubleshooting
                    await self._save_debug_screenshot(self.page, "form_detection_failed")

                    # Provide helpful error message
                    error_msg = "❌ Could not detect login form.\n\n"
                    error_msg += "**Possible reasons:**\n"
                    error_msg += "- Form uses non-standard elements\n"
                    error_msg += "- JavaScript hasn't finished loading\n"
                    error_msg += "- Login requires interaction (e.g., clicking a button to show form)\n\n"
                    error_msg += "**Solutions:**\n"
                    error_msg += "1. Try specifying the exact login URL (e.g., /login, /signin)\n"
                    error_msg += "2. Use manual selector override: login_with_selectors()\n"
                    error_msg += "3. Inspect the page and provide CSS selectors\n"

                    if self.debug:
                        error_msg += f"\n\n**Debug files saved to:**\n{self.debug_dir}\n"
                        error_msg += f"- Screenshots: {self.debug_timestamp}_*.png\n"
                        error_msg += f"- HTML: {self.debug_timestamp}_page_content.html\n"
                        error_msg += f"- Form detection: {self.debug_timestamp}_form_detection.json\n"

                    result['message'] = error_msg
                    return result

                if self.debug:
                    print(f"[DEBUG] Form detected - username: {form['username']}, password: {form['password']}, submit: {form['submit']}")

                # Fill username
                await self.page.fill(form['username'], username)
                await self._save_debug_screenshot(self.page, "3_username_filled")

                # Fill password
                await self.page.fill(form['password'], password)
                await self._save_debug_screenshot(self.page, "4_password_filled")

                # Click submit button (or press Enter if no button found)
                if form['submit']:
                    await self.page.click(form['submit'])
                else:
                    # Press Enter on password field
                    await self.page.press(form['password'], 'Enter')

                await self._save_debug_screenshot(self.page, "5_form_submitted")

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

    async def login_with_selectors(
        self,
        url: str,
        username: str,
        password: str,
        username_selector: str,
        password_selector: str,
        submit_selector: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Login using manually specified CSS selectors (Phase 4.4.5).

        Use this when automatic form detection fails.

        Args:
            url: Login page URL
            username: Username/email
            password: Password
            username_selector: CSS selector for username field (e.g., '#username')
            password_selector: CSS selector for password field (e.g., '#password')
            submit_selector: CSS selector for submit button (optional)

        Returns:
            Dictionary with login result

        Example:
            result = await browser_auth.login_with_selectors(
                url="http://example.com/login",
                username="user",
                password="pass",
                username_selector='#user_login',
                password_selector='#user_pass',
                submit_selector='#wp-submit'
            )
        """
        result = {
            'success': False,
            'message': '',
            'cookies': None,
            'requires_2fa': False,
            'has_captcha': False
        }

        try:
            async with async_playwright() as p:
                self.browser = await p.chromium.launch(headless=self.headless)
                self.page = await self.browser.new_page()

                # Navigate to URL
                await self.page.goto(url, timeout=self.timeout)
                await self._save_debug_screenshot(self.page, "manual_selector_page")

                # Check for CAPTCHA
                if await self._detect_captcha(self.page):
                    result['has_captcha'] = True
                    result['message'] = "CAPTCHA detected. Please complete CAPTCHA manually."
                    return result

                # Fill username
                await self.page.fill(username_selector, username)
                await self._save_debug_screenshot(self.page, "manual_selector_username_filled")

                # Fill password
                await self.page.fill(password_selector, password)
                await self._save_debug_screenshot(self.page, "manual_selector_password_filled")

                # Submit
                if submit_selector:
                    await self.page.click(submit_selector)
                else:
                    # Press Enter on password field
                    await self.page.press(password_selector, 'Enter')

                await self._save_debug_screenshot(self.page, "manual_selector_submitted")

                # Wait for navigation
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeout:
                    pass

                # Check for 2FA
                if await self._detect_2fa(self.page):
                    result['requires_2fa'] = True
                    result['message'] = "2FA required. Please enter verification code manually."
                    result['cookies'] = await self.page.context.cookies()
                    return result

                # Check if login successful
                current_url = self.page.url

                # Look for error messages
                error_indicators = [
                    'text="incorrect password" i',
                    'text="invalid credentials" i',
                    'text="login failed" i',
                    'div[class*="error"]'
                ]

                has_error = False
                for selector in error_indicators:
                    if await self.page.locator(selector).count() > 0:
                        has_error = True
                        break

                if has_error:
                    result['message'] = "Login failed. Incorrect username or password."
                    return result

                # If redirected or has logout button, assume success
                if current_url != url:
                    result['success'] = True
                    result['message'] = f"Login successful! (manual selectors)"
                    result['cookies'] = await self.page.context.cookies()
                else:
                    # Check for logout button
                    success_indicators = [
                        'text="logout" i',
                        'text="sign out" i',
                        'a[href*="logout"]'
                    ]

                    for selector in success_indicators:
                        if await self.page.locator(selector).count() > 0:
                            result['success'] = True
                            result['message'] = "Login successful! (manual selectors)"
                            result['cookies'] = await self.page.context.cookies()
                            break

                    if not result['success']:
                        result['message'] = "Login status unclear with manual selectors."

        except Exception as e:
            result['message'] = f"Error during manual selector login: {str(e)}"

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
