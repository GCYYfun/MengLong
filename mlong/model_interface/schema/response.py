from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class MessageContent(BaseModel):
    """消息内容模型"""
    content: str = Field(description="生成的文本内容")
    reasoning_content: Optional[str] = Field(default=None, description="思考过程内容")

class Choice(BaseModel):
    """选择项模型"""
    message: MessageContent = Field(description="消息内容")
    index: Optional[int] = Field(default=0, description="选择项索引")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    choices: List[Choice] = Field(description="响应选项列表")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")
    usage: Optional[Dict[str, int]] = Field(default=None, description="token使用统计")

class StreamDelta(BaseModel):
    """流式响应增量内容"""
    content: Optional[str] = Field(default=None, description="增量文本内容")
    reasoning_content: Optional[str] = Field(default=None, description="增量思考过程内容")

class StreamChoice(BaseModel):
    """流式响应选择项"""
    delta: StreamDelta = Field(description="增量内容")
    index: int = Field(default=0, description="选择项索引")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")

class ChatStreamResponse():
    """流式聊天响应模型"""
    def __init__(self):
        self.stream = None
    
class EmbedResponse(BaseModel):
    """嵌入响应模型"""
    embeddings: List[List[float]] = Field(description="嵌入向量列表")
    texts: Optional[List[str]] = Field(default=None, description="文本数据列表")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")