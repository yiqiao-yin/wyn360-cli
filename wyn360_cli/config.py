"""Configuration management for WYN360 CLI.

This module handles loading and merging configuration from:
1. User config: ~/.wyn360/config.yaml
2. Project config: .wyn360.yaml (in current directory)
3. Default values

Configuration precedence (highest to lowest):
- Project config (.wyn360.yaml)
- User config (~/.wyn360/config.yaml)
- Default values
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class WYN360Config:
    """Configuration for WYN360 CLI."""

    # Model settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Custom system prompt additions
    custom_instructions: str = ""

    # Project context (from .wyn360.yaml)
    project_context: str = ""
    project_dependencies: list = field(default_factory=list)
    project_commands: Dict[str, str] = field(default_factory=dict)

    # User shortcuts/aliases (from ~/.wyn360/config.yaml)
    aliases: Dict[str, str] = field(default_factory=dict)
    workspaces: list = field(default_factory=list)

    # Browser use settings (Phase 12.1)
    browser_use_max_tokens: int = 50000
    browser_use_truncate_strategy: str = "smart"  # smart, head, tail
    browser_use_cache_enabled: bool = True
    browser_use_cache_ttl: int = 1800  # 30 minutes
    browser_use_cache_max_size_mb: int = 100

    # Browser automation optimization settings (v0.3.69)
    browser_navigation_timeout: int = 45000      # Navigation timeout (ms) - Optimized from 90s
    browser_action_timeout: int = 15000          # Action timeout (ms) - Optimized from 20s
    browser_default_timeout: int = 30000         # Default timeout (ms) - Optimized from 45s
    browser_max_retries: int = 2                 # Max retry attempts - Optimized from 3
    browser_retry_delay: float = 1.5             # Retry delay (seconds) - Optimized from 2s
    browser_timeout_strategy: str = "progressive"  # fixed|progressive|adaptive
    browser_wait_strategy: str = "domcontentloaded"  # load|domcontentloaded|networkidle|commit
    browser_wait_after_navigation: float = 2.0   # Wait after navigation (seconds) - Optimized from 3s
    browser_wait_after_action: float = 1.0       # Wait after action (seconds) - Optimized from 1.5s
    browser_enable_stealth: bool = True           # Enable anti-detection measures
    browser_auto_site_detection: bool = True     # Auto-detect site-specific optimizations

    # Config file paths (for reference)
    user_config_path: Optional[str] = None
    project_config_path: Optional[str] = None


def get_user_config_path() -> Path:
    """Get the path to the user configuration file."""
    return Path.home() / ".wyn360" / "config.yaml"


def get_project_config_path() -> Optional[Path]:
    """Get the path to the project configuration file in current directory."""
    project_config = Path.cwd() / ".wyn360.yaml"
    if project_config.exists():
        return project_config
    return None


def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a YAML file and return its contents as a dictionary.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dictionary containing the YAML contents, or None if file doesn't exist or has errors
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError as e:
        print(f"Warning: Error parsing {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Error reading {file_path}: {e}")
        return None


def load_user_config() -> Dict[str, Any]:
    """
    Load user configuration from ~/.wyn360/config.yaml.

    Returns:
        Dictionary containing user configuration, or empty dict if not found
    """
    user_config_path = get_user_config_path()
    config = load_yaml_file(user_config_path)
    return config if config else {}


def load_project_config() -> Dict[str, Any]:
    """
    Load project configuration from .wyn360.yaml in current directory.

    Returns:
        Dictionary containing project configuration, or empty dict if not found
    """
    project_config_path = get_project_config_path()
    if not project_config_path:
        return {}

    config = load_yaml_file(project_config_path)
    return config if config else {}


def merge_configs(user_config: Dict[str, Any], project_config: Dict[str, Any]) -> WYN360Config:
    """
    Merge user and project configurations with default values.

    Configuration precedence (highest to lowest):
    1. Project config (.wyn360.yaml)
    2. User config (~/.wyn360/config.yaml)
    3. Default values

    Args:
        user_config: User configuration dictionary
        project_config: Project configuration dictionary

    Returns:
        WYN360Config object with merged configuration
    """
    config = WYN360Config()

    # Apply user config (overrides defaults)
    if user_config:
        config.model = user_config.get("model", config.model)
        config.max_tokens = user_config.get("max_tokens", config.max_tokens)
        config.temperature = user_config.get("temperature", config.temperature)
        config.custom_instructions = user_config.get("custom_instructions", "")
        config.aliases = user_config.get("aliases", {})
        config.workspaces = user_config.get("workspaces", [])

        # Browser use settings
        browser_use_config = user_config.get("browser_use", {})
        if browser_use_config:
            config.browser_use_max_tokens = browser_use_config.get("max_tokens", config.browser_use_max_tokens)
            config.browser_use_truncate_strategy = browser_use_config.get("truncate_strategy", config.browser_use_truncate_strategy)
            cache_config = browser_use_config.get("cache", {})
            if cache_config:
                config.browser_use_cache_enabled = cache_config.get("enabled", config.browser_use_cache_enabled)
                config.browser_use_cache_ttl = cache_config.get("ttl", config.browser_use_cache_ttl)
                config.browser_use_cache_max_size_mb = cache_config.get("max_size_mb", config.browser_use_cache_max_size_mb)

        config.user_config_path = str(get_user_config_path()) if get_user_config_path().exists() else None

    # Apply project config (overrides user config and defaults)
    if project_config:
        # Project can override model settings
        config.model = project_config.get("model", config.model)
        config.max_tokens = project_config.get("max_tokens", config.max_tokens)
        config.temperature = project_config.get("temperature", config.temperature)

        # Project-specific fields
        config.project_context = project_config.get("context", "")
        config.project_dependencies = project_config.get("dependencies", [])
        config.project_commands = project_config.get("commands", {})

        # Project can add to custom instructions
        project_instructions = project_config.get("custom_instructions", "")
        if project_instructions:
            if config.custom_instructions:
                config.custom_instructions += "\n\n" + project_instructions
            else:
                config.custom_instructions = project_instructions

        project_config_path = get_project_config_path()
        config.project_config_path = str(project_config_path) if project_config_path else None

    return config


def load_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.

    Supports browser automation optimization settings with WYN360_ prefix.

    Returns:
        Dictionary with environment variable configuration
    """
    env_config = {}

    # Browser automation timeouts
    if timeout := os.getenv("WYN360_NAVIGATION_TIMEOUT"):
        env_config["browser_navigation_timeout"] = int(timeout)

    if timeout := os.getenv("WYN360_ACTION_TIMEOUT"):
        env_config["browser_action_timeout"] = int(timeout)

    if timeout := os.getenv("WYN360_DEFAULT_TIMEOUT"):
        env_config["browser_default_timeout"] = int(timeout)

    # Retry settings
    if retries := os.getenv("WYN360_MAX_RETRIES"):
        env_config["browser_max_retries"] = int(retries)

    if delay := os.getenv("WYN360_RETRY_DELAY"):
        env_config["browser_retry_delay"] = float(delay)

    # Strategy settings
    if strategy := os.getenv("WYN360_TIMEOUT_STRATEGY"):
        if strategy.lower() in ["fixed", "progressive", "adaptive"]:
            env_config["browser_timeout_strategy"] = strategy.lower()

    if wait_strategy := os.getenv("WYN360_WAIT_STRATEGY"):
        if wait_strategy.lower() in ["load", "domcontentloaded", "networkidle", "commit"]:
            env_config["browser_wait_strategy"] = wait_strategy.lower()

    # Wait times
    if wait_nav := os.getenv("WYN360_WAIT_AFTER_NAVIGATION"):
        env_config["browser_wait_after_navigation"] = float(wait_nav)

    if wait_action := os.getenv("WYN360_WAIT_AFTER_ACTION"):
        env_config["browser_wait_after_action"] = float(wait_action)

    # Advanced settings
    if stealth := os.getenv("WYN360_ENABLE_STEALTH"):
        env_config["browser_enable_stealth"] = stealth.lower() in ("true", "1", "yes")

    if auto_detect := os.getenv("WYN360_AUTO_SITE_DETECTION"):
        env_config["browser_auto_site_detection"] = auto_detect.lower() in ("true", "1", "yes")

    return env_config


