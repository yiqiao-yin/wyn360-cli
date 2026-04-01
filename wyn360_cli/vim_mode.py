"""
WYN360 Vim Mode - Vim keybindings for terminal input.

Provides a vi-style editing experience in the prompt input,
with normal/insert mode, motions, and common operators.
"""

import logging
from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass, field
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.enums import EditingMode

logger = logging.getLogger(__name__)


class VimModeState(Enum):
    NORMAL = "NORMAL"
    INSERT = "INSERT"
    VISUAL = "VISUAL"


@dataclass
class VimConfig:
    """Vim mode configuration."""
    enabled: bool = False
    show_mode_indicator: bool = True
    jk_escape: bool = True  # Map 'jk' to Escape in insert mode


class VimModeManager:
    """Manages vim keybindings for prompt_toolkit."""

    def __init__(self, config: Optional[VimConfig] = None):
        self.config = config or VimConfig()
        self._mode = VimModeState.INSERT
        self._status_callback: Optional[Callable[[str], None]] = None

    @property
    def mode(self) -> VimModeState:
        return self._mode

    @property
    def mode_indicator(self) -> str:
        """Get mode indicator string for the status bar."""
        if not self.config.enabled:
            return ""
        indicators = {
            VimModeState.NORMAL: "-- NORMAL --",
            VimModeState.INSERT: "-- INSERT --",
            VimModeState.VISUAL: "-- VISUAL --",
        }
        return indicators.get(self._mode, "")

    def get_editing_mode(self) -> EditingMode:
        """Get the prompt_toolkit editing mode."""
        if self.config.enabled:
            return EditingMode.VI
        return EditingMode.EMACS

    def toggle(self) -> bool:
        """Toggle vim mode on/off. Returns new state."""
        self.config.enabled = not self.config.enabled
        if not self.config.enabled:
            self._mode = VimModeState.INSERT
        return self.config.enabled

    def enable(self):
        """Enable vim mode."""
        self.config.enabled = True

    def disable(self):
        """Disable vim mode."""
        self.config.enabled = False
        self._mode = VimModeState.INSERT

    def get_status(self) -> dict:
        """Get current vim mode status."""
        return {
            "enabled": self.config.enabled,
            "mode": self._mode.value if self.config.enabled else "DISABLED",
            "jk_escape": self.config.jk_escape,
        }
