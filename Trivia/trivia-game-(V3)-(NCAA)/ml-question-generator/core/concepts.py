# concepts.py - Concept extraction from regulatory text

import re

# ============================================================================
# CONCEPT EXTRACTION
# ============================================================================

def extract_concepts(text):
    """Extract key concepts, definitions, responsibilities, and procedures
    
    Args:
        text: Document text to analyze
        
    Returns:
        Dictionary with keys: definitions, responsibilities, procedures,
        requirements, purposes, components
    """
    concepts = {
        "definitions": [],
        "responsibilities": [],
        "procedures": [],
        "requirements": [],
        "purposes": [],
        "components": [],
    }
    
    # Extract definitions
    def_patterns = [
        r'([A-Z][a-zA-Z\s\-]{3,40})\s*[-–:]\s*(?:means?|is\s+defined\s+as|refers?\s+to|is\s+a[n]?)\s+([^.]+\.)',
        r'"([^"]+)"\s+(?:means?|is\s+defined\s+as)\s+([^.]+\.)',
        r'([A-Z][a-zA-Z\s]{3,30})\.\s*[-–]\s*([A-Z][^.]+\.)',
    ]
    for pattern in def_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            term = match.group(1).strip().strip('.-–:')
            meaning = match.group(2).strip()
            if len(term) > 3 and len(meaning) > 20 and len(term) < 50:
                concepts["definitions"].append({
                    "term": term,
                    "meaning": meaning,
                    "context": text[max(0, match.start()-100):min(len(text), match.end()+100)]
                })
    
    # Extract responsibilities (who does what)
    resp_patterns = [
        r'(?:the\s+)?([A-Za-z\s]+(?:provider|operator|authority|manager|executive|personnel|organization))\s+(?:shall|must|will|is\s+responsible\s+for|has\s+responsibility)\s+([^.]+\.)',
        r'([A-Za-z\s]+)\s+(?:is|are)\s+responsible\s+for\s+([^.]+\.)',
        r'(?:responsibility|accountability)\s+(?:of|for)\s+(?:the\s+)?([A-Za-z\s]+)\s+(?:includes?|is|are)\s+([^.]+\.)',
    ]
    for pattern in resp_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            who = match.group(1).strip()
            what = match.group(2).strip()
            if len(who) > 3 and len(what) > 15:
                concepts["responsibilities"].append({
                    "entity": who,
                    "action": what,
                    "full_text": match.group(0)
                })
    
    # Extract procedures/processes
    proc_patterns = [
        r'(?:process|procedure|method)\s+(?:for|of|to)\s+([^.]+)(?:\s+(?:includes?|involves?|consists?\s+of|requires?)\s+([^.]+))?',
        r'(?:steps?|stages?)\s+(?:for|in|of)\s+([^:]+):\s*([^.]+\.)',
        r'(?:to\s+ensure|in\s+order\s+to)\s+([^,]+),\s+(?:the\s+)?(\w+)\s+(?:shall|must|should)\s+([^.]+\.)',
    ]
    for pattern in proc_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            concepts["procedures"].append({
                "text": match.group(0),
                "groups": match.groups()
            })
    
    # Extract requirements
    req_patterns = [
        r'(?:shall|must|is\s+required\s+to|are\s+required\s+to)\s+([^.]+\.)',
        r'(?:requirement|obligation)\s+(?:to|for|that)\s+([^.]+\.)',
        r'(?:it\s+is\s+)?(?:mandatory|compulsory|required)\s+(?:to|that|for)\s+([^.]+\.)',
    ]
    for pattern in req_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            req = match.group(1).strip() if match.groups() else match.group(0).strip()
            if len(req) > 20:
                # Get context before to understand what entity this applies to
                start = max(0, match.start() - 150)
                context_before = text[start:match.start()]
                concepts["requirements"].append({
                    "requirement": req,
                    "context": context_before,
                    "full_text": match.group(0)
                })
    
    # Extract purposes
    purpose_patterns = [
        r'(?:purpose|objective|aim|goal)\s+(?:of|is\s+to)\s+([^.]+\.)',
        r'(?:in\s+order\s+to|to\s+ensure|designed\s+to|intended\s+to)\s+([^.]+\.)',
        r'(?:this|the\s+\w+)\s+(?:ensures?|provides?|enables?|facilitates?)\s+([^.]+\.)',
    ]
    for pattern in purpose_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            concepts["purposes"].append({
                "purpose": match.group(1).strip() if match.groups() else match.group(0).strip(),
                "context": text[max(0, match.start()-100):min(len(text), match.end()+100)]
            })
    
    # Extract components/elements lists
    comp_patterns = [
        r'(?:includes?|comprises?|consists?\s+of|contains?)\s*(?:the\s+following)?[:\s]+([^.]+(?:\([a-z]\)[^.]+)+)',
        r'(?:components?|elements?|parts?)\s+(?:of|include)\s*:?\s*([^.]+\.)',
        r'(?:following|these)\s+(?:are|include)\s*:?\s*([^.]+\.)',
    ]
    for pattern in comp_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            concepts["components"].append({
                "items": match.group(1).strip() if match.groups() else match.group(0).strip(),
                "context": text[max(0, match.start()-100):min(len(text), match.end()+50)]
            })
    
    return concepts
