from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# ======== 基础模型 ========

"""
ChatResponse:
    message: 
        content: 
            text: Optional[str]
            reasoning: Optional[str]
        tool_descriptions: 
            [
                {
                    "id": "string",
                    "type": "function",
                    "name": "string",
                    "arguments": {
                        "location": "string",
                        "unit": "string"
                    }
                }
            ]
        finish_reason: Optional[str]
    model: Optional[str]
    usage: 
        input_tokens: int
        output_tokens: int
        total_tokens: int
"""


class Content(BaseModel):
    """消息内容模型"""

    text: Optional[str] = Field(default=None, description="生成的文本内容")
    reasoning: Optional[str] = Field(default=None, description="思考过程内容")


class ToolDesc(BaseModel):
    """工具调用模型"""

    id: str = Field(description="工具调用ID")
    type: str = Field(description="工具调用类型")
    name: str = Field(description="函数名称")
    arguments: Union[str, dict] = Field(
        default=None, description="函数参数"
    )  # 函数参数信息


class Message(BaseModel):
    """消息模型"""

    content: Content = Field(default=None, description="消息内容")
    tool_descriptions: Optional[List[ToolDesc]] = Field(
        default=None, description="工具调用列表"
    )
    finish_reason: Optional[str] = Field(default=None, description="结束原因")


class Usage(BaseModel):
    """token使用统计模型"""

    input_tokens: int = Field(description="提示token数量")
    output_tokens: int = Field(description="生成token数量")
    total_tokens: int = Field(description="总token数量")


class ChatResponse(BaseModel):
    """聊天响应模型"""

    message: Message = Field(description="响应选项列表")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")
    usage: Optional[Usage] = Field(default=None, description="token使用统计")

    @property
    def text(self) -> Optional[str]:
        """获取响应文本内容"""
        return (
            self.message.content.text if self.message and self.message.content else None
        )


# ======== 流式响应模型 ========

"""
ChatStreamResponse
    message: 
        delta: 
            text: Optional[str]
            reasoning: Optional[str]
        start_reason: Optional[str]
        finish_reason: Optional[str]
    model: Optional[str]
    usage: 
        input_tokens: int
        output_tokens: int
        total_tokens: int
"""


class ContentDelta(BaseModel):
    """流式响应增量内容"""

    text: Optional[str] = Field(default=None, description="增量文本内容")
    reasoning: Optional[str] = Field(default=None, description="增量思考过程内容")


class StreamMessage(BaseModel):
    """流式响应选择项"""

    delta: ContentDelta = Field(default=None, description="增量内容")
    start_reason: Optional[str] = Field(default=None, description="开始原因")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")


class ChatStreamResponse(BaseModel):
    """流式聊天响应模型"""

    message: StreamMessage = Field(description="流式响应选择项")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")
    usage: Optional[Usage] = Field(default=None, description="token使用统计")


# ======== 嵌入响应模型 ========
class EmbedResponse(BaseModel):
    """嵌入响应模型"""

    embeddings: List[List[float]] = Field(description="嵌入向量列表")
    texts: Optional[List[str]] = Field(default=None, description="文本数据列表")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")
