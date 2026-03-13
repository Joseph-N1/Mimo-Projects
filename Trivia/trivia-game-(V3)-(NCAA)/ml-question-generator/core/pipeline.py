# pipeline.py - Main question generation pipeline

import random
from .chunking import split_into_chunks
from .concepts import extract_concepts
from .questions import (
    generate_definition_questions,
    generate_responsibility_questions,
    generate_scenario_questions,
    generate_purpose_questions,
    generate_requirement_questions,
    generate_not_questions,
)
from .hints import find_page_for_text, generate_context_aware_hint
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
        chunks = [result["text"] for result in search_results if result.get("text")]
        all_text = "\n\n".join(chunks)
        # Build pages_data from search results for page references
        if not pages_data:
            pages_data = []
            for result in search_results:
                if result.get("page"):
                    pages_data.append({
                        "page_num": result["page"],
                        "text": result.get("text", ""),
                        "headings": [result.get("section")] if result.get("section") else []
                    })
    else:
        # Legacy mode: use full document text
        if not text:
            raise ValueError("Either text or (doc_id + query) must be provided")
        chunks = split_into_chunks(text)
        all_text = "\n".join(chunks)
    
    # Extract concepts from text
    concepts = extract_concepts(all_text)
    
    # Generate different types of questions
    all_questions = []
    
    # Mix of question types for a balanced exam
    definition_qs = generate_definition_questions(concepts, max_questions // 5)
    responsibility_qs = generate_responsibility_questions(concepts, max_questions // 5)
    scenario_qs = generate_scenario_questions(concepts, chunks, max_questions // 3)
    purpose_qs = generate_purpose_questions(concepts, max_questions // 6)
    requirement_qs = generate_requirement_questions(concepts, max_questions // 4)
    not_qs = generate_not_questions(concepts, max_questions // 10)
    
    all_questions.extend(definition_qs)
    all_questions.extend(responsibility_qs)
    all_questions.extend(scenario_qs)
    all_questions.extend(purpose_qs)
    all_questions.extend(requirement_qs)
    all_questions.extend(not_qs)
    
    # Deduplicate by question text
    seen = set()
    unique_questions = []
    for q in all_questions:
        key = q["question"][:50].lower()
        if key not in seen:
            seen.add(key)
            unique_questions.append(q)
    
    # Shuffle and limit
    random.shuffle(unique_questions)
    unique_questions = unique_questions[:max_questions]
    
    # Format for output with enhanced explanations and page references
    questions = []
    for i, q in enumerate(unique_questions):
        category = q.get("category", "General")
        topic = q.get("topic", "")
        correct_answer = q.get("correctAnswer", "")
        context = q.get("context", "")
        
        # Find page reference for this question's content
        page_num = None
        section_ref = None
        if pages_data:
            # Search for the correct answer text in the PDF pages
            page_num, section_ref = find_page_for_text(correct_answer, pages_data)
            if not page_num:
                # Try searching for the question content
                page_num, section_ref = find_page_for_text(q.get("question", ""), pages_data)
        
        # Generate context-aware hint
        hint = generate_context_aware_hint(correct_answer, context, category, topic)
        
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
            "hint": hint,
            "explanation": detailed_explanation,
            "pageRef": page_num,
            "sectionRef": section_ref,
            "pdfReference": page_ref_str,
            "difficulty": DIFFICULTY_MAP.get(category, "medium"),
            "tags": [category.lower(), topic[:20] if topic else "general"]
        })
    
    # Reorder: easy first, then medium, then hard
    questions.sort(key=lambda x: {"easy": 0, "medium": 1, "hard": 2}.get(x["difficulty"], 1))
    
    # Reassign IDs after sorting
    for i, q in enumerate(questions):
        q["id"] = f"Q-{i+1}"
    
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
