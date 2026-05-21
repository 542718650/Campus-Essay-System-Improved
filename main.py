"""
Main entry point for Campus Essay System.
Streamlit application with modular architecture.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

from config import DEFAULT_CONFIG
from models.database import init_db, query_df
from services.auth import (
    login_user, register_user, hash_password,
    is_admin, is_teacher, is_parent, is_student
)
from views.student import render_student_view
from views.teacher import render_teacher_view
from views.parent import render_parent_view
from views.admin import render_admin_view

def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title=DEFAULT_CONFIG["APP_TITLE"],
        page_icon="📝",
        layout="wide"
    )

    init_db()
    st.title(DEFAULT_CONFIG["APP_TITLE"])
    st.caption("支持多角色登录、班级管理、作文布置、看图作文、大语言模型图像识别、分年级 rubric、历史版本对比与成长档案。")

    # Sidebar authentication
    sidebar_auth()

    user = st.session_state.get("user")

    st.sidebar.markdown("---")
    st.sidebar.info(
        "默认账号：\n\n"
        "- teacher1 / 123456\n"
        "- student1 / 123456\n"
        "- student2 / 123456\n"
        "- parent1 / 123456\n"
        "- admin / 123456\n\n"
        "云端数据库：配置 SUPABASE_URL / SUPABASE_KEY 后可继续扩展。"
    )

    if not user:
        st.markdown("### 欢迎使用")
        st.write("请先在左侧登录或注册。")
        st.markdown("#### 功能亮点")
        st.markdown("- 学生端：写作、点评、改写、成长档案")
        st.markdown("- 老师端：布置题目、批量查看、班级管理")
        st.markdown("- 家长端：查看孩子作文与成长趋势")
        st.markdown("- 管理员：用户管理、批量导入导出")
        st.markdown("- 看图作文：使用大语言模型生成观察提示和启发问题")
        return

    # Role-based routing
    role = user["role"]
    if role == "teacher":
        render_teacher_view(user)
    elif role == "student":
        render_student_view(user)
    elif role == "parent":
        render_parent_view(user)
    elif role == "admin":
        render_admin_view(user)
    else:
        st.error(f"未知角色：{role}")

def sidebar_auth() -> None:
    """Render authentication UI in sidebar."""
    st.sidebar.title("账号系统")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        user = st.session_state.user
        st.sidebar.success(f"已登录：{user['real_name']} ({user['role']})")
        if st.sidebar.button("退出登录"):
            st.session_state.user = None
            st.rerun()
        return

    tab1, tab2 = st.sidebar.tabs(["登录", "注册"])

    with tab1:
        username = st.text_input("用户名", key="login_user")
        password = st.text_input("密码", type="password", key="login_pwd")
        if st.button("登录", key="login_btn"):
            user = login_user(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("用户名或密码错误。")

    with tab2:
        reg_user = st.text_input("新用户名", key="reg_user")
        reg_name = st.text_input("姓名", key="reg_name")
        reg_role = st.selectbox("角色", ["student", "teacher", "parent"], key="reg_role")
        reg_grade = st.selectbox("年级", ["三年级", "四年级", "五年级", "六年级"], key="reg_grade") if reg_role == "student" else None
        reg_class = st.text_input("班级（学生可填）", key="reg_class")
        reg_pwd = st.text_input("设置密码", type="password", key="reg_pwd")

        # Parent binding option
        if reg_role == "parent":
            reg_parent_of = st.text_input("绑定孩子用户名（可选）", key="reg_parent_of")
        else:
            reg_parent_of = None

        if st.button("注册", key="reg_btn"):
            if reg_user and reg_name and reg_pwd:
                ok = register_user(
                    reg_user, reg_pwd, reg_role, reg_name,
                    reg_grade, reg_class or None, reg_parent_of
                )
                if ok:
                    st.success("注册成功，请登录。")
                else:
                    st.error("用户名已存在或角色无效。")
            else:
                st.error("请填写完整信息。")

if __name__ == "__main__":
    main()
