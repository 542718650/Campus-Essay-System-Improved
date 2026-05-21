"""
Student view module.
Handles student-facing UI: writing, feedback, revision, and growth tracking.
Includes new "Start Rewrite" entry point.
"""

import streamlit as st
import pandas as pd
import io
from typing import Dict, Any, Optional
from datetime import datetime

from models.database import (
    query_df, save_submission, save_essay_version, save_growth_record
)
from services.llm import llm_json_feedback, vision_observation_prompts
from services.scoring import (
    chinese_word_count, paragraph_count, sentence_count,
    infer_structure_score, infer_expression_score, calculate_total_score,
    generate_feedback_summary
)

# Essay templates and topics
ESSAY_TEMPLATES = {
    "写人": {
        "structure": "开头介绍人物 → 中间描写外貌、性格、事例 → 结尾表达感情",
        "tips": "抓住人物特点，用具体事例表现人物品质",
        "openings": ["我有一个好朋友，他叫……", "我的妈妈有一双……"],
        "endings": ["这就是我的……，我爱他/她。", "他/她是我学习的榜样。"]
    },
    "写事": {
        "structure": "起因 → 经过 → 结果",
        "tips": "把事情的过程写清楚，写出自己的感受",
        "openings": ["今天发生了一件难忘的事……", "记得有一次……"],
        "endings": ["这件事让我明白了……", "现在想起来，我还……"]
    },
    "写景": {
        "structure": "总写 → 分写（按顺序） → 抒发感情",
        "tips": "按一定顺序观察，运用比喻、拟人等修辞",
        "openings": ["春天来了，校园里……", "秋天的校园真美啊！"],
        "endings": ["我爱这美丽的校园。", "这里的景色让人流连忘返。"]
    },
    "想象作文": {
        "structure": "设定情境 → 展开想象 → 回归现实",
        "tips": "想象要合理，情节要有趣",
        "openings": ["假如我有一双翅膀……", "二十年后的我……"],
        "endings": ["这真是一个奇妙的梦。", "我相信，只要努力……"]
    },
    "读后感": {
        "structure": "简介内容 → 谈感受 → 联系实际",
        "tips": "抓住最感动的地方，写出真实感受",
        "openings": ["最近我读了一本书，名叫……", "读完这篇文章，我深受感动。"],
        "endings": ["这本书让我明白了……", "我要像主人公那样……"]
    },
    "日记": {
        "structure": "日期天气 → 记录事件 → 表达心情",
        "tips": "记录真实生活，写出真情实感",
        "openings": ["今天天气晴朗，我……", "今天是星期X，我……"],
        "endings": ["今天真是有意义的一天。", "我希望明天……"]
    },
    "看图作文": {
        "structure": "描述画面 → 想象故事 → 表达感悟",
        "tips": "仔细观察图片，合理想象情节",
        "openings": ["图中画的是……", "这是一个……的故事。"],
        "endings": ["这个故事告诉我们……", "从中我明白了……"]
    }
}

TOPIC_SUGGESTIONS = {
    "写人": ["我的好朋友", "我的老师", "我的妈妈", "我敬佩的一个人", "班级里的'小明星'"],
    "写事": ["一件难忘的事", "第一次做饭", "一次帮助别人", "一次失败后的成长", "校园里的趣事"],
    "写景": ["美丽的校园", "秋天的田野", "春天的公园", "家乡的小河", "雪后的世界"],
    "想象作文": ["假如我有一双翅膀", "二十年后的我", "未来的学校", "我和机器人", "动物王国的故事"],
    "读后感": ["读《XXX》有感", "《XXX》读后感", "我最喜欢的故事", "一本书的启示"],
    "日记": ["今天我真高兴", "难忘的一天", "我的周末", "校园生活日记"],
    "看图作文": ["图中发生了什么", "看图想故事", "请给图片配一个故事"]
}

def render_student_view(user: Dict[str, Any]) -> None:
    """Render the student-facing UI with all features."""
    st.header("学生端：作文练习与成长记录")

    # Main navigation with improved rewrite entry
    menu = st.radio(
        "选择功能",
        ["开始写作文", "看图作文", "继续改写", "历史版本对比", "成长档案"],
        horizontal=True
    )

    if menu == "开始写作文":
        _render_writing_interface(user)
    elif menu == "看图作文":
        _render_image_writing(user)
    elif menu == "继续改写":
        _render_rewrite_interface(user)
    elif menu == "历史版本对比":
        _render_version_comparison(user)
    elif menu == "成长档案":
        _render_growth_records(user)

