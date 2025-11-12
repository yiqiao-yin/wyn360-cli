"""Document readers with intelligent chunking, summarization, and retrieval.

This module provides intelligent document reading capabilities for Excel, Word, and PDF files.
Instead of simple truncation, it implements a chunking + summarization + tagging + retrieval
system that allows handling arbitrarily large documents.

Architecture:
    Document → Chunk → Summarize → Tag → Cache → Query → Retrieve

Phase 1: Core Infrastructure (v0.3.26)
"""

import hashlib
import json
import time
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, asdict

# Optional dependencies (graceful fallback)
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    openpyxl = None

try:
    from docx import Document
    HAS_PYTHON_DOCX = True
except ImportError:
    HAS_PYTHON_DOCX = False
    Document = None

try:
    import pymupdf  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    pymupdf = None

# Import Anthropic at module level for easier mocking in tests
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    Anthropic = None


# ============================================================================
# Token Counting Utilities
# ============================================================================

def count_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses rough approximation: 1 token ≈ 4 characters.
    Same as browser_use.py for consistency.

    Args:
        text: Text to count tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""
    chunk_id: str
    position: Dict[str, Any]  # start, end positions (varies by doc type)
    summary: str
    tags: List[str]
    token_count: int
    summary_tokens: int
    tag_tokens: int
    # Optional type-specific fields
    sheet_name: Optional[str] = None  # Excel
    section_title: Optional[str] = None  # Word
    page_range: Optional[Tuple[int, int]] = None  # PDF


@dataclass
class DocumentMetadata:
    """Metadata for a cached document."""
    file_path: str
    file_hash: str
    file_size: int
    total_tokens: int
    chunk_count: int
    chunk_size: int
    created_at: float
    ttl: int
    doc_type: str  # "excel" | "word" | "pdf"


# ============================================================================
# DocumentChunker Class
# ============================================================================

