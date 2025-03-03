"""
Adapted from https://github.com/andrewyng/aisuite/blob/main/aisuite/client.py
"""

from typing import List, Dict, Any
from mlong.provider import ProviderFactory
from mlong.types.type_model import MODEL_LIST
from mlong.utils.config import config

class Model:

    def __init__(self, model_id: str = None, model_configs: dict = None):
        """
        模型的一个抽象, 通过 model 可以调用不同的模型, 但是 model 本身并不关心模型的实现细节, 只关心模型的调用方式.
        
        Args:
            model_id: 模型的 id, 用于区分不同的模型
            model_configs: 模型的配置信息
        """
        # 从配置文件加载默认模型
        self.default_model = config.get("model.default_model", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
        
        if model_id is None:
            self.model_id = self.default_model
        else:
            if model_id not in MODEL_LIST:
                raise ValueError(f"Model {model_id} is not supported")
            self.model_id = model_id
            
        # 从配置文件加载默认模型配置
        self.model_configs = config.get("configs", {})

        
        # 合并用户提供的配置和默认配置
        if model_configs is not None:
            self.model_configs.update(model_configs)

        # Backends
        self.backends = {}

        # API
        self._chat = None
        self._embed = None

        # Init
        self.init_backends()

    def init_backends(self):
        """初始化所有配置的后端提供商"""
        for provider, provider_config in self.model_configs.items():
            provider = self.validate(provider)
            self.backends[provider] = ProviderFactory.provider(provider, provider_config)

    def validate(self, provider: str) -> str:
        """验证提供商是否支持
        
        Args:
            provider: 提供商名称
            
        Returns:
            验证后的提供商名称
            
        Raises:
            ValueError: 如果提供商不支持
        """
        available_provider = ProviderFactory.list_provider()
        if provider not in available_provider:
            raise ValueError(f"Provider {provider} is not supported")
        return provider

    def chat(self, model_id: str = None, messages: List[Dict[str, Any]] = [], **kwargs):
        """发送聊天请求
        
        Args:
            model_id: 模型ID，如果为None则使用默认模型
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            模型响应
            
        Raises:
            ValueError: 如果模型或提供商不支持
        """
        if model_id is None:
            model_id = self.model_id
        else:
            if model_id not in MODEL_LIST:
                raise ValueError(f"Model {model_id} is not supported")

        provider, model = MODEL_LIST[model_id]

        # 确保提供商已初始化
        if provider not in self.backends:
            config = self.model_configs.get(provider, {})
            try:
                self.backends[provider] = ProviderFactory.provider(provider, config)
            except Exception as e:
                raise ValueError(f"Failed to initialize provider {provider}: {str(e)}")

        model_client = self.backends.get(provider)
        if not model_client:
            raise ValueError(f"Provider {provider} is not supported")

        try:
            return model_client.chat(messages=messages, model=model, **kwargs)
        except Exception as e:
            # 统一错误处理
            raise RuntimeError(f"Chat request failed: {str(e)}")

    # @property
    # def embed(self):
    #     if not self._embed:
    #         self._embed = Embed(self)
    #     return self._embed
