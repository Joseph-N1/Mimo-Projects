#!/usr/bin/env python3
"""
Content Index Builder for Aviation Regulation PDFs
===================================================
This script pre-processes all PDFs in the database folder and builds
a persistent content index for faster question generation and future
ML-based semantic search capabilities.

Usage:
    python scripts/build_content_index.py [--rebuild]

The index includes:
- Extracted text from each PDF
- Page-level data with headings
- Extracted concepts (definitions, responsibilities, procedures, etc.)
- Chunk boundaries for efficient retrieval

Future ML enhancements can add:
- Sentence embeddings for semantic search
- FAISS index for fast similarity lookup
- Concept clustering for related question generation
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    extract_text_from_pdf,
    split_into_chunks,
    extract_concepts,
    clean_text,
)

# ============================================================================
# CONFIGURATION
# ============================================================================

DATABASE_DIR = Path(__file__).parent.parent.parent / "database"
INDEX_DIR = Path(__file__).parent.parent / "content_index"
INDEX_MANIFEST = INDEX_DIR / "manifest.json"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_file_hash(filepath):
    """Calculate MD5 hash of file for change detection"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_manifest():
    """Load existing manifest or create empty one"""
    if INDEX_MANIFEST.exists():
        with open(INDEX_MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "files": {}
    }


def save_manifest(manifest):
    """Save manifest to disk"""
    manifest["updated"] = datetime.now().isoformat()
    with open(INDEX_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def index_pdf(pdf_path, force_rebuild=False):
    """
    Index a single PDF file
    
    Returns:
        dict: Index entry with text, pages, concepts, chunks
    """
    pdf_name = pdf_path.stem
    index_file = INDEX_DIR / f"{pdf_name}.json"
    file_hash = get_file_hash(pdf_path)
    
    # Check if already indexed and unchanged
    manifest = load_manifest()
    if not force_rebuild and pdf_name in manifest["files"]:
        if manifest["files"][pdf_name].get("hash") == file_hash:
            print(f"  [SKIP] {pdf_name} - unchanged")
            return None
    
    print(f"  [INDEX] {pdf_name}...")
    
    # Extract text and pages
    full_text, pages_data = extract_text_from_pdf(str(pdf_path))
    
    # Split into chunks with page tracking
    chunks = []
    doc_id = pdf_path.stem

    for page in pages_data:
        page_num = page.get("page_num")
        page_text = page.get("text", "")

        page_chunks = split_into_chunks(page_text)

        for i, chunk_text in enumerate(page_chunks):
            # Extract the longest/deepest section number in the chunk
            # Regex limits to 1-2 digits first, then 1-3 digits per level
            # This prevents page footers like "5-77" or dates from matching
            section_matches = re.findall(r"\b\d{1,2}(\.\d{1,3})+\b", chunk_text)

            if section_matches:
                # Rebuild full matches because findall only returns the group
                full_matches = re.findall(r"\b\d{1,2}(?:\.\d{1,3})+\b", chunk_text)
                section = max(full_matches, key=len)
            else:
                section = None

            chunks.append({
                "chunk_id": f"{doc_id}_p{page_num}_c{i}",
                "doc_id": doc_id,
                "page": page_num,
                "section": section,
                "text": chunk_text,
            })
    
    # Extract concepts
    concepts = extract_concepts(full_text)
    
    # Build index entry
    index_entry = {
        "filename": pdf_path.name,
        "filepath": str(pdf_path),
        "hash": file_hash,
        "indexed_at": datetime.now().isoformat(),
        "stats": {
            "total_chars": len(full_text),
            "total_pages": len(pages_data),
            "total_chunks": len(chunks),
            "definitions": len(concepts.get("definitions", [])),
            "responsibilities": len(concepts.get("responsibilities", [])),
            "requirements": len(concepts.get("requirements", [])),
            "procedures": len(concepts.get("procedures", [])),
            "purposes": len(concepts.get("purposes", [])),
        },
        "pages": pages_data,
        "chunks": chunks,
        "concepts": concepts,
    }
    
    # Save individual index file
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_entry, f, indent=2, ensure_ascii=False)
    
    # Update manifest
    manifest["files"][pdf_name] = {
        "hash": file_hash,
        "indexed_at": index_entry["indexed_at"],
        "stats": index_entry["stats"],
        "index_file": str(index_file.relative_to(INDEX_DIR)),
    }
    save_manifest(manifest)
    
    return index_entry


def build_full_index(force_rebuild=False):
    """
    Build index for all PDFs in database folder
    
    Args:
        force_rebuild: If True, rebuild all indexes regardless of changes
    """
    print("=" * 60)
    print("Content Index Builder")
    print("=" * 60)
    
    # Ensure index directory exists
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all PDFs
    pdf_files = list(DATABASE_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {DATABASE_DIR}")
        return
    
    print(f"Found {len(pdf_files)} PDF files in {DATABASE_DIR}")
    print(f"Index directory: {INDEX_DIR}")
    print()
    
    # Index each PDF
    indexed = 0
    skipped = 0
    errors = 0
    
    for pdf_path in sorted(pdf_files):
        try:
            result = index_pdf(pdf_path, force_rebuild)
            if result:
                indexed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [ERROR] {pdf_path.name}: {e}")
            errors += 1
    
    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Indexed: {indexed}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")
    print(f"  Total:   {len(pdf_files)}")
    print()
    
    # Load and display manifest stats
    manifest = load_manifest()
    total_pages = sum(f["stats"]["total_pages"] for f in manifest["files"].values())
    total_chunks = sum(f["stats"]["total_chunks"] for f in manifest["files"].values())
    total_defs = sum(f["stats"]["definitions"] for f in manifest["files"].values())
    total_reqs = sum(f["stats"]["requirements"] for f in manifest["files"].values())
    
    print("Index Statistics:")
    print(f"  Total pages indexed: {total_pages}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Total definitions: {total_defs}")
    print(f"  Total requirements: {total_reqs}")


# ============================================================================
# FUTURE ML ENHANCEMENTS (Placeholder)
# ============================================================================

def build_embeddings_index():
    """
    Future: Build sentence embeddings for semantic search
    
    Requires: sentence-transformers, faiss-cpu
    
    This will enable:
    - Semantic question generation
    - Similar content clustering
    - Cross-document concept matching
    """
    print("Embeddings index not yet implemented.")
    print("Install ML dependencies first:")
    print("  pip install sentence-transformers faiss-cpu")


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build content index for aviation regulation PDFs"
    )
    parser.add_argument(
        "--rebuild", "-r",
        action="store_true",
        help="Force rebuild all indexes regardless of changes"
    )
    parser.add_argument(
        "--embeddings", "-e",
        action="store_true",
        help="Also build embeddings index (requires ML dependencies)"
    )
    
    args = parser.parse_args()
    
    build_full_index(force_rebuild=args.rebuild)
    
    if args.embeddings:
        print()
        build_embeddings_index()
