# 代码改动对照表

> 基准：`tiejianluo/Campus-Writing-Tutoring-System` (master, 1033 行)
> 改进版：`Campus-Essay-System-Improved` (模块化架构)

---

## 文件结构对比

| 原始文件 | 改进后位置 | 说明 |
|---------|-----------|------|
| `campus_essay_system.py` (1033 行) | `main.py` (~100 行) | 入口文件，仅保留路由逻辑 |
| (内联) | `config.py` (~60 行) | **新增**：配置管理模块 |
| (内联) | `models/database.py` (~250 行) | **新增**：数据库操作模块 |
| (内联) | `services/auth.py` (~180 行) | **新增**：认证授权模块 |
| (内联) | `services/llm.py` (~150 行) | **新增**：LLM 集成模块 |
| (内联) | `services/scoring.py` (~150 行) | **新增**：评分逻辑模块 |
| (内联) | `views/student.py` (~300 行) | **新增**：学生端 UI 模块 |
| (内联) | `views/teacher.py` (~120 行) | **新增**：教师端 UI 模块 |
| (内联) | `views/parent.py` (~100 行) | **新增**：家长端 UI 模块 |
| (内联) | `views/admin.py` (~200 行) | **新增**：管理员 UI 模块 |
| `.gitignore` | `.gitignore` | **改进**：增加敏感文件排除 |
| `requirements.txt` | `requirements.txt` | **改进**：清理非必要依赖 |
| (无) | `CHANGES.md` | **新增**：改动记录文档 |
| (无) | `CODE_COMPARISON.md` | **新增**：本对照文档 |

---

## 关键代码段对比

### 1. API Key 获取

**原始** (`campus_essay_system.py:24`)：
```python
OPENAI_API_KEY = "sk-bGelDOkVt64HBKNhMtgxI3v2Au04hsjohTykYSWUef0mape9"
```

**改进** (`config.py:25-36`)：
```python
def get_config_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """优先级：环境变量 > Streamlit secrets > 默认值"""
    env_value = os.getenv(name)
    if env_value:
        return env_value
    if HAS_STREAMLIT:
        try:
            return str(st.secrets.get(name))
        except Exception:
            pass
    return default
```

### 2. 数据库连接

**原始** (`campus_essay_system.py:141`)：
```python
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
```

**改进** (`models/database.py:18-26`)：
```python
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")  # 启用 WAL 模式
conn.execute("PRAGMA foreign_keys=ON;")   # 启用外键约束
```

### 3. 数据库初始化

**原始**：`users` 表无 `parent_of` 字段

**改进** (`models/database.py:52-60`)：
```python
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    real_name TEXT NOT NULL,
    grade TEXT,
    class_name TEXT,
    parent_of TEXT,        # <-- 新增字段
    created_at TEXT NOT NULL
)
```

### 4. 家长视图

**原始** (`campus_essay_system.py:953`)：
```python
def parent_view(user):
    students = query_df("SELECT ... FROM users WHERE role='student'")  # 查所有学生
    selected = st.selectbox("选择学生", students["username"].tolist())
```

**改进** (`views/parent.py:20-40`)：
```python
def render_parent_view(user):
    bound_children = get_parent_children(user["username"])  # 仅查绑定的孩子
    if bound_children:
        # 显示绑定孩子的数据
    else:
        # 显示绑定界面（通过账号 / 从班级列表选择）
```

### 5. 学生端菜单

**原始**：
```python
menu = st.radio("选择功能", ["开始写作文", "看图作文", "历史版本对比", "成长档案"])
```

**改进** (`views/student.py:85`)：
```python
menu = st.radio("选择功能", [
    "开始写作文", "看图作文", "继续改写",  # <-- 新增
    "历史版本对比", "成长档案"
])
```

### 6. 管理员视图

**原始** (`campus_essay_system.py:978-983`)：
```python
def admin_view():
    st.dataframe(query_df("SELECT ... FROM users"))
    st.dataframe(query_df("SELECT * FROM classes"))
```

**改进** (`views/admin.py`)：
```python
def render_admin_view(user):
    # Tab 1: 用户总览 (保留原有功能)
    # Tab 2: 批量导入 (CSV 导入用户)
    # Tab 3: 批量管理 (重置密码/修改角色/分配班级/批量删除)
    # Tab 4: 数据导出 (用户列表/作文记录/成长档案/班级信息)
```

### 7. 评分逻辑

**原始** (`campus_essay_system.py:344-356`)：
```python
def infer_structure_score(text: str) -> int:
    score = 60
    if wc >= 180: score += 10
    if wc >= 300: score += 10
    if pc >= 3: score += 10
    keywords = ["首先", "然后", "接着", "最后", "后来", "终于"]
    if any(x in text for x in keywords): score += 10
    return min(score, 100)
```

**改进** (`services/scoring.py:40-70`)：
```python
GRADE_RUBRICS = {
    "三年级": {"min_words": 150, "target_words": 200, "min_paragraphs": 2},
    "四年级": {"min_words": 250, "target_words": 350, "min_paragraphs": 3},
    # ...
}

def infer_structure_score(text: str, grade: str = "三年级") -> int:
    rubric = GRADE_RUBRICS.get(grade, ...)
    # 多维权重评分：字数(15分) + 段落(10分) + 过渡词(10分) + 句子多样性(5分)
```

### 8. .gitignore

**原始**：
```
log/
__pycache__/
*.py[cod]
```

**改进**：
```
.env
.streamlit/secrets.toml
*.db
*.sqlite
venv/
```

### 9. requirements.txt

**原始**：
```
streamlit, pandas, pillow, reportlab, opencv-python, numpy, openai, bcrypt, supabase, rapidocr-onnxruntime
```

**改进**：
```
# Core: streamlit, pandas, pillow, openai, bcrypt
# Optional: supabase, reportlab, opencv-python, rapidocr-onnxruntime
```

---

## 新增测试

| 测试文件 | 行数 | 用途 |
|---------|------|------|
| `test_security.py` | 125 | 安全测试（硬编码 Key 检测、SQL 注入防护等） |
| `test_performance.py` | 105 | 性能测试（大文本处理延迟） |

> 以上测试文件已从原始仓库复制，保持不变。

---

## 行数统计

| 模块 | 原始行数 | 改进后行数 | 变化 |
|------|---------|-----------|------|
| 入口/路由 | (内联) | ~100 | +100 |
| 配置管理 | (内联) | ~60 | +60 |
| 数据库 | (内联) | ~250 | +250 |
| 认证授权 | (内联) | ~180 | +180 |
| LLM 集成 | (内联) | ~150 | +150 |
| 评分逻辑 | (内联) | ~150 | +150 |
| 学生端 | (内联) | ~300 | +300 |
| 教师端 | (内联) | ~120 | +120 |
| 家长端 | (内联) | ~100 | +100 |
| 管理员 | (内联) | ~200 | +200 |
| **总计** | **1033** | **~1610** | **+577** |

> 行数增加是因为模块化拆分带来的样板代码，实际业务逻辑行数基本持平。
