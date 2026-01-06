from typing import List, Generator, Dict, Any, Optional, AsyncGenerator
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
            credentials = getattr(config, "google_application_credentials")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials
            project = getattr(config, "project", os.getenv("GOOGLE_CLOUD_PROJECT"))
            location = getattr(config, "location", "global") # 默认 location
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
                                url = part.image_url.get("url", "") if isinstance(part.image_url, dict) else part.image_url
                                google_parts.append(types.Part.from_uri(file_uri=url, mime_type=part.media_type or "image/jpeg"))
                            elif part.data:
                                google_parts.append(types.Part.from_bytes(data=base64.b64decode(part.data), mime_type=part.media_type or "image/jpeg"))
                        elif part.type == "document":
                            google_parts.append(types.Part.from_bytes(data=base64.b64decode(part.data), mime_type=part.media_type or "application/pdf"))
                        elif part.type == "audio":
                            # Gemini 2.0 Flash 支持音频
                            if part.audio_url:
                                google_parts.append(types.Part.from_uri(file_uri=part.audio_url, mime_type=part.media_type or "audio/mp3"))
                            elif part.data:
                                google_parts.append(types.Part.from_bytes(data=base64.b64decode(part.data), mime_type=part.media_type or "audio/mp3"))
                        elif part.type == "video":
                            # Gemini 2.0 Flash 支持视频
                            if part.video_url:
                                google_parts.append(types.Part.from_uri(file_uri=part.video_url, mime_type=part.media_type or "video/mp4"))
                            elif part.data:
                                google_parts.append(types.Part.from_bytes(data=base64.b64decode(part.data), mime_type=part.media_type or "video/mp4"))
                        elif part.type == "action":
                            google_parts.append(types.Part(function_call=types.FunctionCall(
                                name=part.name,
                                args=part.arguments)
                            ,thought_signature=part.id))
                        elif part.type == "outcome":
                            # Google 要求 function_response 的 response 必须是字典
                            res = part.result
                            if isinstance(res, str):
                                try:
                                    res = json.loads(res)
                                except:
                                    pass
                            
                            if not isinstance(res, dict):
                                res = {"result": res}
                                
                            google_parts.append(types.Part.from_function_response(
                                name=part.name,
                                response=res
                            ))
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
        text_content = ""
        actions = []
        
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        text_content += part.text
                    elif hasattr(part, "function_call") and part.function_call:
                        actions.append(Action(
                            id=part.thought_signature,
                            name=part.function_call.name,
                            arguments=part.function_call.args,
                        ))

        content_obj = Content(text=text_content if text_content else None)
        output = Output(
            content=content_obj,
            actions=actions if actions else None,
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

    def _convert_tools(self, tools: List[Any]) -> List[types.Tool]:
        """将标准化工具转换为 Google GenAI 格式"""
        functions = []
        for t in tools:
            if hasattr(t, "function"):
                functions.append(types.FunctionDeclaration(
                    name=t.function.name,
                    description=t.function.description,
                    parameters=t.function.parameters
                ))
            elif isinstance(t, dict) and "function" in t:
                functions.append(types.FunctionDeclaration(
                    name=t["function"]["name"],
                    description=t["function"]["description"],
                    parameters=t["function"]["parameters"]
                ))
            else:
                # Fallback for other tool types if any, or raise error
                # For now, assuming only function declarations are converted this way
                # and other tool types (if any) would be handled differently or passed through.
                # The original code had `other_tools.append(t)` for non-function tools.
                # This simplified version assumes all tools here are function-like.
                # If `t` is already a `types.Tool` or `types.FunctionDeclaration`, it will be appended directly.
                functions.append(t)
        
        # If there are function declarations, wrap them in a single Tool object.
        # The original code created a list of tools, where one item could be Tool(function_declarations=decls)
        # and others could be raw tools. This simplified version assumes all tools passed to _convert_tools
        # are meant to be function declarations.
        if functions:
            return [types.Tool(function_declarations=functions)]
        return []

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
        
        if system_instruction:
            params["system_instruction"] = system_instruction

        if "tools" in params:
             params["tools"] = self._convert_tools(params["tools"])

        response = self.client.models.generate_content(
            model=model,
            contents=self._convert_messages(messages),
            config=types.GenerateContentConfig(**params)
        )
        return self._normalize_response(response, model)

    def stream_chat(self, messages: List[Message], model: str, **kwargs) -> Generator[StreamResponse, None, None]:
        params = self._convert_params(model, **kwargs)
        
        # 处理工具转换 (MengLong Standard -> Google GenAI Spec)
        google_tools = None
        if "tools" in params:
            decls = []
            other_tools = []
            for t in params.pop("tools"):
                if hasattr(t, "function"):
                    decls.append(types.FunctionDeclaration(
                        name=t.function.name,
                        description=t.function.description,
                        parameters=t.function.parameters
                    ))
                elif isinstance(t, dict) and "function" in t:
                    decls.append(types.FunctionDeclaration(
                        name=t["function"]["name"],
                        description=t["function"]["description"],
                        parameters=t["function"]["parameters"]
                    ))
                else:
                    other_tools.append(t)
            
            google_tools = []
            if decls:
                google_tools.append(types.Tool(function_declarations=decls))
            google_tools.extend(other_tools)

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
                tools=google_tools,
                **params
            )
        )
        
        for chunk in response:
            yield self._normalize_stream_chunk(chunk, model)

    # ==========================================
    #         异步能力接口实现
    # ==========================================

    async def async_chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        params = self._convert_params(model, **kwargs)
        
        # 提取系统指令
        system_instruction = None
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_instruction = m.content
                break
        
        if system_instruction:
            params["system_instruction"] = system_instruction

        if "tools" in params:
             params["tools"] = self._convert_tools(params["tools"])

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=self._convert_messages(messages),
            config=types.GenerateContentConfig(**params)
        )
        return self._normalize_response(response, model)

    async def async_stream_chat(self, messages: List[Message], model: str, **kwargs) -> AsyncGenerator[StreamResponse, None]:
        params = self._convert_params(model, **kwargs)
        
        # 处理工具转换 (MengLong Standard -> Google GenAI Spec)
        google_tools = None
        if "tools" in params:
            decls = []
            other_tools = []
            for t in params.pop("tools"):
                if hasattr(t, "function"):
                    decls.append(types.FunctionDeclaration(
                        name=t.function.name,
                        description=t.function.description,
                        parameters=t.function.parameters
                    ))
                elif isinstance(t, dict) and "function" in t:
                    decls.append(types.FunctionDeclaration(
                        name=t["function"]["name"],
                        description=t["function"]["description"],
                        parameters=t["function"]["parameters"]
                    ))
                else:
                    other_tools.append(t)
            
            google_tools = []
            if decls:
                google_tools.append(types.Tool(function_declarations=decls))
            google_tools.extend(other_tools)

        system_instruction = None
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_instruction = m.content
                break

        response = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=self._convert_messages(messages),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=google_tools,
                **params
            )
        )
        
        async for chunk in response:
            yield self._normalize_stream_chunk(chunk, model)
