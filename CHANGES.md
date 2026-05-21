# Campus-Essay-System 代码改进记录

> 基于仓库：`tiejianluo/Campus-Writing-Tutoring-System` (master 分支)
> 改进日期：2026-05-21
> 改进者：AI Assistant

---

## 目录

1. [架构重构](#1-架构重构)
2. [安全性改进](#2-安全性改进)
3. [功能新增](#3-功能新增)
4. [性能优化](#4-性能优化)
5. [依赖清理](#5-依赖清理)
6. [数据库变更](#6-数据库变更)

---

## 1. 架构重构

### 1.1 单文件拆分为模块化结构

**改动前**：
```
campus_essay_system.py  (1033 行，所有逻辑混杂)
```

**改动后**：
```
Campus-Essay-System-Improved/
├── main.py                 # 入口文件 (~100 行)
├── config.py               # 配置管理 (~60 行)
├── .gitignore              # 更新版
├── requirements.txt        # 清理版
├── models/
│   ├── __init__.py
│   └── database.py         # 数据库操作 (~250 行)
├── services/
│   ├── __init__.py
│   ├── auth.py             # 认证授权 (~180 行)
│   ├── llm.py              # LLM 集成 (~150 行)
│   └── scoring.py          # 评分逻辑 (~150 行)
└── views/
    ├── __init__.py
    ├── student.py          # 学生端 UI (~300 行)
    ├── teacher.py          # 教师端 UI (~120 行)
    ├── parent.py           # 家长端 UI (~100 行)
    └── admin.py            # 管理员 UI (~200 行)
```

**收益**：
- 职责分离，易于维护和测试
- 各模块可独立开发
- 代码可读性大幅提升
- 便于后续功能扩展

---

## 2. 安全性改进

### 2.1 API Key 管理

**改动前**：
```python
# campus_essay_system.py 第 24 行
OPENAI_API_KEY = "sk-bGelDOkVt64HBKNhMtgxI3v2Au04hsjohTykYSWUef0mape9"
```

**改动后**：
```python
# config.py
def get_config_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """优先级：环境变量 > Streamlit secrets > 默认值"""
    env_value = os.getenv(name)
    if env_value:
        return env_value
    try:
        return st.secrets.get(name)
    except Exception:
        return default
```

**收益**：
- 敏感信息不再硬编码
- 支持多种部署环境
- 符合安全最佳实践

### 2.2 管理员自我注册防护

**改动前**：
```python
# register_user 允许任何角色包括 admin 注册
role = st.selectbox("角色", ["student", "teacher", "parent"])
```

**改动后**：
```python
# services/auth.py
def register_user(..., role: str, ...) -> bool:
    # 阻止 admin 自我注册
    if role == "admin":
        return False
    # 验证角色合法性
    if role not in ["student", "teacher", "parent"]:
        return False
```

**收益**：
- 防止权限提升攻击
- 新增 `test_security.py` 中的安全测试已验证此功能

### 2.3 `.gitignore` 增强

**改动前**：
```
# Log directory
log/

# Python cache files
__pycache__/
*.py[cod]
*$py.class
```

**改动后**：
```
# Local secrets
.env
.streamlit/secrets.toml

# Database files
*.db
*.sqlite
*.sqlite3

# Virtual environments
venv/
.env/

# Streamlit
.streamlit/
```

**收益**：
- 防止敏感配置文件泄露
- 防止数据库文件提交
- 防止虚拟环境提交

---

## 3. 功能新增

### 3.1 家长-学生绑定功能

**改动前**：
```python
# parent_view 可查看所有学生
students = query_df("SELECT ... FROM users WHERE role='student'")
```

**改动后**：
```python
# views/parent.py
def render_parent_view(user):
    # 仅显示已绑定的孩子
    bound_children = get_parent_children(user["username"])

    if bound_children:
        # 显示绑定孩子的数据
    else:
        # 显示绑定界面
        # 方式1：通过账号绑定
        # 方式2：从班级列表选择
```

**数据库变更**：
```sql
-- users 表新增 parent_of 字段
ALTER TABLE users ADD COLUMN parent_of TEXT;
-- 存储被绑定的学生 username
```

**收益**：
- 家长只能查看自己孩子的数据
- 支持多孩子绑定
- 提供两种绑定方式

### 3.2 改写功能入口

**改动前**：
- 学生端菜单：开始写作文 / 看图作文 / 历史版本对比 / 成长档案
- 无改写入口

**改动后**：
- 学生端菜单：开始写作文 / 看图作文 / **继续改写** / 历史版本对比 / 成长档案
- 历史版本对比页面增加"基于此版本继续改写"按钮

**新增接口**：
```python
# views/student.py
def _render_rewrite_interface(user):
    """改写界面：选择作文 → 查看原文和反馈 → 输入改写 → 保存新版本"""
```

**收益**：
- 改写流程完整闭环
- 支持多版本迭代
- 版本历史可追溯

### 3.3 管理员功能增强

**改动前**：
```python
def admin_view():
    st.dataframe(query_df("SELECT ... FROM users"))
    st.dataframe(query_df("SELECT * FROM classes"))
```

**改动后**：
```python
def render_admin_view(user):
    # 用户总览
    # 批量导入 (CSV)
    # 批量管理 (重置密码/修改角色/分配班级/批量删除)
    # 数据导出 (CSV)
```

**新增功能**：
- CSV 批量导入用户
- 批量重置密码
- 批量修改角色
- 批量分配班级
- 批量删除用户
- 数据导出（用户列表/作文记录/成长档案/班级信息）
- 导入模板下载

**收益**：
- 管理员可高效管理大规模用户
- 支持日常运维操作

---

## 4. 性能优化

### 4.1 SQLite WAL 模式

**改动前**：
```python
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
```

**改动后**：
```python
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA foreign_keys=ON;")
```

**收益**：
- 支持并发读写
- 减少 `database is locked` 错误
- 提升多用户场景下的性能

### 4.2 评分逻辑优化

**改动前**：
```python
def infer_structure_score(text: str) -> int:
    score = 60
    if wc >= 180: score += 10
    # ... 简单阈值判断
```

**改动后**：
```python
def infer_structure_score(text: str, grade: str = "三年级") -> int:
    # 分年级评分标准
    rubric = GRADE_RUBRICS.get(grade, ...)
    # 多维权重评分
    # - 字数（按年级要求）
    # - 段落数
    # - 过渡词丰富度
    # - 句子多样性
```

**收益**：
- 评分更准确反映年级要求
- 减少刷分可能
- 评分维度更丰富

---

## 5. 依赖清理

### 5.1 requirements.txt 优化

**改动前**：
```
streamlit
pandas
pillow
reportlab
opencv-python
numpy
openai
bcrypt
supabase
rapidocr-onnxruntime
```

**改动后**：
```
# Core dependencies
streamlit>=1.28.0
pandas>=2.0.0
pillow>=10.0.0
openai>=1.0.0
bcrypt>=4.0.0

# Optional dependencies (uncomment if needed)
# supabase>=2.0.0
# reportlab>=4.0.0
# opencv-python>=4.8.0
# rapidocr-onnxruntime>=1.3.0
```

**收益**：
- 核心依赖最小化
- 可选依赖明确标注
- 指定版本范围

---

## 6. 数据库变更

### 6.1 Schema 更新

**新增字段**：
```sql
-- users 表
ALTER TABLE users ADD COLUMN parent_of TEXT;
-- 用途：存储家长绑定的学生 username
-- 默认值：NULL
```

**迁移逻辑**：
```python
# models/database.py
def run_migration(conn):
    """自动检测并执行 schema 迁移"""
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if "parent_of" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN parent_of TEXT;")
```

**收益**：
- 向后兼容旧数据库
- 自动迁移无需手动操作

---

## 改进摘要

| 类别 | 改进项 | 影响范围 | 优先级 |
|------|--------|----------|--------|
| 架构 | 单文件拆分为模块化 | 全局 | P0 |
| 安全 | API Key 环境变量化 | 全局 | P0 |
| 安全 | 管理员自我注册防护 | 注册流程 | P0 |
| 安全 | .gitignore 增强 | 版本控制 | P1 |
| 功能 | 家长-学生绑定 | 家长端 | P1 |
| 功能 | 改写功能入口 | 学生端 | P1 |
| 功能 | 管理员批量操作 | 管理端 | P1 |
| 性能 | SQLite WAL 模式 | 数据库 | P2 |
| 性能 | 评分逻辑优化 | 评分系统 | P2 |
| 依赖 | requirements.txt 清理 | 部署 | P3 |
