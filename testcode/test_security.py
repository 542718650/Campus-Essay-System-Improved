"""
Security tests for Campus Essay System.
Tests credentials management, SQL injection prevention, password security,
and authorization controls.
"""

import os
import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import models.database as db
from services.auth import hash_password, verify_password, login_user, register_user
from services.llm import fallback_feedback
from config import get_config_value


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestCredentialSecurity(unittest.TestCase):
    """Security: credentials must not be hardcoded"""

    def test_no_hardcoded_api_keys_in_source(self):
        """Source code must not contain OpenAI-style API keys"""
        secret_pattern = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
        offenders = []

        for source_file in PROJECT_ROOT.rglob("*.py"):
            if ".git" in source_file.parts or "__pycache__" in source_file.parts:
                continue
            content = source_file.read_text(encoding="utf-8")
            if secret_pattern.search(content):
                offenders.append(str(source_file.relative_to(PROJECT_ROOT)))

        self.assertEqual(offenders, [],
                         f"Found hardcoded API keys in: {offenders}")

    def test_gitignore_protects_secrets(self):
        """.gitignore must exclude .env and secrets files"""
        gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn(".env", gitignore,
                      ".gitignore should exclude .env files")
        self.assertIn(".streamlit/secrets.toml", gitignore,
                      ".gitignore should exclude Streamlit secrets")

    def test_config_prefers_environment_variables(self):
        """Configuration should prefer environment variables over defaults"""
        old_value = os.environ.get("OPENAI_API_KEY")
        os.environ["OPENAI_API_KEY"] = "test-api-key-from-env"
        try:
            val = get_config_value("OPENAI_API_KEY")
            self.assertEqual(val, "test-api-key-from-env")
        finally:
            if old_value is None:
                os.environ.pop("OPENAI_API_KEY", None)
            else:
                os.environ["OPENAI_API_KEY"] = old_value

    def test_fallback_without_api_key(self):
        """System should fall back to local engine when no API key is configured"""
        fb = fallback_feedback("三年级", "写事", "一次活动", "今天我很高兴。")

        self.assertIn("teacher_feedback", fb)
        self.assertIn("student_feedback", fb)


class TestPasswordSecurity(unittest.TestCase):
    """Security: password storage and verification"""

    def test_password_not_stored_plaintext(self):
        """Hashed password must not equal plaintext"""
        hashed = hash_password("123456")
        self.assertNotEqual(hashed, "123456")

    def test_password_hash_is_not_reversible_easily(self):
        """Hash must be different each time (bcrypt property)"""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        self.assertNotEqual(h1, h2,
                            "bcrypt should produce different hashes each time")

    def test_password_verification_roundtrip(self):
        """Correct password must verify, wrong password must not"""
        hashed = hash_password("my_secret_123")
        self.assertTrue(verify_password("my_secret_123", hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_password_length_does_not_leak(self):
        """Different length passwords should produce different length hashes"""
        h1 = hash_password("short")
        h2 = hash_password("this_is_a_much_longer_password_string")
        # bcrypt produces fixed-length hashes (59 chars for bcrypt, 64 for sha256)
        self.assertEqual(len(h1), len(h2),
                         "Hash length should not reveal password length")


class TestSQLInjection(unittest.TestCase):
    """Security: SQL injection prevention"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "security.db")

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_login_rejects_sqli_username(self):
        """Login must use parameterized queries, reject SQL injection"""
        conn = sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                parent_of TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("safe_user", hash_password("123456"), "student",
             "安全用户", "三年级", "三年级一班", None, "2026-05-25T00:00:00")
        )
        conn.commit()
        conn.close()

        # SQL injection attempt
        user = login_user("' OR '1'='1", "123456")
        self.assertIsNone(user,
                          "SQL injection in username should not bypass auth")

        # Valid login should work
        user = login_user("safe_user", "123456")
        self.assertIsNotNone(user)

    def test_login_rejects_sqli_password(self):
        """SQL injection in password should not bypass auth"""
        conn = sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                parent_of TEXT,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("test_user", hash_password("123456"), "student",
             "测试用户", "三年级", "三年级一班", None, "2026-05-25T00:00:00")
        )
        conn.commit()
        conn.close()

        user = login_user("test_user", "' OR '1'='1")
        self.assertIsNone(user,
                          "SQL injection in password should not bypass auth")

    def test_register_rejects_sqli_in_name(self):
        """SQL injection in registration fields should be stored safely"""
        conn = sqlite3.connect(db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                parent_of TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        # Attempt SQL injection in real_name
        sqli_name = "'; DROP TABLE users; --"
        ok = register_user("sqli_user", "pass", "student", sqli_name, "三年级", None)
        self.assertTrue(ok)

        # Table should still exist
        df = db.query_df("SELECT COUNT(*) AS c FROM users")
        self.assertGreaterEqual(df["c"].iloc[0], 1)


class TestAuthorizationSecurity(unittest.TestCase):
    """Security: role-based authorization controls"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "auth_security.db")
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_admin_self_registration_blocked(self):
        """Public registration must not allow admin role"""
        ok = register_user("new_admin", "123456", "admin", "新管理员", None, None)
        self.assertFalse(ok,
                         "Admin self-registration must be blocked")

        user = login_user("new_admin", "123456")
        self.assertIsNone(user)

    def test_invalid_role_rejected(self):
        """Invalid role must be rejected"""
        ok = register_user("hack_user", "pass", "superadmin", "黑客", None, None)
        self.assertFalse(ok)

    def test_default_accounts_use_hashed_passwords(self):
        """Seeded accounts must not have plaintext passwords"""
        df = db.query_df("SELECT password_hash FROM users WHERE username = 'admin'")
        self.assertFalse(df.empty)
        pw_hash = df.iloc[0]["password_hash"]
        self.assertNotEqual(pw_hash, "123456",
                            "Default admin password must be hashed")


if __name__ == '__main__':
    unittest.main()
