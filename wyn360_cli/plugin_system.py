"""
WYN360 Plugin System - User-installable plugins.

Plugins are Python packages or single-file modules that extend WYN360
with new tools, skills, or hooks. They are installed in ~/.wyn360/plugins/.

Plugin manifest format (plugin.yaml):
  name: my-plugin
  version: 1.0.0
  description: What the plugin does
  author: Name
  entry_point: main.py  (or package name)
  type: tool | skill | hook
"""

import os
import sys
import json
import yaml
import shutil
import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    """Plugin metadata from plugin.yaml."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    entry_point: str = "main.py"
    plugin_type: str = "tool"  # tool, skill, hook
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True
    source: str = "local"  # local, git, pypi


@dataclass
class LoadedPlugin:
    """A plugin that has been loaded into memory."""
    manifest: PluginManifest
    module: Any = None
    path: str = ""
    loaded: bool = False
    error: Optional[str] = None


class PluginManager:
    """Manages plugin discovery, installation, and loading."""

    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or (Path.home() / ".wyn360" / "plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: Dict[str, LoadedPlugin] = {}
        self._registry_path = self.plugins_dir / "registry.json"

    def discover(self) -> List[PluginManifest]:
        """Discover all plugins in the plugins directory."""
        manifests = []
        for subdir in self.plugins_dir.iterdir():
            if not subdir.is_dir():
                continue
            manifest_path = subdir / "plugin.yaml"
            if not manifest_path.exists():
                manifest_path = subdir / "plugin.yml"
            if not manifest_path.exists():
                continue

            try:
                manifest = self._load_manifest(manifest_path)
                manifests.append(manifest)
            except Exception as e:
                logger.warning(f"Failed to load plugin manifest from {subdir}: {e}")

        return manifests

    def load_all(self) -> Dict[str, LoadedPlugin]:
        """Discover and load all enabled plugins."""
        self._plugins.clear()
        for manifest in self.discover():
            if not manifest.enabled:
                continue
            plugin = self._load_plugin(manifest)
            self._plugins[manifest.name] = plugin

        loaded_count = sum(1 for p in self._plugins.values() if p.loaded)
        logger.info(f"Loaded {loaded_count}/{len(self._plugins)} plugins")
        return self._plugins

    def install_from_directory(self, source_path: str, name: Optional[str] = None) -> bool:
        """
        Install a plugin from a local directory.

        Copies the directory into ~/.wyn360/plugins/<name>/.
        """
        source = Path(source_path)
        if not source.exists():
            logger.error(f"Source path not found: {source_path}")
            return False

        plugin_name = name or source.name
        dest = self.plugins_dir / plugin_name

        try:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)

            # Ensure plugin.yaml exists
            if not (dest / "plugin.yaml").exists() and not (dest / "plugin.yml").exists():
                self._create_default_manifest(dest, plugin_name)

            logger.info(f"Installed plugin '{plugin_name}' from {source_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return False

    def create_plugin(self, name: str, plugin_type: str = "tool",
                      description: str = "") -> Path:
        """
        Create a new plugin scaffold.

        Returns the path to the created plugin directory.
        """
        plugin_dir = self.plugins_dir / name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create manifest
        manifest = {
            "name": name,
            "version": "0.1.0",
            "description": description or f"WYN360 {plugin_type} plugin",
            "author": os.getenv("USER", "unknown"),
            "entry_point": "main.py",
            "type": plugin_type,
        }
        (plugin_dir / "plugin.yaml").write_text(
            yaml.dump(manifest, default_flow_style=False),
            encoding="utf-8",
        )

        # Create entry point
        if plugin_type == "tool":
            template = '''"""WYN360 Plugin: {name}"""

def register(agent):
    """Called when the plugin is loaded. Register tools here."""
    pass

def get_tools():
    """Return a list of tool functions to register."""
    return []
'''
        elif plugin_type == "hook":
            template = '''"""WYN360 Plugin: {name}"""

from wyn360_cli.hooks import HookPoint, HookContext, HookResult

def register(hook_manager):
    """Called when the plugin is loaded. Register hooks here."""
    hook_manager.register("{name}", HookPoint.POST_RESPONSE, on_response)

def on_response(ctx: HookContext) -> HookResult:
    """Example post-response hook."""
    return HookResult()
'''
        else:
            template = '''"""WYN360 Plugin: {name}"""

def register(registry):
    """Called when the plugin is loaded."""
    pass
'''

        (plugin_dir / "main.py").write_text(
            template.format(name=name),
            encoding="utf-8",
        )

        logger.info(f"Created plugin scaffold at {plugin_dir}")
        return plugin_dir

    def uninstall(self, name: str) -> bool:
        """Remove an installed plugin."""
        plugin_dir = self.plugins_dir / name
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)
            self._plugins.pop(name, None)
            logger.info(f"Uninstalled plugin '{name}'")
            return True
        return False

    def enable(self, name: str) -> bool:
        """Enable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin.manifest.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin.manifest.enabled = False
            return True
        return False

    def get_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> List[LoadedPlugin]:
        """List all known plugins."""
        return list(self._plugins.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        return {
            "total_plugins": len(self._plugins),
            "loaded": sum(1 for p in self._plugins.values() if p.loaded),
            "failed": sum(1 for p in self._plugins.values() if p.error),
            "disabled": sum(1 for p in self._plugins.values() if not p.manifest.enabled),
        }

    def _load_manifest(self, path: Path) -> PluginManifest:
        """Load and validate a plugin manifest."""
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return PluginManifest(
            name=data.get("name", path.parent.name),
            version=data.get("version", "0.1.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            entry_point=data.get("entry_point", "main.py"),
            plugin_type=data.get("type", "tool"),
            dependencies=data.get("dependencies", []),
            enabled=data.get("enabled", True),
        )

    def _load_plugin(self, manifest: PluginManifest) -> LoadedPlugin:
        """Load a single plugin module."""
        plugin_dir = self.plugins_dir / manifest.name
        entry = plugin_dir / manifest.entry_point
        plugin = LoadedPlugin(manifest=manifest, path=str(plugin_dir))

        if not entry.exists():
            plugin.error = f"Entry point not found: {entry}"
            return plugin

        try:
            spec = importlib.util.spec_from_file_location(
                f"wyn360_plugin_{manifest.name}", str(entry)
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin.module = module
                plugin.loaded = True
            else:
                plugin.error = "Could not create module spec"
        except Exception as e:
            plugin.error = str(e)
            logger.warning(f"Failed to load plugin '{manifest.name}': {e}")

        return plugin

    def _create_default_manifest(self, plugin_dir: Path, name: str):
        """Create a minimal default manifest."""
        manifest = {"name": name, "version": "0.1.0", "entry_point": "main.py"}
        (plugin_dir / "plugin.yaml").write_text(
            yaml.dump(manifest), encoding="utf-8"
        )
