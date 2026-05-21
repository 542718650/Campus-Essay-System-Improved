"""
Configuration and settings management.
Supports environment variables and Streamlit secrets.
"""

import os
from typing import Optional
from pathlib import Path

# Import Streamlit conditionally to allow running without it in some contexts
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Default configuration
DEFAULT_CONFIG = {
    "DB_PATH": "essay_campus_system.db",
    "OPENAI_BASE_URL": "https://4.0.wokaai.com/v1/",
    "OPENAI_MODEL": "gpt-4.1-2025-04-14",
    "APP_TITLE": "校园作文辅导系统（老师端 + 学生端 + 班级管理）",
}

def get_config_value(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read configuration value with priority:
    1. Environment variables
    2. Streamlit secrets (if running in Streamlit)
    3. Default value
    """
    # 1. Check environment variables
    env_value = os.getenv(name)
    if env_value:
        return env_value

    # 2. Check Streamlit secrets
    if HAS_STREAMLIT:
        try:
            secret_value = st.secrets.get(name)
            if secret_value:
                return str(secret_value)
        except Exception:
            pass

    # 3. Return default
    return default

def get_db_path() -> str:
    """Get database path from config or default."""
    return get_config_value("ESSAY_APP_DB", DEFAULT_CONFIG["DB_PATH"])

def get_openai_config() -> dict:
    """Get OpenAI configuration."""
    return {
        "api_key": get_config_value("OPENAI_API_KEY"),
        "base_url": get_config_value("OPENAI_BASE_URL", DEFAULT_CONFIG["OPENAI_BASE_URL"]),
        "model": get_config_value("OPENAI_MODEL", DEFAULT_CONFIG["OPENAI_MODEL"]),
    }

def get_supabase_config() -> dict:
    """Get Supabase configuration."""
    return {
        "url": get_config_value("SUPABASE_URL"),
        "key": get_config_value("SUPABASE_KEY"),
    }

# Initialize OpenAI config on import
OPENAI_CONFIG = get_openai_config()
OPENAI_API_KEY = OPENAI_CONFIG["api_key"]
OPENAI_BASE_URL = OPENAI_CONFIG["base_url"]
OPENAI_MODEL = OPENAI_CONFIG["model"]
SUPABASE_URL = get_supabase_config()["url"]
SUPABASE_KEY = get_supabase_config()["key"]
