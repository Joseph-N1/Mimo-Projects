# hints.py - Hint generation and page reference utilities

import re
import random

# ============================================================================
# PAGE REFERENCE FINDER
# ============================================================================

def find_page_for_text(text_snippet, pages_data):
    """Find which page contains a text snippet
    
    Args:
        text_snippet: Text to search for
        pages_data: List of {page_num, text, headings} dicts
        
    Returns:
        tuple: (page_number, section_heading) or (None, None)
    """
    if not pages_data or not text_snippet:
        return None, None
    
    text_snippet_lower = text_snippet[:100].lower()
    for page in pages_data:
        if text_snippet_lower in page['text'].lower():
            section = page['headings'][0] if page['headings'] else None
            return page['page_num'], section
    return None, None

# ============================================================================
# KEY TERM EXTRACTION
# ============================================================================

def extract_key_terms(text, max_terms=5):
    """Extract key terms from text for hint generation"""
    if not text:
        return []
    
    # Remove common words and extract meaningful terms
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'of', 'to', 'in',
                  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                  'and', 'or', 'but', 'if', 'because', 'while', 'that', 'which', 'this',
                  'these', 'those', 'their', 'its', 'all', 'any', 'each', 'every', 'both'}
    
    words = re.findall(r'\b[A-Za-z]{4,}\b', text)
    key_terms = []
    seen = set()
    for word in words:
        word_lower = word.lower()
        if word_lower not in stop_words and word_lower not in seen:
            seen.add(word_lower)
            key_terms.append(word)
            if len(key_terms) >= max_terms:
                break
    return key_terms

# ============================================================================
# CONTEXT-AWARE HINT GENERATION
# ============================================================================

def generate_context_aware_hint(correct_answer, context, category, topic):
    """Generate a helpful, context-aware hint
    
    Args:
        correct_answer: The correct answer text
        context: Additional context about the question
        category: Question category (Understanding, Responsibility, etc.)
        topic: Topic/subject of the question
        
    Returns:
        A helpful hint string
    """
    key_terms = extract_key_terms(correct_answer, 3)
    
    hint_templates = {
        "Understanding": [
            f"Focus on what '{topic}' fundamentally means or represents.",
            f"Consider the defining characteristics of this concept.",
            f"Think about how '{topic}' relates to overall safety management.",
        ],
        "Responsibility": [
            f"Consider which role has the authority to {topic.lower() if topic else 'perform this function'}.",
            f"Think about who is accountable when things go wrong in this area.",
            f"Focus on organizational hierarchy and designated safety roles.",
        ],
        "Requirement": [
            f"Look for language indicating obligation ('shall', 'must', 'required').",
            f"Consider what is mandatory vs. what is merely recommended.",
            f"Think about compliance requirements vs. best practices.",
        ],
        "Purpose": [
            f"Consider the ultimate goal or objective being achieved.",
            f"Think about why this element exists in the safety framework.",
            f"Focus on outcomes and benefits, not just processes.",
        ],
        "Application": [
            f"Consider practical implementation in a real organization.",
            f"Think about which situations would trigger this requirement.",
            f"Focus on how this applies to day-to-day operations.",
        ],
        "Critical Thinking": [
            f"Carefully compare each option - one differs fundamentally from the others.",
            f"Look for the option that contradicts established requirements.",
            f"Consider which statement would NOT be found in regulations.",
        ],
    }
    
    templates = hint_templates.get(category, hint_templates["Understanding"])
    base_hint = random.choice(templates)
    
    # Add key term hints if available
    if key_terms and len(key_terms) >= 2:
        term_hint = f" Key concepts: {', '.join(key_terms[:2])}."
        return base_hint + term_hint
    
    return base_hint
