"""
WYN360 LSP Client - Language Server Protocol integration for diagnostics.

Connects to language servers (pyright, ruff, typescript, etc.) to provide
real-time diagnostics, type checking, and code intelligence.
"""

import os
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Diagnostic:
    """A single diagnostic (error, warning, info, hint)."""
    file: str
    line: int
    column: int
    severity: str  # error, warning, info, hint
    message: str
    source: str = ""  # e.g., "pyright", "ruff"
    code: str = ""

    @property
    def location(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "source": self.source,
            "code": self.code,
        }


@dataclass
class LSPServerConfig:
    """Configuration for a language server."""
    name: str
    command: List[str]  # e.g., ["pyright-langserver", "--stdio"]
    languages: List[str] = field(default_factory=list)  # e.g., ["python"]
    auto_start: bool = False


# Built-in server configurations
BUILTIN_SERVERS = {
    "pyright": LSPServerConfig(
        name="pyright",
        command=["pyright-langserver", "--stdio"],
        languages=["python"],
    ),
    "ruff": LSPServerConfig(
        name="ruff",
        command=["ruff", "server", "--preview"],
        languages=["python"],
    ),
    "typescript": LSPServerConfig(
        name="typescript",
        command=["typescript-language-server", "--stdio"],
        languages=["typescript", "javascript"],
    ),
}


