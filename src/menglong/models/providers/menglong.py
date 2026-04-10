import json
from typing import List, Generator, Dict, Any, Optional, AsyncGenerator
import os
import httpx

from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message,
    Response,
    StreamResponse,
    Output,
    Content,
    Usage,
    Action,
    StreamOutput,
    Delta,
)
from menglong.utils.config.config_type import ProviderConfig


@ProviderRegistry.register("menglong")
class MengLongProvider(BaseProvider):
    """
    MengLong (朦胧) Provider
    使用纯 httpx 实现，支持同步和异步操作。
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

        # 设置默认 base_url
        if not config.base_url:
            config.base_url = "https://localhost:8000"

        # 允许从环境变量读取 key
        if not config.api_key:
            config.api_key = os.getenv("MENGLONG_API_KEY")

        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key

        # 初始化同步和异步客户端
        self.client = httpx.Client(
            base_url=self.base_url, headers=self._get_headers(), timeout=60.0
        )
        self.async_client = httpx.AsyncClient(
            base_url=self.base_url, headers=self._get_headers(), timeout=60.0
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ==========================================
    #         生命周期钩子实现
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将内部消息格式转换为 MengLong API 格式"""
        menglong_msgs = []
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else msg.role

            content = msg.content
            if isinstance(content, list):
                # 转换 ContentPart 列表
                serialized_content = []
                for part in content:
                    if hasattr(part, "model_dump"):
                        serialized_content.append(part.model_dump(exclude_none=True))
                    elif isinstance(part, dict):
                        serialized_content.append(part)
                    else:
                        serialized_content.append({"type": "text", "text": str(part)})
                content = serialized_content

            m = {"role": role_val, "content": content}
            if hasattr(msg, "tool_id") and msg.tool_id:
                m["tool_id"] = msg.tool_id

            menglong_msgs.append(m)
        return menglong_msgs

    def _normalize_response(
        self, response_data: Dict[str, Any], model: str
    ) -> Response:
        """将 MengLong API 响应归一化为 SDK Response 对象"""
        # MengLong API 响应结构与 SDK schemas 一致，直接解析
        return Response.model_validate(response_data)

    def _normalize_stream_chunk(
        self, chunk_data: Dict[str, Any], model: str
    ) -> StreamResponse:
        """将 MengLong API 流式碎片归一化为 SDK StreamResponse 对象"""
        # MengLong API 响应结构与 SDK schemas 一致，直接解析
        return StreamResponse.model_validate(chunk_data)

    def _convert_tools(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """将标准化工具转换为 MengLong API 格式"""
        menglong_tools = []
        for t in tools:
            if hasattr(t, "model_dump"):
                menglong_tools.append(t.model_dump(exclude_none=True))
            elif isinstance(t, dict):
                menglong_tools.append(t)
            else:
                menglong_tools.append(t)
        return menglong_tools

    # ==========================================
    #         能力接口实现 (同步)
    # ==========================================

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        """同步聊天接口"""
        params = self._convert_params(model, **kwargs)

        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            **params,
        }

        response = self.client.post("/chat", json=payload)
        response.raise_for_status()

        return self._normalize_response(response.json(), model)

    def stream_chat(
        self, messages: List[Message], model: str, **kwargs
    ) -> Generator[StreamResponse, None, None]:
        """同步流式聊天接口"""
        params = self._convert_params(model, **kwargs)

        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "stream": True,
            **params,
        }

        with self.client.stream("POST", "/chat", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.strip():
                    # 处理 SSE 格式: "data: {...}"
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除 "data: " 前缀
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            yield self._normalize_stream_chunk(chunk_data, model)
                        except json.JSONDecodeError:
                            continue

    # ==========================================
    #         能力接口实现 (异步)
    # ==========================================

    async def async_chat(
        self, messages: List[Message], model: str, **kwargs
    ) -> Response:
        """异步聊天接口"""
        params = self._convert_params(model, **kwargs)

        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            **params,
        }

        response = await self.async_client.post("/chat", json=payload)
        response.raise_for_status()

        return self._normalize_response(response.json(), model)

    async def async_stream_chat(
        self, messages: List[Message], model: str, **kwargs
    ) -> AsyncGenerator[StreamResponse, None]:
        """异步流式聊天接口"""
        params = self._convert_params(model, **kwargs)

        if "tools" in params:
            params["tools"] = self._convert_tools(params["tools"])

        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "stream": True,
            **params,
        }

        async with self.async_client.stream("POST", "/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    # 处理 SSE 格式: "data: {...}"
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除 "data: " 前缀
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            yield self._normalize_stream_chunk(chunk_data, model)
                        except json.JSONDecodeError:
                            continue

    def __del__(self):
        """清理资源"""
        try:
            self.client.close()
        except:
            pass
