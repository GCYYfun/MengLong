from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# ======== 基础模型 ========


class Content(BaseModel):
    """消息内容模型"""

    text_content: str = Field(description="生成的文本内容")
    reasoning_content: Optional[str] = Field(default=None, description="思考过程内容")


# class Choice(BaseModel):
#     """选择项模型"""
#     message: MessageContent = Field(description="消息内容")
#     index: Optional[int] = Field(default=0, description="选择项索引")
#     finish_reason: Optional[str] = Field(default=None, description="结束原因")


class Function(BaseModel):
    """函数调用模型"""

    name: str = Field(description="函数名称")
    arguments: str = Field(default=None, description="函数参数")  # 函数参数信息


class ToolCall(BaseModel):
    """工具调用模型"""

    id: str = Field(description="工具调用ID")
    type: str = Field(description="工具调用类型")
    function: Optional[Function] = Field(
        default=None, description="函数调用信息"
    )  # 可能包含函数名称和参数等信息


class Message(BaseModel):
    """消息模型"""

    content: Content = Field(default=None, description="消息内容")
    tool_calls: Optional[List[ToolCall]] = Field(
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


# ======== 流式响应模型 ========


class ContentDelta(BaseModel):
    """流式响应增量内容"""

    text_content: Optional[str] = Field(default=None, description="增量文本内容")
    reasoning_content: Optional[str] = Field(
        default=None, description="增量思考过程内容"
    )


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
