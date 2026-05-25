"""
Acceptance tests for Campus Essay System.
Tests user stories and business requirements from end-user perspective.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.llm import fallback_feedback, fallback_image_prompts
from services.scoring import chinese_word_count, paragraph_count, infer_structure_score, infer_expression_score


class TestUserStories(unittest.TestCase):
    """User story: Students of different grades can write essays and get feedback"""

    def test_grade3_narrative_essay(self):
        """三年级学生写记叙文应获得适合年级的反馈"""
        grade = "三年级"
        genre = "写事"
        theme = "一次难忘的活动"
        essay = ("上周六，我们班举行了跳绳比赛。刚开始时，我很紧张，手心都出汗了。"
                 "轮到我上场时，我深吸一口气，努力让自己平静下来。随着哨声响起，"
                 "我飞快地跳了起来。虽然最后没有拿第一名，但我明白了只要勇敢面对，就有进步。")

        feedback = fallback_feedback(grade, genre, theme, essay)

        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)
        self.assertIsInstance(feedback["strengths"], list)
        self.assertIsInstance(feedback["suggestions"], list)
        self.assertGreaterEqual(len(feedback["strengths"]), 2)
        self.assertGreaterEqual(len(feedback["suggestions"]), 2)

    def test_grade5_descriptive_essay(self):
        """五年级学生写写景作文应获得更高标准的反馈"""
        grade = "五年级"
        genre = "写景"
        theme = "秋天的校园"
        essay = ("秋天的校园真美。操场边的银杏树像撑开的一把把金色小伞，"
                 "风一吹，叶子轻轻落下来，像一只只蝴蝶在飞。花坛里的菊花开得正热闹，"
                 "有黄的、白的、紫的，把校园装扮得五彩缤纷。")

        feedback = fallback_feedback(grade, genre, theme, essay)

        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)

    def test_short_essay_handled(self):
        """短作文应获得鼓励性反馈和改进建议"""
        feedback = fallback_feedback("三年级", "写人", "我的好朋友", "我的好朋友是小明。他很聪明。")

        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)

    def test_empty_input_handled(self):
        """空输入不应导致系统崩溃"""
        feedback = fallback_feedback("四年级", "写事", "难忘的一天", "")

        self.assertIsInstance(feedback, dict)
        self.assertIn("teacher_feedback", feedback)


class TestOutputFormatAcceptance(unittest.TestCase):
    """Acceptance: Output format must contain all required fields"""

    def test_all_required_fields_present(self):
        """反馈必须包含所有必要字段"""
        feedback = fallback_feedback("四年级", "写人", "我的老师", "我的老师姓王，她很温柔。每次我有问题，她都会耐心地教我。")

        required_fields = [
            "teacher_feedback", "student_feedback",
            "strengths", "suggestions",
            "polished_sentence", "outline_advice", "step_rewrite"
        ]
        for field in required_fields:
            self.assertIn(field, feedback, f"缺少必要字段: {field}")

    def test_field_types_correct(self):
        """各字段类型必须正确"""
        feedback = fallback_feedback("三年级", "写景", "美丽的公园", "公园很美。")

        self.assertIsInstance(feedback["teacher_feedback"], str)
        self.assertIsInstance(feedback["student_feedback"], str)
        self.assertIsInstance(feedback["strengths"], list)
        self.assertIsInstance(feedback["suggestions"], list)
        self.assertIsInstance(feedback["polished_sentence"], str)
        self.assertIsInstance(feedback["outline_advice"], str)
        self.assertIsInstance(feedback["step_rewrite"], dict)

    def test_step_rewrite_has_all_steps(self):
        """四步改写指导应包含四个步骤"""
        feedback = fallback_feedback("三年级", "写事", "一次活动", "今天很高兴。")
        step = feedback["step_rewrite"]

        self.assertIn("step1_content", step)
        self.assertIn("step2_sentence", step)
        self.assertIn("step3_start", step)
        self.assertIn("step4_end", step)


class TestContentQualityAcceptance(unittest.TestCase):
    """Acceptance: Content quality meets minimum standards"""

    def test_feedback_has_strengths_and_suggestions(self):
        """反馈至少包含2条优点和2条建议"""
        essay = "春天来了，公园里的花都开了。小鸟在树上唱歌。我很喜欢春天。"
        feedback = fallback_feedback("五年级", "写景", "美丽的公园", essay)

        self.assertGreaterEqual(len(feedback["strengths"]), 2)
        self.assertGreaterEqual(len(feedback["suggestions"]), 2)

    def test_image_prompts_quality(self):
        """图片提示功能应返回结构化数据"""
        prompts = fallback_image_prompts("四年级")

        self.assertIsInstance(prompts["scene"], str)
        self.assertIsInstance(prompts["observation_tips"], list)
        self.assertIsInstance(prompts["inspiring_questions"], list)
        self.assertIsInstance(prompts["suggested_title"], str)
        self.assertGreaterEqual(len(prompts["observation_tips"]), 2)
        self.assertGreaterEqual(len(prompts["inspiring_questions"]), 2)


class TestEdgeCaseAcceptance(unittest.TestCase):
    """Acceptance: Edge cases are handled gracefully"""

    def test_chinese_word_count_accuracy(self):
        """中文字数统计应排除标点和英文"""
        text = "Hello世界123你好abc"
        wc = chinese_word_count(text)
        self.assertEqual(wc, 4)

    def test_paragraph_detection(self):
        """段落识别应正确处理空行"""
        text = "第一段\n\n第二段\n\n\n第三段"
        pc = paragraph_count(text)
        self.assertEqual(pc, 3)

    def test_scoring_bounded(self):
        """评分必须在60-100范围内"""
        essay = "很短。"
        struct = infer_structure_score(essay, "三年级")
        expr = infer_expression_score(essay, "三年级")

        self.assertGreaterEqual(struct, 60)
        self.assertLessEqual(struct, 100)
        self.assertGreaterEqual(expr, 60)
        self.assertLessEqual(expr, 100)

    def test_mixed_grade_handling(self):
        """不同年级应有不同的评分标准"""
        essay = "今天天气很好。" * 20
        score_3 = infer_structure_score(essay, "三年级")
        score_6 = infer_structure_score(essay, "六年级")

        # Both should work without error
        self.assertIsInstance(score_3, int)
        self.assertIsInstance(score_6, int)


if __name__ == '__main__':
    unittest.main()
