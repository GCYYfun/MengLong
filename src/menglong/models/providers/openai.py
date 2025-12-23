from typing import List, Generator, Dict, Any, Optional
import os
import openai
import json

from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse, 
    Output, Content, Usage, Action,
    StreamOutput, Delta, MessageRole
)
from menglong.schemas.embedding import EmbedResponse
from menglong.utils.config.config_type import ProviderConfig

@ProviderRegistry.register("openai")
class OpenAIProvider(BaseProvider):
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is missing.")
            
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=config.base_url or "https://api.openai.com/v1"
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
                    if hasattr(part, "type"):
                        # 处理特定类型映射
                        if part.type == "text":
                            serialized_content.append({"type": "text", "text": part.text})
                        elif part.type == "image":
                            # OpenAI 格式: {"type": "image_url", "image_url": {"url": "..."}}
                            img_data = {}
                            if part.image_url:
                                img_data = {"url": part.image_url.get("url", "")}
                            elif part.data:
                                # 处理 Base64
                                mime = part.media_type or "image/jpeg"
                                img_data = {"url": f"data:{mime};base64,{part.data}"}
                            serialized_content.append({"type": "image_url", "image_url": img_data})
                        else:
                            # 兜底转换
                            serialized_content.append(part.model_dump(exclude_none=True) if hasattr(part, "model_dump") else part)
                    else:
                        serialized_content.append(part)
                content = serialized_content

            m = {
                "role": role_val,
                "content": content
            }
            if msg.name:
                m["name"] = msg.name
            if msg.tool_id:
                m["tool_call_id"] = msg.tool_id
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

        # 构造统一输出
        content_obj = Content(text=choice.message.content, reasoning=None)
        output = Output(content=content_obj, actions=actions, status=choice.finish_reason)

        # 构造 Usage
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

    # ==========================================
    #         能力接口实现
    # ==========================================

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        
        response = self.client.chat.completions.create(
            model=model,
            messages=self._convert_messages(messages),
            **params
        )
        return self._normalize_response(response, model)

    def stream_chat(self, messages: List[Message], model: str, **kwargs) -> Generator[StreamResponse, None, None]:
        params = self._convert_params(model, **kwargs)
        
        stream = self.client.chat.completions.create(
            model=model,
            messages=self._convert_messages(messages),
            stream=True,
            **params
        )
        for chunk in stream:
            yield self._normalize_stream_chunk(chunk, model)

    def embed(self, texts: List[str], model: str, **kwargs) -> EmbedResponse:
        response = self.client.embeddings.create(
            input=texts,
            model=model,
            **kwargs
        )
        
        embeddings = [item.embedding for item in response.data]
        return EmbedResponse(
            embeddings=embeddings,
            texts=texts,
            model=model,
            usage=response.usage.model_dump() if hasattr(response.usage, "model_dump") else response.usage
        )
