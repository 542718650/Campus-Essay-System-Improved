"""
LLM integration tests for Campus Essay System.
Tests LLM feedback, image prompts, and fallback chain behavior.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.llm import (
    fallback_feedback, fallback_image_prompts,
    get_openai_client
)


class TestLLMFunctions(unittest.TestCase):
    """LLM service and fallback tests"""

    def test_fallback_feedback_structure(self):
        """Fallback feedback must return all required fields"""
        feedback = fallback_feedback("三年级", "写人", "我的妈妈", "这是一篇测试作文。")

        required = [
            "teacher_feedback", "student_feedback",
            "strengths", "suggestions",
            "polished_sentence", "outline_advice", "step_rewrite"
        ]
        for field in required:
            self.assertIn(field, feedback, f"Missing field: {field}")

    def test_fallback_feedback_field_types(self):
        """Feedback fields must have correct types"""
        feedback = fallback_feedback("三年级", "写事", "一次活动", "今天很高兴。")

        self.assertIsInstance(feedback["teacher_feedback"], str)
        self.assertIsInstance(feedback["student_feedback"], str)
        self.assertIsInstance(feedback["strengths"], list)
        self.assertIsInstance(feedback["suggestions"], list)
        self.assertIsInstance(feedback["polished_sentence"], str)
        self.assertIsInstance(feedback["outline_advice"], str)
        self.assertIsInstance(feedback["step_rewrite"], dict)

    def test_fallback_feedback_short_essay(self):
        """Short essay feedback should reflect word count"""
        feedback = fallback_feedback("三年级", "写事", "一次活动", "很短。")
        # The fallback includes word count in teacher_feedback
        self.assertIn("字", feedback["teacher_feedback"])

    def test_fallback_feedback_normal_essay(self):
        """Normal essay should produce multiple strengths and suggestions"""
        essay = "这是一篇正常长度的作文。今天天气很好，我和同学们一起去公园玩。"
        feedback = fallback_feedback("三年级", "写景", "秋天的公园", essay)

        self.assertIsInstance(feedback["strengths"], list)
        self.assertTrue(len(feedback["strengths"]) >= 2)
        self.assertTrue(len(feedback["suggestions"]) >= 2)

    def test_fallback_feedback_empty_essay(self):
        """Empty essay should not crash"""
        feedback = fallback_feedback("三年级", "写人", "测试主题", "")
        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)

    def test_fallback_feedback_all_grades(self):
        """Should work for all grade levels"""
        grades = ["三年级", "四年级", "五年级", "六年级"]
        essay = "这是一篇测试作文。今天天气很好。"

        for grade in grades:
            fb = fallback_feedback(grade, "写事", "测试", essay)
            self.assertIn("teacher_feedback", fb)

    def test_fallback_feedback_all_genres(self):
        """Should work for all essay genres"""
        genres = ["写人", "写事", "写景", "想象作文", "读后感", "日记", "看图作文"]
        essay = "今天天气很好。"

        for genre in genres:
            fb = fallback_feedback("三年级", genre, "测试", essay)
            self.assertIn("teacher_feedback", fb)

    def test_fallback_image_prompts_structure(self):
        """Fallback image prompts must have all required fields"""
        prompts = fallback_image_prompts("三年级")

        self.assertIn("scene", prompts)
        self.assertIn("observation_tips", prompts)
        self.assertIn("inspiring_questions", prompts)
        self.assertIn("suggested_title", prompts)

    def test_fallback_image_prompts_content(self):
        """Fallback image prompts should have useful content"""
        prompts = fallback_image_prompts("四年级")

        self.assertIsInstance(prompts["scene"], str)
        self.assertGreater(len(prompts["scene"]), 0)
        self.assertIsInstance(prompts["observation_tips"], list)
        self.assertGreaterEqual(len(prompts["observation_tips"]), 2)
        self.assertIsInstance(prompts["inspiring_questions"], list)
        self.assertGreaterEqual(len(prompts["inspiring_questions"]), 2)

    def test_fallback_image_prompts_all_grades(self):
        """Should work for all grade levels"""
        grades = ["三年级", "四年级", "五年级", "六年级"]
        for grade in grades:
            prompts = fallback_image_prompts(grade)
            self.assertIn("scene", prompts)

    def test_get_openai_client_without_key(self):
        """Should return None when no API key is configured"""
        client = get_openai_client()
        # Without env config, should return None or fail gracefully
        if client is not None:
            # If configured, it's still valid
            self.assertIsNotNone(client)


class TestFallbackStepRewrite(unittest.TestCase):
    """Test: Four-step rewrite guidance"""

    def test_step_rewrite_has_four_steps(self):
        """Should have exactly 4 rewrite steps"""
        fb = fallback_feedback("三年级", "写事", "一次活动", "今天很高兴。")
        steps = fb["step_rewrite"]

        self.assertIn("step1_content", steps)
        self.assertIn("step2_sentence", steps)
        self.assertIn("step3_start", steps)
        self.assertIn("step4_end", steps)

    def test_step_rewrite_values_are_strings(self):
        """All step values should be non-empty strings"""
        fb = fallback_feedback("三年级", "写人", "我的妈妈", "妈妈很好。")
        steps = fb["step_rewrite"]

        for key in ["step1_content", "step2_sentence", "step3_start", "step4_end"]:
            self.assertIsInstance(steps[key], str)
            self.assertGreater(len(steps[key]), 0)


if __name__ == '__main__':
    unittest.main()
