"""
Admin view module.
Enhanced with bulk import, batch edit, and export capabilities.
"""

import streamlit as st
import pandas as pd
import csv
import io
from typing import Dict, Any
from datetime import datetime

from models.database import query_df, get_conn
from services.auth import hash_password

def render_admin_view(user: Dict[str, Any]) -> None:
    """
    Render admin view with enhanced features.
    NEW: Bulk import, batch edit, export functionality.
    """
    st.header("管理员视图")

    t1, t2, t3, t4 = st.tabs(["用户总览", "批量导入", "批量管理", "数据导出"])

    with t1:
        _render_user_overview()
    with t2:
        _render_bulk_import()
    with t3:
        _render_batch_management()
    with t4:
        _render_data_export()

def _render_user_overview() -> None:
    """Render user overview table."""
    st.subheader("用户总览")
    users = query_df(
        "SELECT username, real_name, role, grade, class_name, created_at FROM users ORDER BY created_at DESC"
    )
    if not users.empty:
        st.dataframe(users, use_container_width=True)
    else:
        st.info("暂无用户数据")

    st.subheader("班级总览")
    classes = query_df("SELECT * FROM classes ORDER BY grade, class_name")
    if not classes.empty:
        st.dataframe(classes, use_container_width=True)
    else:
        st.info("暂无班级数据")

def _render_bulk_import() -> None:
    """
    NEW FEATURE: Bulk import users from CSV.
    """
    st.subheader("批量导入")

    st.info("支持 CSV 格式导入学生、教师数据。格式：用户名,真实姓名,角色,年级,班级")

    uploaded = st.file_uploader("上传 CSV 文件", type=["csv"])
    if uploaded:
        try:
            content = uploaded.read().decode("utf-8")
            df = pd.read_csv(io.StringIO(content))

            st.write("预览数据：")
            st.dataframe(df.head(), use_container_width=True)

            if st.button("确认导入"):
                success_count = 0
                fail_count = 0

                conn = get_conn()
                cur = conn.cursor()
                try:
                    for _, row in df.iterrows():
                        try:
                            username = str(row.iloc[0]).strip()
                            real_name = str(row.iloc[1]).strip()
                            role = str(row.iloc[2]).strip().lower()
                            grade = str(row.iloc[3]).strip() if len(row) > 3 and pd.notna(row.iloc[3]) else None
                            class_name = str(row.iloc[4]).strip() if len(row) > 4 and pd.notna(row.iloc[4]) else None

                            # Validate role
                            if role not in ["student", "teacher", "parent"]:
                                fail_count += 1
                                continue

                            # Check if user exists
                            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
                            if cur.fetchone()[0] == 0:
                                cur.execute(
                                    """INSERT INTO users
                                       (username, password_hash, role, real_name, grade, class_name, parent_of, created_at)
                                       VALUES (?, ?, ?, ?, ?, ?, NULL, ?)""",
                                    (username, hash_password("123456"), role, real_name, grade, class_name, datetime.now().isoformat())
                                )
                                success_count += 1
                        except Exception:
                            fail_count += 1

                    conn.commit()
                    st.success(f"导入完成：成功 {success_count} 条，失败 {fail_count} 条")
                    st.info("默认密码均为 123456，请通知用户首次登录后修改")
                finally:
                    conn.close()
        except Exception as e:
            st.error(f"导入失败：{str(e)}")

    # Download template
    template_csv = "用户名,真实姓名,角色,年级,班级\nstudent001,张三,student,三年级,三年级一班\nteacher001,李老师,teacher,,"
    st.download_button(
        label="下载导入模板",
        data=template_csv,
        file_name="import_template.csv",
        mime="text/csv"
    )

