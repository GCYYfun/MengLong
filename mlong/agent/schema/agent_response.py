from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# ======== Agent 响应模型 ========
class TextContentData(BaseModel):
    """文本内容"""
    data: Optional[str] = Field(default=None, description="文本内容")

class ReasoningContentData(BaseModel):
    """思考过程内容"""
    reasoning_data: Optional[str] = Field(default=None, description="思考过程内容")

class StreamEvent(BaseModel):
    """事件"""
    event: Optional[str] = Field(default=None, description="事件")