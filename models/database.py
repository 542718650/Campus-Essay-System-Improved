"""
Database module for Campus Essay System.
Handles SQLite connections, schema initialization, and common queries.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from config import get_db_path

DB_PATH = get_db_path()

def get_conn() -> sqlite3.Connection:
    """
    Get a database connection with WAL mode enabled for better concurrency.
    Uses check_same_thread=False for Streamlit compatibility.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Enable WAL mode for better concurrent read/write performance
    conn.execute("PRAGMA journal_mode=WAL;")
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def run_migration(conn: sqlite3.Connection) -> None:
    """
    Run database migrations to add new tables/columns.
    Handles SQLite's limited ALTER TABLE support.
    """
    cur = conn.cursor()
    # Check if parent_of column exists in users table
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if "parent_of" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN parent_of TEXT;")

    # Check if parent_student_bindings table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parent_student_bindings'")
    if not cur.fetchone():
        cur.execute("""
            CREATE TABLE parent_student_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_username TEXT NOT NULL,
                student_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(parent_username, student_username),
                FOREIGN KEY (parent_username) REFERENCES users(username),
                FOREIGN KEY (student_username) REFERENCES users(username)
            )
        """)
    conn.commit()

def init_db() -> None:
    """
    Initialize database schema and seed data if not exists.
    Includes migration for schema updates.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        # Users table with new parent_of column
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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                grade TEXT NOT NULL,
                teacher_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_username) REFERENCES users(username)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                genre TEXT NOT NULL,
                prompt TEXT,
                grade TEXT NOT NULL,
                class_name TEXT NOT NULL,
                teacher_username TEXT NOT NULL,
                due_date TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (teacher_username) REFERENCES users(username)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_username TEXT NOT NULL,
                assignment_id INTEGER,
                essay_text TEXT NOT NULL,
                image_data TEXT,
                grade TEXT NOT NULL,
                genre TEXT NOT NULL,
                topic TEXT NOT NULL,
                word_count INTEGER,
                structure_score INTEGER,
                expression_score INTEGER,
                total_score INTEGER,
                teacher_feedback TEXT,
                student_feedback TEXT,
                strengths TEXT,
                suggestions TEXT,
                polished_sentence TEXT,
                outline_advice TEXT,
                step_rewrite TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (student_username) REFERENCES users(username),
                FOREIGN KEY (assignment_id) REFERENCES assignments(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS essay_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                version_no INTEGER NOT NULL,
                essay_text TEXT NOT NULL,
                word_count INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (submission_id) REFERENCES submissions(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS growth_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_username TEXT NOT NULL,
                genre TEXT NOT NULL,
                word_count INTEGER,
                structure_score INTEGER,
                expression_score INTEGER,
                total_score INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (student_username) REFERENCES users(username)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS parent_student_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_username TEXT NOT NULL,
                student_username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(parent_username, student_username),
                FOREIGN KEY (parent_username) REFERENCES users(username),
                FOREIGN KEY (student_username) REFERENCES users(username)
            )
        """)

        # Run migrations for existing databases
        run_migration(conn)

        # Seed data only if users table is empty
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            now = datetime.now().isoformat()
            from services.auth import hash_password

            seed_users = [
                ("teacher1", hash_password("123456"), "teacher", "教师示例", None, None, None, now),
                ("student1", hash_password("123456"), "student", "学生示例1", "三年级", "三年级一班", None, now),
                ("student2", hash_password("123456"), "student", "学生示例2", "三年级", "三年级一班", None, now),
                ("parent1", hash_password("123456"), "parent", "家长示例", None, None, "student1", now),
                ("admin", hash_password("123456"), "admin", "管理员", None, None, None, now),
            ]

            cur.executemany(
                """INSERT INTO users (username, password_hash, role, real_name, grade, class_name, parent_of, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                seed_users
            )

            seed_classes = [
                ("三年级一班", "三年级", "teacher1", now),
                ("四年级一班", "四年级", "teacher1", now),
            ]

            cur.executemany(
                """INSERT INTO classes (class_name, grade, teacher_username, created_at)
                   VALUES (?, ?, ?, ?)""",
                seed_classes
            )

            # Seed parent-student binding
            cur.execute(
                """INSERT INTO parent_student_bindings (parent_username, student_username, created_at)
                   VALUES (?, ?, ?)""",
                ("parent1", "student1", now)
            )

        conn.commit()
    finally:
        conn.close()

def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a query and return results as a DataFrame."""
    conn = get_conn()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()

def save_submission(data: Dict[str, Any]) -> int:
    """Save a new submission and return its ID."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO submissions
               (student_username, assignment_id, essay_text, image_data, grade, genre, topic,
                word_count, structure_score, expression_score, total_score,
                teacher_feedback, student_feedback, strengths, suggestions,
                polished_sentence, outline_advice, step_rewrite, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["student_username"],
                data.get("assignment_id"),
                data["essay_text"],
                data.get("image_data"),
                data["grade"],
                data["genre"],
                data["topic"],
                data.get("word_count"),
                data.get("structure_score"),
                data.get("expression_score"),
                data.get("total_score"),
                data.get("teacher_feedback"),
                data.get("student_feedback"),
                json.dumps(data["strengths"]) if isinstance(data.get("strengths"), (list, dict)) else data.get("strengths"),
                json.dumps(data["suggestions"]) if isinstance(data.get("suggestions"), (list, dict)) else data.get("suggestions"),
                data.get("polished_sentence"),
                data.get("outline_advice"),
                json.dumps(data["step_rewrite"]) if data.get("step_rewrite") else None,
                datetime.now().isoformat(),
            )
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def save_essay_version(submission_id: int, version_no: int, essay_text: str, word_count: int) -> None:
    """Save a new version of an essay."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO essay_versions (submission_id, version_no, essay_text, word_count, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (submission_id, version_no, essay_text, word_count, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()

def save_growth_record(data: Dict[str, Any]) -> None:
    """Save a growth record for a student."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO growth_records
               (student_username, genre, word_count, structure_score, expression_score, total_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data["student_username"],
                data["genre"],
                data.get("word_count"),
                data.get("structure_score"),
                data.get("expression_score"),
                data.get("total_score"),
                datetime.now().isoformat(),
            )
        )
        conn.commit()
    finally:
        conn.close()

def bind_parent_student(parent_username: str, student_username: str) -> bool:
    """Create a parent-student binding. Returns False if already bound."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO parent_student_bindings (parent_username, student_username, created_at) VALUES (?, ?, ?)",
            (parent_username, student_username, datetime.now().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def unbind_parent_student(parent_username: str, student_username: str) -> bool:
    """Remove a specific parent-student binding."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM parent_student_bindings WHERE parent_username = ? AND student_username = ?",
            (parent_username, student_username)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()

def get_parent_children(parent_username: str) -> list:
    """Get all students bound to a parent."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT u.username, u.real_name, u.grade, u.class_name
               FROM users u
               JOIN parent_student_bindings b ON u.username = b.student_username
               WHERE b.parent_username = ?""",
            (parent_username,)
        )
        return cur.fetchall()
    finally:
        conn.close()
