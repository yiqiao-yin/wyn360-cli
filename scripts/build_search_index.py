#!/usr/bin/env python3
"""
WYN360 CLI Documentation - AI Search Index Builder

This script processes the documentation markdown files and creates an AI-optimized
search index with semantic embeddings for intelligent document retrieval.

Features:
- Markdown content parsing and extraction
- Semantic chunking of documentation sections
- Embedding generation using sentence-transformers
- JSON index creation for client-side search
- Metadata extraction for search optimization

Usage:
    python scripts/build_search_index.py

Output:
    site/assets/search-index.json - Complete search index
    site/assets/embedding-model-info.json - Model metadata
"""

import os
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    import torch
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
    logger.info("✅ Embedding dependencies available")
except ImportError:
    HAS_EMBEDDINGS = False
    logger.warning("⚠️ Embedding dependencies not available. Install with: pip install sentence-transformers torch")


class DocumentChunk:
    """Represents a semantic chunk of documentation content."""

    def __init__(self,
                 content: str,
                 title: str,
                 url: str,
                 section: str = "",
                 chunk_id: str = "",
                 tags: List[str] = None):
        self.content = content.strip()
        self.title = title.strip()
        self.url = url
        self.section = section
        self.chunk_id = chunk_id or self._generate_id()
        self.tags = tags or []
        self.embedding = None

    def _generate_id(self) -> str:
        """Generate unique ID for chunk based on content hash."""
        content_hash = hashlib.md5(f"{self.title}_{self.content[:100]}".encode()).hexdigest()
        return f"chunk_{content_hash[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for JSON serialization."""
        return {
            'id': self.chunk_id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'section': self.section,
            'tags': self.tags,
            'length': len(self.content),
            'word_count': len(self.content.split())
        }


