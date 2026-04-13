from typing import List, Generator, Dict, Any, Optional, AsyncGenerator
import boto3
import json
import os
import base64

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
from menglong.schemas.model_info import ModelInfo
from menglong.utils.config.config_type import ProviderConfig


@ProviderRegistry.register("aws")
class AWSProvider(BaseProvider):
    """
    AWS Bedrock Provider
    基于 boto3 的 converse API 实现。
    """

    # Bedrock converse 同步调用 max_tokens 上限（超过偏大值需要 stream 模式）
    _SYNC_MAX_TOKENS: int = 21000   # 安全上限（API 硬限 21332）
    _STREAM_MAX_TOKENS: int = 64000 # 流式模式默认最大值

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        region = getattr(config, "region", None) or os.getenv("AWS_REGION", "us-west-2")
        bedrock_token = getattr(config, "aws_bearer_token_bedrock", None)
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bedrock_token
        self.client = boto3.Session().client(
            service_name="bedrock-runtime", region_name=region
        )

    def _convert_params(self, model: str, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        转换参数，并根据 stream 模式自动调整 max_tokens。

        - stream=False (chat)：max_tokens 截断至 _SYNC_MAX_TOKENS（21000）避免 API 报错。
        - stream=True  (stream_chat)：允许完整配置值，未指定时默认 _STREAM_MAX_TOKENS。
        """
        params = super()._convert_params(model, **kwargs)
        # Bedrock inferenceConfig 不接受 stream 字段
        params.pop("stream", None)

        if not stream:
            current = params.get("max_tokens")
            if current is None:
                params["max_tokens"] = self._SYNC_MAX_TOKENS
            elif current > self._SYNC_MAX_TOKENS:
                params["max_tokens"] = self._SYNC_MAX_TOKENS
        else:
            if params.get("max_tokens") is None:
                params["max_tokens"] = self._STREAM_MAX_TOKENS

        return params

    # ==========================================
    #         生命周期钩子实现
    # ==========================================

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        将消息转换为 Bedrock Converse API 格式。
        支持多模态 ContentPart 到 Bedrock ContentBlock 的映射。
        """

        bedrock_msgs = []
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else msg.role
            if role == "system":
                continue

            # Bedrock 不支持 tool 角色，工具结果必须放在 user 角色中
            if role == "tool":
                role = "user"

            content = msg.content
            bedrock_content = []

            if isinstance(content, str):
                bedrock_content.append({"text": content})
            elif isinstance(content, list):
                for part in content:
                    if hasattr(part, "type"):
                        if part.type == "text":
                            bedrock_content.append({"text": part.text})
                        elif part.type == "image":
                            # Bedrock image 格式
                            fmt = "jpeg"
                            if part.media_type:
                                fmt = part.media_type.split("/")[-1]

                            source = {}
                            if part.image_url:
                                # Bedrock converse 目前不支持直接传 URL，通常需要下载或传字节
                                # 这里假设如果是 URL，用户暂不传，或者我们报错。
                                # 但为了演示，我们假设存在 bytes
                                source = {"bytes": b""}
                            elif part.data:
                                source = {"bytes": base64.b64decode(part.data)}

                            bedrock_content.append(
                                {"image": {"format": fmt, "source": source}}
                            )
                        elif part.type == "document":
                            fmt = (
                                part.media_type.split("/")[-1]
                                if part.media_type
                                else "pdf"
                            )
                            bedrock_content.append(
                                {
                                    "document": {
                                        "format": fmt,
                                        "name": "document",
                                        "source": {
                                            "bytes": base64.b64decode(part.data)
                                        },
                                    }
                                }
                            )
                        elif part.type == "audio":
                            # AWS Bedrock 目前不支持音频输入
                            import warnings

                            warnings.warn(
                                "AWS Bedrock Converse API 目前不支持音频输入。音频内容将被忽略。",
                                UserWarning,
                            )
                            continue
                        elif part.type == "video":
                            # AWS Bedrock 目前不支持视频输入
                            import warnings

                            warnings.warn(
                                "AWS Bedrock Converse API 目前不支持视频输入。视频内容将被忽略。",
                                UserWarning,
                            )
                            continue
                        elif part.type == "action":
                            bedrock_content.append(
                                {
                                    "toolUse": {
                                        "toolUseId": part.id,
                                        "name": part.name,
                                        "input": part.arguments,
                                    }
                                }
                            )
                        elif part.type == "outcome":
                            # Bedrock 要求 toolResult 的 content.json 必须是对象
                            res = part.result
                            if isinstance(res, str):
                                try:
                                    res = json.loads(res)
                                except:
                                    pass

                            if not isinstance(res, dict):
                                res = {"result": res}

                            bedrock_content.append(
                                {
                                    "toolResult": {
                                        "toolUseId": part.id,
                                        "content": [{"json": res}],
                                        # "status": "error" if part.is_error else "success"
                                    }
                                }
                            )
                        else:
                            # 兜底
                            bedrock_content.append(
                                part.model_dump(exclude_none=True)
                                if hasattr(part, "model_dump")
                                else part
                            )
                    else:
                        bedrock_content.append(part)

            bedrock_msgs.append({"role": role, "content": bedrock_content})
        return bedrock_msgs

    def _normalize_response(self, response: Any, model: str) -> Response:
        """归一化 Bedrock 同步响应"""
        output_msg = response["output"]["message"]
        text_content = ""
        actions = []
        for part in output_msg.get("content", []):
            if "text" in part:
                text_content += part["text"]
            elif "toolUse" in part:
                tu = part["toolUse"]
                actions.append(
                    Action(
                        id=tu.get("toolUseId"),
                        name=tu.get("name"),
                        arguments=tu.get("input"),
                    )
                )

        content_obj = Content(text=text_content if text_content else None)
        output = Output(
            content=content_obj,
            actions=actions if actions else None,
            status=response.get("stopReason"),
        )

        usage_data = response.get("usage", {})
        usage = Usage(
            input_tokens=usage_data.get("inputTokens", 0),
            output_tokens=usage_data.get("outputTokens", 0),
            total_tokens=usage_data.get("totalTokens", 0),
        )

        return Response(output=output, model=model, usage=usage)

    def _normalize_stream_chunk(self, chunk: Any, model: str) -> StreamResponse:
        """归一化 Bedrock 流式碎片"""
        # Bedrock 流式返回的是事件载荷
        delta_text = None
        finish_reason = None
        usage = None

        if "contentBlockDelta" in chunk:
            delta_text = chunk["contentBlockDelta"]["delta"].get("text")
        elif "messageStop" in chunk:
            finish_reason = chunk["messageStop"].get("stopReason")
        elif "metadata" in chunk and "usage" in chunk["metadata"]:
            u = chunk["metadata"]["usage"]
            usage = Usage(
                input_tokens=u.get("inputTokens", 0),
                output_tokens=u.get("outputTokens", 0),
                total_tokens=u.get("totalTokens", 0),
            )

        delta_obj = Delta(text=delta_text)
        stream_output = StreamOutput(delta=delta_obj, end=finish_reason)

        return StreamResponse(output=stream_output, model=model, usage=usage)

    def _convert_tools(self, tools: List[Any]) -> Dict[str, Any]:
        """将标准化工具转换为 AWS Bedrock toolConfig 格式"""
        aws_tools = []
        for t in tools:
            if hasattr(t, "function"):
                aws_tools.append(
                    {
                        "toolSpec": {
                            "name": t.function.name,
                            "description": t.function.description,
                            "inputSchema": {"json": t.function.parameters},
                        }
                    }
                )
            elif isinstance(t, dict) and "function" in t:
                aws_tools.append(
                    {
                        "toolSpec": {
                            "name": t["function"]["name"],
                            "description": t["function"]["description"],
                            "inputSchema": {"json": t["function"]["parameters"]},
                        }
                    }
                )
            else:
                aws_tools.append(t)
        return {"tools": aws_tools}

    def list_models(self) -> List[ModelInfo]:
        """返回 AWS Bedrock 当前可用的文本输出模型列表（仅 ACTIVE 状态）"""
        region = getattr(self.config, "region", None) or "us-west-2"
        bedrock = boto3.Session().client("bedrock", region_name=region)
        resp = bedrock.list_foundation_models(byOutputModality="TEXT")
        models = []
        for m in resp.get("modelSummaries", []):
            status = m.get("modelLifecycle", {}).get("status", "")
            if status == "ACTIVE":
                models.append(
                    ModelInfo(
                        id=m["modelId"],
                        provider=self.provider_name,
                        display_name=m.get("modelName"),
                    )
                )
        return models

    # ==========================================
    #         能力接口实现
    # ==========================================

    def chat(self, messages: List[Message], model: str, **kwargs) -> Response:
        # stream=False：同步模式，max_tokens 自动截断至 21000
        params = self._convert_params(model, stream=False, **kwargs)

        tool_config = None
        if "tools" in params:
            tool_config = self._convert_tools(params.pop("tools"))

        system_prompts = []
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_prompts.append({"text": m.content})

        converse_kwargs = {
            "modelId": model,
            "messages": self._convert_messages(messages),
            "inferenceConfig": params,
        }
        if system_prompts:
            converse_kwargs["system"] = system_prompts
        if tool_config:
            converse_kwargs["toolConfig"] = tool_config

        response = self.client.converse(**converse_kwargs)
        return self._normalize_response(response, model)

    def stream_chat(
        self, messages: List[Message], model: str, **kwargs
    ) -> Generator[StreamResponse, None, None]:
        # stream=True：流式模式，允许完整 max_tokens
        params = self._convert_params(model, stream=True, **kwargs)

        tool_config = None
        if "tools" in params:
            tool_config = self._convert_tools(params.pop("tools"))

        system_prompts = []
        for m in messages:
            role_val = m.role.value if hasattr(m.role, "value") else m.role
            if role_val == "system":
                system_prompts.append({"text": m.content})

        converse_stream_kwargs = {
            "modelId": model,
            "messages": self._convert_messages(messages),
            "inferenceConfig": params,
        }
        if system_prompts:
            converse_stream_kwargs["system"] = system_prompts
        if tool_config:
            converse_stream_kwargs["toolConfig"] = tool_config

        response = self.client.converse_stream(**converse_stream_kwargs)

        for event in response.get("stream"):
            yield self._normalize_stream_chunk(event, model)

    async def async_chat(
        self, messages: List[Message], model: str, **kwargs
    ) -> Response:
        """异步聊天接口"""
        raise ValueError("boto3 converse api not support async,at now.")
        pass

    async def async_stream_chat(
        self, messages: List[Message], model: str, **kwargs
    ) -> AsyncGenerator[StreamResponse, None]:
        """异步流式聊天接口"""
        raise ValueError("boto3 converse api not support async,at now.")
        pass
