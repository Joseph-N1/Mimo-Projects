# pipeline.py - Main question generation pipeline

import re
from .chunking import filter_source_chunks, normalize_source_text, split_into_chunks
from .concepts import extract_concepts
from .questions import (
    generate_definition_questions,
    generate_responsibility_questions,
    generate_scenario_questions,
    generate_purpose_questions,
    generate_requirement_questions,
    generate_not_questions,
)
from .hints import enrich_concepts_with_page_context, find_page_for_text, generate_context_aware_hint
from .explanations import build_detailed_explanation, build_page_reference
from .search import query_vector_index

# ============================================================================
# DIFFICULTY MAPPING
# ============================================================================

DIFFICULTY_MAP = {
    "Understanding": "easy",
    "Responsibility": "medium",
    "Application": "hard",
    "Purpose": "medium",
    "Requirement": "medium",
    "Critical Thinking": "hard",
}

CATEGORY_PRIORITY = {
    "Requirement": 28,
    "Application": 25,
    "Responsibility": 20,
    "Purpose": 17,
    "Understanding": 15,
    "Critical Thinking": 12,
}

CATEGORY_TARGET_RATIO = {
    "Requirement": 0.24,
    "Application": 0.20,
    "Responsibility": 0.18,
    "Purpose": 0.14,
    "Understanding": 0.16,
    "Critical Thinking": 0.08,
}

LOW_SIGNAL_PATTERNS = [
    re.compile(r"\bnote\b", re.IGNORECASE),
    re.compile(r"\bgeneral principles\b", re.IGNORECASE),
    re.compile(r"\bthe applicable organization\b", re.IGNORECASE),
    re.compile(r"\brequirements analysis\b", re.IGNORECASE),
    re.compile(r"\b(?:of|for|to)\s+airworthiness\?$", re.IGNORECASE),
    re.compile(r"\b(?:of|for|to)\s+applicability\?$", re.IGNORECASE),
    re.compile(r"\b(?:of|for|to)\s+volume\?$", re.IGNORECASE),
]


def normalize_question_key(question):
    return re.sub(r"\s+", " ", (question or "").strip().lower())


def looks_low_signal(text):
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    return any(pattern.search(cleaned) for pattern in LOW_SIGNAL_PATTERNS)


def score_question_candidate(question):
    category = question.get("category", "Understanding")
    prompt = question.get("question", "")
    answer = question.get("correctAnswer", "")
    topic = question.get("topic", "")
    study_focus = question.get("studyFocus", "")
    context = question.get("context", "")

    score = CATEGORY_PRIORITY.get(category, 10)

    question_word_count = len(prompt.split())
    if 8 <= question_word_count <= 20:
        score += 5
    elif question_word_count < 6 or question_word_count > 26:
        score -= 3

    answer_word_count = len(answer.split())
    if category != "Critical Thinking":
        if 8 <= answer_word_count <= 28:
            score += 6
        elif answer_word_count < 6 or answer_word_count > 38:
            score -= 4

    if study_focus and not looks_low_signal(study_focus):
        score += 6
    elif study_focus:
        score -= 5
    if topic and not looks_low_signal(topic):
        score += 4
    elif topic:
        score -= 6
    if context:
        score += 2
    if question.get("section_heading"):
        score += 4
    if question.get("page_num"):
        score += 2

    if looks_low_signal(prompt):
        score -= 10
    if category != "Critical Thinking" and looks_low_signal(answer):
        score -= 6

    return score


