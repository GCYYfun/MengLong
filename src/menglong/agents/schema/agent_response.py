from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ===== Steam Event ========

START_TEXT = "START_TEXT"
START_REASONING = "START_REASONING"
END_REASONING = "END_REASONING"
END_TURN = "END_TURN"


# ======== Agent 响应模型 ========
class TextContentData(BaseModel):
    """文本内容"""

    data: Optional[str] = Field(default=None, description="文本内容")

    def __contains__(self, item):
        """支持 in 操作符，检查某个键是否存在"""
        return item in self.__dict__ or item in self.model_dump()


class ReasoningContentData(BaseModel):
    """思考过程内容"""

    reasoning_data: Optional[str] = Field(default=None, description="思考过程内容")

    def __contains__(self, item):
        """支持 in 操作符，检查某个键是否存在"""
        return item in self.__dict__ or item in self.model_dump()


class StreamEvent(BaseModel):
    """事件"""

    event: Optional[str] = Field(default=None, description="事件")

    def __contains__(self, item):
        """支持 in 操作符，检查某个键是否存在"""
        return item in self.__dict__ or item in self.model_dump()
