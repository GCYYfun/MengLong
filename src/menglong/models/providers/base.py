from abc import ABC, abstractmethod
from typing import List, Generator, Union, Dict, Any, Optional

from menglong.schemas.chat import (
    Message, 
    Response,
    StreamResponse,
    StreamOutput,
    Delta
)
from menglong.schemas.embedding import EmbedResponse
from menglong.utils.config.config_type import ProviderConfig


class BaseProvider(ABC):
    """
    LLM 供应商基类
    负责定义统一的适配层协议 (Hooks)。
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    # ==========================================
    #         生命周期钩子 (Hooks)
    # ==========================================

    @abstractmethod
    def _convert_messages(self, messages: List[Message]) -> Any:
        """[由内向外]：将 SDK 内部 Message 转换为供应商特定格式"""
        pass

    @abstractmethod
    def _normalize_response(self, raw_response: Any, model: str) -> Response:
        """[由外向内]：将供应商原始响应归一化为 SDK 内部 Response 对象"""
        pass

    @abstractmethod
    def _normalize_stream_chunk(self, raw_chunk: Any, model: str) -> StreamResponse:
        """[由外向内]：将供应商流式碎片归一化为 SDK 内部 StreamResponse 对象"""
        pass

    @abstractmethod
    def _convert_tools(self, tools: List[Any]) -> Any:
        """[由内向外]：将标准化工具列表转换为供应商特定格式"""
        pass

    def _convert_params(self, model: str, **kwargs) -> Dict[str, Any]:
        """
        [由内向外]：统一转换控制参数。
        职责：
        1. 从配置文件加载模型默认参数。
        2. 合并运行时传入的覆盖参数。
        3. 过滤掉 None 值。
        """
        params = {}
        # 1. 静态配置合并
        if model in self.config.models:
            model_config = self.config.models[model]
            params.update(model_config.model_dump(exclude_none=True))
        
        # 2. 动态运行时参数合并
        for k, v in kwargs.items():
            if v is not None:
                params[k] = v
        
        return params

    # ==========================================
    #         核心能力接口
    # ==========================================

    @abstractmethod
    def chat(
        self, 
        messages: List[Message], 
        model: str,
        **kwargs
    ) -> Response:
        """同步聊天接口"""
        pass

    @abstractmethod
    def stream_chat(
        self, 
        messages: List[Message], 
        model: str,
        **kwargs
    ) -> Generator[StreamResponse, None, None]:
        """流式聊天接口"""
        pass

    def embed(self, texts: List[str], model: str, **kwargs) -> EmbedResponse:
        """
        [可选] 向量嵌入接口。
        并非所有 Provider 都支持，默认抛出异常。
        """
        raise NotImplementedError(f"Provider '{self.provider_name}' does not support embeddings.")

    @property
    def provider_name(self) -> str:
        return self.__class__.__name__.replace("Provider", "").lower()
