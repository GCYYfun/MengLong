from typing import List, Generator, Dict, Any, Optional, Union, AsyncGenerator
import os
from anthropic import Anthropic, AnthropicBedrock, AsyncAnthropic, AsyncAnthropicBedrock

from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse, 
    Output, Content, Usage, Action,
    StreamOutput, Delta
)
from menglong.utils.config.config_type import ProviderConfig

@ProviderRegistry.register("anthropic")
class AnthropicProvider(BaseProvider):
    """
    Unified Anthropic Provider
    内部自动识别并切换 Native (Anthropic API) 与 Bedrock (AWS) 客户端。
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._native_client = None
        self._bedrock_client = None
        self._async_native_client = None
        self._async_bedrock_client = None

    def _get_client(self, model: str) -> Union[Anthropic, AnthropicBedrock]:
        """
        根据模型 ID 智能识别应使用的客户端类。
        Bedrock 模型 ID 通常包含 'anthropic.' 且可能有 'us.' 或 'global.' 前缀。
        Native 模型 ID 通常是 'claude-x-y-...'
        """
        # 判断标准：包含 anthropic. 或者以 us./global. 开头
        is_bedrock = "anthropic." in model or model.startswith(("us.", "global."))
        
        if is_bedrock:
            if not self._bedrock_client:
                region = getattr(self.config, "region", None) or os.getenv("AWS_REGION", "us-west-2")
                # 支持 AWS 凭证透传
                aws_access_key = getattr(self.config, "aws_access_key", os.getenv("AWS_ACCESS_KEY_ID"))
                aws_secret_key = getattr(self.config, "aws_secret_key", os.getenv("AWS_SECRET_ACCESS_KEY"))
                
                self._bedrock_client = AnthropicBedrock(
                    aws_access_key=aws_access_key,
                    aws_secret_key=aws_secret_key,
                    aws_region=region
                )
            return self._bedrock_client
        else:
            if not self._native_client:
                api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("Anthropic API key is missing for native call.")
                self._native_client = Anthropic(api_key=api_key, base_url=self.config.base_url)
            return self._native_client
    
    def _get_async_client(self, model: str) -> Union[AsyncAnthropic, AsyncAnthropicBedrock]:
        """
        根据模型 ID 智能识别应使用的异步客户端类。
        """
        is_bedrock = "anthropic." in model or model.startswith(("us.", "global."))
        
        if is_bedrock:
            if not self._async_bedrock_client:
                region = getattr(self.config, "region", None) or os.getenv("AWS_REGION", "us-west-1")
                aws_access_key = getattr(self.config, "aws_access_key", os.getenv("AWS_ACCESS_KEY_ID"))
                aws_secret_key = getattr(self.config, "aws_secret_key", os.getenv("AWS_SECRET_ACCESS_KEY"))
                
                self._async_bedrock_client = AsyncAnthropicBedrock(
                    aws_access_key=aws_access_key,
                    aws_secret_key=aws_secret_key,
                    aws_region=region
                )
            return self._async_bedrock_client
        else:
            if not self._async_native_client:
                api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("Anthropic API key is missing for native call.")
                self._async_native_client = AsyncAnthropic(api_key=api_key, base_url=self.config.base_url)
            return self._async_native_client

    def _convert_params(self, model: str, **kwargs) -> Dict[str, Any]:
        """[由内向外]：转换参数，并注入 Anthropic 强制要求的默认值"""
        params = super()._convert_params(model, **kwargs)
        
        # Anthropic SDK 强制要求 max_tokens
        if "max_tokens" not in params:
            params["max_tokens"] = 4096
            
        return params

    # ==========================================
    #         生命周期钩子实现
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        转换为 Anthropic Messages API 格式。
        支持多模态内容列表，如果是 Pydantic 对象则转换为 dict。
        """
        anthropic_msgs = []
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else msg.role
            if role_val == "system":
                continue
            
            # Anthropic 不支持 tool 角色，工具结果必须放在 user 角色中
            if role_val == "tool":
                role_val = "user"
            
            content = msg.content
            if isinstance(content, list):
                serialized_content = []
                for part in content:
                    # part_type = getattr(part, "type", None) or (part.get("type") if isinstance(part, dict) else None)
                    
                    if part.type == "text":
                        serialized_content.append({"type": "text", "text": part.text})
                    elif part.type == "image":
                        if part.image_url:
                            serialized_content.append({
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": part.image_url.get("url", "")
                                }
                            })
                        elif part.data:
                            serialized_content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": part.media_type or "image/jpeg",
                                    "data": part.data
                                }
                            })
                    elif part.type == "action":
                        serialized_content.append({
                            "type": "tool_use",
                            "id": part.id,
                            "name": part.name,
                            "input": part.arguments
                        })
                    elif part.type == "outcome":
                        serialized_content.append({
                            "type": "tool_result",
                            "tool_use_id": part.id,
                            "content": part.result,
                            # "is_error": part.is_error
                        })
                    elif hasattr(part, "model_dump"):
                        serialized_content.append(part.model_dump(exclude_none=True))
                    else:
                        serialized_content.append(part)
                content = serialized_content
            
            anthropic_msgs.append({
                "role": role_val,
                "content": content
            })
        return anthropic_msgs

    def _normalize_response(self, response: Any, model: str) -> Response:
        """归一化响应（Native 与 Bedrock SDK 返回的消息对象结构一致）"""
        text_content = ""
        actions = []
        for block in response.content:
            if hasattr(block, "text"):
                text_content += block.text
            elif hasattr(block, "type") and block.type == "tool_use":
                actions.append(Action(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    text_content += block.get("text", "")
                elif block.get("type") == "tool_use":
                    actions.append(Action(
                        id=block.get("id"),
                        name=block.get("name"),
                        arguments=block.get("input")
                    ))

        content_obj = Content(text=text_content if text_content else None)
        output = Output(
            content=content_obj,
            actions=actions if actions else None,
            status=getattr(response, "stop_reason", None)
        )

        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens
        )
        return Response(output=output, model=model, usage=usage)

    def _normalize_stream_chunk(self, chunk: Any, model: str) -> StreamResponse:
        """归一化流式碎片"""
        delta_text = None
        finish_reason = None
        usage = None

        chunk_type = getattr(chunk, "type", None)
        if chunk_type == "content_block_delta":
            if hasattr(chunk.delta, "text"):
                delta_text = chunk.delta.text
        elif chunk_type == "message_delta":
            if hasattr(chunk, "delta") and hasattr(chunk.delta, "stop_reason"):
                finish_reason = chunk.delta.stop_reason
            if hasattr(chunk, "usage"):
                usage = Usage(
                    output_tokens=getattr(chunk.usage, "output_tokens", 0),
                    total_tokens=getattr(chunk.usage, "output_tokens", 0)
                )
        elif chunk_type == "message_start":
            if hasattr(chunk.message, "usage"):
                usage = Usage(
                    input_tokens=chunk.message.usage.input_tokens,
                    total_tokens=chunk.message.usage.input_tokens
                )

        delta_obj = Delta(text=delta_text)
        stream_output = StreamOutput(delta=delta_obj, end=finish_reason)
        return StreamResponse(output=stream_output, model=model, usage=usage)

    def _convert_tools(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """将标准化工具转换为 Anthropic 格式"""
        anthropic_tools = []
        for t in tools:
            if hasattr(t, "function"):
                anthropic_tools.append({
                    "name": t.function.name,
                    "description": t.function.description,
                    "input_schema": t.function.parameters
                })
            else:
                anthropic_tools.append(t)
        return anthropic_tools

    # ==========================================
    #         能力接口实现
    # ==========================================

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        client = self._get_client(model)
        
        # 处理工具转换 (MengLong Standard -> Anthropic Format)
        if "tools" in params:
             params["tools"] = self._convert_tools(params["tools"])

        # 提取系统提示词
        system_prompt = ""
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_prompt = m.content
                break

        response = client.messages.create(
            model=model,
            messages=self._convert_messages(messages),
            system=system_prompt,
            **params
        )
        return self._normalize_response(response, model)

    def stream_chat(self, messages: List[Message], model: str, **kwargs) -> Generator[StreamResponse, None, None]:
        params = self._convert_params(model, **kwargs)
        client = self._get_client(model)
        
        # 处理工具转换
        if "tools" in params:
             params["tools"] = self._convert_tools(params["tools"])

        # 提取系统提示词
        system_prompt = ""
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_prompt = m.content
                break

        with client.messages.stream(
            model=model,
            messages=self._convert_messages(messages),
            system=system_prompt,
            **params
        ) as stream:
            for event in stream:
                yield self._normalize_stream_chunk(event, model)

    # ==========================================
    #         异步能力接口实现
    # ==========================================

    async def async_chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        client = self._get_async_client(model)
        
        # 处理工具转换 (MengLong Standard -> Anthropic Format)
        if "tools" in params:
             params["tools"] = self._convert_tools(params["tools"])

        # 提取系统提示词
        system_prompt = ""
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_prompt = m.content
                break

        response = await client.messages.create(
            model=model,
            messages=self._convert_messages(messages),
            system=system_prompt,
            **params
        )
        return self._normalize_response(response, model)

    async def async_stream_chat(self, messages: List[Message], model: str, **kwargs) -> AsyncGenerator[StreamResponse, None]:
        params = self._convert_params(model, **kwargs)
        client = self._get_async_client(model)
        
        # 处理工具转换
        if "tools" in params:
             params["tools"] = self._convert_tools(params["tools"])

        # 提取系统提示词
        system_prompt = ""
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_prompt = m.content
                break

        async with client.messages.stream(
            model=model,
            messages=self._convert_messages(messages),
            system=system_prompt,
            **params
        ) as stream:
            async for event in stream:
                yield self._normalize_stream_chunk(event, model)
