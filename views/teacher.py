"""
Teacher view module.
Handles teacher-facing UI: assignments, review, and class management.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime

from models.database import query_df, get_conn

def render_teacher_view(user: Dict[str, Any]) -> None:
    """Render teacher-facing UI."""
    st.header("老师端：布置作文题与批量查看")

    t1, t2, t3 = st.tabs(["布置作文题", "批量查看提交", "班级管理"])

    with t1:
        _render_assignment_tab(user)
    with t2:
        _render_review_tab(user)
    with t3:
        _render_class_management_tab(user)

def _render_assignment_tab(user: Dict[str, Any]) -> None:
    """Render assignment creation tab."""
    st.subheader("布置作文题")

    classes = query_df(
        "SELECT class_name, grade FROM classes WHERE teacher_username = ?",
        (user["username"],)
    )

    class_options = classes["class_name"].tolist() if not classes.empty else ["默认班级"]
    class_name = st.selectbox("选择班级", class_options)

    grade = "三年级"
    if not classes.empty and class_name in classes["class_name"].values:
        grade = classes[classes["class_name"] == class_name]["grade"].iloc[0]

    genre = st.selectbox("作文类型", [
        "写人", "写事", "写景", "想象作文", "读后感", "日记", "看图作文"
    ])

    title = st.text_input("作文题目")
    prompt = st.text_area("布置说明", placeholder="写作要求、观察提示、注意事项")
    due_date = st.date_input("截止日期", value=datetime.now())

    if st.button("发布作文题"):
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO assignments
                   (title, genre, prompt, grade, class_name, teacher_username, due_date, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title, genre, prompt, grade, class_name, user["username"], str(due_date), datetime.now().isoformat())
            )
            conn.commit()
            st.success("作文题发布成功！")
        finally:
            conn.close()

def _render_review_tab(user: Dict[str, Any]) -> None:
    """Render submission review tab."""
    st.subheader("批量查看提交")

    # Get all submissions
    submissions = query_df(
        """SELECT s.id, s.student_username, u.real_name, s.topic, s.genre, s.grade,
                  s.total_score, s.created_at, s.word_count
           FROM submissions s
           JOIN users u ON s.student_username = u.username
           ORDER BY s.created_at DESC"""
    )

    if submissions.empty:
        st.info("暂无学生提交")
        return

    st.dataframe(submissions, use_container_width=True)

    # Filter by student
    selected_student = st.selectbox("查看特定学生", ["全部"] + submissions["student_username"].unique().tolist())

    if selected_student != "全部":
        student_subs = submissions[submissions["student_username"] == selected_student]
        st.dataframe(student_subs, use_container_width=True)

def _render_class_management_tab(user: Dict[str, Any]) -> None:
    """Render class management tab."""
    st.subheader("班级管理")

    classes = query_df(
        "SELECT * FROM classes WHERE teacher_username = ? ORDER BY grade, class_name",
        (user["username"],)
    )

    if not classes.empty:
        st.dataframe(classes, use_container_width=True)

    # Add new class
    with st.expander("添加新班级"):
        new_class = st.text_input("班级名称", placeholder="如：三年级二班")
        new_grade = st.selectbox("年级", ["三年级", "四年级", "五年级", "六年级"])
        if st.button("创建班级"):
            if new_class:
                conn = get_conn()
                cur = conn.cursor()
                try:
                    cur.execute(
                        """INSERT INTO classes (class_name, grade, teacher_username, created_at)
                           VALUES (?, ?, ?, ?)""",
                        (new_class, new_grade, user["username"], datetime.now().isoformat())
                    )
                    conn.commit()
                    st.success("班级创建成功")
                    st.rerun()
                finally:
                    conn.close()
