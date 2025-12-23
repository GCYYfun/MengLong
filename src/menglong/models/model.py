from typing import List, Generator, Tuple, Optional, Dict, Any, Union

from menglong.schemas.chat import (
    Message, 
    Response, 
    StreamResponse,
    MessageRole,
    Context
)
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
        self.default_model_id = default_model_id
        self._providers: Dict[str, BaseProvider] = {}

    def _parse_model_id(self, model_id: str) -> tuple[str, str]:
        """Parse 'provider/model' string"""
        if not model_id or "/" not in model_id:
             raise ValueError(f"Invalid model_id format: '{model_id}'. Expected 'provider/model'.")
        
        parts = model_id.split("/", 1)
        return parts[0], parts[1]

    def _get_provider_and_model_name(self, model_override: str = None) -> tuple[BaseProvider, str]:
        """
        根据传入的覆盖模型 ID 或默认 ID，获取对应的 Provider 实例和模型名称。
        """
        target_id = model_override or self.default_model_id
        if not target_id:
            raise ValueError("No model specified and no default_model_id set.")
        
        provider_name, model_name = self._parse_model_id(target_id)
        
        # 从缓存池获取或创建新 Provider
        if provider_name not in self._providers:
            self._providers[provider_name] = ProviderRegistry.get_instance(provider_name, self.config)
            
        return self._providers[provider_name], model_name

    def _ensure_messages(self, messages: Union[Context, List[Union[Message, Dict[str, Any], str]]]) -> List[Message]:
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

    def chat(self, messages: List[Union[Message, Dict[str, Any]]], model: Optional[str] = None, **kwargs) -> Response:
        """
        发送聊天请求。
        - messages: 消息列表
        - model: 可选，覆盖初始化时的默认模型 (格式: 'provider/model')
        - kwargs: 其他参数 (temperature, max_tokens, thinking 等)
        """
        provider, model_name = self._get_provider_and_model_name(model)
        messages = self._ensure_messages(messages)
        return provider.chat(messages, model=model_name, **kwargs)

    def stream_chat(self, messages: List[Union[Message, Dict[str, Any]]], model: Optional[str] = None, **kwargs) -> Generator[StreamResponse, None, None]:
        """
        流式发送聊天请求。
        """
        provider, model_name = self._get_provider_and_model_name(model)
        messages = self._ensure_messages(messages)
        return provider.stream_chat(messages, model=model_name, **kwargs)

    def embed(self, texts: List[str], model: Optional[str] = None, **kwargs) -> EmbedResponse:
        """
        发送向量嵌入请求。
        - texts: 文本列表
        - model: 可选，覆盖默认模型
        """
        provider, model_name = self._get_provider_and_model_name(model)
        return provider.embed(texts, model=model_name, **kwargs)
