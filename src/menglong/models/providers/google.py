from typing import List, Generator, Dict, Any, Optional
import os
from google import genai
from google.genai import types
import base64
from menglong.models.providers.base import BaseProvider
from menglong.models.providers.registry import ProviderRegistry
from menglong.schemas.chat import (
    Message, Response, StreamResponse, 
    Output, Content, Usage, Action,
    StreamOutput, Delta
)
from menglong.utils.config.config_type import ProviderConfig

@ProviderRegistry.register("google")
class GoogleProvider(BaseProvider):
    """
    Google Gemini Provider
    基于最新的 google-genai SDK 实现。
    """
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        # 优先检查是否为 Vertex AI 模式
        vertexai = getattr(config, "vertexai", False)
        
        if vertexai:
            project = getattr(config, "project", os.getenv("GOOGLE_CLOUD_PROJECT"))
            location = getattr(config, "location", "us-central1") # 默认 location
            self.client = genai.Client(
                vertexai=True, 
                project=project, 
                location=location
            )
        else:
            api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("Google API key is missing. Set 'api_key' in config or 'GOOGLE_API_KEY' env var.")
                
            self.client = genai.Client(
                api_key=api_key,
                http_options={'api_version': 'v1beta'}
            )

    # ==========================================
    #         生命周期钩子实现
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[types.Content]:
        """
        讲 SDK 内部消息转换为 Google GenAI 格式。
        支持多模态 ContentPart 到 Google Part 的映射。
        """

        contents = []
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else msg.role
            
            # 系统消息在 generate_content 的 system_instruction 中处理
            if role_val == "system":
                continue
                
            # 映射角色
            genai_role = "model" if role_val == "assistant" else "user"
            
            content_val = msg.content
            google_parts = []
            
            if isinstance(content_val, str):
                google_parts.append(types.Part(text=content_val))
            elif isinstance(content_val, list):
                for part in content_val:
                    if hasattr(part, "type"):
                        if part.type == "text":
                            google_parts.append(types.Part(text=part.text))
                        elif part.type == "image":
                            if part.image_url:
                                google_parts.append(types.Part.from_uri(uri=part.image_url.get("url", ""), mime_type=part.media_type or "image/jpeg"))
                            elif part.data:
                                google_parts.append(types.Part.from_bytes(data=base64.b64decode(part.data), mime_type=part.media_type or "image/jpeg"))
                        elif part.type == "document":
                            google_parts.append(types.Part.from_bytes(data=base64.b64decode(part.data), mime_type=part.media_type or "application/pdf"))
                        else:
                            # 兜底转换
                            google_parts.append(types.Part(text=str(part)))
                    else:
                        # 兼容普通字典
                        if isinstance(part, dict) and "text" in part:
                             google_parts.append(types.Part(text=part["text"]))
                        else:
                             google_parts.append(types.Part(text=str(part)))
            
            contents.append(types.Content(
                role=genai_role,
                parts=google_parts
            ))
        return contents

    def _normalize_response(self, response: Any, model: str) -> Response:
        """归一化 Google GenAI 同步响应"""
        # response 是 GenerateContentResponse
        text_content = response.text
        
        content_obj = Content(text=text_content)
        output = Output(
            content=content_obj,
            status=str(response.candidates[0].finish_reason) if response.candidates else None
        )

        # 提取消耗
        usage = None
        if hasattr(response, "usage_metadata"):
            usage = Usage(
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count,
                total_tokens=response.usage_metadata.total_token_count
            )

        return Response(output=output, model=model, usage=usage)

    def _normalize_stream_chunk(self, chunk: Any, model: str) -> StreamResponse:
        """归一化 Google GenAI 流式碎片"""
        text = chunk.text
        delta_obj = Delta(text=text)
        
        finish_reason = None
        if chunk.candidates:
            finish_reason = str(chunk.candidates[0].finish_reason)

        stream_output = StreamOutput(
            delta=delta_obj,
            end=finish_reason
        )

        usage = None
        if hasattr(chunk, "usage_metadata"):
             usage = Usage(
                input_tokens=chunk.usage_metadata.prompt_token_count,
                output_tokens=chunk.usage_metadata.candidates_token_count,
                total_tokens=chunk.usage_metadata.total_token_count
            )

        return StreamResponse(output=stream_output, model=model, usage=usage)

    # ==========================================
    #         能力接口实现
    # ==========================================

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        
        # 提取系统指令
        system_instruction = None
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_instruction = m.content
                break

        response = self.client.models.generate_content(
            model=model,
            contents=self._convert_messages(messages),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                **params
            )
        )
        return self._normalize_response(response, model)

    def stream_chat(self, messages: List[Message], model: str, **kwargs) -> Generator[StreamResponse, None, None]:
        params = self._convert_params(model, **kwargs)
        
        system_instruction = None
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_instruction = m.content
                break

        response = self.client.models.generate_content_stream(
            model=model,
            contents=self._convert_messages(messages),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                **params
            )
        )
        
        for chunk in response:
            yield self._normalize_stream_chunk(chunk, model)
