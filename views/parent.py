"""
Parent view module.
Handles parent-facing UI with proper child binding and filtering.
"""

import streamlit as st
from typing import Dict, Any

from models.database import query_df
from services.auth import (
    bind_parent_student, unbind_parent_student,
    get_parent_children
)

def render_parent_view(user: Dict[str, Any]) -> None:
    """
    Render parent view with proper child filtering.
    Supports multiple children binding.
    """
    st.header("家长视图")

    # Check for bound children
    bound_children = get_parent_children(user["username"])

    if bound_children:
        # Parent has bound children - show only their data
        st.subheader("我的孩子")
        child_options = [f"{child[1]} ({child[2]})" for child in bound_children]
        selected_child = st.selectbox("选择孩子", child_options)

        # Get child username from selection
        selected_idx = child_options.index(selected_child)
        child_username = bound_children[selected_idx][0]

        st.markdown(f"**学生**：{bound_children[selected_idx][1]} / {bound_children[selected_idx][2]} / {bound_children[selected_idx][3]}")

        # Show recent submissions
        latest = query_df(
            "SELECT * FROM submissions WHERE student_username = ? ORDER BY created_at DESC LIMIT 1",
            (child_username,)
        )

        if not latest.empty:
            row = latest.iloc[0]
            st.subheader("最近一次作文")
            st.write(row["essay_text"])
            st.markdown("**教师点评**")
            st.write(row.get("teacher_feedback", "暂无点评"))

            # Growth trend
            growth = query_df(
                "SELECT created_at, word_count, total_score FROM growth_records "
                "WHERE student_username = ? ORDER BY created_at",
                (child_username,)
            )
            if not growth.empty:
                st.subheader("成长趋势")
                st.line_chart(growth.set_index("created_at")[["word_count", "total_score"]])
        else:
            st.info("该孩子还没有作文记录。")

        # Unbind specific child
        with st.expander("管理绑定"):
            st.write("**已绑定的孩子**：")
            for child in bound_children:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"- {child[1]} ({child[2]})")
                with col2:
                    if st.button("解除", key=f"unbind_{child[0]}"):
                        if unbind_parent_student(user["username"], child[0]):
                            st.success(f"已解除与 {child[1]} 的绑定")
                            st.rerun()
    else:
        # Parent has no bound children - show binding interface
        st.subheader("绑定孩子")
        st.info("请先绑定您的孩子，以便查看其作文和成长记录。")

        # Binding method 1: Enter child's username
        with st.expander("通过账号绑定", expanded=True):
            child_username = st.text_input("孩子的用户名", placeholder="请输入孩子的账号")
            if st.button("绑定此账号"):
                if child_username:
                    # Verify child exists
                    child_info = query_df(
                        "SELECT username, real_name, role FROM users WHERE username = ?",
                        (child_username,)
                    )
                    if not child_info.empty:
                        if child_info.iloc[0]["role"] == "student":
                            if bind_parent_student(user["username"], child_username):
                                st.success(f"已绑定 {child_info.iloc[0]['real_name']}")
                                st.rerun()
                            else:
                                st.error("绑定失败，请重试")
                        else:
                            st.error("该账号不是学生账号")
                    else:
                        st.error("找不到该用户，请检查用户名")

        # Binding method 2: Select from class (if teacher provided class info)
        with st.expander("从班级列表选择"):
            all_students = query_df(
                "SELECT username, real_name, grade, class_name FROM users WHERE role='student'"
            )
            if not all_students.empty:
                student_options = [
                    f"{row['real_name']} ({row['grade']} {row['class_name']})"
                    for _, row in all_students.iterrows()
                ]
                selected = st.selectbox("选择学生", student_options)
                if st.button("绑定选中学生"):
                    idx = student_options.index(selected)
                    child_username = all_students.iloc[idx]["username"]
                    if bind_parent_student(user["username"], child_username):
                        st.success(f"已绑定 {all_students.iloc[idx]['real_name']}")
                        st.rerun()
                    else:
                        st.error("绑定失败")
            else:
                st.info("暂无学生数据")

        st.caption("提示：如果找不到孩子，请联系老师确认孩子的账号信息。")
