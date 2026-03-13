import sys
import re
import string
from pathlib import Path
from typing import Dict, List

# Add project root to path
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.append(str(PROJECT_ROOT))

from core.vector_store import search_similar_chunks


# ==========================
# CONFIG
# ==========================

TOP_K = 3


# ==========================
# DOMAIN MAPPING
# ==========================

DOMAIN_MAP = {
    "1": "Definitions & Abbreviations",
    "2": "Personnel Licensing",
    "3": "Medical Standards",
    "4": "Aircraft Registration & Marking",
    "5": "Airworthiness",
    "6": "Instrument & Equipment",
    "7": "Flight Operations",
    "8": "Air Transport Operations",
    "9": "Aerial Work",
    "10": "Air Navigation Services",
    "11": "Aerodromes",
    "12": "Search & Rescue",
    "13": "Aircraft Accident Investigation",
    "14": "Environmental Protection",
    "15": "Information Services",
    "16": "Aviation Training Organizations",
    "17": "Aviation Security",
    "18": "Dangerous Goods",
    "19": "Safety Management",
}


# ==========================
# CITATION HELPERS
# ==========================

def extract_part_from_doc_id(doc_id: str):
    match = re.search(r"part-(\d+)", doc_id.lower())
    if match:
        return f"Part {match.group(1)}"
    return None


def format_citation(metadata: Dict):
    doc_id = metadata.get("doc_id")
    page = metadata.get("page")
    section = metadata.get("section")

    part = extract_part_from_doc_id(doc_id)

    citation = "Nig. CARs"

    if part:
        citation += f" {part}"

    if section:
        citation += f" – Section {section}"

    if page:
        citation += f" (Page {page})"

    return citation


# ==========================
# QUERY EXPANSION
# ==========================

def expand_query(question: str, detected_domain: str) -> str:
    """Expand query with domain-specific terms for better retrieval."""
    q = question.lower()

    if detected_domain == "Part 5" and "return to service" in q:
        return question + " maintenance release airworthy certification maintenance records compliance"

    return question


# ==========================
# RETRIEVAL
# ==========================

def retrieve_context(query: str):
    # Detect expected domain from question keywords first
    detected_domain = detect_question_domain(query)

    # Expand query with domain-specific terms
    expanded_query = expand_query(query, detected_domain)

    results = search_similar_chunks(expanded_query, top_k=TOP_K)

    chunk_data = []

    for result in results:
        metadata = result["metadata"]
        text = metadata["text"]
        base_score = result["score"]

        citation = format_citation(metadata)

        # Boost score if chunk matches detected domain
        boosted_score = base_score
        if detected_domain != "Unknown" and detected_domain in citation:
            boosted_score += 0.05  # Domain match boost (normalized scale)

        chunk_data.append({
            "text": text,
            "citation": citation,
            "score": boosted_score,
            "base_score": base_score
        })

    # Re-sort by boosted score (descending) - matching domain dominates
    chunk_data.sort(key=lambda x: x["score"], reverse=True)

    # Filter chunks by detected domain if known
    if detected_domain != "Unknown":
        filtered_chunks = [
            chunk for chunk in chunk_data
            if detected_domain in chunk["citation"]
        ]
        # Use filtered chunks if we have any, otherwise fallback to all
        top_chunks = filtered_chunks if filtered_chunks else chunk_data
    else:
        top_chunks = chunk_data

    context_blocks = [c["text"] for c in top_chunks]
    citations = [c["citation"] for c in top_chunks]
    scores = [c["score"] for c in top_chunks]

    combined_context = "\n\n".join(context_blocks)

    avg_score = sum(scores) / len(scores) if scores else 0

    return combined_context, list(dict.fromkeys(citations)), avg_score, detected_domain


# ==========================
# CONFIDENCE LABELING
# ==========================

def get_confidence_label(confidence: float) -> str:
    if confidence > 0.70:
        return "High"
    elif confidence > 0.50:
        return "Medium"
    else:
        return "Low"


# ==========================
# GUARDRAILS
# ==========================

def guardrail_check(context: str, avg_score: float):
    if len(context.strip()) < 200:
        return False, "Insufficient regulatory context retrieved."

    if avg_score < 0.60:
        return False, "Retrieved content has low semantic similarity."

    return True, None


def check_topic_consistency(question: str, answer: str, threshold: int = 2) -> bool:
    """
    Check that key nouns from question appear in answer.
    Returns True if overlap >= threshold.
    """
    # Common stop words to exclude
    stop_words = {
        "what", "who", "where", "when", "why", "how", "is", "are", "the",
        "a", "an", "in", "on", "at", "for", "to", "of", "and", "or",
        "does", "do", "can", "should", "must", "will", "be", "been",
        "with", "from", "by", "about", "between", "into", "through"
    }

    question_words = set(clean_text_for_matching(question).split()) - stop_words
    answer_words = set(clean_text_for_matching(answer).split()) - stop_words

    overlap = len(question_words.intersection(answer_words))
    return overlap >= threshold


