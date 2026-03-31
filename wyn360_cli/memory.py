"""
WYN360 Memory System - Persistent cross-session memory with relevance selection.

File-based memory stored in ~/.wyn360/memory/ with MEMORY.md as index.
Each memory is a separate .md file with YAML frontmatter.
"""

import os
import re
import yaml
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MEMORY_DIR_NAME = "memory"
MEMORY_INDEX = "MEMORY.md"
MAX_INDEX_LINES = 200
MAX_RELEVANT_MEMORIES = 5

VALID_TYPES = {"user", "feedback", "project", "reference"}


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""
    name: str
    description: str
    type: str
    content: str
    filename: str
    mtime: float = 0.0

    def to_frontmatter(self) -> str:
        """Serialize to markdown with YAML frontmatter."""
        return f"""---
name: {self.name}
description: {self.description}
type: {self.type}
---

{self.content}
"""


class MemoryManager:
    """Manages persistent file-based memories across sessions."""

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_dir = memory_dir or (Path.home() / ".wyn360" / MEMORY_DIR_NAME)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.memory_dir / MEMORY_INDEX

    def save_memory(self, name: str, description: str, memory_type: str,
                    content: str, filename: Optional[str] = None) -> str:
        """
        Save a memory to disk and update the index.

        Returns the filename used.
        """
        if memory_type not in VALID_TYPES:
            raise ValueError(f"Invalid memory type '{memory_type}'. Must be one of: {VALID_TYPES}")

        if not filename:
            # Generate filename from type and name
            safe_name = re.sub(r'[^a-z0-9_]', '_', name.lower().strip())
            safe_name = re.sub(r'_+', '_', safe_name).strip('_')
            filename = f"{memory_type}_{safe_name}.md"

        entry = MemoryEntry(
            name=name,
            description=description,
            type=memory_type,
            content=content,
            filename=filename,
        )

        # Write the memory file
        filepath = self.memory_dir / filename
        filepath.write_text(entry.to_frontmatter(), encoding="utf-8")

        # Update the index
        self._update_index(name, filename, description)

        return filename

    def delete_memory(self, filename: str) -> bool:
        """Delete a memory file and remove from index."""
        filepath = self.memory_dir / filename
        if filepath.exists():
            filepath.unlink()
            self._remove_from_index(filename)
            return True
        return False

    def get_memory(self, filename: str) -> Optional[MemoryEntry]:
        """Read a single memory file."""
        filepath = self.memory_dir / filename
        if not filepath.exists():
            return None
        return self._parse_memory_file(filepath)

    def list_memories(self) -> List[MemoryEntry]:
        """List all memory entries (headers only, content truncated)."""
        memories = []
        for f in sorted(self.memory_dir.glob("*.md")):
            if f.name == MEMORY_INDEX:
                continue
            entry = self._parse_memory_file(f)
            if entry:
                memories.append(entry)
        return memories

    def get_index_content(self) -> str:
        """Read the MEMORY.md index, truncated to MAX_INDEX_LINES."""
        if not self.index_path.exists():
            return ""
        content = self.index_path.read_text(encoding="utf-8").strip()
        lines = content.split("\n")
        if len(lines) > MAX_INDEX_LINES:
            content = "\n".join(lines[:MAX_INDEX_LINES])
            content += f"\n\n> WARNING: MEMORY.md has {len(lines)} lines (limit: {MAX_INDEX_LINES}). Truncated."
        return content

    def find_relevant_memories(self, query: str, max_results: int = MAX_RELEVANT_MEMORIES) -> List[MemoryEntry]:
        """
        Find memories relevant to a query using keyword matching.

        This is a lightweight local approach. For LLM-based selection,
        use find_relevant_memories_llm() which makes a side-call.
        """
        all_memories = self.list_memories()
        if not all_memories:
            return []

        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        scored = []
        for mem in all_memories:
            # Score based on keyword overlap with name, description, and content
            mem_text = f"{mem.name} {mem.description} {mem.content}".lower()
            mem_words = set(re.findall(r'\w+', mem_text))
            overlap = len(query_words & mem_words)

            # Boost for type-specific relevance
            if "feedback" in mem.type and any(w in query_lower for w in ["how", "style", "approach", "prefer"]):
                overlap += 2
            if "user" in mem.type and any(w in query_lower for w in ["who", "role", "experience"]):
                overlap += 2

            if overlap > 0:
                scored.append((overlap, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in scored[:max_results]]

    async def find_relevant_memories_llm(self, query: str, model,
                                          max_results: int = MAX_RELEVANT_MEMORIES) -> List[MemoryEntry]:
        """
        Use an LLM side-call to select the most relevant memories.

        Args:
            query: The user's current query
            model: A pydantic-ai model instance to use for selection
            max_results: Maximum number of memories to return
        """
        all_memories = self.list_memories()
        if not all_memories:
            return []

        # Build manifest of available memories
        manifest_lines = []
        for mem in all_memories:
            manifest_lines.append(f"- {mem.filename}: [{mem.type}] {mem.description}")
        manifest = "\n".join(manifest_lines)

        try:
            from pydantic_ai import Agent

            selector = Agent(
                model=model,
                system_prompt=(
                    "You select memories relevant to a user's query. "
                    "Return ONLY a JSON array of filenames (strings) for the most relevant memories. "
                    f"Select at most {max_results}. If none are relevant, return an empty array []."
                ),
                retries=0,
            )

            result = await selector.run(
                f"Query: {query}\n\nAvailable memories:\n{manifest}"
            )

            response = getattr(result, 'data', None) or getattr(result, 'output', str(result))
            if not isinstance(response, str):
                response = str(response)

            # Parse JSON array from response
            import json
            # Try to extract JSON array from response
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                filenames = json.loads(match.group())
                valid_names = {m.filename for m in all_memories}
                selected = [m for m in all_memories if m.filename in filenames and m.filename in valid_names]
                return selected[:max_results]

        except Exception as e:
            logger.warning(f"LLM memory selection failed, falling back to keyword: {e}")

        # Fallback to keyword matching
        return self.find_relevant_memories(query, max_results)

    def build_memory_prompt(self) -> str:
        """Build a system prompt section with memory context."""
        index = self.get_index_content()
        if not index:
            return ""

        return f"""
## Memory

You have access to a persistent memory system at {self.memory_dir}.
The memory index (MEMORY.md) contains:

{index}

To save a memory, create a .md file with YAML frontmatter (name, description, type) in the memory directory,
then add a one-line entry to MEMORY.md.
Valid memory types: user, feedback, project, reference.
"""

    def _parse_memory_file(self, filepath: Path) -> Optional[MemoryEntry]:
        """Parse a memory file with YAML frontmatter."""
        try:
            text = filepath.read_text(encoding="utf-8")
            # Parse YAML frontmatter between --- markers
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
            if not match:
                return None

            frontmatter = yaml.safe_load(match.group(1))
            content = match.group(2).strip()

            return MemoryEntry(
                name=frontmatter.get("name", filepath.stem),
                description=frontmatter.get("description", ""),
                type=frontmatter.get("type", "project"),
                content=content,
                filename=filepath.name,
                mtime=filepath.stat().st_mtime,
            )
        except Exception as e:
            logger.warning(f"Failed to parse memory file {filepath}: {e}")
            return None

    def _update_index(self, name: str, filename: str, description: str):
        """Add or update an entry in MEMORY.md."""
        lines = []
        if self.index_path.exists():
            lines = self.index_path.read_text(encoding="utf-8").strip().split("\n")

        # Remove existing entry for this file
        lines = [l for l in lines if filename not in l]

        # Add new entry (keep under ~150 chars)
        entry = f"- [{name}]({filename}) — {description}"
        if len(entry) > 150:
            entry = entry[:147] + "..."
        lines.append(entry)

        self.index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _remove_from_index(self, filename: str):
        """Remove an entry from MEMORY.md."""
        if not self.index_path.exists():
            return
        lines = self.index_path.read_text(encoding="utf-8").strip().split("\n")
        lines = [l for l in lines if filename not in l]
        self.index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
