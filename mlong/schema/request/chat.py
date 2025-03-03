from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .base import BaseRequest

@dataclass
class ChatRequest(BaseRequest):
    """聊天请求类型"""
    messages: List[Dict[str, Any]]
    stream: bool = False
    
    def validate(self) -> None:
        """验证请求参数
        
        Raises:
            ValueError: 当参数不合法时抛出
        """
        super().validate()
        
        if not self.messages:
            raise ValueError("messages is required")
            
        for message in self.messages:
            if "role" not in message or "content" not in message:
                raise ValueError("每条消息必须包含role和content字段")
                
            if message["role"] not in ["system", "user", "assistant"]:
                raise ValueError(f"不支持的消息角色: {message['role']}")

@dataclass
class ChatStreamRequest(ChatRequest):
    """流式聊天请求类型"""
    stream: bool = True