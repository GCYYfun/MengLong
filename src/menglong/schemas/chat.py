"""
聊天模版(Chat Template)下的相关的基础数据结构
Chat Template 是指目前Instruction模型所遵循的的基础模版，定义了消息的角色、内容格式等。(Instruction 模型是基于指令的交互模型，如GPT-5、Claude4.5等。
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path

from menglong.utils.multimodal_utils import (
    load_image_from_path,
    load_document_from_path,
    load_audio_from_path,
    load_video_from_path,
)

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
    """图片片段

    支持三种输入方式:
    1. URL: image_url={"url": "https://..."}
    2. Base64: data="base64_string", media_type="image/jpeg"
    3. 本地文件路径: 通过 User() 函数自动处理

    可选参数:
    - detail: OpenAI 特有参数,控制图片分析精度 ("low", "high", "auto")
    """

    type: str = "image"
    image_url: Optional[Dict[str, Any]] = None  # {"url": "...", "detail": "high"}
    data: Optional[str] = None  # Base64
    media_type: Optional[str] = None  # e.g., "image/jpeg", "image/png"
    detail: Optional[str] = None  # OpenAI specific: "low", "high", "auto"


class DocumentPart(ContentPart):
    """文档片段 (如 PDF)

    支持两种输入方式:
    1. Base64: data="base64_string"
    2. 本地文件路径: 通过 User() 函数自动处理
    """

    type: str = "document"
    data: str  # Base64
    media_type: str = "application/pdf"


class AudioPart(ContentPart):
    """音频片段

    支持三种输入方式:
    1. URL: audio_url="https://..."
    2. Base64: data="base64_string", media_type="audio/mp3"
    3. 本地文件路径: 通过 User() 函数自动处理

    常见格式: mp3, wav, m4a, ogg, flac
    注意: 不是所有模型都支持音频输入,主要支持 Gemini 3
    """

    type: str = "audio"
    audio_url: Optional[str] = None
    data: Optional[str] = None  # Base64
    media_type: Optional[str] = None  # e.g., "audio/mp3", "audio/wav"


class VideoPart(ContentPart):
    """视频片段

    支持三种输入方式:
    1. URL: video_url="https://..."
    2. Base64: data="base64_string", media_type="video/mp4"
    3. 本地文件路径: 通过 User() 函数自动处理

    常见格式: mp4, mov, avi, webm
    注意: 不是所有模型都支持视频输入,主要支持 Gemini 3
    """

    type: str = "video"
    video_url: Optional[str] = None
    data: Optional[str] = None  # Base64
    media_type: Optional[str] = None  # e.g., "video/mp4", "video/mov"


class Action(ContentPart):
    """动作描述 (用于 Response 输出)"""

    type: str = "action"
    id: Any = None
    index: Optional[int] = None  # 用于流式合并
    name: str = ""
    arguments: Optional[Union[Dict[str, Any], str]] = None


class Outcome(ContentPart):
    """工具处理结果 (用于 Request 输入)"""

    type: str = "outcome"
    id: Any
    name: Optional[str] = None
    result: str


class ThinkingPart(ContentPart):
    """思维/推理过程片段"""

    type: str = "thinking"
    thinking: str


class Message(BaseModel):
    """聊天消息"""

    role: MessageRole
    content: Optional[
        Union[
            str,
            List[
                Union[
                    Action,
                    Outcome,
                    VideoPart,
                    AudioPart,
                    DocumentPart,
                    ImagePart,
                    TextPart,
                    ThinkingPart,
                    Dict[str, Any],
                ]
            ],
        ]
    ] = None
    # outcomes: Optional[List[Outcome]] = None
    # tool_id: Any = None

    model_config = ConfigDict(use_enum_values=True)


class Context(BaseModel):
    """
    Managed Context / 历史对话容器
    支持辅助管理函数、统计与快捷操作。
    """

    messages: List[Message] = Field(default_factory=list)

    def add(self, message: Union[Message, Dict[str, Any], str]):
        """推荐使用快捷函数 User(), Assistant() 等生成的消息对象"""

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

    def __iter__(self) -> Any:  # type: ignore
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

    支持多模态输入:
    - image: 图片 (URL, 本地路径, 或 Base64)
    - document/pdf: 文档 (本地路径或 Base64)
    - audio: 音频 (URL, 本地路径, 或 Base64)
    - video: 视频 (URL, 本地路径, 或 Base64)

    可选参数:
    - detail: 图片分析精度 (OpenAI 特有, "low"/"high"/"auto")

    示例:
        User("描述这张图片", image="https://example.com/image.jpg")
        User("分析文档", document="/path/to/file.pdf")
        User("转录音频", audio="/path/to/audio.mp3")
        User("描述视频", video="https://example.com/video.mp4")
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
                parts.append(item)  # Provider 会处理
            else:
                parts.append(item)

    # 处理快捷多模态参数
    if "image" in kwargs:
        val = kwargs["image"]
        detail = kwargs.get("detail")  # OpenAI 特有参数

        if isinstance(val, str):
            if val.startswith("http://") or val.startswith("https://"):
                # URL 格式
                image_url = {"url": val}
                if detail:
                    image_url["detail"] = detail
                parts.append(ImagePart(image_url=image_url))
            else:
                # 本地文件路径或 Base64
                if Path(val).exists():
                    # 本地文件,需要加载并编码
                    data, media_type = load_image_from_path(val)
                    parts.append(
                        ImagePart(data=data, media_type=media_type, detail=detail)
                    )
                else:
                    # 假设是 Base64
                    parts.append(ImagePart(data=val, detail=detail))
        else:
            # 直接是 Base64
            parts.append(ImagePart(data=val, detail=detail))

    if "document" in kwargs or "pdf" in kwargs:
        val = kwargs.get("document") or kwargs.get("pdf")
        if isinstance(val, str):
            if Path(val).exists():
                data, media_type = load_document_from_path(val)
                parts.append(DocumentPart(data=data, media_type=media_type))
            else:
                # 假设是 Base64
                parts.append(DocumentPart(data=val))
        else:
            parts.append(DocumentPart(data=val))

    if "audio" in kwargs:
        val = kwargs["audio"]
        if isinstance(val, str):
            if val.startswith("http://") or val.startswith("https://"):
                # URL 格式
                parts.append(AudioPart(audio_url=val))
            else:
                # 本地文件路径或 Base64
                if Path(val).exists():
                    # 本地文件,需要加载并编码
                    data, media_type = load_audio_from_path(val)
                    parts.append(AudioPart(data=data, media_type=media_type))
                else:
                    # 假设是 Base64
                    parts.append(AudioPart(data=val))
        else:
            parts.append(AudioPart(data=val))

    if "video" in kwargs:
        val = kwargs["video"]
        if isinstance(val, str):
            if val.startswith("http://") or val.startswith("https://"):
                # URL 格式
                parts.append(VideoPart(video_url=val))
            else:
                # 本地文件路径或 Base64
                if Path(val).exists():
                    # 本地文件,需要加载并编码
                    data, media_type = load_video_from_path(val)
                    parts.append(VideoPart(data=data, media_type=media_type))
                else:
                    # 假设是 Base64
                    parts.append(VideoPart(data=val))
        else:
            parts.append(VideoPart(data=val))

    return Message(role=MessageRole.USER, content=parts)


def Assistant(
    content: Optional[str] = None,
    actions: Optional[List[Union[Dict[str, Any], Action]]] = None,
    reasoning: Optional[str] = None,
) -> Message:
    """快捷构造 Assistant 消息，支持工具调用负载与思维链"""
    if not actions and not reasoning:
        return Message(role=MessageRole.ASSISTANT, content=content)

    parts = []
    if content:
        parts.append(TextPart(text=content))

    if reasoning:
        parts.append(ThinkingPart(thinking=reasoning))

    if actions:
        for action in actions:
            if isinstance(action, dict):
                # 处理字典类型
                parts.append(
                    Action(
                        id=action.get("id"),
                        name=action.get("name"),
                        arguments=action.get("arguments"),
                    )
                )
            else:
                # 处理对象类型 (Action 或其他带属性的对象)
                parts.append(
                    Action(
                        id=getattr(action, "id", None),
                        name=getattr(action, "name", ""),
                        arguments=getattr(action, "arguments", None),
                    )
                )
    return Message(role=MessageRole.ASSISTANT, content=parts)


def System(content: str) -> Message:
    """快捷构造 System 消息"""
    return Message(role=MessageRole.SYSTEM, content=content)


def Tool(tool_id: Any, content: str, **kwargs) -> Message:
    """
    快捷构造 Tool 结果消息。
    tool_id 存储在 Outcome.id 中，Provider 在转换时从这里读取 tool_call_id。
    部分 Provider 内部会将其映射为 user 或特定 role。
    """
    parts = [
        Outcome(
            id=tool_id,
            name=kwargs.get("name"),
            result=content,
        )
    ]
    return Message(
        role=MessageRole.TOOL,
        content=parts,
    )


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

    @property
    def tool_calls(self) -> Optional[List[Action]]:
        """快捷获取工具调用列表 (Alias for output.actions)"""
        return self.output.actions if self.output else None


# ======== 流式响应模型 ========


class Delta(BaseModel):
    text: Optional[str] = None
    reasoning: Optional[str] = None
    actions: Optional[List[Action]] = None


class StreamOutput(BaseModel):
    delta: Optional[Delta] = None
    start: Optional[str] = None
    end: Optional[str] = None


class StreamResponse(BaseModel):
    output: Optional[StreamOutput] = None
    model: Optional[str] = None
    usage: Optional[Usage] = None
