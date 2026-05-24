"""
Authentication and authorization services.
Handles password hashing, user login, registration, and permission checks.
"""

import sqlite3
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    import hashlib

from models.database import get_conn

def hash_password(password: str) -> str:
    """Hash a password using bcrypt (or SHA-256 fallback)."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback: SHA-256 with salt
        import hashlib
        salt = "campus_essay_salt"
        return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
    else:
        import hashlib
        salt = "campus_essay_salt"
        return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest() == hashed

def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user and return user info.
    Uses parameterized queries to prevent SQL injection.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        row = cur.fetchone()
        if row and verify_password(password, row[1]):
            return {
                "username": row[0],
                "password_hash": row[1],
                "role": row[2],
                "real_name": row[3],
                "grade": row[4],
                "class_name": row[5],
                "parent_of": row[6],
                "created_at": row[7],
            }
        return None
    finally:
        conn.close()

def register_user(
    username: str,
    password: str,
    role: str,
    real_name: str,
    grade: Optional[str],
    class_name: Optional[str],
    parent_of: Optional[str] = None
) -> bool:
    """
    Register a new user.
    Blocks admin self-registration for security.
    """
    # Security: Prevent self-registration as admin
    if role == "admin":
        return False

    # Validate role
    valid_roles = ["student", "teacher", "parent"]
    if role not in valid_roles:
        return False

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO users
               (username, password_hash, role, real_name, grade, class_name, parent_of, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                hash_password(password),
                role,
                real_name,
                grade,
                class_name,
                parent_of,
                datetime.now().isoformat(),
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def bind_parent_student(parent_username: str, student_username: str) -> bool:
    """
    Bind a parent to a student.
    Verifies both users exist and have correct roles, then creates binding.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role FROM users WHERE username = ?", (parent_username,))
        parent_row = cur.fetchone()
        if not parent_row or parent_row[0] != "parent":
            return False

        cur.execute("SELECT role FROM users WHERE username = ?", (student_username,))
        student_row = cur.fetchone()
        if not student_row or student_row[0] != "student":
            return False
    finally:
        conn.close()

    from models.database import bind_parent_student as db_bind
    return db_bind(parent_username, student_username)

def unbind_parent_student(parent_username: str, student_username: str) -> bool:
    """Remove a specific parent-student binding."""
    from models.database import unbind_parent_student as db_unbind
    return db_unbind(parent_username, student_username)

def get_parent_children(parent_username: str) -> list:
    """Get all students bound to a parent via parent_student_bindings table."""
    from models.database import get_parent_children as db_get
    return db_get(parent_username)

def has_permission(user: Dict[str, Any], required_role: str) -> bool:
    """Check if user has the required role."""
    return user.get("role") == required_role

def is_admin(user: Dict[str, Any]) -> bool:
    """Check if user is an admin."""
    return has_permission(user, "admin")

def is_teacher(user: Dict[str, Any]) -> bool:
    """Check if user is a teacher."""
    return has_permission(user, "teacher")

def is_parent(user: Dict[str, Any]) -> bool:
    """Check if user is a parent."""
    return has_permission(user, "parent")

def is_student(user: Dict[str, Any]) -> bool:
    """Check if user is a student."""
    return has_permission(user, "student")
