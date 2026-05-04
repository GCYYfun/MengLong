from typing import List, Generator, Tuple, Optional, Dict, Any, Union, AsyncGenerator

from menglong.schemas.chat import (
    Message,
    Response,
    StreamResponse,
    MessageRole,
    Context,
)
from menglong.schemas.model_info import ModelInfo
from menglong.schemas.embedding import EmbedResponse
from menglong.utils.config.config_type import Config, ProviderConfig
from menglong.models.providers.registry import ProviderRegistry
from menglong.models.providers.base import BaseProvider

# Load Config
from menglong.utils.config.config_loader import load_config


class Model:
    def __init__(self, default_model_id: str = None, config_path: Optional[str] = None):
        """
        初始化统一的模型入口 (Facade)。
        default_model_id: 默认模型 ID (格式: 'provider/model')
        """
        self.config = load_config(config_path)
        self.default_model_id = default_model_id or self.config.default.model_id
        self._providers: Dict[str, BaseProvider] = {}

    def _parse_model_id(self, model_id: str) -> tuple[str, str]:
        """Parse 'provider/model' string"""
        if not model_id or "/" not in model_id:
            raise ValueError(
                f"Invalid model_id format: '{model_id}'. Expected 'provider/model'."
            )

        parts = model_id.split("/", 1)
        return parts[0], parts[1]

    def _get_provider_and_model_name(
        self, model_override: str = None
    ) -> tuple[BaseProvider, str]:
        """
        根据传入的覆盖模型 ID 或默认 ID，获取对应的 Provider 实例和模型名称。
        """
        target_id = model_override or self.default_model_id
        if not target_id:
            raise ValueError("No model specified and no default_model_id set.")

        provider_name, model_name = self._parse_model_id(target_id)

        # 从缓存池获取或创建新 Provider
        if provider_name not in self._providers:
            self._providers[provider_name] = ProviderRegistry.get_instance(
                provider_name, self.config
            )

        return self._providers[provider_name], model_name

    def _ensure_messages(
        self, messages: Union[Context, List[Union[Message, Dict[str, Any], str]]]
    ) -> List[Message]:
        """Ensure messages are Pydantic models"""
        source_msgs = messages
        if isinstance(messages, Context):
            source_msgs = messages.messages
        elif not isinstance(messages, list):
            source_msgs = [messages]

        validated = []
        for msg in source_msgs:
            if isinstance(msg, dict):
                validated.append(Message(**msg))
            elif isinstance(msg, Message):
                validated.append(msg)
            elif isinstance(msg, str):
                validated.append(Message(role=MessageRole.USER, content=msg))
            else:
                raise ValueError(f"Invalid message type: {type(msg)}")
        return validated

    def _ensure_tools(self, tools: Optional[List[Any]]) -> Optional[List[Any]]:
        """归一化工具列表：支持 @tool 函数、ToolInfo 对象或原始字典"""
        if not tools:
            return None

        normalized = []
        for t in tools:
            if callable(t) and hasattr(t, "schema"):
                normalized.append(t.schema())
            else:
                normalized.append(t)
        return normalized

    def chat(
        self,
        messages: Union[Context, List[Union[Message, Dict[str, Any], str]]],
        model: Optional[str] = None,
        **kwargs,
    ) -> Response:
        """
        发送聊天请求。
        """
        provider, model_name = self._get_provider_and_model_name(model)
        messages = self._ensure_messages(messages)

        # 处理工具自动化转换
        if "tools" in kwargs:
            kwargs["tools"] = self._ensure_tools(kwargs["tools"])

        return provider.chat(messages, model=model_name, **kwargs)

    def stream_chat(
        self,
        messages: Union[Context, List[Union[Message, Dict[str, Any], str]]],
        model: Optional[str] = None,
        **kwargs,
    ) -> Generator[StreamResponse, None, None]:
        """
        流式发送聊天请求。
        """
        provider, model_name = self._get_provider_and_model_name(model)
        messages = self._ensure_messages(messages)

        if "tools" in kwargs:
            kwargs["tools"] = self._ensure_tools(kwargs["tools"])

        return provider.stream_chat(messages, model=model_name, **kwargs)

    def embed(
        self, texts: List[str], model: Optional[str] = None, **kwargs
    ) -> EmbedResponse:
        """
        发送向量嵌入请求。
        - texts: 文本列表
        - model: 可选，覆盖默认模型
        """
        provider, model_name = self._get_provider_and_model_name(model)
        return provider.embed(texts, model=model_name, **kwargs)

    def list_models(self, provider: Optional[str] = None) -> List[ModelInfo]:
        """
        返回指定 provider 的可用模型列表。

        Args:
            provider: provider 名称，如 'openai'/'deepseek'/'aws'/'anthropic'/'google'。
                      不传则使用 default_model_id 中的 provider。

        Returns:
            ModelInfo 列表，每个元素的 id 字段可直接用于构造完整 model_id（provider/id）。

        Usage::

            model = Model()
            models = model.list_models('openai')
            for m in models:
                print(m)         # openai/gpt-4o
                print(m.id)      # gpt-4o
        """
        if provider:
            target_id = f"{provider}/placeholder"  # 只需要 provider 名称
            provider_name, _ = self._parse_model_id(target_id)
        else:
            provider_name, _ = self._parse_model_id(self.default_model_id)

        if provider_name not in self._providers:
            self._providers[provider_name] = ProviderRegistry.get_instance(
                provider_name, self.config
            )

        return self._providers[provider_name].list_models()

    def list_all_models(self) -> Dict[str, List[ModelInfo]]:
        """
        遍历所有已配置的 provider，分别返回各自的可用模型列表。

        Returns:
            {“provider_name”: [ModelInfo, ...]}。失败的 provider 会输出警告并返回空列表。
        """
        result: Dict[str, List[ModelInfo]] = {}
        # 兼容处理：如果 providers 是 dict 则直接用，如果是对象则取 __dict__
        providers_source = (
            self.config.providers if hasattr(self.config, "providers") else None
        )
        if isinstance(providers_source, dict):
            configured_providers = list(providers_source.keys())
        else:
            configured_providers = []

        for pname in configured_providers:
            try:
                if pname not in self._providers:
                    self._providers[pname] = ProviderRegistry.get_instance(
                        pname, self.config
                    )
                result[pname] = self._providers[pname].list_models()
            except Exception as e:
                import warnings

                warnings.warn(f"list_all_models: provider '{pname}' 失败 — {e}")
                result[pname] = []
        return result

    async def async_chat(
        self,
        messages: Union[Context, List[Union[Message, Dict[str, Any], str]]],
        model: Optional[str] = None,
        **kwargs,
    ) -> Response:
        """
        异步发送聊天请求。
        """
        provider, model_name = self._get_provider_and_model_name(model)
        messages = self._ensure_messages(messages)

        # 处理工具自动化转换
        if "tools" in kwargs:
            kwargs["tools"] = self._ensure_tools(kwargs["tools"])

        return await provider.async_chat(messages, model=model_name, **kwargs)

    async def async_stream_chat(
        self,
        messages: Union[Context, List[Union[Message, Dict[str, Any], str]]],
        model: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        异步流式发送聊天请求。
        """
        provider, model_name = self._get_provider_and_model_name(model)
        messages = self._ensure_messages(messages)

        if "tools" in kwargs:
            kwargs["tools"] = self._ensure_tools(kwargs["tools"])

        async for chunk in provider.async_stream_chat(
            messages, model=model_name, **kwargs
        ):
            yield chunk
