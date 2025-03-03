from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class ThinkingConfig(BaseModel):
    """思考模式配置"""
    type: str = Field(default="disabled", description="思考模式类型，enabled或disabled")

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(description="消息角色，可以是user、assistant或system")
    content: str = Field(description="消息内容")

class InferenceConfig(BaseModel):
    """推理配置参数"""
    maxTokens: Optional[int] = Field(default=None, description="最大生成token数")
    temperature: Optional[float] = Field(default=None, description="采样温度")
    topP: Optional[float] = Field(default=None, description="核采样概率")
    stopSequences: Optional[List[str]] = Field(default=None, description="停止序列")

class ChatRequest(BaseModel):
    """聊天请求模型"""
    model: str = Field(description="模型标识符")
    messages: List[ChatMessage] = Field(description="聊天消息列表")
    stream: bool = Field(default=False, description="是否使用流式模式")
    thinking: ThinkingConfig = Field(default_factory=ThinkingConfig, description="思考模式配置")
    inference_config: Optional[InferenceConfig] = Field(default=None, description="推理配置")
    additional_fields: Optional[Dict[str, Any]] = Field(default=None, description="额外的模型请求字段")