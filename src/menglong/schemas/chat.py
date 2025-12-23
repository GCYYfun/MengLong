"""
聊天模版(Chat Template)下的相关的基础数据结构
Chat Template 是指目前Instruction模型所遵循的的基础模版，定义了消息的角色、内容格式等。(Instruction 模型是基于指令的交互模型，如GPT-5、Claude4.5等。
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


# =========================
#         Request
# =========================

class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ContentPart(BaseModel):
    """内容片段基类"""
    type: str

class TextPart(ContentPart):
    """文本片段"""
    type: str = "text"
    text: str

class ImagePart(ContentPart):
    """图片片段"""
    type: str = "image"
    image_url: Optional[Dict[str, str]] = None  # {"url": "..."}
    data: Optional[str] = None # Base64
    media_type: Optional[str] = None

class DocumentPart(ContentPart):
    """文档片段 (如 PDF)"""
    type: str = "document"
    data: str # Base64
    media_type: str = "application/pdf"

class ToolCallPart(ContentPart):
    """工具调用片段"""
    type: str = "tool_use"
    id: str
    name: str
    arguments: Dict[str, Any]

class ToolResultPart(ContentPart):
    """工具结果片段"""
    type: str = "tool_result"
    tool_use_id: str
    content: Optional[str] = None
    is_error: bool = False


class Action(BaseModel):
    """动作描述 (用于 Response 输出)"""
    id: str = ""
    name: str = ""
    arguments: Optional[Dict[str, Any]] = None


class Outcome(BaseModel):
    """工具处理结果 (用于 Request 输入)"""
    id: str
    result: str


class Message(BaseModel):
    """聊天消息"""
    role: MessageRole
    content: Optional[Union[str, List[Union[ContentPart, Dict[str, Any]]]]] = None
    outcomes: Optional[List[Outcome]] = None
    name: Optional[str] = None
    tool_id: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class Context(BaseModel):
    """
    Managed Context / 历史对话容器
    支持辅助管理函数、统计与快捷操作。
    """
    messages: List[Message] = Field(default_factory=list)

    def add(self, message: Union[Message, Dict[str, Any], str]):
        """推荐使用快捷函数 User(), Assistant() 等生成的消息对象"""
        from menglong.models.model import Model # 延迟导入
        # 我们在这里做简单的归一化逻辑，更复杂的交由 Model._ensure_messages
        if isinstance(message, str):
             self.messages.append(Message(role=MessageRole.USER, content=message))
        elif isinstance(message, dict):
             self.messages.append(Message(**message))
        else:
             self.messages.append(message)
        return self

    def user(self, content: Union[str, List], **kwargs):
        self.add(User(content, **kwargs))
        return self

    def assistant(self, content: Optional[str] = None, **kwargs):
        self.add(Assistant(content, **kwargs))
        return self

    def system(self, content: str):
        self.add(System(content))
        return self

    def tool(self, tool_id: str, content: str, **kwargs):
        self.add(Tool(tool_id, content, **kwargs))
        return self

    @property
    def last(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None

    def __iter__(self):
        return iter(self.messages)

    def __len__(self):
        return len(self.messages)

    def __getitem__(self, item):
        return self.messages[item]


# =========================
#         Shortcuts
# =========================

def User(content: Union[str, List[Any]], **kwargs) -> Message:
    """
    快捷构造 User 消息。
    支持智能识别 kwargs 中的 image / document / pdf 等。
    """
    if isinstance(content, str) and not kwargs:
        return Message(role=MessageRole.USER, content=content)
    
    parts = []
    if isinstance(content, str):
        parts.append(TextPart(text=content))
    elif isinstance(content, list):
        # 已经是 Part 列表，直接透传或包装字典
        for item in content:
            if isinstance(item, dict):
                parts.append(item) # Provider 会处理
            else:
                parts.append(item)

    # 处理快捷多模态参数
    if "image" in kwargs:
        val = kwargs["image"]
        if isinstance(val, str) and (val.startswith("http") or "/" in val):
             parts.append(ImagePart(image_url={"url": val}))
        else:
             parts.append(ImagePart(data=val))
             
    if "document" in kwargs or "pdf" in kwargs:
        val = kwargs.get("document") or kwargs.get("pdf")
        parts.append(DocumentPart(data=val))

    return Message(role=MessageRole.USER, content=parts)

def Assistant(content: Optional[str] = None, tool_calls: Optional[List[Dict]] = None) -> Message:
    """快捷构造 Assistant 消息，支持工具调用负载"""
    if not tool_calls:
        return Message(role=MessageRole.ASSISTANT, content=content)
    
    parts = []
    if content:
        parts.append(TextPart(text=content))
    
    for tc in tool_calls:
        parts.append(ToolCallPart(
            id=tc.get("id", ""),
            name=tc.get("name", ""),
            arguments=tc.get("arguments", {})
        ))
    return Message(role=MessageRole.ASSISTANT, content=parts)

def System(content: str) -> Message:
    """快捷构造 System 消息"""
    return Message(role=MessageRole.SYSTEM, content=content)

def Tool(tool_id: str, content: str, **kwargs) -> Message:
    """
    快捷构造 Tool 结果消息。
    部分 Provider 内部会将其映射为 user 或特定 role。
    """
    parts = [ToolResultPart(tool_use_id=tool_id, content=content, is_error=kwargs.get("is_error", False))]
    return Message(role=MessageRole.TOOL, content=parts, tool_id=tool_id)


# =========================
#         Response
# =========================

class Content(BaseModel):
    """消息内容 (Response)"""
    text: Optional[str] = None
    reasoning: Optional[str] = None
    
class Usage(BaseModel):
    """token使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

class Output(BaseModel):
    """响应消息体"""
    content: Optional[Content] = None
    actions: Optional[List[Action]] = None
    status: Optional[str] = None

class Response(BaseModel):
    output: Optional[Output] = None
    model: Optional[str] = None
    usage: Optional[Usage] = None

    @property
    def text(self) -> Optional[str]:
        return self.output.content.text if self.output and self.output.content else None


# ======== 流式响应模型 ========

class Delta(BaseModel):
    text: Optional[str] = None
    reasoning: Optional[str] = None

class StreamOutput(BaseModel):
    delta: Optional[Delta] = None
    start: Optional[str] = None
    end: Optional[str] = None

class StreamResponse(BaseModel):
    output: Optional[StreamOutput] = None
    model: Optional[str] = None
    usage: Optional[Usage] = None
