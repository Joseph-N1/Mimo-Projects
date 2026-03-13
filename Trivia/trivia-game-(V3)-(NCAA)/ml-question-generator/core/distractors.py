# distractors.py - Smart distractor generation for MCQ questions

import re
import random

# ============================================================================
# TEXT SUMMARIZATION HELPER
# ============================================================================

def make_concept_summary(text, max_len=150):
    """Create a concise summary suitable for an answer option"""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^\([a-z]\)\s*', '', text)
    text = re.sub(r'^\d+\.\d+\.?\d*\s*', '', text)
    if len(text) > max_len:
        # Try to cut at a sentence boundary
        sentences = re.split(r'(?<=[.;])\s+', text)
        result = ""
        for s in sentences:
            if len(result) + len(s) < max_len:
                result += s + " "
            else:
                break
        text = result.strip() if result else text[:max_len] + "..."
    return text

# ============================================================================
# SMART DISTRACTOR GENERATION
# ============================================================================

def generate_smart_distractors(correct_answer, concept_type, all_concepts, context="", pages_data=None):
    """Generate plausible but incorrect distractors that require understanding to differentiate
    
    Args:
        correct_answer: The correct answer text
        concept_type: Type of concept (definition, responsibility, requirement, etc.)
        all_concepts: Dictionary of all extracted concepts
        context: Additional context (optional)
        pages_data: Page data from PDF (optional)
        
    Returns:
        List of 3 distractor strings
    """
    distractors = []
    correct_lower = correct_answer.lower()
    
    # Strategy 1: Use other similar concepts from the same document (most plausible)
    if concept_type == "definition" and "definitions" in all_concepts:
        others = [d["meaning"] for d in all_concepts["definitions"] 
                  if d["meaning"].lower() != correct_lower and len(d["meaning"]) > 20]
        random.shuffle(others)
        for other in others[:3]:
            # Make sure it's sufficiently different but still plausible
            if other not in distractors:
                distractors.append(make_concept_summary(other, 150))
    
    elif concept_type == "responsibility" and "responsibilities" in all_concepts:
        others = [r["entity"].title() for r in all_concepts["responsibilities"] 
                  if r["entity"].lower() != correct_lower.split()[0].lower()]
        random.shuffle(others)
        seen = set()
        for e in others:
            if e not in seen and e not in distractors and e.lower() != correct_lower:
                seen.add(e)
                distractors.append(e)
                if len(distractors) >= 2:
                    break
    
    elif concept_type in ["requirement", "purpose", "application"]:
        # Use other requirements/purposes as distractors (they're plausible but wrong for this question)
        if "requirements" in all_concepts:
            others = [make_concept_summary(r["requirement"], 120) for r in all_concepts["requirements"]
                      if r["requirement"].lower() != correct_lower]
            random.shuffle(others)
            for other in others[:2]:
                if other not in distractors:
                    distractors.append(other)
        
        if "purposes" in all_concepts and len(distractors) < 2:
            others = [make_concept_summary(p["purpose"], 120) for p in all_concepts["purposes"]
                      if p["purpose"].lower() != correct_lower]
            random.shuffle(others)
            for other in others[:2]:
                if other not in distractors:
                    distractors.append(other)
    
    # Strategy 2: Subtle modifications to correct answer (requires careful reading)
    if len(distractors) < 3:
        subtle_modifications = [
            # Change scope/applicability
            lambda x: re.sub(r'\b(all|every|each)\b', 'some', x, flags=re.IGNORECASE),
            lambda x: re.sub(r'\b(must|shall)\b', 'should', x, flags=re.IGNORECASE),
            lambda x: re.sub(r'\b(required|mandatory)\b', 'recommended', x, flags=re.IGNORECASE),
            # Change timing/frequency
            lambda x: re.sub(r'\b(always|continuously)\b', 'periodically', x, flags=re.IGNORECASE),
            lambda x: re.sub(r'\b(immediately|promptly)\b', 'eventually', x, flags=re.IGNORECASE),
            # Change responsibility
            lambda x: re.sub(r'\b(organization|operator)\b', 'individual', x, flags=re.IGNORECASE),
            # Negate or invert
            lambda x: x.replace("ensure", "consider") if "ensure" in x.lower() else x,
            lambda x: x.replace("prevent", "minimize") if "prevent" in x.lower() else x,
        ]
        
        for mod in subtle_modifications:
            try:
                modified = mod(correct_answer)
                if modified != correct_answer and modified not in distractors and len(modified) > 20:
                    distractors.append(make_concept_summary(modified, 150))
                    if len(distractors) >= 3:
                        break
            except:
                continue
    
    # Strategy 3: Domain-specific plausible alternatives (aviation/safety focused)
    if len(distractors) < 3:
        domain_distractors = [
            "Establishing documentation procedures without practical implementation requirements",
            "Conducting periodic reviews based on organizational preference",
            "Delegating responsibility to departmental managers without central oversight",
            "Implementing voluntary safety measures beyond regulatory requirements",
            "Maintaining records for internal reference purposes only",
            "Coordinating with external stakeholders on an advisory basis",
            "Providing guidance that may be adapted based on operational needs",
            "Ensuring compliance through self-declaration processes",
            "Developing procedures aligned with industry best practices",
            "Establishing communication channels for safety-related information",
        ]
        random.shuffle(domain_distractors)
        for d in domain_distractors:
            if d not in distractors and d.lower() != correct_lower:
                distractors.append(d)
                if len(distractors) >= 3:
                    break
    
    # Ensure we have exactly 3 unique distractors
    distractors = list(dict.fromkeys(distractors))[:3]
    
    # If still short, add fallback that's clearly domain-relevant
    fallback_options = [
        "Following established organizational protocols",
        "Maintaining appropriate safety standards",
        "Ensuring operational efficiency",
    ]
    while len(distractors) < 3:
        for fb in fallback_options:
            if fb not in distractors:
                distractors.append(fb)
                break
    
    return distractors[:3]
