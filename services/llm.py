"""
LLM integration service.
Handles OpenAI API calls and fallback logic.
"""

import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client if API key is configured."""
    if not OPENAI_API_KEY:
        return None
    try:
        return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    except Exception:
        return None

def llm_json_feedback(
    grade: str,
    genre: str,
    topic: str,
    essay: str,
    image_prompt: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get structured feedback from LLM.
    Falls back to local engine if LLM is unavailable.
    """
    client = get_openai_client()
    if not client:
        return fallback_feedback(grade, genre, topic, essay)

    system_prompt = f"""你是一个小学作文辅导专家。请根据以下信息提供详细反馈：
年级：{grade}
类型：{genre}
题目：{topic}

请以JSON格式返回，包含以下字段：
- teacher_feedback: 教师专业版点评（严肃、专业）
- student_feedback: 学生鼓励版点评（亲切、鼓励）
- strengths: 优点列表（3-5条）
- suggestions: 改进建议列表（3-5条）
- polished_sentence: 润色后的佳句示例
- outline_advice: 结构建议
- step_rewrite: 四步改写指导（补内容、改句子、参考开头、参考结尾）
"""

    user_content = f"作文内容：\n{essay}"
    if image_prompt:
        user_content += f"\n\n图片提示：{json.dumps(image_prompt, ensure_ascii=False)}"

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return fallback_feedback(grade, genre, topic, essay)

def vision_observation_prompts(grade: str, image_base64: str) -> Dict[str, Any]:
    """
    Get observation prompts from vision model.
    Falls back to local engine if unavailable.
    """
    client = get_openai_client()
    if not client:
        return fallback_image_prompts(grade)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"你是一位小学{grade}的作文老师。请仔细观察这张图片，为学生提供写作指导。"
                                    "请返回JSON格式，包含：scene（场景概括）、observation_tips（观察提示3-5条）、"
                                    "inspiring_questions（启发问题3-5条）、suggested_title（建议题目）。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return fallback_image_prompts(grade)

def fallback_feedback(grade: str, genre: str, topic: str, essay: str) -> Dict[str, Any]:
    """Local fallback feedback engine when LLM is unavailable."""
    from services.scoring import (
        chinese_word_count, paragraph_count, sentence_count,
        infer_structure_score, infer_expression_score
    )

    wc = chinese_word_count(essay)
    pc = paragraph_count(essay)
    sc = sentence_count(essay)
    struct_score = infer_structure_score(essay)
    expr_score = infer_expression_score(essay)
    total = min(100, (struct_score + expr_score) // 2)

    return {
        "teacher_feedback": f"这是一篇{wc}字的{genre}作文。结构得分{struct_score}，表达得分{expr_score}，总分{total}。",
        "student_feedback": f"你写了{wc}字，很棒！继续努力，你的作文会越来越好。",
        "strengths": ["字数达标", "有分段意识"],
        "suggestions": ["可以增加更多细节描写", "注意开头和结尾的呼应"],
        "polished_sentence": "今天的校园格外热闹，同学们的欢声笑语充满了整个操场。",
        "outline_advice": "建议采用'总-分-总'结构，开头点题，中间展开，结尾升华。",
        "step_rewrite": {
            "step1_content": "思考：这件事发生在哪里？有哪些人物？",
            "step2_sentence": "把'我很高兴'改成具体的动作和表情描写。",
            "step3_start": "开头参考：那是一个阳光明媚的早晨……",
            "step4_end": "结尾参考：这次经历让我明白了……"
        }
    }

def fallback_image_prompts(grade: str) -> Dict[str, Any]:
    """Local fallback for image prompts."""
    return {
        "scene": "这张图片里可能有人物、环境和正在发生的事情，适合做看图作文。",
        "observation_tips": [
            "观察图片中的人物在做什么？",
            "注意图片的背景环境是怎样的？",
            "看看人物的表情和动作有什么特点？"
        ],
        "inspiring_questions": [
            "图中发生了什么故事？",
            "如果你是图中的人物，你会有什么感受？",
            "这个故事告诉我们什么道理？"
        ],
        "suggested_title": "看图作文"
    }