def _render_writing_interface(user: Dict[str, Any]) -> None:
    """Render the main writing interface."""
    st.subheader("开始写作文")

    col1, col2, col3 = st.columns(3)
    with col1:
        grade = st.selectbox("年级", ["三年级", "四年级", "五年级", "六年级"], index=0)
    with col2:
        genre = st.selectbox("作文类型", list(ESSAY_TEMPLATES.keys()))
    with col3:
        topic = st.text_input("作文题目", placeholder="输入或选择题目")

    # Topic suggestions
    if genre in TOPIC_SUGGESTIONS:
        st.caption("推荐题目：")
        cols = st.columns(3)
        for i, t in enumerate(TOPIC_SUGGESTIONS[genre][:6]):
            with cols[i % 3]:
                if st.button(t, key=f"topic_{i}"):
                    st.session_state.selected_topic = t
                    st.rerun()

    if topic or st.session_state.get("selected_topic"):
        actual_topic = topic or st.session_state.get("selected_topic", "")

        # Template guidance
        if actual_topic and genre in ESSAY_TEMPLATES:
            with st.expander("写作指导", expanded=False):
                template = ESSAY_TEMPLATES[genre]
                st.write(f"**结构建议**：{template['structure']}")
                st.write(f"**写作提示**：{template['tips']}")
                st.write("**万能开头参考**：")
                for opening in template["openings"]:
                    st.write(f"- {opening}")
                st.write("**万能结尾参考**：")
                for ending in template["endings"]:
                    st.write(f"- {ending}")

        essay = st.text_area("开始写作文", height=280, placeholder="把你的作文写在这里……")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("提交点评", type="primary", use_container_width=True):
                if essay.strip():
                    _process_submission(user, essay, actual_topic, genre, grade)
                else:
                    st.error("请先写作文再提交")
        with col_b:
            uploaded = st.file_uploader("或上传txt草稿", type=["txt"])
            if uploaded:
                text = uploaded.read().decode("utf-8")
                st.session_state.draft_text = text
                st.rerun()

        if st.session_state.get("draft_text"):
            st.text_area("已加载草稿", st.session_state.draft_text, height=150)
            if st.button("使用此草稿"):
                st.session_state.essay_input = st.session_state.draft_text
                del st.session_state.draft_text
                st.rerun()

def _process_submission(
    user: Dict[str, Any],
    essay: str,
    topic: str,
    genre: str,
    grade: str
) -> None:
    """Process essay submission and generate feedback."""
    with st.spinner("正在分析作文……"):
        wc = chinese_word_count(essay)
        pc = paragraph_count(essay)
        sc = sentence_count(essay)
        struct_score = infer_structure_score(essay, grade)
        expr_score = infer_expression_score(essay, grade)
        total_score = calculate_total_score(struct_score, expr_score)

        # Get LLM feedback
        feedback = llm_json_feedback(grade, genre, topic, essay)

        # Save submission
        submission_data = {
            "student_username": user["username"],
            "essay_text": essay,
            "grade": grade,
            "genre": genre,
            "topic": topic,
            "word_count": wc,
            "structure_score": struct_score,
            "expression_score": expr_score,
            "total_score": total_score,
            **feedback
        }
        submission_id = save_submission(submission_data)

        # Save version
        save_essay_version(submission_id, 1, essay, wc)

        # Save growth record
        save_growth_record({
            "student_username": user["username"],
            "genre": genre,
            "word_count": wc,
            "structure_score": struct_score,
            "expression_score": expr_score,
            "total_score": total_score
        })

        # Store for display
        st.session_state.last_feedback = {
            "submission_id": submission_id,
            "essay": essay,
            "topic": topic,
            "genre": genre,
            "grade": grade,
            "word_count": wc,
            "structure_score": struct_score,
            "expression_score": expr_score,
            "total_score": total_score,
            **feedback
        }
        st.success("点评完成！")
        st.rerun()

