import json
import warnings
from typing import List, Generator, Dict, Any, Optional, AsyncGenerator

import openai

from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse,
    Output, Content, Usage, Action,
    StreamOutput, Delta,
)
from menglong.utils.config.config_type import ProviderConfig


@ProviderRegistry.register("openai")
class OpenAIProvider(BaseProvider):
    """
    OpenAI Provider 适配器。
    实现 BaseProvider 协议，对接 OpenAI Chat Completions API。
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=config.api_key, base_url=config.base_url)
        self.async_client = openai.AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    # ==========================================
    #         消息转换（私有辅助方法）
    # ==========================================

    @staticmethod
    def _get_part_type(part) -> Optional[str]:
        """统一获取 ContentPart 的 type 字段"""
        return getattr(part, "type", None) or (part.get("type") if isinstance(part, dict) else None)

    def _serialize_content_parts(self, parts: list) -> list:
        """将 ContentPart 列表序列化为 OpenAI 兼容格式（跳过工具相关和不支持的类型）"""
        result = []
        for part in parts:
            part_type = self._get_part_type(part)

            if part_type == "text":
                result.append({"type": "text", "text": getattr(part, "text", "")})

            elif part_type == "image":
                if getattr(part, "image_url", None):
                    img_data = part.image_url.copy() if isinstance(part.image_url, dict) else {"url": part.image_url}
                elif getattr(part, "data", None):
                    mime = getattr(part, "media_type", "image/jpeg")
                    img_data = {"url": f"data:{mime};base64,{part.data}"}
                else:
                    img_data = {}
                detail = getattr(part, "detail", None)
                if detail and "detail" not in img_data:
                    img_data["detail"] = detail
                result.append({"type": "image_url", "image_url": img_data})

            elif part_type == "audio":
                warnings.warn(
                    "OpenAI Chat Completions API 不支持音频输入。如需音频转录，请使用 Whisper API。音频内容将被忽略。",
                    UserWarning, stacklevel=3,
                )

            elif part_type == "video":
                warnings.warn(
                    "OpenAI Chat Completions API 不支持视频输入。视频内容将被忽略。",
                    UserWarning, stacklevel=3,
                )

            elif part_type in ("action", "outcome"):
                # 工具相关 part 不放入 content 列表
                pass

            elif hasattr(part, "model_dump"):
                result.append(part.model_dump(exclude_none=True))

            else:
                result.append(part)

        return result

    def _serialize_tool_msg(self, msg: Message) -> Dict[str, Any]:
        """将 role=tool 的消息序列化为 OpenAI 格式，从 Outcome.id 提取 tool_call_id"""
        tool_call_id = None
        text_parts = []

        if isinstance(msg.content, list):
            for part in msg.content:
                if hasattr(part, "result"):
                    text_parts.append(str(part.result))
                    if tool_call_id is None and getattr(part, "id", None) is not None:
                        tool_call_id = str(part.id)
                elif isinstance(part, dict):
                    text_parts.append(str(part.get("result", "")))
                    if tool_call_id is None and part.get("id") is not None:
                        tool_call_id = str(part["id"])
            content = "\n".join(text_parts)
        else:
            content = str(msg.content)

        m = {"role": "tool", "content": content}
        if tool_call_id:
            m["tool_call_id"] = tool_call_id
        return m

    def _serialize_assistant_msg(self, m: Dict[str, Any], content_parts: list, raw_parts: list) -> Dict[str, Any]:
        """补充 assistant 消息的 tool_calls 字段，并在全为工具调用时将 content 置 None"""
        tool_calls = [
            {
                "id": getattr(part, "id", ""),
                "type": "function",
                "function": {
                    "name": getattr(part, "name", ""),
                    "arguments": (
                        json.dumps(part.arguments)
                        if isinstance(getattr(part, "arguments", None), dict)
                        else getattr(part, "arguments", "{}")
                    ),
                },
            }
            for part in raw_parts
            if self._get_part_type(part) == "action"
        ]
        if tool_calls:
            m["tool_calls"] = tool_calls
            has_text = any(
                isinstance(p, dict) and p.get("type") == "text"
                for p in content_parts
            ) if isinstance(content_parts, list) else False
            if not has_text:
                m["content"] = None
        return m

    # ==========================================
    #         主转换方法
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将内部消息格式转换为 OpenAI 格式"""
        openai_msgs = []
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else msg.role

            # tool 消息单独处理（需提取 tool_call_id）
            if role_val == "tool":
                openai_msgs.append(self._serialize_tool_msg(msg))
                continue

            # 序列化 content
            if isinstance(msg.content, list):
                content = self._serialize_content_parts(msg.content)
            else:
                content = msg.content

            m = {"role": role_val, "content": content}

            # assistant 消息追加 tool_calls
            if role_val == "assistant" and isinstance(msg.content, list):
                m = self._serialize_assistant_msg(m, content, msg.content)

            openai_msgs.append(m)
        return openai_msgs

    def _convert_tools(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """将标准化工具转换为 OpenAI 格式"""
        return [t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else t for t in tools]

    # ==========================================
    #         响应归一化（私有辅助方法）
    # ==========================================

    @staticmethod
    def _normalize_usage(usage_obj) -> Optional[Usage]:
        """将 OpenAI usage 对象归一化"""
        if not usage_obj:
            return None
        return Usage(
            input_tokens=usage_obj.prompt_tokens,
            output_tokens=usage_obj.completion_tokens,
            total_tokens=usage_obj.total_tokens,
        )

    def _normalize_response(self, response: Any, model: str) -> Response:
        """将 OpenAI 响应归一化"""
        choice = response.choices[0]

        actions = None
        if choice.message.tool_calls:
            actions = []
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {"raw": tc.function.arguments}
                actions.append(Action(id=tc.id, name=tc.function.name, arguments=args))

        output = Output(
            content=Content(text=choice.message.content),
            actions=actions,
            status=choice.finish_reason,
        )
        return Response(output=output, model=response.model, usage=self._normalize_usage(response.usage))

    def _normalize_stream_chunk(self, chunk: Any, model: str) -> StreamResponse:
        """将 OpenAI 流式碎片归一化"""
        if not chunk.choices:
            return StreamResponse(model=chunk.model)

        delta = chunk.choices[0].delta
        stream_output = StreamOutput(
            delta=Delta(text=delta.content),
            end=chunk.choices[0].finish_reason,
        )
        return StreamResponse(output=stream_output, model=chunk.model, usage=self._normalize_usage(getattr(chunk, "usage", None)))

    # ==========================================
    #         能力接口（公开方法）
    # ==========================================

    def _prepare_params(self, model: str, **kwargs) -> Dict[str, Any]:
        """预处理请求参数，统一转换 tools"""
        params = self._convert_params(model, **kwargs)
        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])
        return params

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._prepare_params(model, **kwargs)
        response = self.client.chat.completions.create(
            model=model, messages=self._convert_messages(messages), **params
        )
        return self._normalize_response(response, model)

    def stream_chat(self, messages: List[Message], model: str, **kwargs) -> Generator[StreamResponse, None, None]:
        params = self._prepare_params(model, **kwargs)
        stream = self.client.chat.completions.create(
            model=model, messages=self._convert_messages(messages), stream=True, **params
        )
        for chunk in stream:
            yield self._normalize_stream_chunk(chunk, model)

    async def async_chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._prepare_params(model, **kwargs)
        response = await self.async_client.chat.completions.create(
            model=model, messages=self._convert_messages(messages), **params
        )
        return self._normalize_response(response, model)

    async def async_stream_chat(self, messages: List[Message], model: str, **kwargs) -> AsyncGenerator[StreamResponse, None]:
        params = self._prepare_params(model, **kwargs)
        stream = await self.async_client.chat.completions.create(
            model=model, messages=self._convert_messages(messages), stream=True, **params
        )
        async for chunk in stream:
            yield self._normalize_stream_chunk(chunk, model)