def dedupe_questions(questions):
    seen = set()
    unique_questions = []
    for question in questions:
        key = (
            normalize_question_key(question.get("question", "")),
            normalize_question_key(question.get("correctAnswer", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_questions.append(question)
    return unique_questions


def build_category_targets(max_questions):
    ordered_categories = sorted(CATEGORY_PRIORITY, key=CATEGORY_PRIORITY.get, reverse=True)
    targets = {category: int(max_questions * CATEGORY_TARGET_RATIO.get(category, 0)) for category in ordered_categories}
    assigned = sum(targets.values())

    while assigned < max_questions:
        for category in ordered_categories:
            if assigned >= max_questions:
                break
            targets[category] += 1
            assigned += 1

    return targets


def select_best_questions(all_questions, max_questions):
    unique_questions = dedupe_questions(all_questions)
    for question in unique_questions:
        question["_quality_score"] = score_question_candidate(question)

    buckets = {}
    for question in unique_questions:
        buckets.setdefault(question.get("category", "Understanding"), []).append(question)

    for category_questions in buckets.values():
        category_questions.sort(key=lambda item: item["_quality_score"], reverse=True)

    selected = []
    targets = build_category_targets(max_questions)
    for category in sorted(CATEGORY_PRIORITY, key=CATEGORY_PRIORITY.get, reverse=True):
        pool = buckets.get(category, [])
        selected.extend(pool[:targets.get(category, 0)])
        buckets[category] = pool[targets.get(category, 0):]

    if len(selected) < max_questions:
        remaining = []
        for pool in buckets.values():
            remaining.extend(pool)
        remaining.sort(key=lambda item: item["_quality_score"], reverse=True)
        selected.extend(remaining[:max_questions - len(selected)])

    selected.sort(
        key=lambda item: (
            {"easy": 0, "medium": 1, "hard": 2}.get(DIFFICULTY_MAP.get(item.get("category", ""), "medium"), 1),
            -item["_quality_score"],
        )
    )
    return selected[:max_questions]

# ============================================================================
# MAIN GENERATION PIPELINE
# ============================================================================

def generate_questions_json(text=None, max_questions=40, section_size=5, pages_data=None, 
                            doc_id=None, query=None, top_k=10):
    """Main function to generate exam-style questions from PDF text
    
    Args:
        text: Full document text (legacy mode)
        max_questions: Maximum number of questions to generate
        section_size: Questions per section
        pages_data: List of {page_num, text, headings} dicts from PDF extraction
        doc_id: Document ID for vector search mode
        query: User query for vector search mode
        top_k: Number of chunks to retrieve in vector search mode
        
    Returns:
        List of section dicts, each containing questions
    """
    
    # Vector search mode: retrieve relevant chunks
    if doc_id and query:
        search_results = query_vector_index(doc_id, query, top_k=top_k)
        # Combine retrieved chunks into context text
        raw_chunks = [result["text"] for result in search_results if result.get("text")]
        chunks = filter_source_chunks(raw_chunks)
        if not chunks:
            chunks = [normalize_source_text(chunk) for chunk in raw_chunks if normalize_source_text(chunk)]
        all_text = "\n\n".join(chunks)
        normalized_chunk_set = {normalize_source_text(chunk) for chunk in chunks}
        # Build pages_data from search results for page references
        if not pages_data:
            pages_data = []
            for result in search_results:
                if result.get("page") and normalize_source_text(result.get("text", "")) in normalized_chunk_set:
                    pages_data.append({
                        "page_num": result["page"],
                        "text": normalize_source_text(result.get("text", "")),
                        "headings": [result.get("section")] if result.get("section") else []
                    })
    else:
        # Legacy mode: use full document text
        if not text:
            raise ValueError("Either text or (doc_id + query) must be provided")
        raw_chunks = split_into_chunks(text)
        chunks = filter_source_chunks(raw_chunks)
        if not chunks:
            chunks = [normalize_source_text(chunk) for chunk in raw_chunks if normalize_source_text(chunk)]
        all_text = "\n\n".join(chunks)
    
    # Extract concepts from text
    concepts = enrich_concepts_with_page_context(extract_concepts(all_text), pages_data)
    
    # Generate different types of questions
    all_questions = []
    
    # Mix of question types for a balanced exam
    definition_qs = generate_definition_questions(concepts, max_questions // 5, pages_data=pages_data)
    responsibility_qs = generate_responsibility_questions(concepts, max_questions // 5, pages_data=pages_data)
    scenario_qs = generate_scenario_questions(concepts, chunks, max_questions // 3, pages_data=pages_data)
    purpose_qs = generate_purpose_questions(concepts, max_questions // 6, pages_data=pages_data)
    requirement_qs = generate_requirement_questions(concepts, max_questions // 4, pages_data=pages_data)
    not_qs = generate_not_questions(concepts, max_questions // 10, pages_data=pages_data)
    
    all_questions.extend(definition_qs)
    all_questions.extend(responsibility_qs)
    all_questions.extend(scenario_qs)
    all_questions.extend(purpose_qs)
    all_questions.extend(requirement_qs)
    all_questions.extend(not_qs)
    
    unique_questions = select_best_questions(all_questions, max_questions)
    
    # Format for output with enhanced explanations and page references
    questions = []
    for i, q in enumerate(unique_questions):
        category = q.get("category", "General")
        topic = q.get("topic", "")
        study_focus = q.get("studyFocus", "") or q.get("section_title", "") or topic
        correct_answer = q.get("correctAnswer", "")
        context = q.get("context", "")
        
        # Find page reference for this question's content
        page_num = q.get("page_num")
        section_ref = q.get("section_heading") or q.get("section_title")
        if pages_data and not page_num:
            # Search for the correct answer text in the PDF pages
            page_num, section_ref = find_page_for_text(correct_answer, pages_data)
            if not page_num:
                # Try searching for the question content
                page_num, section_ref = find_page_for_text(q.get("question", ""), pages_data)
        
        # Generate context-aware hint
        hint_payload = generate_context_aware_hint(
            correct_answer,
            context,
            category,
            topic,
            study_focus=study_focus,
            page_num=page_num,
            section_ref=section_ref,
            question_text=q.get("question", ""),
        )
        
        # Build detailed explanation
        base_explanation = q.get("explanation", "Review this concept for better understanding.")
        detailed_explanation = build_detailed_explanation(base_explanation, category)
        
        # Build page reference string
        page_ref_str = build_page_reference(page_num, section_ref, category)
        
        questions.append({
            "id": f"Q-{i+1}",
            "question": q["question"],
            "options": q["options"],
            "correctAnswer": correct_answer,
            "hint": hint_payload.get("summary"),
            "hintDetails": hint_payload,
            "explanation": detailed_explanation,
            "pageRef": page_num,
            "sectionRef": section_ref,
            "pdfReference": page_ref_str,
            "difficulty": DIFFICULTY_MAP.get(category, "medium"),
            "tags": [category.lower(), study_focus[:20] if study_focus else (topic[:20] if topic else "general")],
            "_quality_score": q.get("_quality_score", 0),
        })
    
    # Reorder: easy first, then medium, then hard
    questions.sort(
        key=lambda x: (
            {"easy": 0, "medium": 1, "hard": 2}.get(x["difficulty"], 1),
            -x.get("_quality_score", 0),
        )
    )
    
    # Reassign IDs after sorting
    for i, q in enumerate(questions):
        q["id"] = f"Q-{i+1}"
        q.pop("_quality_score", None)
    
    # Group into sections
    sections = []
    for s in range(0, len(questions), section_size):
        section_num = s // section_size + 1
        sections.append({
            "section": section_num,
            "questions": questions[s:s + section_size]
        })
    
    return sections


# ============================================================================
# RAG-BASED QUESTION GENERATION
# ============================================================================

def generate_questions_rag(doc_id: str, topic_query: str, num_questions: int = 5):
    """
    Retrieval-Augmented question generation.
    
    Args:
        doc_id: Document ID to search within
        topic_query: Topic or query to find relevant content
        num_questions: Number of questions to generate
        
    Returns:
        Dict with doc_id, query, context_used, and questions
    """

    # 1. Retrieve relevant chunks
    retrieved_chunks = query_vector_index(
        doc_id=doc_id,
        query=topic_query,
        top_k=5
    )

    if not retrieved_chunks:
        return {"error": "No relevant regulatory content found."}

    # 2. Concatenate retrieved text
    context_text = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])

    # 3. Build pages_data from retrieved chunks for page references
    pages_data = []
    for chunk in retrieved_chunks:
        if chunk.get("page"):
            pages_data.append({
                "page_num": chunk["page"],
                "text": chunk.get("text", ""),
                "headings": [chunk.get("section")] if chunk.get("section") else []
            })

    # 4. Generate questions using only retrieved context
    sections = generate_questions_json(
        text=context_text,
        max_questions=num_questions,
        section_size=5,
        pages_data=pages_data
    )

    # Flatten questions from sections
    questions = []
    for section in sections:
        questions.extend(section.get("questions", []))

    return {
        "doc_id": doc_id,
        "query": topic_query,
        "context_used": retrieved_chunks,
        "questions": questions
    }