def detect_domain(citations: List[str]) -> str:
    """
    Detect which Part/domain is being retrieved from citations.
    Returns domain string like "Airworthiness (Part 5)".
    """
    parts_found = []

    for citation in citations:
        match = re.search(r"Part (\d+)", citation)
        if match:
            part_num = match.group(1)
            if part_num not in parts_found:
                parts_found.append(part_num)

    if not parts_found:
        return None

    # Build domain string
    domains = []
    for part_num in parts_found:
        domain_name = DOMAIN_MAP.get(part_num, "Unknown")
        domains.append(f"{domain_name} (Part {part_num})")

    return ", ".join(domains)


def detect_part5_subcontext(text: str) -> str:
    """
    Detect subcontext within Part 5 (damage vs maintenance).
    """
    text = text.lower()

    damage_terms = [
        "damage",
        "sustained",
        "resuming flight",
        "restored to an airworthy condition",
        "authority considers"
    ]

    maintenance_terms = [
        "maintenance release",
        "approval for return to service",
        "maintenance records",
        "certifying",
        "licensed in accordance"
    ]

    damage_score = sum(1 for term in damage_terms if term in text)
    maintenance_score = sum(1 for term in maintenance_terms if term in text)

    if damage_score > 0 and maintenance_score > 0:
        return "Ambiguous"
    elif damage_score > 0:
        return "Damage Context"
    elif maintenance_score > 0:
        return "Maintenance Context"
    else:
        return "Unknown"


def detect_question_domain(question: str) -> str:
    """
    Detect which Part the question is targeting based on keyword matching.
    """
    domain_keywords = {
        "Part 1": [
            "definition",
            "aircraft",
            "airworthiness",
            "operator",
            "commercial air transport",
            "define",
            "meaning",
            "term",
            "interpretation",
            "abbreviation"
        ],
        "Part 2": [
            "pilot",
            "licence",
            "license",
            "rating",
            "commercial pilot",
            "private pilot",
            "flight instructor",
            "ATPL",
            "recency",
            "medical certificate",
            "medical certification",
            "flight crew"
        ],
        "Part 5": [
            "airworthiness",
            "maintenance",
            "component",
            "return to service",
            "return to service after maintenance",
            "damage",
            "repair",
            "unserviceable",
            "aircraft condition",
            "inspection",
            "defect",
            "modification",
            "serviceability"
        ],
        "Part 6": [
            "maintenance engineer",
            "aircraft maintenance engineer",
            "AME",
            "AME licence",
            "certifying staff",
            "certifying engineer",
            "maintenance licence",
            "personnel licensing",
            "maintenance personnel",
            "certification authorization",
            "qualifications",
            "AMEL",
            "engineer licence"
        ],
        "Part 8": [
            "operator",
            "flight operations",
            "pre flight",
            "departure",
            "documents",
            "on board",
            "documents onboard",
            "aircraft documents",
            "carried on board",
            "alternate aerodrome",
            "flight planning",
            "aircraft operator",
            "fuel planning",
            "pilot in command",
            "operational procedures",
            "flight preparation"
        ],
        "Part 12": [
            "accident",
            "investigation",
            "reported",
            "incident",
            "serious",
            "accident investigation",
            "incident reporting",
            "reporting",
            "safety investigation"
        ],
        "Part 17": [
            "security",
            "aviation security",
            "unlawful interference",
            "aerodrome security",
            "security threat",
            "airport security",
            "screening",
            "security measures",
            "security responsibilities"
        ]
    }

    priority_order = [
        "Part 17",  # security first
        "Part 12",  # accident investigation
        "Part 6",   # personnel licensing
        "Part 5",   # airworthiness
        "Part 8",   # operations
        "Part 2",   # pilot licensing
        "Part 1"    # definitions last
    ]

    for part in priority_order:
        keywords = domain_keywords[part]
        if any(k in question.lower() for k in keywords):
            return part

    return "Unknown"


def detect_cross_reference(question):
    question = question.lower()

    cross_refs = []

    # Licensing references
    if any(word in question for word in [
        "licence",
        "license",
        "authorised",
        "authorized",
        "who can sign",
        "certifying staff",
        "engineer licence"
    ]):
        cross_refs.append("Part 6 – Personnel Licensing")

    # Operations references
    if any(word in question for word in [
        "operator",
        "flight operations",
        "operational control",
        "dispatch"
    ]):
        cross_refs.append("Part 8 – Air Transport Operations")

    # Security references
    if any(word in question for word in [
        "security",
        "unlawful interference",
        "airport protection"
    ]):
        cross_refs.append("Part 17 – Aviation Security")

    return cross_refs


