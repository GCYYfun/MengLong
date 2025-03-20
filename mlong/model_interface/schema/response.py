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

class Message(BaseModel):
    """消息模型"""
    content: Content = Field(description="消息内容")
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
    reasoning_content: Optional[str] = Field(default=None, description="增量思考过程内容")

class StreamMessage(BaseModel):
    """流式响应选择项"""
    delta: ContentDelta = Field(description="增量内容")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")

class ChatStreamResponse(BaseModel):
    """流式聊天响应模型"""
    message: StreamMessage = Field(description="流式响应选择项")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")

# ======== 嵌入响应模型 ========
class EmbedResponse(BaseModel):
    """嵌入响应模型"""
    embeddings: List[List[float]] = Field(description="嵌入向量列表")
    texts: Optional[List[str]] = Field(default=None, description="文本数据列表")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")