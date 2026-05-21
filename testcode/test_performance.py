import os
import sys
import tempfile
import time
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import campus_essay_system as app
from campus_essay_system import (
    chinese_word_count,
    paragraph_count,
    sentence_count,
    infer_structure_score,
    infer_expression_score,
    fallback_feedback,
    generate_topics,
)


class TestPerformance(unittest.TestCase):
    """性能测试：核心本地路径应保持轻量可用"""

    def test_text_metrics_bulk_processing_under_budget(self):
        """测试大文本指标计算在本地交互预算内完成"""
        essay = (
            "首先，今天的校园很热闹，大家都在操场上参加活动。\n"
            "然后，我和同学一起完成了接力比赛，心里非常激动。\n"
            "最后，我明白了团结合作很重要，也收获了温暖的友谊。\n"
        ) * 120

        start = time.perf_counter()
        for _ in range(100):
            chinese_word_count(essay)
            paragraph_count(essay)
            sentence_count(essay)
            infer_structure_score(essay)
            infer_expression_score(essay)
        elapsed = time.perf_counter() - start

        self.assertLess(elapsed, 2.0, f"文本指标批量处理耗时过长: {elapsed:.3f}s")

    def test_fallback_feedback_bulk_generation_under_budget(self):
        """测试无外部模型时的批量反馈生成速度"""
        essay = "今天我参加了班级活动。首先我很紧张，然后我努力完成任务，最后我很高兴。"

        start = time.perf_counter()
        for _ in range(300):
            feedback = fallback_feedback("三年级", "写事", "一次活动", essay)
        elapsed = time.perf_counter() - start

        self.assertIn("teacher_feedback", feedback)
        self.assertLess(elapsed, 1.0, f"批量回退反馈耗时过长: {elapsed:.3f}s")

    def test_topic_generation_bulk_under_budget(self):
        """测试批量生成题目建议速度"""
        start = time.perf_counter()
        for idx in range(1000):
            topics = generate_topics("五年级", "想象作文", f"未来{idx}")
        elapsed = time.perf_counter() - start

        self.assertGreaterEqual(len(topics), 3)
        self.assertLess(elapsed, 1.0, f"批量题目生成耗时过长: {elapsed:.3f}s")

    def test_submission_roundtrip_under_budget(self):
        """测试本地 SQLite 保存作文和成长记录的速度"""
        old_db_path = app.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            app.DB_PATH = os.path.join(tmpdir, "performance.db")
            app.init_db()
            feedback = fallback_feedback("三年级", "写事", "一次活动", "今天我很高兴。")

            try:
                start = time.perf_counter()
                for idx in range(12):
                    app.save_submission(
                        {
                            "assignment_id": None,
                            "student_username": f"student_perf_{idx}",
                            "title": f"一次活动{idx}",
                            "genre": "写事",
                            "prompt": "一次活动",
                            "essay_text": "今天我参加了班级活动，心里很高兴。",
                            "word_count": 17,
                            "structure_score": 70,
                            "expression_score": 70,
                            "total_score": 70,
                            "teacher_feedback": feedback["teacher_feedback"],
                            "student_feedback": feedback["student_feedback"],
                            "step_rewrite": feedback["step_rewrite"],
                            "feedback_json": feedback,
                        }
                    )
                elapsed = time.perf_counter() - start
                count = app.query_df("SELECT COUNT(*) AS c FROM submissions")["c"].iloc[0]
            finally:
                app.DB_PATH = old_db_path

        self.assertEqual(count, 12)
        self.assertLess(elapsed, 3.0, f"SQLite 作文保存耗时过长: {elapsed:.3f}s")


if __name__ == '__main__':
    unittest.main()