class MarkdownProcessor:
    """Processes markdown documentation files into semantic chunks."""

    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.chunks = []
        self.sections = set()

        # Chunking configuration
        self.config = {
            'min_chunk_size': 100,      # Minimum characters per chunk
            'max_chunk_size': 1000,     # Maximum characters per chunk
            'overlap_size': 50,         # Overlap between chunks
            'preserve_headers': True,   # Keep headers with their content
            'split_on_headers': True,   # Split at header boundaries
            'include_code_blocks': True # Include code examples
        }

    def process_all_docs(self) -> List[DocumentChunk]:
        """Process all markdown files in the docs directory."""
        logger.info(f"🔍 Scanning documentation directory: {self.docs_dir}")

        if not self.docs_dir.exists():
            logger.error(f"❌ Documentation directory not found: {self.docs_dir}")
            return []

        md_files = list(self.docs_dir.glob("**/*.md"))
        logger.info(f"📝 Found {len(md_files)} markdown files")

        for md_file in md_files:
            try:
                self._process_file(md_file)
            except Exception as e:
                logger.error(f"❌ Error processing {md_file}: {e}")
                continue

        logger.info(f"✅ Processed {len(self.chunks)} chunks from {len(md_files)} files")
        logger.info(f"📊 Sections found: {', '.join(sorted(self.sections))}")

        return self.chunks

    def _process_file(self, file_path: Path) -> None:
        """Process a single markdown file."""
        logger.debug(f"📖 Processing: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata
        url_path = self._get_url_path(file_path)
        section = self._extract_section(file_path)
        self.sections.add(section)

        # Split into semantic chunks
        chunks = self._chunk_content(content, file_path.stem, url_path, section)
        self.chunks.extend(chunks)

    def _get_url_path(self, file_path: Path) -> str:
        """Convert file path to documentation URL path."""
        relative_path = file_path.relative_to(self.docs_dir)

        # Handle index files
        if relative_path.name == 'index.md':
            url_path = f"/{relative_path.parent}/" if relative_path.parent != Path('.') else "/"
        else:
            url_path = f"/{relative_path.with_suffix('')}/"

        return url_path.replace('\\', '/').replace('//', '/')

    def _extract_section(self, file_path: Path) -> str:
        """Extract section name from file path."""
        parts = file_path.relative_to(self.docs_dir).parts
        if len(parts) > 1:
            return parts[0].title().replace('-', ' ')
        return "Documentation"

    def _chunk_content(self, content: str, title: str, url: str, section: str) -> List[DocumentChunk]:
        """Split content into semantic chunks."""
        chunks = []

        # Remove front matter
        content = self._remove_frontmatter(content)

        # Extract main title
        main_title = self._extract_main_title(content) or title.replace('-', ' ').title()

        # Split by headers for semantic boundaries
        if self.config['split_on_headers']:
            sections = self._split_by_headers(content)
        else:
            sections = [('', content)]

        for section_title, section_content in sections:
            # Skip very short sections
            if len(section_content.strip()) < self.config['min_chunk_size']:
                continue

            # Create chunks from section
            section_chunks = self._create_chunks_from_section(
                section_content,
                section_title or main_title,
                url,
                section
            )
            chunks.extend(section_chunks)

        return chunks

    def _remove_frontmatter(self, content: str) -> str:
        """Remove YAML front matter from markdown content."""
        if content.startswith('---'):
            end_index = content.find('---', 3)
            if end_index != -1:
                return content[end_index + 3:].strip()
        return content

    def _extract_main_title(self, content: str) -> Optional[str]:
        """Extract main title from markdown content."""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def _split_by_headers(self, content: str) -> List[Tuple[str, str]]:
        """Split content by markdown headers."""
        sections = []
        current_section = []
        current_title = ""

        lines = content.split('\n')

        for line in lines:
            line = line.rstrip()

            # Check if this is a header
            if re.match(r'^#{1,6}\s+', line):
                # Save previous section
                if current_section:
                    sections.append((current_title, '\n'.join(current_section)))

                # Start new section
                current_title = re.sub(r'^#{1,6}\s+', '', line)
                current_section = [line]  # Include the header
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append((current_title, '\n'.join(current_section)))

        return sections

    def _create_chunks_from_section(self, content: str, title: str, url: str, section: str) -> List[DocumentChunk]:
        """Create optimally-sized chunks from a content section."""
        chunks = []

        # Clean content
        clean_content = self._clean_content(content)

        if len(clean_content) <= self.config['max_chunk_size']:
            # Content fits in single chunk
            chunk = DocumentChunk(
                content=clean_content,
                title=title,
                url=url,
                section=section,
                tags=self._extract_tags(clean_content)
            )
            chunks.append(chunk)
        else:
            # Split into multiple chunks with overlap
            chunk_pieces = self._split_with_overlap(clean_content)
            for i, piece in enumerate(chunk_pieces):
                chunk_title = f"{title} (Part {i+1})" if len(chunk_pieces) > 1 else title
                chunk = DocumentChunk(
                    content=piece,
                    title=chunk_title,
                    url=f"{url}#{self._create_anchor(title)}",
                    section=section,
                    tags=self._extract_tags(piece)
                )
                chunks.append(chunk)

        return chunks

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content for better search."""
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        # Normalize code blocks (keep them but clean formatting)
        if self.config['include_code_blocks']:
            content = re.sub(r'```(\w+)?\n(.*?)\n```', r'[Code: \1]\n\2', content, flags=re.DOTALL)

        # Remove excessive whitespace but preserve structure
        lines = [line.rstrip() for line in content.split('\n')]
        return '\n'.join(lines).strip()

    def _split_with_overlap(self, content: str) -> List[str]:
        """Split content into overlapping chunks."""
        chunks = []
        max_size = self.config['max_chunk_size']
        overlap = self.config['overlap_size']

        words = content.split()
        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space

            if current_size + word_size > max_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))

                # Start new chunk with overlap
                overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_words
                current_size = sum(len(w) + 1 for w in current_chunk)

            current_chunk.append(word)
            current_size += word_size

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content for better categorization."""
        tags = []

        # Technical terms
        if re.search(r'\b(API|CLI|command|install|setup|config)\b', content, re.IGNORECASE):
            tags.append('technical')

        # Feature categories
        if re.search(r'\b(browser|automation|vision|search|web)\b', content, re.IGNORECASE):
            tags.append('features')

        # Getting started content
        if re.search(r'\b(start|begin|first|tutorial|guide|quick)\b', content, re.IGNORECASE):
            tags.append('getting-started')

        # Examples and use cases
        if re.search(r'\b(example|use case|demo|sample)\b', content, re.IGNORECASE):
            tags.append('examples')

        return tags

    def _create_anchor(self, title: str) -> str:
        """Create URL anchor from title."""
        return re.sub(r'[^a-zA-Z0-9\s]', '', title).lower().replace(' ', '-')


class EmbeddingGenerator:
    """Generates semantic embeddings for documentation chunks."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

        if HAS_EMBEDDINGS:
            self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"📥 Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            self.model = None

    def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate embeddings for all chunks."""
        if not self.model:
            logger.warning("⚠️ No embedding model available, skipping embedding generation")
            return chunks

        logger.info(f"🔄 Generating embeddings for {len(chunks)} chunks...")

        # Prepare texts for embedding
        texts = [f"{chunk.title}\n\n{chunk.content}" for chunk in chunks]

        try:
            # Generate embeddings in batches for memory efficiency
            batch_size = 32
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                logger.debug(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

                batch_embeddings = self.model.encode(
                    batch_texts,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True  # Normalize for cosine similarity
                )
                all_embeddings.extend(batch_embeddings)

            # Attach embeddings to chunks
            for chunk, embedding in zip(chunks, all_embeddings):
                chunk.embedding = embedding.tolist()  # Convert to list for JSON serialization

            logger.info("✅ Embeddings generated successfully")

        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {e}")

        return chunks

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        if not self.model:
            return {"error": "No model loaded"}

        return {
            "model_name": self.model_name,
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "max_sequence_length": getattr(self.model, 'max_seq_length', 512),
            "device": str(self.model.device) if hasattr(self.model, 'device') else "cpu"
        }


class SearchIndexBuilder:
    """Builds the final search index for client-side use."""

    def __init__(self, output_dir: str = "site/assets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_index(self, chunks: List[DocumentChunk], model_info: Dict[str, Any] = None) -> str:
        """Build the complete search index."""
        logger.info("🔨 Building search index...")

        # Separate embeddings from chunk data for more efficient storage
        chunk_data = []
        embeddings = []

        for chunk in chunks:
            chunk_dict = chunk.to_dict()
            chunk_data.append(chunk_dict)

            if chunk.embedding:
                embeddings.append(chunk.embedding)
            else:
                embeddings.append(None)

        # Build index structure
        search_index = {
            "version": "1.0",
            "build_date": datetime.now().isoformat(),
            "metadata": {
                "total_chunks": len(chunks),
                "embedding_model": model_info.get("model_name", "none") if model_info else "none",
                "embedding_dimension": model_info.get("embedding_dimension", 0) if model_info else 0,
                "sections": list(set(chunk.section for chunk in chunks)),
                "total_content_length": sum(len(chunk.content) for chunk in chunks),
                "has_embeddings": bool(embeddings and any(e is not None for e in embeddings))
            },
            "chunks": chunk_data,
            "embeddings": embeddings if any(e is not None for e in embeddings) else []
        }

        # Save main index
        index_path = self.output_dir / "search-index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, indent=2, ensure_ascii=False)

        # Save model info separately
        if model_info:
            model_path = self.output_dir / "embedding-model-info.json"
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, indent=2)

        # Calculate and log statistics
        index_size = os.path.getsize(index_path)
        logger.info(f"✅ Search index built successfully")
        logger.info(f"📊 Index size: {index_size:,} bytes ({index_size/1024/1024:.2f} MB)")
        logger.info(f"📝 Total chunks: {len(chunks)}")
        logger.info(f"🎯 Average chunk size: {sum(len(c.content) for c in chunks) // len(chunks)} chars")
        logger.info(f"💾 Saved to: {index_path}")

        return str(index_path)


def main():
    """Main function to build the AI search index."""
    parser = argparse.ArgumentParser(description="Build AI search index for WYN360 CLI documentation")
    parser.add_argument("--docs-dir", default="docs", help="Documentation directory (default: docs)")
    parser.add_argument("--output-dir", default="site/assets", help="Output directory (default: site/assets)")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2",
                        help="Embedding model name")
    parser.add_argument("--no-embeddings", action="store_true",
                        help="Skip embedding generation (faster for testing)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("🚀 Starting AI search index build process...")
    logger.info(f"📂 Documentation directory: {args.docs_dir}")
    logger.info(f"💾 Output directory: {args.output_dir}")

    try:
        # Step 1: Process documentation
        processor = MarkdownProcessor(args.docs_dir)
        chunks = processor.process_all_docs()

        if not chunks:
            logger.error("❌ No chunks generated from documentation")
            return 1

        # Step 2: Generate embeddings (unless disabled)
        model_info = None
        if not args.no_embeddings and HAS_EMBEDDINGS:
            embedding_generator = EmbeddingGenerator(args.model)
            chunks = embedding_generator.generate_embeddings(chunks)
            model_info = embedding_generator.get_model_info()
        else:
            logger.info("⏭️ Skipping embedding generation")

        # Step 3: Build search index
        index_builder = SearchIndexBuilder(args.output_dir)
        index_path = index_builder.build_index(chunks, model_info)

        logger.info("🎉 AI search index build completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"❌ Build process failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())