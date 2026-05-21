import unittest
import sys
import os
import sqlite3
import hashlib

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from campus_essay_system import (
    login_user,
    register_user,
    DB_PATH,
    hash_password
)


class TestRoleAuth(unittest.TestCase):
    """测试角色和认证功能（v3新增）"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 保存原始数据库文件（如果存在）
        if os.path.exists(DB_PATH):
            os.rename(DB_PATH, f"{DB_PATH}.backup")
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试数据库文件
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        # 恢复原始数据库文件
        backup_path = f"{DB_PATH}.backup"
        if os.path.exists(backup_path):
            os.rename(backup_path, DB_PATH)
    
    def test_login_user_valid_teacher(self):
        """测试教师用户登录功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据（密码：123456）
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('test_teacher', hash_password('123456'), 'teacher', '测试老师', None, None, '2024-01-01T00:00:00'))
        
        conn.commit()
        conn.close()
        
        # 测试登录
        user = login_user('test_teacher', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'test_teacher')
        self.assertEqual(user['role'], 'teacher')
        self.assertEqual(user['real_name'], '测试老师')
    
    def test_login_user_valid_student(self):
        """测试学生用户登录功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据（密码：123456）
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('test_student', hash_password('123456'), 'student', '测试学生', '三年级', '三年级一班', '2024-01-01T00:00:00'))
        
        conn.commit()
        conn.close()
        
        # 测试登录
        user = login_user('test_student', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'test_student')
        self.assertEqual(user['role'], 'student')
        self.assertEqual(user['real_name'], '测试学生')
        self.assertEqual(user['grade'], '三年级')
        self.assertEqual(user['class_name'], '三年级一班')
    
    def test_login_user_valid_parent(self):
        """测试家长用户登录功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据（密码：123456）
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('test_parent', hash_password('123456'), 'parent', '测试家长', None, None, '2024-01-01T00:00:00'))
        
        conn.commit()
        conn.close()
        
        # 测试登录
        user = login_user('test_parent', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'test_parent')
        self.assertEqual(user['role'], 'parent')
        self.assertEqual(user['real_name'], '测试家长')
    
    def test_login_user_valid_admin(self):
        """测试管理员用户登录功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据（密码：123456）
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('test_admin', hash_password('123456'), 'admin', '测试管理员', None, None, '2024-01-01T00:00:00'))
        
        conn.commit()
        conn.close()
        
        # 测试登录
        user = login_user('test_admin', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'test_admin')
        self.assertEqual(user['role'], 'admin')
        self.assertEqual(user['real_name'], '测试管理员')
    
    def test_login_user_invalid_username(self):
        """测试无效用户名登录"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 测试无效用户名
        user = login_user('nonexistent', '123456')
        self.assertIsNone(user)
    
    def test_login_user_invalid_password(self):
        """测试无效密码登录"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据（密码：123456）
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('test_user', hash_password('123456'), 'student', '测试用户', '三年级', '三年级一班', '2024-01-01T00:00:00'))
        
        conn.commit()
        conn.close()
        
        # 测试无效密码
        user = login_user('test_user', 'wrong_password')
        self.assertIsNone(user)
    
    def test_register_user_student(self):
        """测试注册学生用户功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 测试注册学生用户
        result = register_user('new_student', '123456', 'student', '新生', '四年级', '四年级二班')
        self.assertTrue(result)
        
        # 验证用户已注册
        user = login_user('new_student', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'new_student')
        self.assertEqual(user['role'], 'student')
        self.assertEqual(user['real_name'], '新生')
        self.assertEqual(user['grade'], '四年级')
        self.assertEqual(user['class_name'], '四年级二班')
    
    def test_register_user_teacher(self):
        """测试注册教师用户功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 测试注册教师用户
        result = register_user('new_teacher', '123456', 'teacher', '新老师', None, None)
        self.assertTrue(result)
        
        # 验证用户已注册
        user = login_user('new_teacher', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'new_teacher')
        self.assertEqual(user['role'], 'teacher')
        self.assertEqual(user['real_name'], '新老师')
    
    def test_register_user_parent(self):
        """测试注册家长用户功能"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 测试注册家长用户
        result = register_user('new_parent', '123456', 'parent', '新家长', None, None)
        self.assertTrue(result)
        
        # 验证用户已注册
        user = login_user('new_parent', '123456')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'new_parent')
        self.assertEqual(user['role'], 'parent')
        self.assertEqual(user['real_name'], '新家长')
    
    def test_register_user_duplicate_username(self):
        """测试注册重复用户名"""
        # 创建测试数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                real_name TEXT NOT NULL,
                grade TEXT,
                class_name TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 插入测试数据
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('existing_user', hash_password('123456'), 'student', '已存在用户', '三年级', '三年级一班', '2024-01-01T00:00:00'))
        
        conn.commit()
        conn.close()
        
        # 测试注册重复用户名
        result = register_user('existing_user', '123456', 'student', '重复用户', '三年级', '三年级一班')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
