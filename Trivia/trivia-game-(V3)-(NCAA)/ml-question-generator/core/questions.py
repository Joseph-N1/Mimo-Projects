# questions.py - Question generators for different question types

import re
import random
from .distractors import generate_smart_distractors, make_concept_summary

# ============================================================================
# EXAM-STYLE QUESTION TEMPLATES
# ============================================================================

SCENARIO_TEMPLATES = [
    "An organization is implementing a {topic}. Which of the following BEST describes {aspect}?",
    "A {role} needs to ensure compliance with {topic} requirements. What should be the PRIMARY focus?",
    "During an audit, an inspector finds issues with {topic}. Which action would be MOST appropriate?",
    "An operator is developing their {topic} documentation. Which element is ESSENTIAL to include?",
    "A safety manager discovers a gap in {topic}. What is the FIRST step to address this?",
    "When establishing a {topic}, which of the following is the MOST important consideration?",
    "A company wants to improve their {topic}. Which approach would be MOST effective?",
    "{role} is reviewing the {topic} framework. Which component is CRITICAL for success?",
]

PURPOSE_TEMPLATES = [
    "What is the PRIMARY purpose of {concept}?",
    "The MAIN objective of {concept} is to:",
    "Which statement BEST describes the goal of {concept}?",
    "{concept} is implemented PRIMARILY to:",
]

RESPONSIBILITY_TEMPLATES = [
    "Who has PRIMARY responsibility for {action}?",
    "Which entity is ACCOUNTABLE for {action}?",
    "{action} is the responsibility of:",
    "Which role is responsible for {action}?",
]

REQUIREMENT_TEMPLATES = [
    "What is REQUIRED regarding {topic}?",
    "Which of the following is a MANDATORY requirement for {topic}?",
    "Organizations MUST ensure which of the following regarding {topic}?",
    "What is an essential requirement for {topic}?",
]

UNDERSTANDING_TEMPLATES = [
    "Which statement BEST describes {concept}?",
    "What is the CORRECT understanding of {concept}?",
    "How would you BEST define {concept}?",
    "{concept} can be BEST described as:",
]

APPLICATION_TEMPLATES = [
    "In which situation would {concept} be MOST applicable?",
    "When would {concept} be MOST relevant?",
    "Which scenario demonstrates proper implementation of {concept}?",
    "How should {concept} be applied in practice?",
]

NOT_TEMPLATES = [
    "Which of the following is NOT a requirement for {topic}?",
    "All of the following are true about {topic} EXCEPT:",
    "Which statement is INCORRECT regarding {topic}?",
]

# ============================================================================
# QUESTION GENERATORS
# ============================================================================

def generate_definition_questions(concepts, max_questions=8):
    """Generate questions testing understanding of key terms"""
    questions = []
    definitions = concepts.get("definitions", [])
    
    for defn in definitions[:max_questions * 2]:
        term = defn["term"]
        meaning = make_concept_summary(defn["meaning"], 180)
        
        # Skip if too short or generic
        if len(meaning) < 30 or len(term) < 3:
            continue
        
        template = random.choice(UNDERSTANDING_TEMPLATES)
        question_text = template.format(concept=term)
        
        distractors = generate_smart_distractors(meaning, "definition", concepts)
        
        options = [meaning] + distractors
        random.shuffle(options)
        
        questions.append({
            "question": question_text,
            "options": options,
            "correctAnswer": meaning,
            "explanation": f"'{term}' refers to {meaning}",
            "category": "Understanding",
            "topic": term,
        })
        
        if len(questions) >= max_questions:
            break
    
    return questions


