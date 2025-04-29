from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class SystemMessage(BaseModel):
    """系统消息模型"""

    content: str = Field(description="内容")
    role: Optional[str] = Field(default="system", description="角色")


class UserMessage(BaseModel):
    """用户消息模型"""

    content: Union[str, List, Dict] = Field(description="内容")
    role: Optional[str] = Field(default="user", description="角色")
    tool_id: Optional[str] = Field(default=None, description="工具调用ID")


class AssistantMessage(BaseModel):
    """助手消息模型"""

    content: Union[str, List] = Field(description="内容")
    role: Optional[str] = Field(default="assistant", description="角色")


class ToolMessage(BaseModel):
    """工具消息模型"""

    content: Union[str, List] = Field(description="内容")
    role: Optional[str] = Field(default="tool", description="角色")
    tool_id: Optional[str] = Field(default=None, description="工具调用ID")
