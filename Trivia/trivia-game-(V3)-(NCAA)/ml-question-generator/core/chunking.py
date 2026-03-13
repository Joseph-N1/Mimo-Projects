# chunking.py - Text chunking utilities for concept extraction

import re
from .clean import UNWANTED_PATTERNS

# ============================================================================
# SECTION IDENTIFIER EXTRACTION
# ============================================================================

SECTION_REGEX = re.compile(
    r"\b(IS\s*)?\d+\.\d+(\.\d+)*\b"
)

def extract_section_identifier(text: str):
    """Extract section identifier like 5.2.1 or IS 5.2.1 from text"""
    match = SECTION_REGEX.search(text)
    if match:
        return match.group(0)
    return None

# ============================================================================
# PARAGRAPH FILTERING
# ============================================================================

def is_useful_paragraph(text):
    """Check if paragraph has educational content worth extracting"""
    if not text or len(text.strip()) < 80:
        return False
    for pattern in UNWANTED_PATTERNS:
        if pattern.search(text[:150]):
            return False
    alpha_ratio = sum(c.isalpha() for c in text) / max(1, len(text))
    if alpha_ratio < 0.5:
        return False
    return True

# ============================================================================
# TEXT CHUNKING
# ============================================================================

def split_into_chunks(text, min_len=100, max_len=1500, return_dicts=False):
    """Split text into meaningful chunks for concept extraction
    
    Args:
        text: Full document text
        min_len: Minimum chunk length
        max_len: Maximum chunk length
        return_dicts: If True, return list of dicts with metadata; else return list of strings
        
    Returns:
        List of text chunks (strings or dicts) suitable for concept extraction
    """
    paragraphs = re.split(r'\n\s*\n|\n(?=\d+\.\d+|\([a-z]\))', text)
    chunks = []
    chunk_id = 0
    
    for para in paragraphs:
        para = para.strip()
        if is_useful_paragraph(para):
            if len(para) > max_len:
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) < max_len:
                        current += " " + sent
                    else:
                        if len(current) > min_len:
                            chunk_text = current.strip()
                            if return_dicts:
                                chunks.append({
                                    "chunk_id": f"chunk_{chunk_id}",
                                    "page": None,
                                    "section": extract_section_identifier(chunk_text),
                                    "text": chunk_text
                                })
                            else:
                                chunks.append(chunk_text)
                            chunk_id += 1
                        current = sent
                if len(current) > min_len:
                    chunk_text = current.strip()
                    if return_dicts:
                        chunks.append({
                            "chunk_id": f"chunk_{chunk_id}",
                            "page": None,
                            "section": extract_section_identifier(chunk_text),
                            "text": chunk_text
                        })
                    else:
                        chunks.append(chunk_text)
                    chunk_id += 1
            else:
                if return_dicts:
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id}",
                        "page": None,
                        "section": extract_section_identifier(para),
                        "text": para
                    })
                else:
                    chunks.append(para)
                chunk_id += 1
    return chunks
