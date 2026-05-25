"""
Unit tests for Campus Essay System.
Tests individual functions in services/scoring.py, services/auth.py, config.py.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.scoring import (
    chinese_word_count, paragraph_count, sentence_count,
    infer_structure_score, infer_expression_score, calculate_total_score,
    generate_feedback_summary, GRADE_RUBRICS, TRANSITION_WORDS, EXPRESSION_INDICATORS
)
from services.auth import (
    hash_password, verify_password,
    has_permission, is_admin, is_teacher, is_student, is_parent
)
from config import get_config_value, DEFAULT_CONFIG


class TestChineseWordCount(unittest.TestCase):
    """Test: Chinese character counting"""

    def test_empty_string(self):
        self.assertEqual(chinese_word_count(""), 0)

    def test_only_chinese(self):
        self.assertEqual(chinese_word_count("你好世界"), 4)

    def test_mixed_text(self):
        self.assertEqual(chinese_word_count("Hello你好World世界"), 4)

    def test_with_punctuation(self):
        self.assertEqual(chinese_word_count("今天天气真好！"), 6)

    def test_numbers_and_letters(self):
        self.assertEqual(chinese_word_count("123中文abc"), 2)

    def test_none_safe(self):
        """Should not crash on None-like edge cases"""
        self.assertEqual(chinese_word_count(" "), 0)

    def test_fullwidth_chars_excluded(self):
        """Full-width ASCII should not be counted as Chinese"""
        self.assertEqual(chinese_word_count("ａｂｃ１２３"), 0)

    def test_chinese_punctuation_excluded(self):
        self.assertEqual(chinese_word_count("，。！？：；""''"), 0)

    def test_complex_mixed(self):
        text = "这是一篇作文！包含标点符号，数字123，字母abc。"
        self.assertEqual(chinese_word_count(text), 16)


class TestParagraphCount(unittest.TestCase):
    """Test: Paragraph counting"""

    def test_empty(self):
        self.assertEqual(paragraph_count(""), 0)

    def test_single(self):
        self.assertEqual(paragraph_count("这是一段文字。"), 1)

    def test_two_paragraphs(self):
        self.assertEqual(paragraph_count("第一段\n第二段"), 2)

    def test_with_blank_lines(self):
        self.assertEqual(paragraph_count("第一段\n\n第二段"), 2)

    def test_three_paragraphs(self):
        self.assertEqual(paragraph_count("第一段\n\n\n第二段\n第三段"), 3)


class TestSentenceCount(unittest.TestCase):
    """Test: Sentence counting (based on Chinese punctuation)"""

    def test_empty(self):
        self.assertEqual(sentence_count(""), 0)

    def test_single_sentence(self):
        self.assertEqual(sentence_count("这是一个句子。"), 1)

    def test_two_sentences(self):
        self.assertEqual(sentence_count("这是第一个句子。这是第二个句子！"), 2)

    def test_mixed_punctuation(self):
        self.assertEqual(sentence_count("你好吗？我很好！真的。"), 3)


class TestStructureScore(unittest.TestCase):
    """Test: Structure scoring with grade-specific rubrics"""

    def test_default_range(self):
        """Score should be between 60 and 100"""
        score = infer_structure_score("你好", "三年级")
        self.assertGreaterEqual(score, 60)
        self.assertLessEqual(score, 100)

    def test_short_text_low_score(self):
        score = infer_structure_score("很短的文章。", "三年级")
        self.assertLess(score, 80)

    def test_long_text_high_score(self):
        """Long text with transition words should score high"""
        text = ("首先，今天的校园很热闹。\n"
                "然后，我和同学一起完成了接力比赛。\n"
                "接着，我们拍了很多照片。\n"
                "最后，我明白了团结合作很重要。") * 3
        score = infer_structure_score(text, "三年级")
        self.assertGreaterEqual(score, 80)

    def test_grade_specific_rubrics(self):
        """Higher grades have higher word expectations"""
        text = "这是一篇作文" * 10
        score_3 = infer_structure_score(text, "三年级")
        score_6 = infer_structure_score(text, "六年级")
        # Both should work without error; 6th grade expects more words
        self.assertGreaterEqual(score_3, 60)
        self.assertGreaterEqual(score_6, 60)

    def test_no_transition_words(self):
        text = "今天天气很好。我们去公园玩。公园里有很多花。"
        score = infer_structure_score(text, "三年级")
        self.assertGreaterEqual(score, 60)


class TestExpressionScore(unittest.TestCase):
    """Test: Expression scoring"""

    def test_default_range(self):
        score = infer_expression_score("他很高兴。", "三年级")
        self.assertGreaterEqual(score, 60)
        self.assertLessEqual(score, 100)

    def test_rich_expression(self):
        text = "他兴高采烈地跑过来，脸上洋溢着灿烂的笑容，眼睛里闪烁着兴奋的光芒。"
        score = infer_expression_score(text, "三年级")
        self.assertGreaterEqual(score, 65)

    def test_simple_text(self):
        text = "他笑了。"
        score = infer_expression_score(text, "三年级")
        self.assertLessEqual(score, 75)


class TestCalculateTotalScore(unittest.TestCase):
    """Test: Total score calculation"""

    def test_equal_weights(self):
        total = calculate_total_score(80, 80)
        self.assertEqual(total, 80)

    def test_different_scores(self):
        total = calculate_total_score(70, 90)
        self.assertEqual(total, 80)

    def test_capped_at_100(self):
        total = calculate_total_score(100, 100)
        self.assertEqual(total, 100)

    def test_low_scores(self):
        total = calculate_total_score(60, 60)
        self.assertEqual(total, 60)


class TestGenerateFeedbackSummary(unittest.TestCase):
    """Test: Feedback summary generation"""

    def test_returns_correct_structure(self):
        result = generate_feedback_summary("三年级", "写事", 200, 85, 80, 82)
        self.assertIn("strengths", result)
        self.assertIn("suggestions", result)
        self.assertIn("grade_expectation", result)
        self.assertIn("score_breakdown", result)

    def test_strengths_for_high_scores(self):
        result = generate_feedback_summary("三年级", "写景", 300, 90, 90, 90)
        self.assertTrue(len(result["strengths"]) > 0)

    def test_suggestions_for_low_scores(self):
        result = generate_feedback_summary("三年级", "写人", 50, 60, 60, 60)
        self.assertTrue(len(result["suggestions"]) > 0)


class TestPasswordHashing(unittest.TestCase):
    """Test: Password security"""

    def test_hash_not_plaintext(self):
        hashed = hash_password("123456")
        self.assertNotEqual(hashed, "123456")

    def test_verify_correct(self):
        hashed = hash_password("123456")
        self.assertTrue(verify_password("123456", hashed))

    def test_verify_wrong(self):
        hashed = hash_password("123456")
        self.assertFalse(verify_password("wrong", hashed))

    def test_different_hashes_same_password(self):
        """bcrypt produces different hashes each time"""
        h1 = hash_password("123456")
        h2 = hash_password("123456")
        self.assertNotEqual(h1, h2)

    def test_empty_password(self):
        hashed = hash_password("")
        self.assertNotEqual(hashed, "")


class TestRolePermission(unittest.TestCase):
    """Test: Role permission checks"""

    def setUp(self):
        self.admin = {"role": "admin"}
        self.teacher = {"role": "teacher"}
        self.student = {"role": "student"}
        self.parent = {"role": "parent"}

    def test_is_admin(self):
        self.assertTrue(is_admin(self.admin))
        self.assertFalse(is_admin(self.teacher))

    def test_is_teacher(self):
        self.assertTrue(is_teacher(self.teacher))
        self.assertFalse(is_teacher(self.student))

    def test_is_student(self):
        self.assertTrue(is_student(self.student))
        self.assertFalse(is_student(self.parent))

    def test_is_parent(self):
        self.assertTrue(is_parent(self.parent))
        self.assertFalse(is_parent(self.admin))

    def test_has_permission(self):
        self.assertTrue(has_permission(self.teacher, "teacher"))
        self.assertFalse(has_permission(self.student, "teacher"))


class TestConfig(unittest.TestCase):
    """Test: Configuration management"""

    def test_default_config_has_keys(self):
        self.assertIn("DB_PATH", DEFAULT_CONFIG)
        self.assertIn("OPENAI_BASE_URL", DEFAULT_CONFIG)
        self.assertIn("OPENAI_MODEL", DEFAULT_CONFIG)

    def test_default_values(self):
        self.assertEqual(DEFAULT_CONFIG["DB_PATH"], "essay_campus_system.db")

    def test_get_config_value_returns_default(self):
        val = get_config_value("OPENAI_BASE_URL", DEFAULT_CONFIG["OPENAI_BASE_URL"])
        self.assertIsNotNone(val)

    def test_get_config_value_env_override(self):
        old = os.environ.get("TEST_CONFIG_KEY")
        os.environ["TEST_CONFIG_KEY"] = "env_value"
        try:
            self.assertEqual(get_config_value("TEST_CONFIG_KEY"), "env_value")
        finally:
            if old is None:
                os.environ.pop("TEST_CONFIG_KEY", None)
            else:
                os.environ["TEST_CONFIG_KEY"] = old


class TestConstants(unittest.TestCase):
    """Test: Rubric and constant validity"""

    def test_grade_rubrics_content(self):
        self.assertIn("三年级", GRADE_RUBRICS)
        self.assertIn("六年级", GRADE_RUBRICS)
        for grade in ["三年级", "四年级", "五年级", "六年级"]:
            self.assertIn("min_words", GRADE_RUBRICS[grade])
            self.assertIn("target_words", GRADE_RUBRICS[grade])

    def test_transition_words_not_empty(self):
        self.assertGreater(len(TRANSITION_WORDS), 5)
        self.assertIn("首先", TRANSITION_WORDS)
        self.assertIn("然后", TRANSITION_WORDS)

    def test_expression_indicators_not_empty(self):
        self.assertGreater(len(EXPRESSION_INDICATORS), 3)


if __name__ == '__main__':
    unittest.main()
