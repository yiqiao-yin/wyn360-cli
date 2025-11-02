"""
WYN360 CLI - An intelligent AI coding assistant powered by Anthropic Claude.

This package provides a command-line interface for interacting with Claude
to build projects, generate code, and improve your codebase.
"""

__version__ = "0.1.1"
__author__ = "Yiqiao Yin"
__email__ = "eagle0504@gmail.com"

from .agent import WYN360Agent
from .cli import main

__all__ = ["WYN360Agent", "main"]