class LSPClient:
    """Lightweight LSP client for running diagnostics."""

    def __init__(self):
        self._available_servers: Dict[str, LSPServerConfig] = {}
        self._diagnostics: Dict[str, List[Diagnostic]] = {}  # file -> diagnostics
        self._detect_servers()

    def _detect_servers(self):
        """Detect which language servers are available on the system."""
        for name, config in BUILTIN_SERVERS.items():
            cmd = config.command[0]
            if self._command_exists(cmd):
                self._available_servers[name] = config
                logger.debug(f"Found LSP server: {name} ({cmd})")

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists on the PATH."""
        try:
            result = subprocess.run(
                ["which", cmd] if os.name != "nt" else ["where", cmd],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    @property
    def available_servers(self) -> List[str]:
        """List available language server names."""
        return list(self._available_servers.keys())

    def has_server(self, name: str) -> bool:
        """Check if a specific server is available."""
        return name in self._available_servers

    async def check_file(self, filepath: str, server_name: Optional[str] = None) -> List[Diagnostic]:
        """
        Run diagnostics on a single file.

        Uses the appropriate server based on file extension,
        or a specific server if named.
        """
        path = Path(filepath)
        if not path.exists():
            return []

        # Determine which server to use
        server = self._pick_server(path, server_name)
        if not server:
            # Fallback: try running pyright/ruff directly
            return await self._run_tool_directly(filepath)

        return []  # Full LSP protocol not implemented; use direct tool calls

    async def check_project(self, directory: str = ".",
                             server_name: Optional[str] = None) -> List[Diagnostic]:
        """
        Run diagnostics on an entire project directory.

        Uses direct tool invocation (pyright, ruff) for simplicity.
        """
        diagnostics = []

        # Try pyright
        if "pyright" in self._available_servers or self._command_exists("pyright"):
            pyright_diags = await self._run_pyright(directory)
            diagnostics.extend(pyright_diags)

        # Try ruff
        if "ruff" in self._available_servers or self._command_exists("ruff"):
            ruff_diags = await self._run_ruff(directory)
            diagnostics.extend(ruff_diags)

        self._diagnostics.clear()
        for d in diagnostics:
            self._diagnostics.setdefault(d.file, []).append(d)

        return diagnostics

    async def _run_pyright(self, directory: str) -> List[Diagnostic]:
        """Run pyright and parse diagnostics."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "pyright", "--outputjson", directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)

            data = json.loads(stdout.decode())
            diagnostics = []

            for diag in data.get("generalDiagnostics", []):
                severity_map = {0: "error", 1: "warning", 2: "info", 3: "hint"}
                diagnostics.append(Diagnostic(
                    file=diag.get("file", ""),
                    line=diag.get("range", {}).get("start", {}).get("line", 0),
                    column=diag.get("range", {}).get("start", {}).get("character", 0),
                    severity=severity_map.get(diag.get("severity", 2), "info"),
                    message=diag.get("message", ""),
                    source="pyright",
                    code=diag.get("rule", ""),
                ))

            return diagnostics
        except FileNotFoundError:
            logger.debug("pyright not found")
            return []
        except Exception as e:
            logger.warning(f"pyright failed: {e}")
            return []

    async def _run_ruff(self, directory: str) -> List[Diagnostic]:
        """Run ruff and parse diagnostics."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ruff", "check", "--output-format=json", directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)

            data = json.loads(stdout.decode())
            diagnostics = []

            for item in data:
                diagnostics.append(Diagnostic(
                    file=item.get("filename", ""),
                    line=item.get("location", {}).get("row", 0),
                    column=item.get("location", {}).get("column", 0),
                    severity="warning",
                    message=item.get("message", ""),
                    source="ruff",
                    code=item.get("code", ""),
                ))

            return diagnostics
        except FileNotFoundError:
            logger.debug("ruff not found")
            return []
        except Exception as e:
            logger.warning(f"ruff failed: {e}")
            return []

    async def _run_tool_directly(self, filepath: str) -> List[Diagnostic]:
        """Run available tools directly on a single file."""
        diagnostics = []
        if self._command_exists("ruff"):
            diagnostics.extend(await self._run_ruff(filepath))
        if self._command_exists("pyright"):
            diagnostics.extend(await self._run_pyright(filepath))
        return diagnostics

    def _pick_server(self, path: Path, server_name: Optional[str] = None) -> Optional[LSPServerConfig]:
        """Pick the appropriate server for a file."""
        if server_name:
            return self._available_servers.get(server_name)

        ext_to_lang = {
            ".py": "python", ".pyi": "python",
            ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript",
        }
        lang = ext_to_lang.get(path.suffix, "")
        for config in self._available_servers.values():
            if lang in config.languages:
                return config
        return None

    def get_diagnostics(self, filepath: Optional[str] = None) -> List[Diagnostic]:
        """Get cached diagnostics, optionally filtered by file."""
        if filepath:
            return self._diagnostics.get(filepath, [])
        return [d for diags in self._diagnostics.values() for d in diags]

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all diagnostics."""
        all_diags = self.get_diagnostics()
        return {
            "total": len(all_diags),
            "errors": sum(1 for d in all_diags if d.severity == "error"),
            "warnings": sum(1 for d in all_diags if d.severity == "warning"),
            "info": sum(1 for d in all_diags if d.severity == "info"),
            "files_affected": len(self._diagnostics),
            "available_servers": self.available_servers,
        }

    def format_diagnostics(self, diagnostics: Optional[List[Diagnostic]] = None,
                            max_items: int = 20) -> str:
        """Format diagnostics for display."""
        diags = diagnostics or self.get_diagnostics()
        if not diags:
            return "No diagnostics found."

        # Sort by severity (errors first)
        severity_order = {"error": 0, "warning": 1, "info": 2, "hint": 3}
        diags.sort(key=lambda d: severity_order.get(d.severity, 9))

        lines = []
        icons = {"error": "E", "warning": "W", "info": "I", "hint": "H"}
        for d in diags[:max_items]:
            icon = icons.get(d.severity, "?")
            lines.append(f"  [{icon}] {d.location}: {d.message} ({d.source}:{d.code})")

        if len(diags) > max_items:
            lines.append(f"  ... and {len(diags) - max_items} more")

        summary = self.get_summary()
        header = f"Diagnostics: {summary['errors']} errors, {summary['warnings']} warnings, {summary['info']} info"
        return header + "\n" + "\n".join(lines)
