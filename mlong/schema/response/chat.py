from dataclasses import dataclass
from typing import Optional, List
from .base import Message, Choice

@dataclass
class ChatResponse:
    """聊天响应类型"""
    choices: List[Choice]

    def __init__(self):
        self.choices = [Choice(Message())]

    @property
    def text(self) -> str:
        """获取响应文本"""
        return self.choices[0].message.content

@dataclass
class ChatStreamResponse:
    """流式聊天响应类型"""
    id: Optional[str] = None
    stream: Optional[bool] = None