def get_progressive_timeout(base_timeout: int, attempt: int, strategy: str = "progressive") -> int:
    """
    Calculate timeout for progressive retry strategy.

    Args:
        base_timeout: Base timeout in milliseconds
        attempt: Retry attempt number (0-based)
        strategy: Timeout strategy ("fixed", "progressive", or "adaptive")

    Returns:
        Calculated timeout in milliseconds
    """
    if strategy != "progressive":
        return base_timeout

    # Progressive multipliers for attempts
    multipliers = [0.5, 1.0, 1.5, 2.0]
    multiplier_idx = min(attempt, len(multipliers) - 1)
    multiplier = multipliers[multiplier_idx]

    return int(base_timeout * multiplier)


def get_site_profile(url: str, auto_detection: bool = True) -> Dict[str, Any]:
    """
    Get site-specific optimization settings for a URL.

    Args:
        url: URL to get profile for
        auto_detection: Whether to enable automatic site detection

    Returns:
        Dictionary with site-specific settings (empty if no match)
    """
    if not auto_detection:
        return {}

    url_lower = url.lower()

    # Amazon and heavy e-commerce sites
    if any(domain in url_lower for domain in ["amazon.com", "amazon.co.uk", "amazon.de"]):
        return {
            "browser_navigation_timeout": 60000,
            "browser_action_timeout": 20000,
            "browser_wait_after_navigation": 5.0,
            "browser_max_retries": 3
        }

    # Fast, simple sites
    if any(domain in url_lower for domain in ["github.com", "stackoverflow.com", "wikipedia.org"]):
        return {
            "browser_navigation_timeout": 30000,
            "browser_action_timeout": 10000,
            "browser_wait_strategy": "load",
            "browser_wait_after_navigation": 1.0,
            "browser_max_retries": 2
        }

    # Standard e-commerce sites
    if any(domain in url_lower for domain in ["ebay.com", "walmart.com", "target.com", "bestbuy.com"]):
        return {
            "browser_navigation_timeout": 45000,
            "browser_action_timeout": 15000,
            "browser_wait_after_navigation": 3.0,
            "browser_max_retries": 2
        }

    return {}


