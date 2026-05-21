
import os
import io
import re
import json
import sqlite3
import base64
import textwrap
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd
import streamlit as st
from PIL import Image
import sys

DB_PATH = os.getenv("ESSAY_APP_DB", "essay_campus_system.db")
APP_TITLE = "校园作文辅导系统（老师端 + 学生端 + 班级管理）"


def get_config_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read deployment config from env first, then Streamlit secrets."""
    env_value = os.getenv(name)
    if env_value:
        return env_value
    try:
        secret_value = st.secrets.get(name)
    except Exception:
        return default
    return secret_value or default

# ----------------------------
# Optional integrations
# ----------------------------
SUPABASE_URL = get_config_value("SUPABASE_URL")
SUPABASE_KEY = get_config_value("SUPABASE_KEY")
OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
OPENAI_BASE_URL = get_config_value("OPENAI_BASE_URL", "https://4.0.wokaai.com/v1/")
OPENAI_MODEL = get_config_value("OPENAI_MODEL", "gpt-4.1-2025-04-14")

try:
    from supabase import create_client  # type: ignore
except Exception:
    create_client = None

try:
    import bcrypt  # type: ignore
except Exception:
    bcrypt = None




# ----------------------------
# Grade rubrics and templates
# ----------------------------
GRADE_RUBRICS = {
    "三年级": {
        "rubric": [
            ("切题", "是否围绕题目写，基本不跑题"),
            ("内容", "有没有把人物、事情或景物写清楚"),
            ("顺序", "有没有按先后顺序写，段落是否简单清楚"),
            ("语言", "句子是否通顺，是否能用恰当词语"),
            ("书写与标点", "标点是否基本正确，字数是否达标"),
        ],
        "target_words": (150, 300),
    },
    "四年级": {
        "rubric": [
            ("切题与中心", "是否围绕主题展开，中心是否明确"),
            ("内容充实", "是否有具体细节和例子"),
            ("结构顺序", "开头、经过、结尾是否较完整"),
            ("语言表达", "句子是否通顺，有没有恰当修辞"),
            ("书写规范", "标点和格式是否规范"),
        ],
        "target_words": (250, 400),
    },
    "五年级": {
        "rubric": [
            ("立意", "主题是否清楚，有没有自己的感受"),
            ("选材", "材料是否贴切，有没有典型细节"),
            ("结构", "段落层次是否清楚，过渡是否自然"),
            ("表达", "语言是否准确、生动"),
            ("规范", "字数、标点、格式是否规范"),
        ],
        "target_words": (350, 500),
    },
    "六年级": {
        "rubric": [
            ("主题与立意", "观点或情感是否明确且集中"),
            ("材料与细节", "材料是否典型，细节是否有支撑力"),
            ("结构与逻辑", "结构是否完整，过渡和呼应是否自然"),
            ("语言与表现", "表达是否准确、生动，有一定文采"),
            ("修改与规范", "格式、标点、错别字与整体完成度"),
        ],
        "target_words": (450, 700),
    },
}

ESSAY_TEMPLATES = {
    "写人": {
        "结构": ["开头：介绍人物是谁", "中间：写两到三件最能表现人物特点的事", "结尾：表达你的感受"],
        "万能开头": "在我的生活中，有一个让我很难忘的人，他（她）就是……",
        "万能结尾": "这就是我眼中的……，他（她）让我明白了……",
    },
    "写事": {
        "结构": ["开头：交代时间、地点、人物", "中间：按事情经过写清楚", "结尾：写结果和感受"],
        "万能开头": "每当想起这件事，我的心里都会泛起一阵……",
        "万能结尾": "通过这件事，我懂得了……",
    },
    "写景": {
        "结构": ["开头：点明写什么地方/季节", "中间：按方位、时间或感官描写", "结尾：抒发喜爱之情"],
        "万能开头": "我最喜欢的景色，要数……",
        "万能结尾": "这样的景色，怎能不让人喜爱呢？",
    },
    "想象作文": {
        "结构": ["开头：设定奇妙情境", "中间：展开想象并推动故事", "结尾：回到主题或表达愿望"],
        "万能开头": "一天早晨，我忽然发现……",
        "万能结尾": "这场奇妙的经历让我久久不能忘怀。",
    },
    "读后感": {
        "结构": ["开头：写读了什么", "中间：概括内容并结合感受", "结尾：联系生活升华主题"],
        "万能开头": "最近，我读了《……》，心里很受触动。",
        "万能结尾": "今后，我也要像书中的……一样……",
    },
    "日记": {
        "结构": ["开头：日期天气", "中间：写当天一件有意思或有感触的事", "结尾：写心情和收获"],
        "万能开头": "今天是……，天气……，我经历了一件……的事。",
        "万能结尾": "这一天真让我难忘。",
    },
    "看图作文": {
        "结构": ["开头：整体观察图片", "中间：按人物/场景/动作/细节展开", "结尾：点出主题或感受"],
        "万能开头": "图画中展现的是一幅……的场景。",
        "万能结尾": "看着这幅图，我不由得想到……",
    },
}

DEFAULT_TOPICS = {
    "写人": ["我的妈妈", "我的老师", "我的同桌", "一个值得敬佩的人"],
    "写事": ["一件难忘的事", "第一次做饭", "一次帮助别人", "一次失败后的成长"],
    "写景": ["校园一角", "家乡的秋天", "雨后的公园", "我喜欢的季节"],
    "想象作文": ["假如我有一双翅膀", "未来的教室", "我和机器人做朋友", "月球旅行记"],
    "读后感": ["读《草房子》有感", "读《西游记》有感", "读《小王子》有感"],
    "日记": ["周末的一天", "春游日记", "运动会日记"],
    "看图作文": ["图中发生了什么", "看图想故事", "请给图片配一个故事"],
}


# ----------------------------
# Persistence
# ----------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            real_name TEXT,
            grade TEXT,
            class_name TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT UNIQUE,
            grade TEXT,
            teacher_username TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            genre TEXT,
            prompt TEXT,
            grade TEXT,
            class_name TEXT,
            teacher_username TEXT,
            due_date TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER,
            student_username TEXT,
            title TEXT,
            genre TEXT,
            prompt TEXT,
            essay_text TEXT,
            word_count INTEGER,
            structure_score INTEGER,
            expression_score INTEGER,
            total_score INTEGER,
            teacher_feedback TEXT,
            student_feedback TEXT,
            revised_steps TEXT,
            model_feedback_json TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS essay_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER,
            version_no INTEGER,
            essay_text TEXT,
            feedback_json TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS growth_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_username TEXT,
            genre TEXT,
            word_count INTEGER,
            structure_score INTEGER,
            expression_score INTEGER,
            total_score INTEGER,
            created_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()
    seed_defaults()


def hash_password(password: str) -> str:
    if bcrypt:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    if bcrypt:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed


def seed_defaults():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    count = cur.fetchone()["c"]
    if count == 0:
        now = datetime.now().isoformat()
        users = [
            ("teacher1", hash_password("123456"), "teacher", "张老师", None, None, now),
            ("student1", hash_password("123456"), "student", "小明", "三年级", "三年级一班", now),
            ("student2", hash_password("123456"), "student", "小红", "六年级", "六年级一班", now),
            ("parent1", hash_password("123456"), "parent", "家长示例", None, None, now),
            ("admin", hash_password("123456"), "admin", "管理员", None, None, now),
        ]
        cur.executemany(
            "INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            users,
        )
        classes = [
            ("三年级一班", "三年级", "teacher1", now),
            ("六年级一班", "六年级", "teacher1", now),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO classes (class_name, grade, teacher_username, created_at) VALUES (?, ?, ?, ?)",
            classes,
        )
        conn.commit()
    conn.close()


# ----------------------------
# Optional cloud login helper
# ----------------------------
@st.cache_resource
def get_supabase():
    if SUPABASE_URL and SUPABASE_KEY and create_client:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None


# ----------------------------
# Utilities
# ----------------------------
def chinese_word_count(text: str) -> int:
    if not text:
        return 0
    chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chars)


def paragraph_count(text: str) -> int:
    paras = [p.strip() for p in text.splitlines() if p.strip()]
    return len(paras)


def sentence_count(text: str) -> int:
    """计算文本中的句子数"""
    if not text:
        return 0
    import re
    sentences = re.split(r'[。！？.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    return max(len(sentences), 1)


def has_beginning_middle_end(text: str) -> bool:
    """检查文章是否有开头、中间和结尾"""
    para_count = paragraph_count(text)
    sent_count = sentence_count(text)
    return para_count >= 3 or sent_count >= 5


def structure_level(text: str) -> str:
    """评估文章结构水平"""
    para_count = paragraph_count(text)
    sent_count = sentence_count(text)
    
    if para_count >= 3 and sent_count >= 6:
        return "较完整"
    elif para_count >= 2 or sent_count >= 4:
        return "基本完整"
    else:
        return "待加强"


def expression_level(text: str) -> str:
    """评估文章表达水平"""
    # 简单的表达水平评估逻辑
    word_count = chinese_word_count(text)
    if word_count >= 200:
        return "较丰富"
    elif word_count >= 100:
        return "一般"
    else:
        return "待丰富"


def infer_structure_score(text: str) -> int:
    wc = chinese_word_count(text)
    pc = paragraph_count(text)
    score = 60
    if wc >= 180:
        score += 10
    if wc >= 300:
        score += 10
    if pc >= 3:
        score += 10
    if any(x in text for x in ["首先", "然后", "接着", "最后", "后来", "终于"]):
        score += 10
    return min(score, 100)


def infer_expression_score(text: str) -> int:
    score = 60
    if any(x in text for x in ["像", "仿佛", "好像", "犹如"]):
        score += 10
    if any(x in text for x in ["高兴", "难过", "激动", "紧张", "惊讶", "温暖"]):
        score += 10
    if chinese_word_count(text) >= 250:
        score += 10
    if any(x in text for x in ["！", "？", "……"]):
        score += 10
    return min(score, 100)


def grade_expectation(grade: str) -> str:
    low, high = GRADE_RUBRICS[grade]["target_words"]
    return f"建议字数：{low}—{high} 字"


def get_rubric_markdown(grade: str) -> str:
    items = GRADE_RUBRICS[grade]["rubric"]
    return "\n".join([f"- **{k}**：{v}" for k, v in items])


def build_prompt(grade: str, genre: str, topic: str, essay: str) -> str:
    rubric = get_rubric_markdown(grade)
    return f"""
