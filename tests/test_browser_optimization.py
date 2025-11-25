"""
Tests for Browser Optimization System

Tests the integrated browser automation optimization system including:
- Progressive timeout strategies
- Site-specific optimization profiles
- Environment variable support
- Browser controller integration
"""

import os
import pytest
from unittest.mock import patch

from wyn360_cli.config import (
    WYN360Config,
    get_progressive_timeout,
    get_site_profile,
    load_env_config
)
from wyn360_cli.browser_controller import BrowserConfig


class TestProgressiveTimeouts:
    """Test progressive timeout strategy"""

    def test_progressive_timeout_calculation(self):
        """Test progressive timeout strategy calculations"""
        base_timeout = 30000

        # Test progressive multipliers
        assert get_progressive_timeout(base_timeout, 0, "progressive") == 15000  # 50%
        assert get_progressive_timeout(base_timeout, 1, "progressive") == 30000  # 100%
        assert get_progressive_timeout(base_timeout, 2, "progressive") == 45000  # 150%
        assert get_progressive_timeout(base_timeout, 3, "progressive") == 60000  # 200%

    def test_fixed_timeout_strategy(self):
        """Test fixed timeout strategy (no progression)"""
        base_timeout = 30000

        # Should return base timeout for all attempts
        assert get_progressive_timeout(base_timeout, 0, "fixed") == 30000
        assert get_progressive_timeout(base_timeout, 1, "fixed") == 30000
        assert get_progressive_timeout(base_timeout, 5, "fixed") == 30000

    def test_progressive_timeout_bounds(self):
        """Test progressive timeout with attempt beyond multiplier array"""
        base_timeout = 40000

        # Beyond array bounds should use last multiplier
        assert get_progressive_timeout(base_timeout, 10, "progressive") == 80000  # 200%


class TestSiteProfiles:
    """Test site-specific optimization profiles"""

    def test_amazon_optimization(self):
        """Test Amazon site optimization"""
        profile = get_site_profile("https://www.amazon.com/product/123", True)

        assert profile["browser_navigation_timeout"] == 60000  # Longer timeout
        assert profile["browser_action_timeout"] == 20000
        assert profile["browser_wait_after_navigation"] == 5.0  # Extra wait
        assert profile["browser_max_retries"] == 3  # More retries

    def test_github_optimization(self):
        """Test GitHub (fast site) optimization"""
        profile = get_site_profile("https://github.com/user/repo", True)

        assert profile["browser_navigation_timeout"] == 30000  # Faster timeout
        assert profile["browser_action_timeout"] == 10000
        assert profile["browser_wait_strategy"] == "load"  # Fast wait strategy
        assert profile["browser_wait_after_navigation"] == 1.0

    def test_ecommerce_optimization(self):
        """Test standard e-commerce site optimization"""
        profile = get_site_profile("https://walmart.com/product", True)

        assert profile["browser_navigation_timeout"] == 45000  # Balanced
        assert profile["browser_action_timeout"] == 15000
        assert profile["browser_wait_after_navigation"] == 3.0

    def test_unknown_site(self):
        """Test unknown site returns no profile"""
        profile = get_site_profile("https://unknown-site.com", True)
        assert profile == {}

    def test_auto_detection_disabled(self):
        """Test site profile with auto-detection disabled"""
        profile = get_site_profile("https://amazon.com", False)
        assert profile == {}


class TestEnvironmentVariables:
    """Test environment variable configuration"""

    def test_timeout_environment_variables(self):
        """Test timeout environment variable loading"""
        with patch.dict(os.environ, {
            'WYN360_NAVIGATION_TIMEOUT': '50000',
            'WYN360_ACTION_TIMEOUT': '25000',
            'WYN360_DEFAULT_TIMEOUT': '35000'
        }):
            env_config = load_env_config()

            assert env_config["browser_navigation_timeout"] == 50000
            assert env_config["browser_action_timeout"] == 25000
            assert env_config["browser_default_timeout"] == 35000

    def test_retry_environment_variables(self):
        """Test retry environment variable loading"""
        with patch.dict(os.environ, {
            'WYN360_MAX_RETRIES': '4',
            'WYN360_RETRY_DELAY': '2.5'
        }):
            env_config = load_env_config()

            assert env_config["browser_max_retries"] == 4
            assert env_config["browser_retry_delay"] == 2.5

    def test_strategy_environment_variables(self):
        """Test strategy environment variable loading"""
        with patch.dict(os.environ, {
            'WYN360_TIMEOUT_STRATEGY': 'fixed',
            'WYN360_WAIT_STRATEGY': 'networkidle'
        }):
            env_config = load_env_config()

            assert env_config["browser_timeout_strategy"] == "fixed"
            assert env_config["browser_wait_strategy"] == "networkidle"

    def test_boolean_environment_variables(self):
        """Test boolean environment variable loading"""
        with patch.dict(os.environ, {
            'WYN360_ENABLE_STEALTH': 'false',
            'WYN360_AUTO_SITE_DETECTION': 'true'
        }):
            env_config = load_env_config()

            assert env_config["browser_enable_stealth"] is False
            assert env_config["browser_auto_site_detection"] is True

    def test_invalid_environment_variables(self):
        """Test handling of invalid environment variables"""
        with patch.dict(os.environ, {
            'WYN360_TIMEOUT_STRATEGY': 'invalid_strategy',
            'WYN360_WAIT_STRATEGY': 'invalid_wait'
        }):
            env_config = load_env_config()

            # Invalid values should not be included
            assert "browser_timeout_strategy" not in env_config
            assert "browser_wait_strategy" not in env_config


