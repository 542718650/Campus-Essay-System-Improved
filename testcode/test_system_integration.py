"""
System integration tests for Campus Essay System.
Tests module interactions: scoring + auth + database + LLM services.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import models.database as db
from services.scoring import (
    chinese_word_count, paragraph_count, sentence_count,
    infer_structure_score, infer_expression_score, calculate_total_score,
    generate_feedback_summary
)
from services.auth import hash_password, login_user, register_user
from services.llm import fallback_feedback, fallback_image_prompts


class TestFullEssayReviewFlow(unittest.TestCase):
    """Integration: complete essay review pipeline"""

    def test_scoring_pipeline_produces_feedback(self):
        """Scoring -> feedback chain should produce valid output"""
        essay = "我的妈妈很爱我。每天早上，她都会给我做早餐。有一次我生病了，妈妈一直照顾我。我觉得妈妈是世界上最好的人。"

        wc = chinese_word_count(essay)
        struct = infer_structure_score(essay, "三年级")
        expr = infer_expression_score(essay, "三年级")
        total = calculate_total_score(struct, expr)

        self.assertGreater(wc, 0)
        self.assertGreaterEqual(struct, 60)
        self.assertGreaterEqual(expr, 60)
        self.assertGreaterEqual(total, 60)

    def test_fallback_feedback_with_scoring(self):
        """Feedback should incorporate scoring metrics"""
        essay = "这是一篇测试作文。今天天气很好，我和同学们一起去公园玩。"
        feedback = fallback_feedback("三年级", "写事", "一次活动", essay)

        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)
        self.assertIn("strengths", feedback)
        self.assertIn("suggestions", feedback)
        self.assertIsInstance(feedback["step_rewrite"], dict)

    def test_short_essay_triggers_word_suggestion(self):
        """Short essay feedback should include word count info"""
        feedback = fallback_feedback("三年级", "写事", "一次活动", "很短。")
        self.assertIn("字", feedback["teacher_feedback"])


class TestDatabaseAuthIntegration(unittest.TestCase):
    """Integration: database + authentication"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "test.db")
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_register_and_login_roundtrip(self):
        """Register user -> login -> verify credentials"""
        ok = register_user(
            "test_student", "secure_pass_123", "student",
            "测试学生", "三年级", "三年级一班"
        )
        self.assertTrue(ok)

        user = login_user("test_student", "secure_pass_123")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "test_student")
        self.assertEqual(user["role"], "student")

    def test_wrong_password_rejected(self):
        """Wrong password should fail authentication"""
        register_user("test_user", "correct", "student", "用户", "三年级", None)
        user = login_user("test_user", "wrong")
        self.assertIsNone(user)

    def test_duplicate_registration_rejected(self):
        """Duplicate username should fail"""
        ok1 = register_user("dup_user", "pass1", "student", "用户", "三年级", None)
        ok2 = register_user("dup_user", "pass2", "student", "用户2", "四年级", None)
        self.assertTrue(ok1)
        self.assertFalse(ok2)

    def test_admin_self_registration_blocked(self):
        """Admin role should not be self-creatable"""
        ok = register_user("hacker", "pass", "admin", "黑客", None, None)
        self.assertFalse(ok)
        user = login_user("hacker", "pass")
        self.assertIsNone(user)