def _render_rewrite_interface(user: Dict[str, Any]) -> None:
    """
    NEW FEATURE: Rewrite interface.
    Allows students to continue revising based on previous feedback.
    """
    st.subheader("继续改写")

    # Get recent submissions for rewriting
    submissions = query_df(
        "SELECT id, topic, genre, grade, total_score, created_at FROM submissions "
        "WHERE student_username = ? ORDER BY created_at DESC LIMIT 10",
        (user["username"],)
    )

    if submissions.empty:
        st.info("还没有作文记录，请先开始写作文。")
        return

    # Select submission to rewrite
    submission_options = [
        f"{row['topic']} ({row['genre']}) - {row['created_at'][:10]} - 得分:{row['total_score']}"
        for _, row in submissions.iterrows()
    ]

    selected_idx = st.selectbox("选择要改写的作文", submission_options)
    selected_submission = submissions.iloc[submission_options.index(selected_idx)]
    submission_id = selected_submission["id"]

    # Load original essay and feedback
    original = query_df(
        "SELECT * FROM submissions WHERE id = ?",
        (submission_id,)
    )

    if original.empty:
        st.error("无法加载作文")
        return

    row = original.iloc[0]
    original_essay = row["essay_text"]

    st.markdown("### 原文")
    st.text_area("原文内容", original_essay, height=100, disabled=True)

    # Show previous feedback
    if row.get("step_rewrite"):
        import json
        try:
            step_rewrite = json.loads(row["step_rewrite"])
            st.markdown("### 改写指导")
            st.info(f"**第一步（补内容）**：{step_rewrite.get('step1_content', '')}")
            st.info(f"**第二步（改句子）**：{step_rewrite.get('step2_sentence', '')}")
            st.info(f"**第三步（参考开头）**：{step_rewrite.get('step3_start', '')}")
            st.info(f"**第四步（参考结尾）**：{step_rewrite.get('step4_end', '')}")
        except Exception:
            st.write(row.get("step_rewrite", ""))

    # Rewrite editor
    st.markdown("### 开始改写")
    rewritten = st.text_area("改写后的作文", height=280, placeholder="根据指导建议，在这里写下改写后的作文……")

    if st.button("提交新版本", type="primary", use_container_width=True):
        if rewritten.strip():
            with st.spinner("正在分析新版本……"):
                wc = chinese_word_count(rewritten)
                pc = paragraph_count(rewritten)
                sc = sentence_count(rewritten)
                struct_score = infer_structure_score(rewritten, row["grade"])
                expr_score = infer_expression_score(rewritten, row["grade"])
                total_score = calculate_total_score(struct_score, expr_score)

                feedback = llm_json_feedback(row["grade"], row["genre"], row["topic"], rewritten)

                # Save new submission
                new_submission_data = {
                    "student_username": user["username"],
                    "assignment_id": row.get("assignment_id"),
                    "essay_text": rewritten,
                    "grade": row["grade"],
                    "genre": row["genre"],
                    "topic": row["topic"],
                    "word_count": wc,
                    "structure_score": struct_score,
                    "expression_score": expr_score,
                    "total_score": total_score,
                    **feedback
                }
                new_submission_id = save_submission(new_submission_data)

                # Get next version number
                versions = query_df(
                    "SELECT MAX(version_no) as max_ver FROM essay_versions WHERE submission_id = ?",
                    (submission_id,)
                )
                next_version = (versions.iloc[0]["max_ver"] or 1) + 1
                save_essay_version(submission_id, next_version, rewritten, wc)

                # Update growth record
                save_growth_record({
                    "student_username": user["username"],
                    "genre": row["genre"],
                    "word_count": wc,
                    "structure_score": struct_score,
                    "expression_score": expr_score,
                    "total_score": total_score
                })

                st.success(f"新版本（v{next_version}）提交成功！")
                st.session_state.last_feedback = {
                    "submission_id": new_submission_id,
                    "essay": rewritten,
                    "topic": row["topic"],
                    "genre": row["genre"],
                    "grade": row["grade"],
                    "word_count": wc,
                    "structure_score": struct_score,
                    "expression_score": expr_score,
                    "total_score": total_score,
                    **feedback
                }
                st.rerun()
        else:
            st.error("请填写改写后的作文")

