from dataclasses import dataclass
from typing import Optional

@dataclass
class Message:
    """消息基础类型"""
    content: str
    reasoning_content: Optional[str] = None

@dataclass
class Choice:
    """选择类型，包含消息内容"""
    message: Message