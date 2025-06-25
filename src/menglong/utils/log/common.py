from enum import Enum


class MessageType(Enum):
    """Message types for different styling."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    # --- 成功/失败 ---
    SUCCESS = "success"
    FAILURE = "failure"
    # --- LLM ---
    SYSTEM = "system"
    USER = "user"
    AGENT = ""
    TOOL = "tool"