def load_config() -> WYN360Config:
    """
    Load and merge all configuration sources.

    This is the main entry point for configuration loading.
    Configuration precedence (highest to lowest):
    1. Environment variables (WYN360_*)
    2. Project config (.wyn360.yaml)
    3. User config (~/.wyn360/config.yaml)
    4. Default values

    Returns:
        WYN360Config object with merged configuration from all sources
    """
    user_config = load_user_config()
    project_config = load_project_config()
    env_config = load_env_config()

    # Merge configs with environment having highest priority
    merged_config = merge_configs(user_config, project_config)

    # Apply environment variable overrides
    for key, value in env_config.items():
        setattr(merged_config, key, value)

    return merged_config


def create_default_user_config() -> bool:
    """
    Create a default user configuration file at ~/.wyn360/config.yaml.

    Returns:
        True if file was created, False if it already exists or there was an error
    """
    config_path = get_user_config_path()

    # Don't overwrite existing config
    if config_path.exists():
        return False

    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = """# WYN360 CLI User Configuration
# Location: ~/.wyn360/config.yaml

# Default model settings
model: claude-sonnet-4-20250514
max_tokens: 4096
temperature: 0.7

# Custom system prompt additions
# These instructions will be added to every conversation
custom_instructions: |
  - Always use type hints in Python code
  - Follow PEP 8 style guidelines
  - Add docstrings to all functions and classes

# Browser use settings (for website fetching)
browser_use:
  max_tokens: 50000  # Max tokens per fetched website (configurable)
  truncate_strategy: "smart"  # Options: smart, head, tail
  cache:
    enabled: true
    ttl: 1800  # Cache duration in seconds (30 minutes)
    max_size_mb: 100  # Maximum cache size in MB

# Command aliases for quick access
aliases:
  test: "run pytest tests/ -v"
  lint: "run ruff check ."
  format: "run ruff format ."

# Favorite workspace directories
workspaces:
  - ~/projects
  - ~/work
"""

    try:
        with open(config_path, 'w') as f:
            f.write(default_config)
        return True
    except Exception as e:
        print(f"Error creating default config: {e}")
        return False


def create_default_project_config() -> bool:
    """
    Create a default project configuration file at .wyn360.yaml in current directory.

    Returns:
        True if file was created, False if it already exists or there was an error
    """
    config_path = Path.cwd() / ".wyn360.yaml"

    # Don't overwrite existing config
    if config_path.exists():
        return False

    default_config = """# WYN360 CLI Project Configuration
# Location: .wyn360.yaml (in project root)

# Project-specific context
# This information helps the AI understand your project
context: |
  This is a [describe your project type] with:
  - [Key technology 1]
  - [Key technology 2]
  - [Key technology 3]

# Project dependencies
dependencies:
  - package1
  - package2
  - package3

# Common project commands
commands:
  dev: "python app.py"
  test: "pytest tests/"
  build: "python setup.py build"

# Optional: Override model settings for this project
# model: claude-3-5-haiku-20241022  # Use faster model for simple projects
# max_tokens: 8192
# temperature: 0.5
"""

    try:
        with open(config_path, 'w') as f:
            f.write(default_config)
        return True
    except Exception as e:
        print(f"Error creating default project config: {e}")
        return False
