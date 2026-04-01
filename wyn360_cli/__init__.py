"""
WYN360 CLI - An intelligent AI coding assistant powered by Anthropic Claude.

This package provides a command-line interface for interacting with Claude
to build projects, generate code, and improve your codebase.
"""

__version__ = "0.5.1"
__author__ = "Yiqiao Yin"
__email__ = "yiqiao.yin@wyn-associates.com"

from .agent import WYN360Agent
from .cli import main
from .memory import MemoryManager
from .subagent import SubAgentManager
from .planner import Planner
from .token_budget import TokenBudgetManager
from .skills import SkillRegistry
from .hooks import HookManager
from .dream import DreamManager
from .compaction import CompactionManager
from .vim_mode import VimModeManager
from .voice import VoiceInputManager
from .buddy import BuddyManager
from .cron_agent import CronManager
from .plugin_system import PluginManager
from .lsp_client import LSPClient
from .rewind import RewindManager

__all__ = [
    "WYN360Agent", "main",
    "MemoryManager", "SubAgentManager", "Planner",
    "TokenBudgetManager", "SkillRegistry", "HookManager",
    "DreamManager", "CompactionManager", "VimModeManager",
    "VoiceInputManager", "BuddyManager", "CronManager",
    "PluginManager", "LSPClient", "RewindManager",
]