class TestDatabaseOperationsIntegration(unittest.TestCase):
    """Integration: database CRUD operations"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "test.db")
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_save_and_query_submission(self):
        """Save submission -> query back -> verify data"""
        submission_data = {
            "student_username": "student1",
            "essay_text": "这是一篇作文。今天天气很好。",
            "grade": "三年级",
            "genre": "写事",
            "topic": "天气",
            "word_count": 8,
            "structure_score": 70,
            "expression_score": 65,
            "total_score": 67,
            "teacher_feedback": "不错",
            "student_feedback": "加油",
            "strengths": ["有分段意识"],
            "suggestions": ["增加细节"],
            "polished_sentence": "润色示例",
            "outline_advice": "建议总-分-总结构",
            "step_rewrite": {"step1_content": "补细节"},
        }

        sid = db.save_submission(submission_data)
        self.assertGreater(sid, 0)

        df = db.query_df("SELECT * FROM submissions WHERE id = ?", (sid,))
        self.assertFalse(df.empty)
        self.assertEqual(df.iloc[0]["student_username"], "student1")

    def test_essay_versioning(self):
        """Save submission -> add version -> verify version history"""
        submission_data = {
            "student_username": "student1",
            "essay_text": "第一版作文。",
            "grade": "三年级", "genre": "写事", "topic": "测试",
            "word_count": 4, "structure_score": 60, "expression_score": 60,
            "total_score": 60, "teacher_feedback": "", "student_feedback": "",
            "strengths": [], "suggestions": [],
            "polished_sentence": "", "outline_advice": "", "step_rewrite": {},
        }
        sid = db.save_submission(submission_data)

        # Add versions
        db.save_essay_version(sid, 1, "第一版作文。", 4)
        db.save_essay_version(sid, 2, "修改后的第二版，增加了更多细节。", 10)

        versions = db.query_df(
            "SELECT * FROM essay_versions WHERE submission_id = ? ORDER BY version_no",
            (sid,)
        )
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions.iloc[1]["word_count"], 10)

    def test_growth_record_tracking(self):
        """Save growth record -> query trends"""
        data = {
            "student_username": "student1",
            "genre": "写景",
            "word_count": 100,
            "structure_score": 75,
            "expression_score": 70,
            "total_score": 72,
        }
        db.save_growth_record(data)

        records = db.query_df(
            "SELECT * FROM growth_records WHERE student_username = ?",
            ("student1",)
        )
        self.assertFalse(records.empty)
        self.assertEqual(records.iloc[0]["total_score"], 72)

    def test_parent_student_binding(self):
        """Bind parent to student -> query children"""
        # Register parent and student
        register_user("parent_test", "pass", "parent", "家长", None, None)
        register_user("student_test", "pass", "student", "学生", "三年级", "三年级一班")

        ok = db.bind_parent_student("parent_test", "student_test")
        self.assertTrue(ok)

        children = db.get_parent_children("parent_test")
        self.assertGreater(len(children), 0)

        # Unbind
        ok2 = db.unbind_parent_student("parent_test", "student_test")
        self.assertTrue(ok2)

        children2 = db.get_parent_children("parent_test")
        self.assertEqual(len(children2), 0)


class TestLLMServiceIntegration(unittest.TestCase):
    """Integration: LLM service with fallback chain"""

    def test_fallback_feedback_has_all_fields(self):
        """Fallback feedback should have same structure as LLM feedback"""
        fb = fallback_feedback("五年级", "写景", "秋天的公园", "公园很美。")
        required = [
            "teacher_feedback", "student_feedback", "strengths",
            "suggestions", "polished_sentence", "outline_advice", "step_rewrite"
        ]
        for field in required:
            self.assertIn(field, fb)

    def test_fallback_image_prompts_structure(self):
        """Fallback image prompts should have required fields"""
        prompts = fallback_image_prompts("四年级")
        self.assertIn("scene", prompts)
        self.assertIn("observation_tips", prompts)
        self.assertIn("inspiring_questions", prompts)
        self.assertIn("suggested_title", prompts)

    def test_empty_essay_does_not_crash(self):
        """Empty essay should not crash the feedback system"""
        fb = fallback_feedback("三年级", "写人", "测试", "")
        self.assertIsInstance(fb, dict)
        self.assertIn("teacher_feedback", fb)


class TestModuleInteractionConsistency(unittest.TestCase):
    """Integration: cross-module consistency"""

    def test_word_paragraph_sentence_consistency(self):
        """Text metrics should be internally consistent"""
        essay = "这是第一段。\n这是第二段。\n这是第三段。"
        wc = chinese_word_count(essay)
        pc = paragraph_count(essay)
        sc = sentence_count(essay)

        self.assertGreater(wc, 0)
        self.assertEqual(pc, 3)
        self.assertGreaterEqual(sc, 3)

    def test_feedback_summary_matches_scores(self):
        """Feedback summary should reflect the input scores"""
        summary = generate_feedback_summary(
            "三年级", "写事", 200, 90, 85, 87
        )
        self.assertIn("score_breakdown", summary)
        breakdown = summary["score_breakdown"]
        self.assertEqual(breakdown["structure"], 90)
        self.assertEqual(breakdown["expression"], 85)
        self.assertEqual(breakdown["total"], 87)


if __name__ == '__main__':
    unittest.main()
