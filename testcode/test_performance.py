"""
Performance tests for Campus Essay System.
Measures response time and throughput of core operations.
"""

import os
import sys
import time
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import models.database as db
from services.scoring import (
    chinese_word_count, paragraph_count, sentence_count,
    infer_structure_score, infer_expression_score
)
from services.llm import fallback_feedback
from services.auth import hash_password, register_user, login_user


class TestTextMetricsPerformance(unittest.TestCase):
    """Performance: text analysis should complete within budget"""

    def setUp(self):
        self.essay = (
            "首先，今天的校园很热闹，大家都在操场上参加活动。\n"
            "然后，我和同学一起完成了接力比赛，心里非常激动。\n"
            "最后，我明白了团结合作很重要，也收获了温暖的友谊。\n"
        ) * 120

    def test_bulk_text_metrics_under_budget(self):
        """100 iterations of text metrics on large text should complete < 2s"""
        start = time.perf_counter()
        for _ in range(100):
            chinese_word_count(self.essay)
            paragraph_count(self.essay)
            sentence_count(self.essay)
            infer_structure_score(self.essay, "三年级")
            infer_expression_score(self.essay, "三年级")
        elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 2.0,
                        f"Text metrics bulk processing took {elapsed:.3f}s, budget is 2s")

    def test_single_metric_under_10ms(self):
        """Single text metric should complete under 10ms"""
        start = time.perf_counter()
        for _ in range(1000):
            chinese_word_count(self.essay)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / 1000) * 1000
        self.assertLess(avg_ms, 10,
                        f"Average chinese_word_count took {avg_ms:.2f}ms, budget is 10ms")


class TestFeedbackPerformance(unittest.TestCase):
    """Performance: feedback generation should be responsive"""

    def test_fallback_feedback_bulk_under_budget(self):
        """300 fallback feedback generations should complete < 1s"""
        essay = "今天我参加了班级活动。首先我很紧张，然后我努力完成任务，最后我很高兴。"

        start = time.perf_counter()
        for _ in range(300):
            feedback = fallback_feedback("三年级", "写事", "一次活动", essay)
        elapsed = time.perf_counter() - start

        self.assertIn("teacher_feedback", feedback)
        self.assertLess(elapsed, 1.0,
                        f"Bulk fallback feedback took {elapsed:.3f}s, budget is 1s")

    def test_single_feedback_under_5ms(self):
        """Single fallback feedback should complete under 5ms"""
        essay = "今天我很高兴。"

        start = time.perf_counter()
        for _ in range(1000):
            fallback_feedback("三年级", "写事", "一次活动", essay)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / 1000) * 1000
        self.assertLess(avg_ms, 5,
                        f"Average fallback_feedback took {avg_ms:.2f}ms, budget is 5ms")


class TestDatabasePerformance(unittest.TestCase):
    """Performance: database operations under load"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "perf.db")
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_submission_roundtrip_under_budget(self):
        """12 submission save+query cycles should complete < 3s"""
        start = time.perf_counter()
        for idx in range(12):
            submission_data = {
                "student_username": "student1",
                "essay_text": "今天我参加了班级活动，心里很高兴。",
                "grade": "三年级", "genre": "写事", "topic": f"活动{idx}",
                "word_count": 17, "structure_score": 70,
                "expression_score": 70, "total_score": 70,
                "teacher_feedback": "不错", "student_feedback": "加油",
                "strengths": [], "suggestions": [],
                "polished_sentence": "", "outline_advice": "", "step_rewrite": {},
            }
            db.save_submission(submission_data)
        elapsed = time.perf_counter() - start

        df = db.query_df("SELECT COUNT(*) AS c FROM submissions")
        count = df["c"].iloc[0]
        self.assertEqual(count, 12)
        self.assertLess(elapsed, 3.0,
                        f"Submission roundtrip took {elapsed:.3f}s, budget is 3s")

    def test_bulk_query_under_budget(self):
        """Query 100 records should complete < 1s"""
        # Insert 100 records
        for idx in range(100):
            db.save_submission({
                "student_username": "student1",
                "essay_text": "作文内容" * 10,
                "grade": "三年级", "genre": "写事", "topic": f"测试{idx}",
                "word_count": 40, "structure_score": 75,
                "expression_score": 70, "total_score": 72,
                "teacher_feedback": "", "student_feedback": "",
                "strengths": [], "suggestions": [],
                "polished_sentence": "", "outline_advice": "", "step_rewrite": {},
            })

        start = time.perf_counter()
        df = db.query_df(
            "SELECT * FROM submissions ORDER BY created_at DESC LIMIT 50"
        )
        elapsed = time.perf_counter() - start

        self.assertEqual(len(df), 50)
        self.assertLess(elapsed, 1.0,
                        f"Bulk query took {elapsed:.3f}s, budget is 1s")


class TestAuthPerformance(unittest.TestCase):
    """Performance: authentication operations under load"""

    def test_bulk_registration_under_budget(self):
        """10 registrations should complete < 5s"""
        old_db = db.DB_PATH
        tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(tmpdir.name, "auth_perf.db")
        db.init_db()

        try:
            start = time.perf_counter()
            for idx in range(10):
                register_user(f"perf_user_{idx}", "password123",
                            "student", f"用户{idx}", "三年级", "三年级一班")
            elapsed = time.perf_counter() - start

            self.assertLess(elapsed, 5.0,
                            f"Bulk registration took {elapsed:.3f}s, budget is 5s")
        finally:
            tmpdir.cleanup()
            db.DB_PATH = old_db

    def test_login_latency(self):
        """Single login should complete under 300ms (bcrypt is intentionally slow)"""
        old_db = db.DB_PATH
        tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(tmpdir.name, "login_perf.db")
        db.init_db()
        register_user("perf_login_user", "password123", "student", "用户", "三年级", None)

        try:
            start = time.perf_counter()
            for _ in range(50):
                login_user("perf_login_user", "password123")
            elapsed = time.perf_counter() - start

            avg_ms = (elapsed / 50) * 1000
            self.assertLess(avg_ms, 300,
                            f"Average login took {avg_ms:.2f}ms, budget is 300ms")
        finally:
            tmpdir.cleanup()
            db.DB_PATH = old_db


if __name__ == '__main__':
    unittest.main()
