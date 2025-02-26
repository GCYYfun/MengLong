"""
Adapted from https://github.com/andrewyng/aisuite/blob/main/aisuite/client.py
"""

from typing import List
from mlong.provider import ProviderFactory
from mlong.types.type_model import MODEL_LIST

# from mlong.utils import get_provider_and_model


class Model:

    def __init__(self, model_id: str = None, model_configs: dict = None):
        """
        模型的一个抽象, 通过 model 可以调用不同的模型, 但是 model 本身并不关心模型的实现细节, 只关心模型的调用方式.
        model_id: 模型的 id, 用于区分不同的模型
        model_configs: 模型的配置信息 (TODO: 需要进一步明确 格式，作用范围)
        """
        # self.default_model = "aws.us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        # anthropic.claude-3-7-sonnet-20250219-v1:0
        if model_id is None:
            self.model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        else:
            if model_id not in MODEL_LIST:
                raise ValueError(f"Model {model_id} is not supported")
            self.model_id = model_id
        # Configs
        if model_configs is None:
            self.model_configs = {}
        else:
            self.model_configs = model_configs

        # Backends
        self.backends = {}

        # API
        self._chat = None
        self._embed = None

        # Init
        self.init_backends()

    def init_backends(self):
        for provider, config in self.model_configs.items():
            provider = self.validate(provider)
            self.backends[provider] = ProviderFactory.provider(provider, config)

    def validate(self, provider):
        available_provider = ProviderFactory.list_provider()
        if provider not in available_provider:
            raise ValueError(f"Provider {provider} is not supported")
        return provider

    def chat(self, model_id: str = None, messages: List[str] = [], **kwargs):
        if model_id is None:
            model_id = self.model_id
        else:
            if model_id not in MODEL_LIST:
                raise ValueError(f"Model {model_id} is not supported")
            model_id = model_id

        provider, model = MODEL_LIST[model_id]

        available_provider = ProviderFactory.list_provider()

        if provider not in available_provider:
            raise ValueError(f"Provider {provider} is not supported")

        if provider not in self.backends:
            config = self.model_configs.get(provider, {})
            self.backends[provider] = ProviderFactory.provider(provider, config)

        model_client = self.backends.get(provider)

        if not model_client:
            raise ValueError(f"Provider {provider} is not supported")

        return model_client.chat(messages=messages, model=model, **kwargs)

    # @property
    # def embed(self):
    #     if not self._embed:
    #         self._embed = Embed(self)
    #     return self._embed
