"""
WYN360 Skills System - User-extensible slash commands via YAML files.

Skills are loaded from:
  1. ~/.wyn360/skills/  (user-level)
  2. .wyn360/skills/    (project-level, higher priority)

Each skill is a .yaml file with metadata and a prompt template.
"""

import re
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """A user-defined skill (slash command)."""
    name: str
    description: str
    prompt: str
    aliases: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    model: Optional[str] = None
    source: str = "user"  # "user", "project", or "builtin"
    file_path: Optional[str] = None

    def render_prompt(self, args: str = "") -> str:
        """Render the prompt template with arguments substituted."""
        rendered = self.prompt
        # Replace {args} placeholder with actual arguments
        rendered = rendered.replace("{args}", args)
        rendered = rendered.replace("{{args}}", args)
        # Replace {cwd} with current working directory
        rendered = rendered.replace("{cwd}", str(Path.cwd()))
        return rendered


class SkillRegistry:
    """Loads and manages skills from disk."""

    def __init__(self,
                 user_skills_dir: Optional[Path] = None,
                 project_skills_dir: Optional[Path] = None):
        self.user_skills_dir = user_skills_dir or (Path.home() / ".wyn360" / "skills")
        self.project_skills_dir = project_skills_dir or (Path.cwd() / ".wyn360" / "skills")
        self._skills: Dict[str, Skill] = {}
        self._alias_map: Dict[str, str] = {}

    def load_all(self):
        """Load skills from user and project directories."""
        self._skills.clear()
        self._alias_map.clear()

        # Load user skills first (lower priority)
        if self.user_skills_dir.exists():
            self._load_from_dir(self.user_skills_dir, source="user")

        # Load project skills (higher priority, overrides user)
        if self.project_skills_dir.exists():
            self._load_from_dir(self.project_skills_dir, source="project")

    def register_builtin(self, skill: Skill):
        """Register a built-in skill programmatically."""
        skill.source = "builtin"
        self._skills[skill.name] = skill
        for alias in skill.aliases:
            self._alias_map[alias] = skill.name

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name or alias."""
        # Direct name lookup
        if name in self._skills:
            return self._skills[name]
        # Alias lookup
        real_name = self._alias_map.get(name)
        if real_name:
            return self._skills.get(real_name)
        return None

    def list_skills(self) -> List[Skill]:
        """List all registered skills."""
        return list(self._skills.values())

    def has_skill(self, name: str) -> bool:
        """Check if a skill exists by name or alias."""
        return name in self._skills or name in self._alias_map

    def _load_from_dir(self, directory: Path, source: str):
        """Load all .yaml skill files from a directory."""
        for filepath in sorted(directory.glob("*.yaml")):
            try:
                skill = self._parse_skill_file(filepath, source)
                if skill:
                    self._skills[skill.name] = skill
                    for alias in skill.aliases:
                        self._alias_map[alias] = skill.name
                    logger.debug(f"Loaded skill '{skill.name}' from {filepath}")
            except Exception as e:
                logger.warning(f"Failed to load skill from {filepath}: {e}")

        # Also support .yml extension
        for filepath in sorted(directory.glob("*.yml")):
            try:
                skill = self._parse_skill_file(filepath, source)
                if skill:
                    self._skills[skill.name] = skill
                    for alias in skill.aliases:
                        self._alias_map[alias] = skill.name
            except Exception as e:
                logger.warning(f"Failed to load skill from {filepath}: {e}")

    def _parse_skill_file(self, filepath: Path, source: str) -> Optional[Skill]:
        """Parse a single skill YAML file."""
        data = yaml.safe_load(filepath.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None

        name = data.get("name")
        if not name:
            # Use filename as name
            name = filepath.stem

        prompt = data.get("prompt", "")
        if not prompt:
            logger.warning(f"Skill '{name}' has no prompt, skipping")
            return None

        return Skill(
            name=name,
            description=data.get("description", f"Custom skill: {name}"),
            prompt=prompt,
            aliases=data.get("aliases", []),
            allowed_tools=data.get("allowed_tools", []),
            model=data.get("model"),
            source=source,
            file_path=str(filepath),
        )

    @staticmethod
    def create_example_skill(directory: Path):
        """Create an example skill file for users to reference."""
        directory.mkdir(parents=True, exist_ok=True)
        example = directory / "example_review.yaml"
        if not example.exists():
            example.write_text("""# Example skill: code review
# Place .yaml files in ~/.wyn360/skills/ (user) or .wyn360/skills/ (project)
name: review
description: Review code changes and suggest improvements
aliases:
  - cr
  - code-review
prompt: |
  Review the following code changes in the current project directory ({cwd}).
  {args}

  Focus on:
  1. Bug risks and edge cases
  2. Performance issues
  3. Code clarity and maintainability
  4. Security concerns

  Provide specific, actionable suggestions with file paths and line numbers.
""", encoding="utf-8")
