import json
from typing import List, Generator, Dict, Any, Optional, AsyncGenerator

from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse, 
    Output, Content, Usage, Action,
    StreamOutput, Delta
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
        import openai
        
        # 支持通过配置指定 api_key 和 base_url
        self.client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        self.async_client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    # ==========================================
    #         生命周期钩子实现
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将内部消息格式转换为 OpenAI 格式"""
        openai_msgs = []
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else msg.role
            
            content = msg.content
            if isinstance(content, list):
                # 转换 ContentPart 列表为 OpenAI 格式
                serialized_content = []
                for part in content:
                    part_type = getattr(part, "type", None) or (part.get("type") if isinstance(part, dict) else None)
                    
                    if part_type == "text":
                        serialized_content.append({"type": "text", "text": getattr(part, "text", "")})
                    elif part_type == "image":
                        # OpenAI 格式: {"type": "image_url", "image_url": {"url": "...", "detail": "high"}}
                        img_data = {}
                        if getattr(part, "image_url", None):
                            # 从 image_url 字典中提取 url 和可选的 detail
                            img_data = part.image_url.copy() if isinstance(part.image_url, dict) else {"url": part.image_url}
                        elif getattr(part, "data", None):
                            # 处理 Base64
                            mime = getattr(part, "media_type", "image/jpeg")
                            img_data = {"url": f"data:{mime};base64,{part.data}"}
                        
                        # 添加 detail 参数(如果提供)
                        detail = getattr(part, "detail", None)
                        if detail and "detail" not in img_data:
                            img_data["detail"] = detail
                            
                        serialized_content.append({"type": "image_url", "image_url": img_data})
                    elif part_type == "audio":
                        # OpenAI 不支持音频输入(除了 Whisper API)
                        import warnings
                        warnings.warn(
                            "OpenAI Chat Completions API 不支持音频输入。"
                            "如需音频转录,请使用 Whisper API。音频内容将被忽略。",
                            UserWarning
                        )
                        continue
                    elif part_type == "video":
                        # OpenAI 不支持视频输入
                        import warnings
                        warnings.warn(
                            "OpenAI Chat Completions API 不支持视频输入。视频内容将被忽略。",
                            UserWarning
                        )
                        continue
                    elif part_type == "action" or part_type == "outcome":
                        # OpenAI 不允许工具调用出现在 content 列表中
                        continue
                    elif hasattr(part, "model_dump"):
                        serialized_content.append(part.model_dump(exclude_none=True))
                    else:
                        serialized_content.append(part)
                content = serialized_content

            # 处理 Tool 角色消息 (OpenAI 要求 content 必须是字符串，且包含 tool_call_id)
            if role_val == "tool":
                if isinstance(msg.content, list):
                    # 提取 ToolResultPart 内容
                    text_parts = []
                    for part in msg.content:
                        if hasattr(part, "result"):
                            text_parts.append(str(part.result))
                        elif isinstance(part, dict):
                            text_parts.append(str(part.get("result", "")))
                    content = "\n".join(text_parts)
                else:
                    content = str(msg.content)

            m = {
                "role": role_val,
                "content": content
            }
            if msg.tool_id:
                m["tool_call_id"] = msg.tool_id
            
            # 处理 Assistant 的 tool_calls 字段
            if role_val == "assistant" and isinstance(msg.content, list):
                tool_calls = []
                for part in msg.content:
                    part_type = getattr(part, "type", None) or (part.get("type") if isinstance(part, dict) else None)
                    if part_type == "action":
                        tool_calls.append({
                            "id": getattr(part, "id", ""),
                            "type": "function",
                            "function": {
                                "name": getattr(part, "name", ""),
                                "arguments": json.dumps(part.arguments) if isinstance(getattr(part, "arguments", None), dict) else getattr(part, "arguments", "{}")
                            }
                        })
                if tool_calls:
                    m["tool_calls"] = tool_calls
                    # 如果只有工具调用，content 应为 None
                    has_text = any(isinstance(p, dict) and p.get("type") == "text" for p in content) if isinstance(content, list) else False
                    if not has_text:
                        m["content"] = None

            openai_msgs.append(m)
        return openai_msgs

    def _normalize_response(self, response: Any, model: str) -> Response:
        """将 OpenAI 响应归一化"""
        choice = response.choices[0]
        
        # 处理 Tool Calls
        actions = None
        if choice.message.tool_calls:
            actions = []
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except:
                    args = {"raw": tc.function.arguments} 
                actions.append(Action(id=tc.id, name=tc.function.name, arguments=args))

        content_obj = Content(text=choice.message.content)

        output = Output(
            content=content_obj,
            actions=actions,
            status=choice.finish_reason
        )

        usage = None
        if response.usage:
            usage = Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )

        return Response(output=output, model=response.model, usage=usage)

    def _normalize_stream_chunk(self, chunk: Any, model: str) -> StreamResponse:
        """将 OpenAI 流式碎片归一化"""
        if not chunk.choices:
            return StreamResponse(model=chunk.model)
            
        delta = chunk.choices[0].delta
        delta_obj = Delta(text=delta.content, reasoning=None)
        
        stream_output = StreamOutput(
            delta=delta_obj,
            start=None,
            end=chunk.choices[0].finish_reason
        )
        
        usage = None
        if getattr(chunk, "usage", None):
             usage = Usage(
                input_tokens=chunk.usage.prompt_tokens,
                output_tokens=chunk.usage.completion_tokens,
                total_tokens=chunk.usage.total_tokens
            )
        
        return StreamResponse(output=stream_output, model=chunk.model, usage=usage)

    def _convert_tools(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """将标准化工具转换为 OpenAI 格式"""
        openai_tools = []
        for t in tools:
            if hasattr(t, "model_dump"):
                # 如果是 ToolInfo 对象，确保输出 type="function" (DeepSeek 需要)
                openai_tools.append(t.model_dump(exclude_none=True))
            else:
                openai_tools.append(t)
        return openai_tools

    # ==========================================
    #         能力接口实现
    # ==========================================

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        
        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        response = self.client.chat.completions.create(
            model=model,
            messages=self._convert_messages(messages),
            **params
        )
        return self._normalize_response(response, model)

    def stream_chat(self, messages: List[Message], model: str, **kwargs) -> Generator[StreamResponse, None, None]:
        params = self._convert_params(model, **kwargs)
        
        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        stream = self.client.chat.completions.create(
            model=model,
            messages=self._convert_messages(messages),
            stream=True,
            **params
        )
        for chunk in stream:
            yield self._normalize_stream_chunk(chunk, model)

    # ==========================================
    #         异步能力接口实现
    # ==========================================

    async def async_chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        
        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        response = await self.async_client.chat.completions.create(
            model=model,
            messages=self._convert_messages(messages),
            **params
        )
        return self._normalize_response(response, model)

    async def async_stream_chat(self, messages: List[Message], model: str, **kwargs) -> AsyncGenerator[StreamResponse, None]:
        params = self._convert_params(model, **kwargs)
        
        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        stream = await self.async_client.chat.completions.create(
            model=model,
            messages=self._convert_messages(messages),
            stream=True,
            **params
        )
        async for chunk in stream:
            yield self._normalize_stream_chunk(chunk, model)