def generate_responsibility_questions(concepts, max_questions=8):
    """Generate questions about who is responsible for what"""
    questions = []
    responsibilities = concepts.get("responsibilities", [])
    
    # Group by action to create "who is responsible" questions
    for resp in responsibilities[:max_questions * 2]:
        entity = resp["entity"].strip()
        action = make_concept_summary(resp["action"], 120)
        
        if len(action) < 20:
            continue
        
        # Clean up entity name
        entity = re.sub(r'^\s*the\s+', '', entity, flags=re.IGNORECASE).strip()
        entity = entity.title()
        
        # Skip if entity is too generic or unclear
        if len(entity) < 4 or entity.lower() in ['the', 'a', 'an', 'it', 'this', 'that']:
            continue
        
        # Create a cleaner action description for the question
        action_summary = action[:80].strip()
        # Remove trailing incomplete words
        if not action_summary.endswith('.'):
            words = action_summary.split()
            if len(words) > 3:
                action_summary = ' '.join(words[:-1])
        # Clean the action for use in question
        action_summary = re.sub(r'^(not\s+|shall\s+|must\s+|to\s+|be\s+)', '', action_summary, flags=re.IGNORECASE)
        action_summary = action_summary.strip()
        
        # Skip if action is too short, too generic, or looks like a fragment
        if len(action_summary) < 15:
            continue
        if action_summary.lower().startswith(('prevented', 'allowed', 'required', 'make available')):
            continue
        
        # Create a clean gerund phrase
        action_words = action_summary.split()
        first_word = action_words[0].lower() if action_words else ""
        
        verbs_to_gerund = {
            'implement': 'implementing', 'maintain': 'maintaining', 'develop': 'developing',
            'manage': 'managing', 'ensure': 'ensuring', 'define': 'defining',
            'establish': 'establishing', 'identify': 'identifying', 'monitor': 'monitoring',
            'assess': 'assessing', 'review': 'reviewing', 'conduct': 'conducting',
            'provide': 'providing', 'coordinate': 'coordinating', 'document': 'documenting',
            'appoint': 'appointing', 'create': 'creating', 'apply': 'applying',
        }
        
        if first_word in verbs_to_gerund:
            rest_of_action = ' '.join(action_words[1:])
            action_summary = verbs_to_gerund[first_word] + ' ' + rest_of_action
        elif first_word.endswith('ing'):
            pass  # Already a gerund
        else:
            # Skip if we can't make a clean gerund phrase
            continue
        
        # Clean up any trailing punctuation
        action_summary = action_summary.rstrip('.,;:')
        
        # Skip if action contains dates or document metadata
        if re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december|\d{4}|amendment)', action_summary, re.IGNORECASE):
            continue
        
        # Capitalize first letter for question formatting
        action_summary = action_summary[0].upper() + action_summary[1:] if action_summary else action_summary
        
        template = random.choice(RESPONSIBILITY_TEMPLATES)
        question_text = template.format(action=action_summary)
        
        # Generate entity-based distractors
        all_entities = list(set([r["entity"].title() for r in responsibilities if len(r["entity"]) > 4]))
        other_entities = [e for e in all_entities if e.lower() != entity.lower()]
        random.shuffle(other_entities)
        
        distractors = other_entities[:2]
        generic_entities = [
            "External consultants only",
            "No specific role - shared responsibility",
            "Government regulatory bodies exclusively",
            "Individual employees at their discretion",
        ]
        while len(distractors) < 3:
            for g in generic_entities:
                if g not in distractors:
                    distractors.append(g)
                    if len(distractors) >= 3:
                        break
        
        options = [entity] + distractors[:3]
        random.shuffle(options)
        
        questions.append({
            "question": question_text,
            "options": options,
            "correctAnswer": entity,
            "explanation": f"{entity} is responsible for {action}",
            "category": "Responsibility",
            "topic": action_summary[:50],
        })
        
        if len(questions) >= max_questions:
            break
    
    return questions


def generate_scenario_questions(concepts, chunks, max_questions=10):
    """Generate scenario-based application questions"""
    questions = []
    
    # Extract topics from requirements and procedures
    topics = []
    for req in concepts.get("requirements", []):
        topics.append(req)
    for proc in concepts.get("procedures", []):
        topics.append(proc)
    
    roles = ["safety manager", "operator", "organization", "service provider", 
             "accountable executive", "compliance officer"]
    
    subject_areas = {
        "safety": "safety management",
        "risk": "risk management", 
        "training": "training programme",
        "compliance": "compliance management",
        "management": "management system",
        "documentation": "documentation requirements",
        "audit": "audit processes",
        "monitoring": "performance monitoring",
        "reporting": "safety reporting",
        "hazard": "hazard identification",
        "sms": "SMS implementation",
        "performance": "safety performance",
    }
    
    for topic in topics[:max_questions * 2]:
        topic_text = topic.get("requirement", topic.get("text", ""))
        if len(topic_text) < 40:
            continue
        
        # Identify the subject area
        subject = None
        for keyword, area in subject_areas.items():
            if keyword in topic_text.lower():
                subject = area
                break
        
        if not subject:
            continue
        
        template = random.choice(SCENARIO_TEMPLATES)
        role = random.choice(roles)
        
        question_text = template.format(
            topic=subject,
            aspect="the appropriate approach",
            role=role
        )
        
        correct_answer = make_concept_summary(topic_text, 150)
        
        # Ensure correct answer is meaningful
        if len(correct_answer) < 30:
            continue
            
        distractors = generate_smart_distractors(correct_answer, "application", concepts)
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        questions.append({
            "question": question_text,
            "options": options,
            "correctAnswer": correct_answer,
            "explanation": f"For {subject}, the correct approach involves: {correct_answer}",
            "category": "Application",
            "topic": subject,
        })
        
        if len(questions) >= max_questions:
            break
    
    return questions