class DocumentChunker:
    """Intelligently chunk documents into manageable pieces."""

    def __init__(self, chunk_size: int = 1000):
        """
        Initialize chunker.

        Args:
            chunk_size: Target tokens per chunk (default: 1000)
        """
        self.chunk_size = chunk_size

    def chunk_by_tokens(self, text: str, preserve_boundaries: bool = True) -> List[str]:
        """
        Chunk text by token count.

        Args:
            text: Text to chunk
            preserve_boundaries: Try to break at paragraph boundaries

        Returns:
            List of text chunks
        """
        target_chars = self.chunk_size * 4  # ~4 chars per token

        if preserve_boundaries:
            return self._chunk_with_boundaries(text, target_chars)
        else:
            return self._chunk_simple(text, target_chars)

    def _chunk_simple(self, text: str, target_chars: int) -> List[str]:
        """Simple chunking by character count."""
        if not text:
            return [""]

        chunks = []
        for i in range(0, len(text), target_chars):
            chunks.append(text[i:i + target_chars])
        return chunks

    def _chunk_with_boundaries(self, text: str, target_chars: int) -> List[str]:
        """Chunk with respect to paragraph boundaries."""
        chunks = []
        paragraphs = text.split('\n\n')

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) <= target_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def chunk_by_structure(
        self,
        sections: List[Dict[str, str]],
        target_chunk_tokens: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Chunk by document structure (headings/sections).

        Used for Word documents where we want to keep sections together.

        Args:
            sections: List of {title, content, level} dicts
            target_chunk_tokens: Target tokens per chunk

        Returns:
            List of chunk dicts with aggregated sections
        """
        chunks = []
        current_chunk = {
            "title": "",
            "content": "",
            "sections": []
        }
        current_tokens = 0

        for section in sections:
            section_text = f"# {section['title']}\n\n{section['content']}\n\n"
            section_tokens = count_tokens(section_text)

            if current_tokens + section_tokens <= target_chunk_tokens:
                current_chunk["content"] += section_text
                current_chunk["sections"].append(section["title"])
                current_tokens += section_tokens
            else:
                if current_chunk["content"]:
                    chunks.append(current_chunk.copy())

                current_chunk = {
                    "title": section["title"],
                    "content": section_text,
                    "sections": [section["title"]]
                }
                current_tokens = section_tokens

        if current_chunk["content"]:
            chunks.append(current_chunk)

        return chunks


# ============================================================================
# ChunkSummarizer Class
# ============================================================================

class ChunkSummarizer:
    """Summarize chunks and generate tags using Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        """
        Initialize summarizer.

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Haiku for cost efficiency)
        """
        self.api_key = api_key
        self.model = model
        self.summary_tokens = 100
        self.tag_count = 8

    async def summarize_chunk(
        self,
        chunk_text: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Summarize a chunk using Claude API.

        Args:
            chunk_text: The chunk content (~1000 tokens)
            context: Metadata (file type, sheet/section/page info)

        Returns:
            {
                "summary": "...",  # ~100 tokens
                "tags": ["tag1", "tag2", ...],  # 5-8 keywords
                "token_counts": {"input": ..., "output": ...}
            }
        """
        # Check if Anthropic is available
        if not HAS_ANTHROPIC or Anthropic is None:
            return self._fallback_summary(chunk_text, "Anthropic library not available")

        client = Anthropic(api_key=self.api_key)

        # Build context string
        context_str = self._format_context(context)

        # Construct prompt
        prompt = f"""Summarize this document chunk in approximately {self.summary_tokens} tokens.
Focus on key information, numbers, main points, and important details.
Then extract {self.tag_count} relevant tags (keywords) that capture the content.

Context: {context_str}

Chunk:
{chunk_text}

Format your response as:
SUMMARY: [your concise summary here]
TAGS: [tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8]
"""

        # Call Claude API
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=200,  # summary (100) + tags (20) + buffer
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            content = response.content[0].text
            summary, tags = self._parse_summary_response(content)

            return {
                "summary": summary,
                "tags": tags,
                "summary_tokens": count_tokens(summary),
                "tag_tokens": count_tokens(" ".join(tags)),
                "api_tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens
                }
            }

        except Exception as e:
            # Fallback: simple extraction if API fails
            return self._fallback_summary(chunk_text, str(e))

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context metadata into readable string."""
        parts = []
        if "doc_type" in context:
            parts.append(f"Document type: {context['doc_type']}")
        if "sheet_name" in context and context["sheet_name"]:
            parts.append(f"Sheet: {context['sheet_name']}")
        if "section_title" in context and context["section_title"]:
            parts.append(f"Section: {context['section_title']}")
        if "page_range" in context and context["page_range"]:
            parts.append(f"Pages: {context['page_range'][0]}-{context['page_range'][1]}")

        return ", ".join(parts) if parts else "No context"

    def _parse_summary_response(self, content: str) -> Tuple[str, List[str]]:
        """Parse Claude's response to extract summary and tags."""
        summary = ""
        tags = []

        lines = content.strip().split('\n')
        for line in lines:
            if line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
            elif line.startswith("TAGS:"):
                tags_str = line.replace("TAGS:", "").strip()
                # Remove brackets and split
                tags_str = tags_str.replace("[", "").replace("]", "")
                tags = [tag.strip() for tag in tags_str.split(",")]

        # Fallback if parsing failed
        if not summary:
            summary = content[:400]  # First 100 tokens
        if not tags:
            tags = self._extract_keywords(content)

        return summary, tags[:self.tag_count]

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction as fallback."""
        # Remove common words and extract meaningful terms
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        # Get unique words, limit to tag_count
        unique_words = list(dict.fromkeys(words))
        return unique_words[:self.tag_count]

    def _fallback_summary(self, chunk_text: str, error: str) -> Dict[str, Any]:
        """Fallback summary if API call fails."""
        # Take first ~100 tokens
        summary = chunk_text[:400]
        tags = self._extract_keywords(chunk_text)

        return {
            "summary": summary + "...",
            "tags": tags,
            "summary_tokens": count_tokens(summary),
            "tag_tokens": count_tokens(" ".join(tags)),
            "error": f"API call failed: {error}",
            "api_tokens": {"input": 0, "output": 0}
        }


# ============================================================================
# ChunkCache Class
# ============================================================================

class ChunkCache:
    """Cache document chunks with TTL-based expiration."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: int = 3600,
        max_size_mb: int = 500
    ):
        """
        Initialize chunk cache.

        Args:
            cache_dir: Cache directory (default: ~/.wyn360/cache/documents/)
            ttl: Time to live in seconds (default: 1 hour)
            max_size_mb: Maximum cache size in MB
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".wyn360" / "cache" / "documents"

        self.cache_dir = cache_dir
        self.ttl = ttl
        self.max_size_mb = max_size_mb

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_file_hash(self, file_path: str) -> str:
        """Generate MD5 hash of file for cache key."""
        hasher = hashlib.md5()

        # Include file path
        hasher.update(file_path.encode())

        # Add file modification time if file exists
        file_obj = Path(file_path)
        if file_obj.exists():
            file_stat = file_obj.stat()
            hasher.update(str(file_stat.st_mtime).encode())

        return hasher.hexdigest()

    def get_cache_path(self, file_hash: str) -> Path:
        """Get cache directory path for a file hash."""
        return self.cache_dir / file_hash

    def load_chunks(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load cached chunks for a file.

        Args:
            file_path: Path to the document file

        Returns:
            Cached data dict or None if cache miss/expired
        """
        file_hash = self.get_file_hash(file_path)
        cache_path = self.get_cache_path(file_hash)

        metadata_file = cache_path / "metadata.json"
        chunks_file = cache_path / "chunks_index.json"

        # Check if cache exists
        if not metadata_file.exists() or not chunks_file.exists():
            return None

        # Load metadata
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Check TTL
            age = time.time() - metadata["created_at"]
            if age > metadata["ttl"]:
                # Expired
                self._remove_cache(cache_path)
                return None

            # Load chunks
            with open(chunks_file, 'r') as f:
                chunks = json.load(f)

            return {
                "metadata": metadata,
                "chunks": chunks["chunks"]
            }

        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
            return None

    def save_chunks(
        self,
        file_path: str,
        metadata: DocumentMetadata,
        chunks: List[ChunkMetadata]
    ) -> bool:
        """
        Save chunks to cache.

        Args:
            file_path: Path to the document file
            metadata: Document metadata
            chunks: List of chunk metadata

        Returns:
            True if saved successfully
        """
        file_hash = self.get_file_hash(file_path)
        cache_path = self.get_cache_path(file_hash)

        # Create cache directory
        cache_path.mkdir(parents=True, exist_ok=True)

        # Check cache size before saving
        self._cleanup_if_needed()

        try:
            # Save metadata
            metadata_file = cache_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)

            # Save chunks
            chunks_file = cache_path / "chunks_index.json"
            chunks_data = {
                "chunks": [asdict(chunk) for chunk in chunks]
            }
            with open(chunks_file, 'w') as f:
                json.dump(chunks_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
            return False

    def clear_cache(self, file_path: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            file_path: Specific file to clear, or None to clear all

        Returns:
            Number of cache entries removed
        """
        if file_path:
            # Clear specific file
            file_hash = self.get_file_hash(file_path)
            cache_path = self.get_cache_path(file_hash)

            if cache_path.exists():
                self._remove_cache(cache_path)
                return 1
            return 0
        else:
            # Clear all
            count = 0
            for cache_path in self.cache_dir.iterdir():
                if cache_path.is_dir():
                    self._remove_cache(cache_path)
                    count += 1
            return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_files = 0
        total_chunks = 0
        total_size = 0
        oldest_time = None
        newest_time = None
        cache_entries = []

        # Check if cache directory exists
        if not self.cache_dir.exists():
            return {
                "total_files": 0,
                "total_chunks": 0,
                "total_size_mb": 0.0,
                "oldest_cache": "N/A",
                "newest_cache": "N/A",
                "cache_entries": []
            }

        for cache_path in self.cache_dir.iterdir():
            if not cache_path.is_dir():
                continue

            metadata_file = cache_path / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                total_files += 1
                total_chunks += metadata["chunk_count"]

                # Calculate directory size
                dir_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                total_size += dir_size

                # Track times
                created_at = metadata["created_at"]
                if oldest_time is None or created_at < oldest_time:
                    oldest_time = created_at
                if newest_time is None or created_at > newest_time:
                    newest_time = created_at

                # Calculate age
                age_seconds = time.time() - created_at
                age_minutes = int(age_seconds / 60)

                cache_entries.append({
                    "file_path": metadata["file_path"],
                    "chunks": metadata["chunk_count"],
                    "age_seconds": age_seconds,
                    "age_display": self._format_age(age_seconds)
                })

            except Exception as e:
                print(f"Warning: Failed to read cache metadata: {e}")

        # Calculate size in MB (use 3 decimal places for better precision with small files)
        size_mb = total_size / (1024 * 1024) if total_size > 0 else 0.0

        return {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "total_size_mb": round(size_mb, 3),
            "oldest_cache": self._format_age(time.time() - oldest_time) if oldest_time else "N/A",
            "newest_cache": self._format_age(time.time() - newest_time) if newest_time else "N/A",
            "cache_entries": sorted(cache_entries, key=lambda x: x["age_seconds"])
        }

    def _format_age(self, seconds: float) -> str:
        """Format age in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)} sec ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)} min ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)} hours ago"
        else:
            return f"{int(seconds / 86400)} days ago"

    def _remove_cache(self, cache_path: Path):
        """Remove a cache directory."""
        import shutil
        try:
            shutil.rmtree(cache_path)
        except Exception as e:
            print(f"Warning: Failed to remove cache: {e}")

    def _cleanup_if_needed(self):
        """Clean up cache if it exceeds max size."""
        stats = self.get_stats()

        if stats["total_size_mb"] > self.max_size_mb:
            # Remove oldest caches until under limit
            cache_entries = stats["cache_entries"]

            for entry in reversed(cache_entries):  # Oldest first
                if stats["total_size_mb"] <= self.max_size_mb * 0.9:  # 90% threshold
                    break

                file_path = entry["file_path"]
                file_hash = self.get_file_hash(file_path)
                cache_path = self.get_cache_path(file_hash)

                # Calculate size before removal
                dir_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())

                self._remove_cache(cache_path)
                stats["total_size_mb"] -= dir_size / (1024 * 1024)