class TestBrowserControllerIntegration:
    """Test integration with BrowserController"""

    def test_browser_config_timeout_retrieval(self):
        """Test BrowserConfig timeout retrieval with defaults"""
        # Test fallback to static configuration (when config loading fails)
        with patch.object(BrowserConfig, 'get_config', return_value=None):
            timeout = BrowserConfig.get_timeout('navigation', '', 0)
            assert timeout == 45000  # Static fallback

    def test_browser_config_with_dynamic_config(self):
        """Test BrowserConfig with dynamic configuration"""
        mock_config = WYN360Config()
        mock_config.browser_navigation_timeout = 50000
        mock_config.browser_timeout_strategy = "progressive"
        mock_config.browser_auto_site_detection = True

        with patch.object(BrowserConfig, 'get_config', return_value=mock_config):
            # Test without site profile
            timeout = BrowserConfig.get_timeout('navigation', 'https://example.com', 0)
            assert timeout == 25000  # 50% of 50000 (progressive, attempt 0)

    def test_browser_config_with_site_profile(self):
        """Test BrowserConfig with site-specific optimization"""
        mock_config = WYN360Config()
        mock_config.browser_navigation_timeout = 45000
        mock_config.browser_timeout_strategy = "progressive"
        mock_config.browser_auto_site_detection = True

        with patch.object(BrowserConfig, 'get_config', return_value=mock_config):
            # Amazon URL should get site-specific timeout
            timeout = BrowserConfig.get_timeout('navigation', 'https://amazon.com/product', 1)
            # Amazon profile: 60000ms, progressive attempt 1 (100%) = 60000ms
            assert timeout == 60000

    def test_browser_config_retry_settings(self):
        """Test BrowserConfig retry settings"""
        mock_config = WYN360Config()
        mock_config.browser_max_retries = 3
        mock_config.browser_retry_delay = 2.0
        mock_config.browser_auto_site_detection = True

        with patch.object(BrowserConfig, 'get_config', return_value=mock_config):
            retries = BrowserConfig.get_retries('https://amazon.com')
            # Amazon profile overrides to 3 retries
            assert retries == 3

            delay = BrowserConfig.get_retry_delay('https://example.com')
            assert delay == 2.0

    def test_browser_config_wait_settings(self):
        """Test BrowserConfig wait settings"""
        mock_config = WYN360Config()
        mock_config.browser_wait_after_navigation = 2.5
        mock_config.browser_wait_after_action = 1.5
        mock_config.browser_wait_strategy = "domcontentloaded"
        mock_config.browser_auto_site_detection = True

        with patch.object(BrowserConfig, 'get_config', return_value=mock_config):
            wait_nav = BrowserConfig.get_wait_after_navigation('https://github.com')
            # GitHub profile overrides to 1.0
            assert wait_nav == 1.0

            wait_action = BrowserConfig.get_wait_after_action('')
            assert wait_action == 1.5

            strategy = BrowserConfig.get_wait_strategy('https://github.com')
            # GitHub profile overrides to "load"
            assert strategy == "load"


class TestConfigurationDefaults:
    """Test default configuration values"""

    def test_optimized_defaults(self):
        """Test that defaults are optimized compared to previous version"""
        config = WYN360Config()

        # These should be optimized (reduced) from previous version
        assert config.browser_navigation_timeout == 45000  # Was 90000
        assert config.browser_action_timeout == 15000      # Was 20000
        assert config.browser_default_timeout == 30000     # Was 45000
        assert config.browser_max_retries == 2             # Was 3
        assert config.browser_retry_delay == 1.5           # Was 2.0
        assert config.browser_wait_after_navigation == 2.0 # Was 3.0
        assert config.browser_wait_after_action == 1.0     # Was 1.5

    def test_improved_strategies(self):
        """Test that default strategies are improved"""
        config = WYN360Config()

        # These should use better strategies
        assert config.browser_timeout_strategy == "progressive"  # Was fixed
        assert config.browser_wait_strategy == "domcontentloaded"  # Was networkidle
        assert config.browser_enable_stealth is True
        assert config.browser_auto_site_detection is True


if __name__ == "__main__":
    pytest.main([__file__])