def _render_image_writing(user: Dict[str, Any]) -> None:
    """Render image-based writing interface."""
    st.subheader("看图作文")

    uploaded = st.file_uploader("上传图片", type=["png", "jpg", "jpeg"])
    if uploaded:
        import base64
        from PIL import Image
        image = Image.open(uploaded)
        st.image(image, caption="已上传图片", use_container_width=True)

        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        grade = st.selectbox("年级", ["三年级", "四年级", "五年级", "六年级"], index=0)

        if st.button("生成观察提示", type="primary"):
            with st.spinner("AI正在分析图片……"):
                prompts = vision_observation_prompts(grade, img_base64)
                st.session_state.image_prompts = prompts
                st.rerun()

        if st.session_state.get("image_prompts"):
            prompts = st.session_state.image_prompts
            st.markdown("### AI观察提示")
            st.write(f"**场景概括**：{prompts.get('scene', '')}")
            st.write("**观察提示**：")
            for tip in prompts.get("observation_tips", []):
                st.write(f"- {tip}")
            st.write("**启发问题**：")
            for q in prompts.get("inspiring_questions", []):
                st.write(f"- {q}")
            st.write(f"**建议题目**：{prompts.get('suggested_title', '')}")

            # Writing area after prompts
            essay = st.text_area("开始写作文", height=200, placeholder="根据提示开始写作……")
            if st.button("提交点评"):
                if essay.strip():
                    _process_submission(
                        user, essay,
                        prompts.get("suggested_title", "看图作文"),
                        "看图作文", grade
                    )
                else:
                    st.error("请先写作文")

def _render_version_comparison(user: Dict[str, Any]) -> None:
    """Render version comparison interface."""
    st.subheader("历史版本对比")

    # Get versions for the latest submission
    submissions = query_df(
        "SELECT id, topic, genre FROM submissions WHERE student_username = ? ORDER BY created_at DESC LIMIT 1",
        (user["username"],)
    )

    if submissions.empty:
        st.info("还没有作文记录。")
        return

    submission_id = submissions.iloc[0]["id"]
    versions = query_df(
        "SELECT version_no, essay_text, word_count, created_at FROM essay_versions "
        "WHERE submission_id = ? ORDER BY version_no",
        (submission_id,)
    )

    if len(versions) < 2:
        st.info("当前作文只有一个版本，完成点评后可继续修改并保存新版本。")
        # Add rewrite entry point here
        if st.button("开始改写此作文", type="primary"):
            st.session_state.rewrite_target_id = submission_id
            st.info("请在顶部菜单切换到'继续改写'标签")
        return

    v1_opts = versions["version_no"].tolist()
    v1_sel = st.selectbox("版本 A", v1_opts, index=0)
    v2_sel = st.selectbox("版本 B", v1_opts, index=len(v1_opts)-1)

    v1_text = versions[versions["version_no"] == v1_sel].iloc[0]["essay_text"]
    v2_text = versions[versions["version_no"] == v2_sel].iloc[0]["essay_text"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**版本 {v1_sel}**")
        st.text_area("版本 A", v1_text, height=200, disabled=True, key="v1_display")
    with col2:
        st.markdown(f"**版本 {v2_sel}**")
        st.text_area("版本 B", v2_text, height=200, disabled=True, key="v2_display")

    # Comparison analysis
    wc1 = chinese_word_count(v1_text)
    wc2 = chinese_word_count(v2_text)
    st.metric("字数变化", f"{wc2 - wc1:+d}字")

    # Rewrite entry point from comparison
    if st.button("基于此版本继续改写", type="primary"):
        st.session_state.rewrite_target_id = submission_id
        st.session_state.rewrite_version = v2_sel
        # Navigate to rewrite (simplified)
        st.info("请切换到'继续改写'标签开始修改")

def _render_growth_records(user: Dict[str, Any]) -> None:
    """Render growth records and trends."""
    st.subheader("成长档案")

    growth = query_df(
        "SELECT created_at, genre, word_count, structure_score, expression_score, total_score "
        "FROM growth_records WHERE student_username = ? ORDER BY created_at",
        (user["username"],)
    )

    if growth.empty:
        st.info("还没有成长记录，完成作文后将自动记录。")
        return

    st.dataframe(growth, use_container_width=True)

    # Trend chart
    if len(growth) > 1:
        st.subheader("成长趋势")
        chart_data = growth.set_index("created_at")[["word_count", "total_score"]]
        st.line_chart(chart_data)

    # Statistics
    st.subheader("统计摘要")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("作文篇数", len(growth))
    with col2:
        st.metric("平均字数", int(growth["word_count"].mean()))
    with col3:
        st.metric("平均得分", int(growth["total_score"].mean()))