# ============================================================================
# ChunkRetriever Class
# ============================================================================

class ChunkRetriever:
    """Retrieve relevant chunks based on user queries."""

    def __init__(self, top_k: int = 3):
        """
        Initialize retriever.

        Args:
            top_k: Number of top chunks to retrieve (default: 3)
        """
        self.top_k = top_k

    def match_query(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match user query against chunk tags.

        Uses simple keyword matching (Phase 1).
        Future: Semantic matching with embeddings (Phase 5).

        Args:
            query: User's question or search query
            chunks: List of chunk dicts from cache

        Returns:
            Top-K most relevant chunks
        """
        # Tokenize query (simple word splitting)
        query_terms = self._tokenize_query(query)

        # Score each chunk
        scored_chunks = []
        for chunk in chunks:
            score = self._score_chunk(query_terms, chunk)
            scored_chunks.append({
                "chunk": chunk,
                "score": score
            })

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # Return top-K
        return [item["chunk"] for item in scored_chunks[:self.top_k]]

    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenize query into searchable terms."""
        # Convert to lowercase
        query = query.lower()

        # Extract words (4+ characters)
        terms = re.findall(r'\b[a-z0-9]{3,}\b', query)

        return terms

    def _score_chunk(self, query_terms: List[str], chunk: Dict[str, Any]) -> float:
        """
        Score a chunk based on query term overlap with tags.

        Simple keyword matching:
        - Exact tag match: +3 points
        - Partial tag match: +1 point
        - Summary match: +0.5 points

        Args:
            query_terms: List of query terms
            chunk: Chunk dict with tags and summary

        Returns:
            Score (higher = more relevant)
        """
        score = 0.0

        # Get chunk tags and summary
        tags = [tag.lower() for tag in chunk.get("tags", [])]
        summary = chunk.get("summary", "").lower()

        for term in query_terms:
            # Check exact tag match
            if term in tags:
                score += 3.0
                # Skip partial match check for exact matches
                continue

            # Check partial tag match (only if not exact match)
            partial_match = False
            for tag in tags:
                if term in tag or tag in term:
                    score += 1.0
                    partial_match = True
                    break

            # Check summary match (only if no tag match)
            if not partial_match and term in summary:
                score += 0.5

        return score

    def get_relevant_chunks(
        self,
        query: Optional[str],
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get relevant chunks based on query.

        If no query provided, return all chunks (for full document summary).

        Args:
            query: Optional user query
            chunks: All cached chunks

        Returns:
            Relevant chunks (filtered if query provided)
        """
        if query:
            return self.match_query(query, chunks)
        else:
            # No query: return all chunks (for full document summary)
            return chunks


# ============================================================================
# ExcelReader Class (Phase 2)
# ============================================================================

class ExcelReader:
    """Read and process Excel files with intelligent chunking."""

    def __init__(
        self,
        file_path: str,
        chunk_size: int = 1000,
        include_sheets: Optional[List[str]] = None
    ):
        """
        Initialize Excel reader.

        Args:
            file_path: Path to Excel file
            chunk_size: Target tokens per chunk
            include_sheets: Optional list of sheet names to include
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.include_sheets = include_sheets
        self.chunker = DocumentChunker(chunk_size)

    def read(self) -> Dict[str, Any]:
        """
        Read Excel file and return structured data.

        Returns:
            {
                "sheets": [
                    {
                        "name": "Sheet1",
                        "data_region": (min_row, min_col, max_row, max_col),
                        "markdown": "...",
                        "row_count": 100,
                        "col_count": 10,
                        "has_merged_cells": True
                    },
                    ...
                ],
                "total_sheets": 3,
                "total_tokens": 5000
            }
        """
        if not HAS_OPENPYXL:
            raise ImportError(
                "openpyxl not installed. Install with: pip install openpyxl"
            )

        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.file_path}")

        try:
            # Open workbook (data_only=True to get evaluated formula values)
            workbook = openpyxl.load_workbook(
                self.file_path,
                data_only=True,
                read_only=False
            )

            sheets_data = []
            total_tokens = 0

            # Process each sheet
            for sheet_name in workbook.sheetnames:
                # Filter sheets if include_sheets specified
                if self.include_sheets and sheet_name not in self.include_sheets:
                    continue

                sheet = workbook[sheet_name]

                # Detect data region
                data_region = self._detect_data_region(sheet)

                # Check if sheet has any data
                if data_region is None:
                    continue

                min_row, min_col, max_row, max_col = data_region

                # Get merged cells info
                merged_cells = self._get_merged_cells_map(sheet)

                # Convert to markdown
                markdown = self._sheet_to_markdown(
                    sheet,
                    data_region,
                    merged_cells
                )

                # Count tokens
                tokens = count_tokens(markdown)
                total_tokens += tokens

                sheets_data.append({
                    "name": sheet_name,
                    "data_region": data_region,
                    "markdown": markdown,
                    "row_count": max_row - min_row + 1,
                    "col_count": max_col - min_col + 1,
                    "has_merged_cells": len(merged_cells) > 0,
                    "tokens": tokens
                })

            workbook.close()

            return {
                "sheets": sheets_data,
                "total_sheets": len(sheets_data),
                "total_tokens": total_tokens
            }

        except Exception as e:
            raise Exception(f"Failed to read Excel file: {e}")

    def _detect_data_region(self, sheet) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect the actual data region in a sheet.

        Does not assume data starts at A1. Scans the sheet to find
        the bounding box of all non-empty cells.

        Args:
            sheet: openpyxl worksheet

        Returns:
            (min_row, min_col, max_row, max_col) or None if empty
        """
        min_row = None
        min_col = None
        max_row = None
        max_col = None

        # Scan all cells to find data region
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:
                    # Update bounding box
                    if min_row is None or cell.row < min_row:
                        min_row = cell.row
                    if max_row is None or cell.row > max_row:
                        max_row = cell.row
                    if min_col is None or cell.column < min_col:
                        min_col = cell.column
                    if max_col is None or cell.column > max_col:
                        max_col = cell.column

        if min_row is None:
            return None  # Empty sheet

        return (min_row, min_col, max_row, max_col)

    def _get_merged_cells_map(self, sheet) -> Dict[Tuple[int, int], Tuple[int, int, int, int]]:
        """
        Get mapping of merged cells.

        Args:
            sheet: openpyxl worksheet

        Returns:
            Dict mapping (row, col) to (min_row, min_col, max_row, max_col)
        """
        merged_map = {}

        for merged_range in sheet.merged_cells.ranges:
            min_row = merged_range.min_row
            min_col = merged_range.min_col
            max_row = merged_range.max_row
            max_col = merged_range.max_col

            # Map all cells in the merged range to the range bounds
            for row in range(min_row, max_row + 1):
                for col in range(min_col, max_col + 1):
                    merged_map[(row, col)] = (min_row, min_col, max_row, max_col)

        return merged_map

    def _sheet_to_markdown(
        self,
        sheet,
        data_region: Tuple[int, int, int, int],
        merged_cells: Dict
    ) -> str:
        """
        Convert sheet data to markdown table.

        Args:
            sheet: openpyxl worksheet
            data_region: (min_row, min_col, max_row, max_col)
            merged_cells: Merged cells mapping

        Returns:
            Markdown formatted table
        """
        min_row, min_col, max_row, max_col = data_region

        lines = []
        lines.append(f"## Sheet: {sheet.title}\n")
        lines.append(f"Data Region: Rows {min_row}-{max_row}, Columns {min_col}-{max_col}\n")

        # Build table
        table_rows = []

        for row_idx in range(min_row, max_row + 1):
            row_cells = []

            for col_idx in range(min_col, max_col + 1):
                cell = sheet.cell(row=row_idx, column=col_idx)
                value = cell.value

                # Handle merged cells
                if (row_idx, col_idx) in merged_cells:
                    merge_info = merged_cells[(row_idx, col_idx)]
                    merge_min_row, merge_min_col, merge_max_row, merge_max_col = merge_info

                    # Only show value in the top-left cell of merged range
                    if row_idx == merge_min_row and col_idx == merge_min_col:
                        # Get the value from the merged cell
                        value = sheet.cell(row=merge_min_row, column=merge_min_col).value
                    else:
                        # Other cells in merged range show empty
                        value = ""

                # Format value
                if value is None:
                    value = ""
                else:
                    value = str(value)

                # Escape pipe characters in cell values
                value = value.replace("|", "\\|")

                row_cells.append(value)

            table_rows.append(row_cells)

        # Format as markdown table
        if table_rows:
            # Header row
            header = "| " + " | ".join(table_rows[0]) + " |"
            lines.append(header)

            # Separator
            num_cols = len(table_rows[0])
            separator = "| " + " | ".join(["---"] * num_cols) + " |"
            lines.append(separator)

            # Data rows
            for row_cells in table_rows[1:]:
                row_line = "| " + " | ".join(row_cells) + " |"
                lines.append(row_line)

        return "\n".join(lines)

    def chunk_sheets(
        self,
        sheets_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk sheet data intelligently.

        Strategy:
        - Each sheet is initially one chunk
        - If sheet exceeds chunk_size, split by row ranges
        - Preserve table structure within chunks

        Args:
            sheets_data: List of sheet data dicts

        Returns:
            List of chunk dicts with metadata
        """
        chunks = []
        chunk_id_counter = 1

        for sheet_data in sheets_data:
            sheet_name = sheet_data["name"]
            markdown = sheet_data["markdown"]
            tokens = sheet_data["tokens"]

            # If sheet fits in one chunk, use as-is
            if tokens <= self.chunk_size:
                chunks.append({
                    "chunk_id": f"{chunk_id_counter:03d}",
                    "sheet_name": sheet_name,
                    "content": markdown,
                    "tokens": tokens,
                    "position": {
                        "sheet": sheet_name,
                        "chunk_type": "full_sheet"
                    }
                })
                chunk_id_counter += 1
            else:
                # Sheet too large - split by row ranges
                # Simple approach: split markdown by lines
                lines = markdown.split("\n")

                # Try to preserve table header + rows in each chunk
                header_lines = []
                data_lines = []
                in_table = False

                for line in lines:
                    if line.startswith("##"):
                        header_lines.append(line)
                    elif line.startswith("|") and "---" in line:
                        # Separator line
                        header_lines.append(line)
                        in_table = True
                    elif line.startswith("|") and not in_table:
                        # Table header
                        header_lines.append(line)
                    elif line.startswith("|") and in_table:
                        # Table data row
                        data_lines.append(line)
                    else:
                        header_lines.append(line)

                # Chunk data rows
                target_chars = self.chunk_size * 4
                current_chunk_lines = header_lines.copy()
                current_chunk_tokens = count_tokens("\n".join(current_chunk_lines))

                for data_line in data_lines:
                    line_tokens = count_tokens(data_line)

                    if current_chunk_tokens + line_tokens > self.chunk_size:
                        # Flush current chunk
                        chunk_content = "\n".join(current_chunk_lines)
                        chunks.append({
                            "chunk_id": f"{chunk_id_counter:03d}",
                            "sheet_name": sheet_name,
                            "content": chunk_content,
                            "tokens": current_chunk_tokens,
                            "position": {
                                "sheet": sheet_name,
                                "chunk_type": "partial"
                            }
                        })
                        chunk_id_counter += 1

                        # Start new chunk with header
                        current_chunk_lines = header_lines.copy()
                        current_chunk_lines.append(data_line)
                        current_chunk_tokens = count_tokens("\n".join(current_chunk_lines))
                    else:
                        current_chunk_lines.append(data_line)
                        current_chunk_tokens += line_tokens

                # Flush final chunk
                if current_chunk_lines:
                    chunk_content = "\n".join(current_chunk_lines)
                    chunks.append({
                        "chunk_id": f"{chunk_id_counter:03d}",
                        "sheet_name": sheet_name,
                        "content": chunk_content,
                        "tokens": current_chunk_tokens,
                        "position": {
                            "sheet": sheet_name,
                            "chunk_type": "partial"
                        }
                    })
                    chunk_id_counter += 1

        return chunks


# ============================================================================
# WordReader Class (Phase 3)
# ============================================================================

class WordReader:
    """Read and process Word documents with intelligent chunking."""

    def __init__(
        self,
        file_path: str,
        chunk_size: int = 1000,
        image_handling: str = "describe"
    ):
        """
        Initialize Word reader.

        Args:
            file_path: Path to Word file
            chunk_size: Target tokens per chunk
            image_handling: How to handle images (skip|describe|vision)
        """
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.image_handling = image_handling
        self.chunker = DocumentChunker(chunk_size)

    def read(self) -> Dict[str, Any]:
        """
        Read Word file and return structured data.

        Returns:
            {
                "sections": [
                    {
                        "level": 1,
                        "title": "Introduction",
                        "content": "...",  # markdown
                        "tokens": 500
                    },
                    ...
                ],
                "total_sections": 5,
                "total_tokens": 5000,
                "has_tables": True,
                "has_images": True
            }
        """
        if not HAS_PYTHON_DOCX:
            raise ImportError(
                "python-docx not installed. Install with: pip install python-docx"
            )

        if not self.file_path.exists():
            raise FileNotFoundError(f"Word file not found: {self.file_path}")

        try:
            # Open document
            doc = Document(str(self.file_path))

            # Extract sections with structure
            sections = self._extract_sections(doc)

            # Calculate totals
            total_tokens = sum(s["tokens"] for s in sections)
            has_tables = any(s.get("has_tables", False) for s in sections)
            has_images = any(s.get("has_images", False) for s in sections)

            return {
                "sections": sections,
                "total_sections": len(sections),
                "total_tokens": total_tokens,
                "has_tables": has_tables,
                "has_images": has_images
            }

        except Exception as e:
            raise Exception(f"Failed to read Word file: {e}")

    def _extract_sections(self, doc) -> List[Dict[str, Any]]:
        """
        Extract document structure with headings as section boundaries.

        Args:
            doc: python-docx Document object

        Returns:
            List of section dicts with title, content, level
        """
        sections = []
        current_section = None
        current_content = []

        for element in doc.element.body:
            # Check if paragraph
            if element.tag.endswith('p'):
                para = None
                # Find the paragraph object
                for p in doc.paragraphs:
                    if p._element == element:
                        para = p
                        break

                if para is None:
                    continue

                # Check if heading
                if para.style.name.startswith('Heading'):
                    # Flush current section
                    if current_section is not None:
                        content_md = "\n\n".join(current_content)
                        current_section["content"] = content_md
                        current_section["tokens"] = count_tokens(content_md)
                        sections.append(current_section)

                    # Start new section
                    level = int(para.style.name.replace('Heading ', '').replace('Heading', '1'))
                    current_section = {
                        "level": level,
                        "title": para.text,
                        "has_tables": False,
                        "has_images": False
                    }
                    current_content = []
                else:
                    # Regular paragraph
                    if para.text.strip():
                        current_content.append(para.text)

            # Check if table
            elif element.tag.endswith('tbl'):
                # Find the table object
                table = None
                for t in doc.tables:
                    if t._element == element:
                        table = t
                        break

                if table is not None:
                    # Convert table to markdown
                    table_md = self._table_to_markdown(table)
                    current_content.append(table_md)

                    if current_section:
                        current_section["has_tables"] = True

        # Flush final section
        if current_section is not None:
            content_md = "\n\n".join(current_content)
            current_section["content"] = content_md
            current_section["tokens"] = count_tokens(content_md)
            sections.append(current_section)

        # If no sections found, create a single section with all content
        if not sections and current_content:
            content_md = "\n\n".join(current_content)
            sections.append({
                "level": 1,
                "title": "Document",
                "content": content_md,
                "tokens": count_tokens(content_md),
                "has_tables": False,
                "has_images": False
            })

        return sections

    def _table_to_markdown(self, table) -> str:
        """
        Convert Word table to markdown.

        Args:
            table: python-docx Table object

        Returns:
            Markdown formatted table
        """
        lines = []

        # Get all rows
        rows = list(table.rows)
        if not rows:
            return ""

        # Header row (first row)
        header_cells = [cell.text.strip() for cell in rows[0].cells]
        header_line = "| " + " | ".join(header_cells) + " |"
        lines.append(header_line)

        # Separator
        separator = "| " + " | ".join(["---"] * len(header_cells)) + " |"
        lines.append(separator)

        # Data rows
        for row in rows[1:]:
            cells = [cell.text.strip().replace("|", "\\|") for cell in row.cells]
            row_line = "| " + " | ".join(cells) + " |"
            lines.append(row_line)

        return "\n".join(lines)

    def chunk_sections(
        self,
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk sections intelligently.

        Strategy:
        - Try to keep complete sections in chunks
        - Split large sections by paragraphs
        - Preserve section hierarchy in metadata

        Args:
            sections: List of section dicts

        Returns:
            List of chunk dicts with metadata
        """
        chunks = []
        chunk_id_counter = 1

        for section in sections:
            title = section["title"]
            content = section["content"]
            tokens = section["tokens"]
            level = section["level"]

            # If section fits in one chunk, use as-is
            if tokens <= self.chunk_size:
                chunks.append({
                    "chunk_id": f"{chunk_id_counter:03d}",
                    "section_title": title,
                    "section_level": level,
                    "content": content,
                    "tokens": tokens,
                    "position": {
                        "section": title,
                        "level": level,
                        "chunk_type": "full_section"
                    }
                })
                chunk_id_counter += 1
            else:
                # Section too large - split by paragraphs
                paragraphs = content.split("\n\n")

                current_chunk_paras = []
                current_chunk_tokens = 0

                for para in paragraphs:
                    para_tokens = count_tokens(para)

                    if current_chunk_tokens + para_tokens > self.chunk_size and current_chunk_paras:
                        # Flush current chunk
                        chunk_content = "\n\n".join(current_chunk_paras)
                        chunks.append({
                            "chunk_id": f"{chunk_id_counter:03d}",
                            "section_title": title,
                            "section_level": level,
                            "content": chunk_content,
                            "tokens": current_chunk_tokens,
                            "position": {
                                "section": title,
                                "level": level,
                                "chunk_type": "partial"
                            }
                        })
                        chunk_id_counter += 1

                        # Start new chunk
                        current_chunk_paras = [para]
                        current_chunk_tokens = para_tokens
                    else:
                        current_chunk_paras.append(para)
                        current_chunk_tokens += para_tokens

                # Flush final chunk
                if current_chunk_paras:
                    chunk_content = "\n\n".join(current_chunk_paras)
                    chunks.append({
                        "chunk_id": f"{chunk_id_counter:03d}",
                        "section_title": title,
                        "section_level": level,
                        "content": chunk_content,
                        "tokens": current_chunk_tokens,
                        "position": {
                            "section": title,
                            "level": level,
                            "chunk_type": "partial"
                        }
                    })
                    chunk_id_counter += 1

        return chunks