# ==========================
# PROMPT BUILDER
# ==========================

def build_prompt(question: str, context: str) -> str:
    return f"""
You are an aviation regulatory assistant.

Answer strictly using the provided regulatory context.
Do NOT invent information.
Write a structured, professional answer.

Question:
{question}

Regulatory Context:
{context}
"""


# ==========================
# REGULATORY WEIGHTING
# ==========================

OBLIGATION_TERMS = [
    "shall", "must", "required", "approved",
    "certified", "completed", "no person may",
    "ensure", "shall not", "is required to",
    "shall ensure", "is responsible for",
    "may not", "must not"
]

CONDITION_TERMS = [
    "before", "prior", "until", "unless",
    "condition", "requirement"
]


# ==========================
# MOCK LLM (FREE)
# ==========================

def clean_regulatory_artifacts(text: str) -> str:
    # Remove isolated numbering like "(1).", "(7)."
    text = re.sub(r"\(\d+\)\.?", "", text)

    # Remove stray numbering lines like "Part 5 - AIRWORTHINESS 1."
    text = re.sub(r"Part\s+\d+\s*-\s*AIRWORTHINESS\s*\d*\.?", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_text_for_matching(text):
    return text.lower().translate(str.maketrans('', '', string.punctuation))


def remove_fragments(sentences):
    """Remove broken clause fragments that are too short or start with conjunctions."""
    cleaned = []
    for s in sentences:
        if len(s.split()) > 8 and not s.strip().lower().startswith(("when", "if", "and")):
            cleaned.append(s)
    return cleaned


def extract_intent_terms(question: str):
    q = question.lower()

    intent_boost_terms = []
    penalty_terms = []
    hard_negative_terms = []

    if "return to service" in q or "before" in q or "maintenance" in q or "airworthiness" in q:
        intent_boost_terms += [
            "return to service",
            "maintenance release",
            "airworthy",
            "certifying",
            "signed",
            "completed",
            "approval"
        ]

        penalty_terms += [
            "expiry",
            "service life",
            "incident",
            "accident",
            "disposal"
        ]

        # Part 17 bleed prevention
        hard_negative_terms += [
            "security programme",
            "airport",
            "screening",
            "passengers",
            "cargo",
            "sterile area"
        ]

    if "licence" in q or "licensing" in q:
        intent_boost_terms += [
            "licence",
            "rating",
            "medical",
            "authorisation",
            "knowledge test",
            "skill test"
        ]

        # Prevent airworthiness bleed
        hard_negative_terms += [
            "maintenance release",
            "return to service",
            "airworthy"
        ]

    if "security" in q:
        intent_boost_terms += [
            "screening",
            "sterile area",
            "security programme",
            "unauthorized interference"
        ]

        # Prevent airworthiness bleed
        hard_negative_terms += [
            "maintenance release",
            "return to service",
            "airworthy",
            "certificate of airworthiness"
        ]

    return intent_boost_terms, penalty_terms, hard_negative_terms


def mock_llm_generate(prompt: str, context: str, question: str = ""):
    """
    Returns: tuple of (answer_text, confidence_score)
    """
    sentences = re.split(r'[.;]\s+', context)

    question_words = set(clean_text_for_matching(question).split())

    intent_boost_terms, penalty_terms, hard_negative_terms = extract_intent_terms(question)

    scored_sentences = []

    for sentence in sentences:
        sentence_clean = clean_text_for_matching(sentence)
        sentence_words = set(sentence_clean.split())

        overlap = len(question_words.intersection(sentence_words))

        obligation_weight = sum(
            1 for term in OBLIGATION_TERMS if term in sentence_clean
        )

        condition_weight = sum(
            1 for term in CONDITION_TERMS if term in sentence_clean
        )

        intent_boost = sum(
            1 for term in intent_boost_terms if term in sentence_clean
        )

        penalty = sum(
            1 for term in penalty_terms if term in sentence_clean
        )

        # Hard negative filter for domain drift prevention
        hard_negative_hit = any(
            term in sentence_clean for term in hard_negative_terms
        )

        score = (
            overlap
            + (2 * obligation_weight)
            + condition_weight
            + (3 * intent_boost)
            - (2 * penalty)
        )

        if intent_boost > 0:
            score += 2

        if hard_negative_hit:
            score -= 5

        scored_sentences.append((score, sentence))

    scored_sentences.sort(reverse=True, key=lambda x: x[0])

    # Real confidence scoring with sigmoid-like soft cap
    max_score = scored_sentences[0][0] if scored_sentences else 0
    confidence = round(
        max_score / (max_score + 5),
        2
    )

    # Topic coherence filter: keep sentences that share tokens with top sentence
    top_sentences = [(s[0], s[1]) for s in scored_sentences if s[0] > 0][:8]

    if not top_sentences:
        return "No clearly defined regulatory conditions were identified in the retrieved context.", confidence

    # Get key tokens from top scoring sentence
    primary_tokens = set(clean_text_for_matching(top_sentences[0][1]).split())

    # Filter to sentences sharing at least 1 key token with top sentence
    filtered_sentences = [
        s for s in top_sentences
        if len(primary_tokens.intersection(set(clean_text_for_matching(s[1]).split()))) >= 1
    ]

    # Take top 6 coherent sentences
    best_sentences = [s[1] for s in filtered_sentences][:6]

    if not best_sentences:
        # Fallback to top sentences if filter is too strict
        best_sentences = [s[1] for s in top_sentences][:6]

    cleaned_sentences = [clean_regulatory_artifacts(s) for s in best_sentences]

    # Remove broken clause fragments
    cleaned_sentences = remove_fragments(cleaned_sentences)

    if not cleaned_sentences:
        return "No clearly defined regulatory conditions were identified in the retrieved context.", confidence

    intro = "Based on the applicable provisions of the Nigerian Civil Aviation Regulations, the following conditions must be satisfied:"

    bullet_points = "\n".join(f"- {s.strip()}" for s in cleaned_sentences)

    return f"{intro}\n\n{bullet_points}", confidence


# ==========================
# MAIN QA ENGINE
# ==========================

def run_engine(question: str):
    """
    Run the QA engine and return structured result.
    
    Returns:
        dict with keys: detected_domain, subcontext, confidence, answer
    """
    context, citations, avg_score, detected_domain = retrieve_context(question)

    print(f"\nDetected Regulatory Domain: {detected_domain}")

    cross_refs = detect_cross_reference(question)
    if cross_refs:
        print("\nCross-Referenced Regulations:")
        for ref in cross_refs:
            print(f"- {ref}")

    subcontext = None

    # Check for Part 5 subcontext ambiguity
    if detected_domain == "Part 5":
        subcontext = detect_part5_subcontext(context)
        print(f"Part 5 Subcontext: {subcontext}")

        if subcontext == "Ambiguous":
            return {
                "detected_domain": detected_domain,
                "subcontext": subcontext,
                "confidence": None,
                "answer": """⚠ Ambiguity Detected in Regulatory Context.

The phrase 'returned to service' appears in multiple regulatory contexts under Part 5:
1. Return to service after maintenance (maintenance release requirements)
2. Return to service after damage (airworthiness restoration by Authority)

Please clarify which context you are referring to:
- For maintenance: "What are the requirements for maintenance release?"
- For damage: "What are the requirements after aircraft damage?\""""
            }

        # Damage context clarification (warning, not a stop)
        if subcontext == "Damage Context" and "maintenance" not in question.lower():
            print("\nNote: The question has been interpreted in the context of aircraft damage restoration under Part 5.")
            print("If you intended return to service after maintenance, please specify.")

    valid, reason = guardrail_check(context, avg_score)

    if not valid:
        return {
            "detected_domain": detected_domain,
            "subcontext": subcontext,
            "confidence": avg_score,
            "answer": f"Unable to generate reliable answer.\n\nReason: {reason}"
        }

    prompt = build_prompt(question, context)

    answer, real_confidence = mock_llm_generate(prompt, context, question)

    # Topic consistency check - downgrade confidence if poor overlap
    topic_consistent = check_topic_consistency(question, answer)
    if not topic_consistent:
        real_confidence = max(0.3, real_confidence - 0.2)  # Penalize topic drift

    # Safety rules based on confidence
    if real_confidence < 0.65:
        print("\nNote: Confidence is moderate. Consider refining the question for a more precise regulatory reference.")
    if real_confidence < 0.55:
        print("\nWarning: The system is uncertain about this answer. Please verify the cited regulation manually.")

    # Detect domain from retrieved citations
    retrieved_domain = detect_domain(citations)

    citation_block = "\n".join(f"- {c}" for c in citations)

    # Build domain info - show both detected and retrieved for transparency
    domain_line = ""
    if detected_domain != "Unknown":
        domain_line += f"\nExpected Domain: {detected_domain}"
    if retrieved_domain:
        domain_line += f"\nRetrieved Domain: {retrieved_domain}"

    final_answer = f"""Answer:
{answer}

Confidence: {real_confidence:.2f}{domain_line}

Sources:
{citation_block}
"""

    return {
        "detected_domain": detected_domain,
        "subcontext": subcontext,
        "confidence": real_confidence,
        "answer": final_answer
    }


def answer_question(question: str):
    """
    User-friendly wrapper around run_engine for backward compatibility.
    """
    result = run_engine(question)
    return result["answer"]


# ==========================
# CLI
# ==========================

if __name__ == "__main__":
    question = input("Enter your question: ")
    response = answer_question(question)
    print(response)
