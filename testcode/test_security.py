import os
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import campus_essay_system as app
from campus_essay_system import hash_password, verify_password


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestSecurity(unittest.TestCase):
    """安全测试：凭据、认证和数据库输入防护"""

    def test_source_does_not_contain_hardcoded_api_keys(self):
        """测试源码中不包含 OpenAI 风格的硬编码密钥"""
        secret_pattern = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
        offenders = []

        for source_file in PROJECT_ROOT.rglob("*.py"):
            if ".git" in source_file.parts or "__pycache__" in source_file.parts:
                continue
            content = source_file.read_text(encoding="utf-8")
            if secret_pattern.search(content):
                offenders.append(str(source_file.relative_to(PROJECT_ROOT)))

        self.assertEqual(offenders, [], f"发现疑似硬编码密钥: {offenders}")

    def test_local_secret_files_are_gitignored(self):
        """测试本地密钥文件不会被提交到仓库"""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(".env", gitignore)
        self.assertIn(".streamlit/secrets.toml", gitignore)

    def test_openai_config_prefers_environment_variables(self):
        """测试部署配置优先从环境变量读取"""
        old_value = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-api-key"
        try:
            self.assertEqual(app.get_config_value("OPENAI_API_KEY"), "test-api-key")
        finally:
            if old_value is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_value

    def test_llm_feedback_falls_back_without_api_key(self):
        """测试未配置 API 密钥时不会调用外部模型，而是使用本地回退反馈"""
        old_key = app.OPENAI_API_KEY
        app.OPENAI_API_KEY = ""
        try:
            feedback = app.llm_json_feedback("三年级", "写事", "一次活动", "今天我很高兴。")
        finally:
            app.OPENAI_API_KEY = old_key

        self.assertIn("teacher_feedback", feedback)
        self.assertIn("student_feedback", feedback)

    def test_password_hash_does_not_store_plaintext(self):
        """测试密码哈希不等于明文且可正常校验"""
        hashed = hash_password("123456")

        self.assertNotEqual(hashed, "123456")
        self.assertTrue(verify_password("123456", hashed))
        self.assertFalse(verify_password("wrong-password", hashed))

    def test_login_rejects_sql_injection_username(self):
        """测试登录查询使用参数化 SQL，拒绝用户名注入"""
        old_db_path = app.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            app.DB_PATH = os.path.join(tmpdir, "security.db")
            conn = sqlite3.connect(app.DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    real_name TEXT NOT NULL,
                    grade TEXT,
                    class_name TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("safe_user", hash_password("123456"), "student", "安全用户", "三年级", "三年级一班", "2026-05-13T00:00:00"),
            )
            conn.commit()
            conn.close()

            try:
                self.assertIsNone(app.login_user("' OR '1'='1", "123456"))
                self.assertIsNotNone(app.login_user("safe_user", "123456"))
            finally:
                app.DB_PATH = old_db_path

    def test_register_user_blocks_admin_self_registration(self):
        """测试普通注册入口不能创建管理员账号"""
        old_db_path = app.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            app.DB_PATH = os.path.join(tmpdir, "roles.db")
            app.init_db()
            try:
                self.assertFalse(app.register_user("new_admin", "123456", "admin", "新管理员", None, None))
                self.assertIsNone(app.login_user("new_admin", "123456"))
            finally:
                app.DB_PATH = old_db_path


if __name__ == '__main__':
    unittest.main()