def _render_batch_management() -> None:
    """
    NEW FEATURE: Batch management of users.
    """
    st.subheader("批量管理")

    users = query_df("SELECT username, real_name, role, grade, class_name FROM users")
    if users.empty:
        st.info("暂无用户数据")
        return

    # Select users for batch operation
    selected_users = st.multiselect(
        "选择要操作的用户",
        options=[f"{row['username']} ({row['real_name']})" for _, row in users.iterrows()],
        key="batch_select"
    )

    if selected_users:
        operation = st.radio("选择操作", ["重置密码", "修改角色", "分配班级", "批量删除"])

        if operation == "重置密码":
            new_password = st.text_input("新密码", type="password")
            if st.button("执行重置"):
                if new_password:
                    conn = get_conn()
                    cur = conn.cursor()
                    try:
                        count = 0
                        for sel in selected_users:
                            username = sel.split(" (")[0]
                            cur.execute(
                                "UPDATE users SET password_hash = ? WHERE username = ?",
                                (hash_password(new_password), username)
                            )
                            count += 1
                        conn.commit()
                        st.success(f"已重置 {count} 个用户的密码")
                    finally:
                        conn.close()

        elif operation == "修改角色":
            new_role = st.selectbox("新角色", ["student", "teacher", "parent"])
            if st.button("执行修改"):
                conn = get_conn()
                cur = conn.cursor()
                try:
                    count = 0
                    for sel in selected_users:
                        username = sel.split(" (")[0]
                        cur.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
                        count += 1
                    conn.commit()
                    st.success(f"已修改 {count} 个用户的角色")
                    st.rerun()
                finally:
                    conn.close()

        elif operation == "分配班级":
            classes = query_df("SELECT class_name FROM classes")
            class_options = classes["class_name"].tolist() if not classes.empty else []
            new_class = st.selectbox("新班级", class_options)
            if st.button("执行分配"):
                if new_class:
                    conn = get_conn()
                    cur = conn.cursor()
                    try:
                        count = 0
                        for sel in selected_users:
                            username = sel.split(" (")[0]
                            cur.execute("UPDATE users SET class_name = ? WHERE username = ?", (new_class, username))
                            count += 1
                        conn.commit()
                        st.success(f"已分配 {count} 个用户到班级")
                        st.rerun()
                    finally:
                        conn.close()

        elif operation == "批量删除":
            st.warning("删除操作不可恢复，请谨慎操作！")
            if st.button("确认删除", type="primary"):
                conn = get_conn()
                cur = conn.cursor()
                try:
                    count = 0
                    for sel in selected_users:
                        username = sel.split(" (")[0]
                        # Don't allow deleting admin
                        cur.execute("SELECT role FROM users WHERE username = ?", (username,))
                        role_row = cur.fetchone()
                        if role_row and role_row[0] != "admin":
                            cur.execute("DELETE FROM users WHERE username = ?", (username,))
                            count += 1
                    conn.commit()
                    st.success(f"已删除 {count} 个用户")
                    st.rerun()
                finally:
                    conn.close()

def _render_data_export() -> None:
    """
    NEW FEATURE: Data export functionality.
    """
    st.subheader("数据导出")

    export_type = st.radio("选择导出类型", ["用户列表", "作文提交记录", "成长档案", "班级信息"])

    if export_type == "用户列表":
        df = query_df("SELECT username, real_name, role, grade, class_name, created_at FROM users")
    elif export_type == "作文提交记录":
        df = query_df("""
            SELECT s.student_username, u.real_name, s.topic, s.genre, s.grade,
                   s.word_count, s.total_score, s.created_at
            FROM submissions s
            JOIN users u ON s.student_username = u.username
            ORDER BY s.created_at DESC
        """)
    elif export_type == "成长档案":
        df = query_df("""
            SELECT g.student_username, u.real_name, g.genre, g.word_count,
                   g.structure_score, g.expression_score, g.total_score, g.created_at
            FROM growth_records g
            JOIN users u ON g.student_username = u.username
            ORDER BY g.created_at DESC
        """)
    else:
        df = query_df("SELECT * FROM classes ORDER BY grade, class_name")

    if not df.empty:
        # Display preview
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"共 {len(df)} 条记录，此处仅显示前 10 条")

        # Export button
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label=f"导出 {export_type} (CSV)",
            data=csv_data,
            file_name=f"{export_type}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("暂无数据可导出")
