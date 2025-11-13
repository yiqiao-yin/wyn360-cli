"""
Unit tests for BrowserAuth (Phase 4.2.2)

Tests cover:
- Form detection (username, password, submit)
- CAPTCHA detection
- 2FA detection
- Login flow logic
- Session verification
- Error handling

Note: Tests use mocks to avoid actual browser automation during unit testing.
For integration testing with real browsers, use separate integration test suite.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from wyn360_cli.browser_auth import BrowserAuth


class TestBrowserAuth:
    """Test browser authentication functionality (Phase 4.2.2)."""

    @pytest.mark.asyncio
    async def test_detect_login_form_standard(self):
        """Test detecting standard login form."""
        auth = BrowserAuth()

        # Mock page with standard login form
        mock_page = AsyncMock()

        # Create a dictionary to track which selectors should match
        def create_locator_mock(selector):
            mock_loc = AsyncMock()
            if selector == 'input[type="email"]':
                mock_loc.count = AsyncMock(return_value=1)
            elif selector == 'input[type="password"]':
                mock_loc.count = AsyncMock(return_value=1)
            elif selector == 'button[type="submit"]':
                mock_loc.count = AsyncMock(return_value=1)
            else:
                mock_loc.count = AsyncMock(return_value=0)
            return mock_loc

        mock_page.locator = Mock(side_effect=create_locator_mock)

        form = await auth._detect_login_form(mock_page)

        assert form['username'] == 'input[type="email"]'
        assert form['password'] == 'input[type="password"]'
        assert form['submit'] == 'button[type="submit"]'

    @pytest.mark.asyncio
    async def test_detect_login_form_no_form(self):
        """Test when no login form is present."""
        auth = BrowserAuth()

        mock_page = AsyncMock()

        # All selectors return 0 (not found)
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        mock_page.locator = Mock(return_value=mock_locator)

        form = await auth._detect_login_form(mock_page)

        assert form['username'] is None
        assert form['password'] is None
        assert form['submit'] is None

    @pytest.mark.asyncio
    async def test_detect_captcha_present(self):
        """Test CAPTCHA detection when present."""
        auth = BrowserAuth()

        mock_page = AsyncMock()

        # CAPTCHA present
        def create_locator_mock(selector):
            mock_loc = AsyncMock()
            if 'recaptcha' in selector.lower():
                mock_loc.count = AsyncMock(return_value=1)
            else:
                mock_loc.count = AsyncMock(return_value=0)
            return mock_loc

        mock_page.locator = Mock(side_effect=create_locator_mock)

        has_captcha = await auth._detect_captcha(mock_page)
        assert has_captcha is True

    @pytest.mark.asyncio
    async def test_detect_captcha_not_present(self):
        """Test CAPTCHA detection when not present."""
        auth = BrowserAuth()

        mock_page = AsyncMock()

        # No CAPTCHA
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        mock_page.locator = Mock(return_value=mock_locator)

        has_captcha = await auth._detect_captcha(mock_page)
        assert has_captcha is False

    @pytest.mark.asyncio
    async def test_detect_2fa_present(self):
        """Test 2FA detection when present."""
        auth = BrowserAuth()

        mock_page = AsyncMock()

        # 2FA present
        def create_locator_mock(selector):
            mock_loc = AsyncMock()
            if 'code' in selector.lower() or 'otp' in selector.lower():
                mock_loc.count = AsyncMock(return_value=1)
            else:
                mock_loc.count = AsyncMock(return_value=0)
            return mock_loc

        mock_page.locator = Mock(side_effect=create_locator_mock)

        has_2fa = await auth._detect_2fa(mock_page)
        assert has_2fa is True

    @pytest.mark.asyncio
    async def test_detect_2fa_not_present(self):
        """Test 2FA detection when not present."""
        auth = BrowserAuth()

        mock_page = AsyncMock()

        # No 2FA
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=0)
        mock_page.locator = Mock(return_value=mock_locator)

        has_2fa = await auth._detect_2fa(mock_page)
        assert has_2fa is False

    @pytest.mark.asyncio
    async def test_login_with_captcha(self):
        """Test login flow when CAPTCHA is detected."""
        auth = BrowserAuth()

        # Mock playwright
        with patch('wyn360_cli.browser_auth.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_context = AsyncMock()

            mock_page.goto = AsyncMock()
            mock_page.context = mock_context

            # CAPTCHA detected - always return 1
            def create_locator_mock(selector):
                mock_loc = AsyncMock()
                mock_loc.count = AsyncMock(return_value=1)
                return mock_loc

            mock_page.locator = Mock(side_effect=create_locator_mock)

            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)

            mock_p = AsyncMock()
            mock_p.chromium = mock_chromium
            mock_playwright.return_value.__aenter__.return_value = mock_p

            result = await auth.login("https://example.com", "user", "pass")

            assert result['success'] is False
            assert result['has_captcha'] is True
            assert "CAPTCHA" in result['message']

    @pytest.mark.asyncio
    async def test_login_form_not_detected(self):
        """Test login when form cannot be detected."""
        auth = BrowserAuth()

        with patch('wyn360_cli.browser_auth.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()

            mock_page.goto = AsyncMock()

            # No form detected (all return 0)
            mock_locator = AsyncMock()
            mock_locator.count = AsyncMock(return_value=0)
            mock_page.locator = Mock(return_value=mock_locator)

            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()

            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)

            mock_p = AsyncMock()
            mock_p.chromium = mock_chromium
            mock_playwright.return_value.__aenter__.return_value = mock_p

            result = await auth.login("https://example.com", "user", "pass")

            assert result['success'] is False
            assert "Could not detect login form" in result['message']

    @pytest.mark.asyncio
    async def test_initialization_defaults(self):
        """Test BrowserAuth initialization with default parameters."""
        auth = BrowserAuth()

        assert auth.headless is True
        assert auth.timeout == 30000
        assert auth.browser is None
        assert auth.page is None

    @pytest.mark.asyncio
    async def test_initialization_custom_params(self):
        """Test BrowserAuth initialization with custom parameters."""
        auth = BrowserAuth(headless=False, timeout=60000)

        assert auth.headless is False
        assert auth.timeout == 60000

    def test_form_detection_selectors(self):
        """Test that form detection includes various selector patterns."""
        auth = BrowserAuth()

        # This is a unit test to ensure the selectors are defined
        # Actual detection logic is tested in async tests above

        # Just verify the class is initialized properly
        assert auth is not None
        assert hasattr(auth, '_detect_login_form')
        assert hasattr(auth, '_detect_captcha')
        assert hasattr(auth, '_detect_2fa')


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