def generate_purpose_questions(concepts, max_questions=6):
    """Generate questions about the purpose/objectives of concepts"""
    questions = []
    purposes = concepts.get("purposes", [])
    
    # Known good subjects for purpose questions
    valid_subjects = [
        "safety management system", "SMS", "SSP", "State Safety Programme",
        "safety data protection", "safety information", "risk management",
        "hazard identification", "safety reporting", "safety training",
        "safety performance monitoring", "safety assurance", "safety promotion",
        "compliance monitoring", "safety oversight", "safety policy",
    ]
    
    for purpose_item in purposes[:max_questions * 2]:
        purpose = make_concept_summary(purpose_item["purpose"], 150)
        context = purpose_item.get("context", "")
        
        if len(purpose) < 30:
            continue
        
        # Try to identify what the purpose is for using known subjects
        subject = None
        context_lower = context.lower()
        
        for valid_subj in valid_subjects:
            if valid_subj.lower() in context_lower:
                subject = valid_subj
                break
        
        # If no known subject, try to extract one but be strict
        if not subject:
            match = re.search(r'(?:the|a|an)\s+([A-Z][a-z]+(?:\s+[a-z]+)?\s+(?:system|programme|program|process|framework|policy|management|plan))', context)
            if match:
                subject = match.group(1).strip()
        
        # Skip if we still don't have a good subject
        if not subject or len(subject) < 5 or subject.lower().startswith(('and ', 'or ', 'the ')):
            continue
        
        template = random.choice(PURPOSE_TEMPLATES)
        question_text = template.format(concept=subject)
        
        distractors = generate_smart_distractors(purpose, "purpose", concepts)
        
        options = [purpose] + distractors
        random.shuffle(options)
        
        questions.append({
            "question": question_text,
            "options": options,
            "correctAnswer": purpose,
            "explanation": f"The primary purpose is to {purpose}",
            "category": "Purpose",
            "topic": subject,
        })
        
        if len(questions) >= max_questions:
            break
    
    return questions


def generate_requirement_questions(concepts, max_questions=8):
    """Generate questions about mandatory requirements"""
    questions = []
    requirements = concepts.get("requirements", [])
    
    subject_keywords = {
        "service provider": "service providers",
        "operator": "operators",
        "authority": "the Authority",
        "organization": "organizations",
        "sms": "SMS implementation",
        "ssp": "SSP requirements",
        "safety manager": "safety managers",
        "accountable executive": "accountable executives",
        "training": "training programmes",
        "documentation": "documentation",
        "reporting": "safety reporting",
        "risk": "risk management",
        "hazard": "hazard identification",
    }
    
    for req in requirements[:max_questions * 2]:
        requirement = make_concept_summary(req["requirement"], 150)
        context = req.get("context", "")
        full_context = context + " " + req.get("full_text", "")
        
        if len(requirement) < 30:
            continue
        
        # Find the best topic match
        topic = None
        for keyword, topic_name in subject_keywords.items():
            if keyword in full_context.lower():
                topic = topic_name
                break
        
        if not topic:
            topic = "safety management"
        
        template = random.choice(REQUIREMENT_TEMPLATES)
        question_text = template.format(topic=topic)
        
        distractors = generate_smart_distractors(requirement, "requirement", concepts)
        
        options = [requirement] + distractors
        random.shuffle(options)
        
        questions.append({
            "question": question_text,
            "options": options,
            "correctAnswer": requirement,
            "explanation": f"The requirement states: {requirement}",
            "category": "Requirement",
            "topic": topic,
        })
        
        if len(questions) >= max_questions:
            break
    
    return questions


def generate_not_questions(concepts, max_questions=4):
    """Generate 'which is NOT' style questions for variety"""
    questions = []
    requirements = concepts.get("requirements", [])
    definitions = concepts.get("definitions", [])
    
    # Create NOT questions from requirements
    if len(requirements) >= 4:
        for i in range(min(max_questions, len(requirements) // 4)):
            topic_reqs = requirements[i*4:(i+1)*4]
            if len(topic_reqs) < 4:
                continue
            
            # Get 3 correct requirements and 1 wrong answer
            correct_reqs = [make_concept_summary(r["requirement"], 100) for r in topic_reqs[:3]]
            
            # The wrong answer (what we're looking for)
            wrong_answers = [
                "This is recommended but not mandatory",
                "This is at the discretion of individual organizations",
                "This requirement has been waived for most operators",
                "This applies only in emergency situations",
            ]
            wrong_answer = random.choice(wrong_answers)
            
            template = random.choice(NOT_TEMPLATES)
            question_text = template.format(topic="safety management")
            
            options = correct_reqs + [wrong_answer]
            random.shuffle(options)
            
            questions.append({
                "question": question_text,
                "options": options,
                "correctAnswer": wrong_answer,
                "explanation": f"The incorrect statement is: {wrong_answer}. The other options are actual requirements.",
                "category": "Critical Thinking",
                "topic": "requirements analysis",
            })
    
    return questions
