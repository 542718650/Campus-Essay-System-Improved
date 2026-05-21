"""
Scoring service for essay evaluation.
Implements rule-based scoring with grade-specific rubrics.
"""

import re
from typing import Dict, Any

# Grade-specific rubrics
GRADE_RUBRICS = {
    "三年级": {"min_words": 150, "target_words": 200, "min_paragraphs": 2},
    "四年级": {"min_words": 250, "target_words": 350, "min_paragraphs": 3},
    "五年级": {"min_words": 350, "target_words": 450, "min_paragraphs": 3},
    "六年级": {"min_words": 450, "target_words": 600, "min_paragraphs": 4},
}

# Transition words for structure scoring
TRANSITION_WORDS = ["首先", "然后", "接着", "最后", "后来", "终于", "于是", "因此", "所以", "然而", "但是", "虽然", "尽管", "因为", "所以"]

# Expression quality indicators
EXPRESSION_INDICATORS = [
    "像", "仿佛", "犹如", "好似", "宛如",  # Similes
    "高兴地", "伤心地", "兴奋地", "激动地", "难过地",  # Adverbs
    "红彤彤", "绿油油", "金灿灿", "白茫茫",  # Reduplicated adjectives
    "有的……有的……", "一会儿……一会儿……",  # Parallel structures
]

def chinese_word_count(text: str) -> int:
    """Count Chinese characters in text."""
    return len(re.findall(r'[一-鿿]', text))

def paragraph_count(text: str) -> int:
    """Count paragraphs in text."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    return len(paragraphs)

def sentence_count(text: str) -> int:
    """Count sentences in text."""
    return len(re.findall(r'[。！？]', text))

def infer_structure_score(text: str, grade: str = "三年级") -> int:
    """
    Infer structure score based on grade-specific rubrics.
    Improved from simple keyword matching to weighted criteria.
    """
    rubric = GRADE_RUBRICS.get(grade, GRADE_RUBRICS["三年级"])
    wc = chinese_word_count(text)
    pc = paragraph_count(text)
    sc = sentence_count(text)

    # Base score
    score = 60

    # Word count scoring (weighted)
    if wc >= rubric["target_words"]:
        score += 15
    elif wc >= rubric["min_words"]:
        score += 10
    elif wc >= rubric["min_words"] * 0.7:
        score += 5

    # Paragraph scoring
    if pc >= rubric["min_paragraphs"] + 1:
        score += 10
    elif pc >= rubric["min_paragraphs"]:
        score += 8
    elif pc >= 2:
        score += 5

    # Structure markers (transition words)
    transitions_found = [w for w in TRANSITION_WORDS if w in text]
    if len(transitions_found) >= 4:
        score += 10
    elif len(transitions_found) >= 2:
        score += 7
    elif len(transitions_found) >= 1:
        score += 4

    # Sentence variety
    if sc >= 10:
        score += 5

    return min(score, 100)

def infer_expression_score(text: str, grade: str = "三年级") -> int:
    """
    Infer expression score based on language quality indicators.
    """
    wc = chinese_word_count(text)
    score = 60

    # Length bonus (normalized by grade expectations)
    rubric = GRADE_RUBRICS.get(grade, GRADE_RUBRICS["三年级"])
    if wc >= rubric["target_words"]:
        score += 10

    # Expression indicators
    expressions_found = [e for e in EXPRESSION_INDICATORS if e in text]
    if len(expressions_found) >= 3:
        score += 15
    elif len(expressions_found) >= 2:
        score += 10
    elif len(expressions_found) >= 1:
        score += 5

    # Punctuation variety
    punctuations = set(re.findall(r'[，。！？；：""''（）《》]', text))
    if len(punctuations) >= 5:
        score += 10
    elif len(punctuations) >= 3:
        score += 5

    # Paragraph coherence (check for consistent paragraph lengths)
    paragraphs = [len(p) for p in text.split('\n') if p.strip()]
    if paragraphs:
        avg_len = sum(paragraphs) / len(paragraphs)
        variance = sum((l - avg_len) ** 2 for l in paragraphs) / len(paragraphs)
        if variance < 1000:  # Consistent paragraph lengths
            score += 5

    return min(score, 100)

def calculate_total_score(structure: int, expression: int) -> int:
    """Calculate total score as weighted average."""
    return min(100, int(structure * 0.5 + expression * 0.5))

def generate_feedback_summary(
    grade: str,
    genre: str,
    word_count: int,
    structure_score: int,
    expression_score: int,
    total_score: int
) -> Dict[str, Any]:
    """Generate a summary feedback based on scores."""
    rubric = GRADE_RUBRICS.get(grade, GRADE_RUBRICS["三年级"])

    strengths = []
    suggestions = []

    # Word count analysis
    if word_count >= rubric["target_words"]:
        strengths.append(f"字数达标（{word_count}字），超过{grade}要求")
    elif word_count >= rubric["min_words"]:
        strengths.append(f"字数基本达标（{word_count}字）")
        suggestions.append(f"建议写到{rubric['target_words']}字以上会更充实")
    else:
        suggestions.append(f"字数不足（{word_count}字），{grade}建议至少{rubric['min_words']}字")

    # Structure analysis
    if structure_score >= 85:
        strengths.append("文章结构清晰，层次分明")
    elif structure_score >= 70:
        strengths.append("文章结构基本完整")
        suggestions.append("可以尝试使用更多过渡词连接段落")
    else:
        suggestions.append("建议加强文章结构，注意分段和过渡")

    # Expression analysis
    if expression_score >= 85:
        strengths.append("语言表达生动，用词丰富")
    elif expression_score >= 70:
        strengths.append("语言表达基本通顺")
        suggestions.append("可以尝试使用比喻、拟人等修辞手法")
    else:
        suggestions.append("建议丰富语言表达，多使用形容词和副词")

    return {
        "strengths": strengths,
        "suggestions": suggestions,
        "grade_expectation": f"{grade}目标字数：{rubric['min_words']}-{rubric['target_words']}字",
        "score_breakdown": {
            "structure": structure_score,
            "expression": expression_score,
            "total": total_score
        }
    }