你是一名温和、专业、懂小学生写作教学的中文作文老师。
请按照以下要求分析作文。

学生年级：{grade}
作文类型：{genre}
作文题目/主题：{topic}

该年级评价标准：
{rubric}

请输出 JSON，字段包括：
teacher_feedback, student_feedback, strengths, suggestions, polished_sentence, outline_advice, step_rewrite

其中：
- teacher_feedback：教师版点评，专业、具体、分点
- student_feedback：学生鼓励版点评，温暖、具体、易懂
- strengths：3条优点
- suggestions：3条改进建议
- polished_sentence：挑一两句原句润色示范
- outline_advice：给出更清晰的写作提纲
- step_rewrite：四步改写建议（先补内容、再改句子、参考开头、参考结尾）

学生作文：
{essay}
""".strip()


def llm_json_feedback(grade: str, genre: str, topic: str, essay: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return fallback_feedback(grade, genre, topic, essay)

    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        prompt = build_prompt(grade, genre, topic, essay)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是小学作文辅导老师，只输出合法JSON。"},
                {"role": "user", "content": prompt},
            ],
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception:
        return fallback_feedback(grade, genre, topic, essay)


def fallback_feedback(grade: str, genre: str, topic: str, essay: str) -> Dict[str, Any]:
    wc = chinese_word_count(essay)
    strengths = []
    suggestions = []

    if wc > 0:
        strengths.append("能够围绕题目完成写作。")
    if paragraph_count(essay) >= 2:
        strengths.append("已经有基本的分段意识。")
    if any(x in essay for x in ["高兴", "难过", "激动", "紧张"]):
        strengths.append("能写出人物或自己的感受。")

    if wc < GRADE_RUBRICS[grade]["target_words"][0]:
        suggestions.append("字数还可以再充实一些，多补充细节。")
    if paragraph_count(essay) < 3:
        suggestions.append("建议分成开头、中间、结尾三个部分。")
    if not any(x in essay for x in ["首先", "然后", "最后", "接着", "后来"]):
        suggestions.append("可以加入表示顺序的词语，让事情发展更清楚。")

    while len(strengths) < 3:
        strengths.append("作文态度认真，主题比较明确。")
    while len(suggestions) < 3:
        suggestions.append("可以多写动作、语言、心理活动，让内容更生动。")

    return {
        "teacher_feedback": f"这篇{genre}基本围绕“{topic}”展开，完成度较好。当前更需要加强的是内容细节与结构层次，建议围绕年级要求继续补充典型细节，并提升段落之间的衔接。",
        "student_feedback": f"你已经把《{topic}》这个主题写出来了，真不错！如果再多写一点经过、感受和细节，这篇作文会更精彩。",
        "strengths": strengths,
        "suggestions": suggestions,
        "polished_sentence": "示例润色：把“我很开心”改成“我高兴得一路小跑，心里像开了一朵花”。",
        "outline_advice": "建议提纲：开头点题——中间写具体经过或观察到的细节——结尾写感受或收获。",
        "step_rewrite": {
            "先补内容": "补上人物动作、语言和心理活动。",
            "再改句子": "把短句补充完整，尽量写清谁在做什么。",
            "参考开头": ESSAY_TEMPLATES.get(genre, {}).get("万能开头", "开头先点明主题。"),
            "参考结尾": ESSAY_TEMPLATES.get(genre, {}).get("万能结尾", "结尾写感受或收获。"),
        },
    }


def generate_topics(grade: str, genre: str, keyword: str = "") -> List[str]:
    base = DEFAULT_TOPICS.get(genre, []).copy()
    if keyword:
        base = [f"{keyword}：{t}" for t in base[:3]] + [f"围绕“{keyword}”自拟题目"]
    if grade in ["五年级", "六年级"]:
        base += [f"我眼中的{keyword or '成长'}", f"一次关于{keyword or '勇气'}的思考"]
    return base[:6]


def compare_with_model_essay(student_text: str, genre: str, topic: str) -> str:
    tpl = ESSAY_TEMPLATES.get(genre, {})
    return (
        f"范文对比提示：优秀{genre}通常会有更清晰的结构（{ ' / '.join(tpl.get('结构', [])) }）。\n"
        f"对照你的作文，可以重点检查：\n"
        f"1. 开头是否点题；\n2. 中间是否有足够细节；\n3. 结尾是否表达感受；\n"
        f"4. 是否用了表示顺序或描写感受的词语。"
    )


def save_submission(data: Dict[str, Any]) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO submissions (
            assignment_id, student_username, title, genre, prompt, essay_text, word_count,
            structure_score, expression_score, total_score, teacher_feedback, student_feedback,
            revised_steps, model_feedback_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("assignment_id"),
            data["student_username"],
            data["title"],
            data["genre"],
            data["prompt"],
            data["essay_text"],
            data["word_count"],
            data["structure_score"],
            data["expression_score"],
            data["total_score"],
            data["teacher_feedback"],
            data["student_feedback"],
            json.dumps(data["step_rewrite"], ensure_ascii=False),
            json.dumps(data["feedback_json"], ensure_ascii=False),
            datetime.now().isoformat(),
        ),
    )
    submission_id = cur.lastrowid
    cur.execute(
        "INSERT INTO essay_versions (submission_id, version_no, essay_text, feedback_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (submission_id, 1, data["essay_text"], json.dumps(data["feedback_json"], ensure_ascii=False), datetime.now().isoformat()),
    )
    cur.execute(
        "INSERT INTO growth_records (student_username, genre, word_count, structure_score, expression_score, total_score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data["student_username"],
            data["genre"],
            data["word_count"],
            data["structure_score"],
            data["expression_score"],
            data["total_score"],
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return submission_id


def add_new_version(submission_id: int, essay_text: str, feedback_json: Dict[str, Any]) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(version_no), 0) AS m FROM essay_versions WHERE submission_id=?", (submission_id,))
    next_v = cur.fetchone()["m"] + 1
    cur.execute(
        "INSERT INTO essay_versions (submission_id, version_no, essay_text, feedback_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (submission_id, next_v, essay_text, json.dumps(feedback_json, ensure_ascii=False), datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def text_to_data_url(img: Image.Image) -> str:
    """将图片转换为base64编码的数据URL"""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def fallback_image_prompts(grade: str) -> Dict[str, Any]:
    """回退图像提示"""
    return {
        "scene": "这张图片里可能有人物、环境和正在发生的事情，适合做看图作文。",
        "observe": [
            "先说清楚图上有谁，他们在哪里。",
            "仔细看人物的动作、表情和周围环境。",
            "想一想：这件事发生前后可能有什么故事？",
            "最后写出你的感受或明白的道理。"
        ],
        "questions": [
            "谁是画面中的主角？",
            "他们在做什么？",
            "周围环境告诉了你什么信息？",
            "如果给这幅图取一个题目，你会怎么取？"
        ],
        "suggested_title": "看图作文"
    }


def vision_observation_prompts(image: Image.Image, grade: str) -> Dict[str, Any]:
    """使用大语言模型识别图像并生成观察提示"""
    if not OPENAI_API_KEY:
        return fallback_image_prompts(grade)
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        
        prompt = textwrap.dedent(f"""
        你是一位小学作文老师。请根据图片，为{grade}学生生成看图作文辅助信息。
        输出 JSON，包含：
        scene 写1句场景概括；
        observe 给4条观察提示；
        questions 给4条启发问题；
        suggested_title 给1个推荐题目；
        语言适合小学生。
        """).strip()
        
        data_url = text_to_data_url(image)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "你是小学作文辅导老师，只输出合法JSON。"},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]}
            ]
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return fallback_image_prompts(grade)


# ----------------------------
# UI helpers
# ----------------------------
def login_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


ALLOWED_SELF_REGISTER_ROLES = {"student", "teacher", "parent"}


def register_user(username: str, password: str, role: str, real_name: str, grade: Optional[str], class_name: Optional[str]) -> bool:
    if role not in ALLOWED_SELF_REGISTER_ROLES:
        return False
    if not username.strip() or not password or not real_name.strip():
        return False

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, real_name, grade, class_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, hash_password(password), role, real_name, grade, class_name, datetime.now().isoformat()),
        )
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    conn.close()
    return ok


def sidebar_auth():
    st.sidebar.title("账号系统")
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user:
        u = st.session_state.user
        st.sidebar.success(f"已登录：{u['real_name']}（{u['role']}）")
        if st.sidebar.button("退出登录"):
            st.session_state.user = None
            st.rerun()
    else:
        tab1, tab2 = st.sidebar.tabs(["登录", "注册"])
        with tab1:
            username = st.text_input("用户名", key="login_user")
            password = st.text_input("密码", type="password", key="login_pwd")
            if st.button("登录"):
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("用户名或密码错误。")
        with tab2:
            username = st.text_input("新用户名", key="reg_user")
            real_name = st.text_input("姓名", key="reg_name")
            role = st.selectbox("角色", ["student", "teacher", "parent"])
            grade = st.selectbox("年级", ["三年级", "四年级", "五年级", "六年级"], key="reg_grade") if role == "student" else None
            class_name = st.text_input("班级（学生可填）", key="reg_class")
            password = st.text_input("设置密码", type="password", key="reg_pwd")
            if st.button("注册"):
                ok = register_user(username, password, role, real_name, grade, class_name or None)
                if ok:
                    st.success("注册成功，请登录。")
                else:
                    st.error("用户名已存在。")


def teacher_view(user: Dict[str, Any]):
    st.header("老师端：布置作文题与批量查看")
    t1, t2, t3 = st.tabs(["布置作文题", "批量查看提交", "班级管理"])

    with t1:
        conn = get_conn()
        classes = query_df("SELECT class_name, grade FROM classes WHERE teacher_username=?", (user["username"],))
        conn.close()
        class_options = classes["class_name"].tolist() or ["三年级一班"]
        class_name = st.selectbox("选择班级", class_options, key="assign_class")
        grade = classes[classes["class_name"] == class_name]["grade"].iloc[0] if not classes.empty and class_name in classes["class_name"].values else "三年级"
        genre = st.selectbox("作文类型", list(ESSAY_TEMPLATES.keys()), key="assign_genre")
        title = st.text_input("作文题目")
        prompt = st.text_area("布置说明", placeholder="写作要求、观察提示、注意事项")
        due_date = st.date_input("截止日期")
        if st.button("发布作文题"):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO assignments (title, genre, prompt, grade, class_name, teacher_username, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, genre, prompt, grade, class_name, user["username"], str(due_date), datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
            st.success("作文题已发布。")

    with t2:
        df = query_df("""
            SELECT s.id, s.student_username, s.title, s.genre, s.word_count, s.total_score, s.created_at, u.real_name
            FROM submissions s
            LEFT JOIN users u ON s.student_username = u.username
            ORDER BY s.created_at DESC
        """)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            sid = st.selectbox("查看某次提交", df["id"].tolist())
            row = query_df("SELECT * FROM submissions WHERE id=?", (int(sid),)).iloc[0]
            st.subheader(f"{row['title']} / {row['student_username']}")
            st.write(row["essay_text"])
            st.markdown("**教师点评**")
            st.write(row["teacher_feedback"])
            st.markdown("**学生鼓励版**")
            st.write(row["student_feedback"])

    with t3:
        st.subheader("班级管理")
        new_grade = st.selectbox("年级", ["三年级", "四年级", "五年级", "六年级"], key="class_grade")
        new_class = st.text_input("新班级名称")
        if st.button("新增班级"):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO classes (class_name, grade, teacher_username, created_at) VALUES (?, ?, ?, ?)",
                (new_class, new_grade, user["username"], datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
            st.success("已新增班级。")
        st.dataframe(query_df("SELECT * FROM classes ORDER BY grade, class_name"), use_container_width=True)


def student_view(user: Dict[str, Any]):
    st.header("学生端：作文练习与成长记录")
    menu = st.radio("选择功能", ["开始写作文", "看图作文", "历史版本对比", "成长档案"], horizontal=True)

    if menu == "开始写作文":
        assignments = query_df(
            "SELECT * FROM assignments WHERE grade=? ORDER BY created_at DESC",
            (user.get("grade") or "三年级",),
        )
        with st.expander("老师布置的作文题", expanded=True):
            if assignments.empty:
                st.info("暂时没有老师布置的作文题，你也可以自己练习。")
            else:
                st.dataframe(assignments[["id", "title", "genre", "class_name", "due_date"]], use_container_width=True)

        grade = user.get("grade") or st.selectbox("年级", list(GRADE_RUBRICS.keys()))
        genre = st.selectbox("作文类型", list(ESSAY_TEMPLATES.keys()), index=0)
        topic_options = generate_topics(grade, genre)
        topic = st.selectbox("主题/题目", topic_options)
        custom_title = st.text_input("自定义题目（可选）")
        title = custom_title or topic
        st.caption(grade_expectation(grade))
        with st.expander("本类型作文模板"):
            tpl = ESSAY_TEMPLATES[genre]
            st.markdown("**推荐结构**")
            for x in tpl["结构"]:
                st.markdown(f"- {x}")
            st.markdown(f"**参考开头**：{tpl['万能开头']}")
            st.markdown(f"**参考结尾**：{tpl['万能结尾']}")

        essay = st.text_area("开始写作文", height=280, placeholder="把你的作文写在这里……")
        uploaded_txt = st.file_uploader("或上传 txt 草稿", type=["txt"])
        if uploaded_txt:
            essay = uploaded_txt.read().decode("utf-8", errors="ignore")
            st.text_area("已读取草稿", essay, height=200)

        if st.button("生成点评并保存"):
            if not essay.strip():
                st.warning("请先输入作文内容。")
            else:
                feedback = llm_json_feedback(grade, genre, title, essay)
                wc = chinese_word_count(essay)
                structure = infer_structure_score(essay)
                expression = infer_expression_score(essay)
                total = int((structure + expression) / 2)
                sid = save_submission(
                    {
                        "assignment_id": None,
                        "student_username": user["username"],
                        "title": title,
                        "genre": genre,
                        "prompt": title,
                        "essay_text": essay,
                        "word_count": wc,
                        "structure_score": structure,
                        "expression_score": expression,
                        "total_score": total,
                        "teacher_feedback": feedback["teacher_feedback"],
                        "student_feedback": feedback["student_feedback"],
                        "step_rewrite": feedback["step_rewrite"],
                        "feedback_json": feedback,
                    }
                )
                st.success(f"已保存本次作文，编号：{sid}")
                show_feedback(grade, title, essay, feedback, wc, structure, expression, total)

    elif menu == "看图作文":
        grade = user.get("grade") or "三年级"
        image_file = st.file_uploader("上传图片（看图作文）", type=["png", "jpg", "jpeg"])
        if image_file:
            image = Image.open(image_file).convert("RGB")
            st.image(image, caption="上传的图片", use_container_width=True)
            
            if st.button("生成观察提示"):
                obs = vision_observation_prompts(image, grade)
                st.markdown("### 场景概括")
                st.write(obs.get("scene", ""))
                
                st.markdown("### 观察提示")
                for item in obs.get("observe", []):
                    st.markdown(f"- {item}")
                
                st.markdown("### 启发问题")
                for item in obs.get("questions", []):
                    st.markdown(f"- {item}")
                
                if "suggested_title" in obs:
                    st.markdown(f"### 推荐题目")
                    st.success(obs["suggested_title"])

    elif menu == "历史版本对比":
        df = query_df(
            "SELECT id, title, created_at FROM submissions WHERE student_username=? ORDER BY created_at DESC",
            (user["username"],),
        )
        if df.empty:
            st.info("还没有历史作文。")
        else:
            sid = st.selectbox("选择作文", df["id"].tolist())
            versions = query_df(
                "SELECT version_no, essay_text, created_at FROM essay_versions WHERE submission_id=? ORDER BY version_no",
                (int(sid),),
            )
            if len(versions) >= 2:
                v1 = st.selectbox("版本 A", versions["version_no"].tolist(), index=0)
                v2 = st.selectbox("版本 B", versions["version_no"].tolist(), index=len(versions)-1)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**版本 {v1}**")
                    st.write(versions[versions["version_no"] == v1]["essay_text"].iloc[0])
                with c2:
                    st.markdown(f"**版本 {v2}**")
                    st.write(versions[versions["version_no"] == v2]["essay_text"].iloc[0])
            else:
                st.info("当前作文只有一个版本，可以在点评后继续修改并保存新版本。")

    elif menu == "成长档案":
        df = query_df(
            "SELECT created_at, genre, word_count, structure_score, expression_score, total_score FROM growth_records WHERE student_username=? ORDER BY created_at",
            (user["username"],),
        )
        if df.empty:
            st.info("还没有成长记录。")
        else:
            st.dataframe(df, use_container_width=True)
            st.metric("累计练习次数", len(df))
            st.metric("平均字数", int(df["word_count"].mean()))
            st.metric("平均总分", int(df["total_score"].mean()))
            st.line_chart(df.set_index("created_at")[["word_count", "total_score"]])


def show_feedback(grade, title, essay, feedback, wc, structure, expression, total):
    st.subheader("作文点评结果")
    c1, c2, c3 = st.columns(3)
    c1.metric("字数", wc)
    c2.metric("结构分", structure)
    c3.metric("表达分", expression)
    st.metric("综合分", total)

    st.markdown("### 教师点评版")
    st.write(feedback["teacher_feedback"])
    st.markdown("### 学生鼓励版")
    st.success(feedback["student_feedback"])

    st.markdown("### 优点")
    for s in feedback.get("strengths", []):
        st.markdown(f"- {s}")

    st.markdown("### 改进建议")
    for s in feedback.get("suggestions", []):
        st.markdown(f"- {s}")

    st.markdown("### 范文对比提示")
    genre_guess = "写事"
    for k in ESSAY_TEMPLATES:
        if k in title:
            genre_guess = k
    st.info(compare_with_model_essay(essay, genre_guess, title))

    st.markdown("### 分步改写")
    step = feedback.get("step_rewrite", {})
    if isinstance(step, dict):
        st.write(f"1. 先补内容：{step.get('先补内容', '')}")
        st.write(f"2. 再改句子：{step.get('再改句子', '')}")
        st.write(f"3. 参考开头：{step.get('参考开头', '')}")
        st.write(f"4. 参考结尾：{step.get('参考结尾', '')}")
    elif isinstance(step, list):
        for i, item in enumerate(step, 1):
            st.write(f"{i}. {item}")
    else:
        st.write(str(step))


def parent_view(user: Dict[str, Any]):
    st.header("家长/老师视图")
    st.write("可查看最近作文与成长趋势。")
    students = query_df("SELECT username, real_name, grade, class_name FROM users WHERE role='student'")
    if students.empty:
        st.info("暂无学生数据。")
        return
    selected = st.selectbox("选择学生", students["username"].tolist())
    info = students[students["username"] == selected].iloc[0]
    st.write(f"学生：{info['real_name']} / {info['grade']} / {info['class_name']}")
    latest = query_df("SELECT * FROM submissions WHERE student_username=? ORDER BY created_at DESC LIMIT 1", (selected,))
    if not latest.empty:
        row = latest.iloc[0]
        st.subheader("最近一次作文")
        st.write(row["essay_text"])
        st.markdown("**教师点评**")
        st.write(row["teacher_feedback"])
        st.markdown("**家长可关注**")
        st.write("建议先关注是否切题、有没有具体细节、分段是否清楚，再鼓励孩子继续修改。")
    growth = query_df("SELECT created_at, word_count, total_score FROM growth_records WHERE student_username=? ORDER BY created_at", (selected,))
    if not growth.empty:
        st.subheader("成长趋势")
        st.line_chart(growth.set_index("created_at")[["word_count", "total_score"]])


def admin_view():
    st.header("管理员视图")
    st.subheader("用户总览")
    st.dataframe(query_df("SELECT username, real_name, role, grade, class_name, created_at FROM users ORDER BY created_at DESC"), use_container_width=True)
    st.subheader("班级总览")
    st.dataframe(query_df("SELECT * FROM classes ORDER BY grade, class_name"), use_container_width=True)


# ----------------------------
# Main
# ----------------------------
def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📝", layout="wide")
    init_db()
    st.title(APP_TITLE)
    st.caption("支持多角色登录、班级管理、作文布置、看图作文、大语言模型图像识别、分年级 rubric、历史版本对比与成长档案。")

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
        st.markdown("- 家长/老师视图：查看最近练习与趋势")
        st.markdown("- 看图作文：使用大语言模型生成观察提示和启发问题")
        return

    role = user["role"]
    if role == "teacher":
        teacher_view(user)
    elif role == "student":
        student_view(user)
    elif role == "parent":
        parent_view(user)
    elif role == "admin":
        admin_view()
    else:
        st.warning("未知角色。")


if __name__ == "__main__":
    main()
