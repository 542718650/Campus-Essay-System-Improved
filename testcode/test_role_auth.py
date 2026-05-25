"""
Role authorization tests for Campus Essay System.
Tests user login, registration, and role-based access for all user types.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import models.database as db
from services.auth import (
    hash_password, login_user, register_user,
    has_permission, is_admin, is_teacher, is_student, is_parent,
    bind_parent_student, unbind_parent_student, get_parent_children
)


class TestRoleAuth(unittest.TestCase):
    """Role-based authentication tests"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "role_auth.db")
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_teacher_login(self):
        """Teacher user should login successfully"""
        user = login_user("teacher1", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "teacher1")
        self.assertEqual(user["role"], "teacher")

    def test_student_login(self):
        """Student user should login successfully"""
        user = login_user("student1", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "student1")
        self.assertEqual(user["role"], "student")
        self.assertEqual(user["grade"], "三年级")

    def test_parent_login(self):
        """Parent user should login successfully"""
        user = login_user("parent1", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "parent1")
        self.assertEqual(user["role"], "parent")

    def test_admin_login(self):
        """Admin user should login successfully"""
        user = login_user("admin", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")
        self.assertEqual(user["role"], "admin")

    def test_invalid_username_rejected(self):
        """Non-existent username should return None"""
        user = login_user("nonexistent", "123456")
        self.assertIsNone(user)

    def test_wrong_password_rejected(self):
        """Wrong password should return None"""
        user = login_user("student1", "wrong_password")
        self.assertIsNone(user)


class TestRoleRegistration(unittest.TestCase):
    """Role-based registration tests"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "role_reg.db")

        # Create bare table (no seed data)
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
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

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_register_student(self):
        """Student registration should succeed"""
        ok = register_user("new_student", "123456", "student", "新生", "四年级", "四年级二班")
        self.assertTrue(ok)

        user = login_user("new_student", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")
        self.assertEqual(user["grade"], "四年级")

    def test_register_teacher(self):
        """Teacher registration should succeed"""
        ok = register_user("new_teacher", "123456", "teacher", "新老师", None, None)
        self.assertTrue(ok)

        user = login_user("new_teacher", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "teacher")

    def test_register_parent(self):
        """Parent registration should succeed"""
        ok = register_user("new_parent", "123456", "parent", "新家长", None, None)
        self.assertTrue(ok)

        user = login_user("new_parent", "123456")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "parent")

    def test_register_admin_blocked(self):
        """Admin self-registration should be blocked"""
        ok = register_user("new_admin", "123456", "admin", "新管理员", None, None)
        self.assertFalse(ok)

    def test_register_invalid_role_blocked(self):
        """Invalid role should be rejected"""
        ok = register_user("hacker", "pass", "root", "黑客", None, None)
        self.assertFalse(ok)

    def test_register_duplicate_username_blocked(self):
        """Duplicate username registration should fail"""
        ok1 = register_user("existing_user", "123456", "student", "已存在", "三年级", "三年级一班")
        ok2 = register_user("existing_user", "123456", "student", "重复", "三年级", "三年级一班")
        self.assertTrue(ok1)
        self.assertFalse(ok2)


class TestParentStudentBinding(unittest.TestCase):
    """Parent-student binding tests"""

    def setUp(self):
        self.old_db = db.DB_PATH
        self.tmpdir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmpdir.name, "binding.db")
        db.init_db()

    def tearDown(self):
        self.tmpdir.cleanup()
        db.DB_PATH = self.old_db

    def test_bind_and_query(self):
        """Bind parent to student -> query children"""
        register_user("bind_parent", "pass", "parent", "家长", None, None)
        register_user("bind_student", "pass", "student", "学生", "三年级", "三年级一班")

        ok = bind_parent_student("bind_parent", "bind_student")
        self.assertTrue(ok)

        children = get_parent_children("bind_parent")
        self.assertGreater(len(children), 0)

    def test_unbind(self):
        """Bind -> unbind -> children list should be empty"""
        register_user("unbind_parent", "pass", "parent", "家长", None, None)
        register_user("unbind_student", "pass", "student", "学生", "三年级", None)

        bind_parent_student("unbind_parent", "unbind_student")
        ok = unbind_parent_student("unbind_parent", "unbind_student")
        self.assertTrue(ok)

        children = get_parent_children("unbind_parent")
        self.assertEqual(len(children), 0)

    def test_bind_non_parent_fails(self):
        """Non-parent user binding should fail"""
        register_user("not_parent", "pass", "teacher", "老师", None, None)
        register_user("some_student", "pass", "student", "学生", "三年级", None)

        # The service-level bind_parent_student checks roles first
        from services.auth import bind_parent_student as svc_bind
        ok = svc_bind("not_parent", "some_student")
        self.assertFalse(ok)


class TestPermissionChecks(unittest.TestCase):
    """Permission check function tests"""

    def test_has_permission_exact_match(self):
        user = {"role": "teacher"}
        self.assertTrue(has_permission(user, "teacher"))
        self.assertFalse(has_permission(user, "student"))

    def test_is_admin(self):
        self.assertTrue(is_admin({"role": "admin"}))
        self.assertFalse(is_admin({"role": "teacher"}))

    def test_is_teacher(self):
        self.assertTrue(is_teacher({"role": "teacher"}))
        self.assertFalse(is_teacher({"role": "student"}))

    def test_is_student(self):
        self.assertTrue(is_student({"role": "student"}))
        self.assertFalse(is_student({"role": "parent"}))

    def test_is_parent(self):
        self.assertTrue(is_parent({"role": "parent"}))
        self.assertFalse(is_parent({"role": "admin"}))


if __name__ == '__main__':
    unittest.main()
