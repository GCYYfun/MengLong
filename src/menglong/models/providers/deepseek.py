from typing import List, Generator, Dict, Any, Optional
import os
import openai
import json

from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse, 
    Output, Content, Usage, Action,
    StreamOutput, Delta
)
from menglong.utils.config.config_type import ProviderConfig

@ProviderRegistry.register("deepseek")
class DeepSeekProvider(BaseProvider):
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        api_key = config.api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DeepSeek API key is missing.")
            
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=config.base_url or "https://api.deepseek.com"
        )

    # ==========================================
    #         生命周期钩子实现
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """将内部消息格式转换为 OpenAI/DeepSeek 格式"""
        openai_msgs = []
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else msg.role
            m = {
                "role": role_val,
                "content": msg.content
            }
            if msg.name:
                m["name"] = msg.name
            if msg.tool_id:
                m["tool_call_id"] = msg.tool_id
            openai_msgs.append(m)
        return openai_msgs

    def _convert_params(self, model: str, **kwargs) -> Dict[str, Any]:
        """DeepSeek 特定参数转换（如思维链强度等未来扩展点）"""
        params = super()._convert_params(model, **kwargs)
        # 示例：如果用户传 thinking=True，可以映射到特定供应商参数
        # if params.get("thinking"): ...
        return params

    def _normalize_response(self, response: Any, model: str) -> Response:
        """将 DeepSeek 响应归一化，支持 reasoning_content"""
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

        # 提取推理内容 (DeepSeek 特有字段)
        deepseek_reasoning = getattr(choice.message, "reasoning_content", None)

        content_obj = Content(
             text=choice.message.content,
             reasoning=deepseek_reasoning
        )

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
        """将 DeepSeek 流式碎片归一化，支持 reasoning_content"""
        if not chunk.choices:
            return StreamResponse(model=chunk.model)
            
        delta = chunk.choices[0].delta
        deepseek_reasoning = getattr(delta, "reasoning_content", None)

        delta_obj = Delta(
            text=delta.content,
            reasoning=deepseek_reasoning
        )
        
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
