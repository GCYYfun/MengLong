from typing import Dict, Any, Optional, List
from .provider import ProviderFactory
from .utils import load_config, MODEL_REGISTRY
from ..utils.log import print_json


class Model:
    """统一模型API的主入口类

    该类负责根据模型ID自动选择并实例化对应厂商的客户端，并提供统一的API调用接口。
    """

    def __init__(self, model_id: Optional[str] = None, configs: Dict[str, Any] = None):
        """初始化Model实例

        Args:
            model_id: 模型ID，如果为None则使用配置文件中的默认值
            configs: 配置信息，会与配置文件中的配置合并
        """
        self.provider_client = {}
        self.provider_config = {}

        # 加载配置文件
        key_config = load_config()
        # print_json(provider_config, title="配置文件内容")

        # 检查配置文件中是否含有default键
        if "default" in key_config:
            # 如果有，将default的值作为默认值
            default_config = key_config.pop("default")
            self.model_id = model_id or default_config.get("model_id")
            self._embed_model_id = default_config.get("embed_id") or None
        else:
            self.model_id = model_id
            self._embed_model_id = None

        self.provider, _ = MODEL_REGISTRY[self.model_id]

        # 合并配置
        self.provider_config = key_config
        if isinstance(configs, Dict[str, Dict]):
            for provider, config in configs.items():
                if provider in self.provider_config:
                    self.provider_config[provider].update(config)
                else:
                    self.provider_config[provider] = config
        elif isinstance(configs, Dict):
            # 如果configs是单个提供商的配置，直接更新
            self.provider_config[self.provider] = configs
        else:
            raise ValueError("Invalid configs format")

        # 初始化核心组件
        self.init_providers(self.provider_config)

    @property
    def chat_model_id(self):
        return self.model_id

    @chat_model_id.setter
    def chat_model_id(self, model_id: str):
        self.model_id = model_id

    @property
    def embed_model_id(self):
        return self._embed_model_id

    @embed_model_id.setter
    def embed_model_id(self, model_id: str):
        self._embed_model_id = model_id

    def init_providers(self, configs: Dict[str, Any]):
        """初始化所有提供商

        Args:
            configs: 提供商配置信息
        """
        for provider, provider_config in configs.items():
            if provider == "default":
                continue
            provider = self.provider_validate(provider)
            self.provider_client[provider] = ProviderFactory.create_provider(
                provider, provider_config
            )

    def provider_validate(self, provider: str) -> str:
        """验证提供商是否支持

        Args:
            provider: 提供商名称

        Returns:
            验证后的提供商名称

        Raises:
            ValueError: 如果提供商不支持
        """
        available_providers = ProviderFactory.list_provider()
        if provider not in available_providers:
            raise ValueError(f"Provider {provider} is not supported")
        return provider

    def get_or_create_client(self, provider: str) -> Any:
        """获取或创建提供商后端

        Args:
            provider: 提供商名称

        Returns:
            提供商实例
        """
        if provider not in self.provider_client:
            config = self.provider_config.get(provider, {})
            self.provider_client[provider] = ProviderFactory.create_provider(
                provider, config
            )
        return self.provider_client[provider]

    def chat(self, messages: List[Dict[str, Any]] = [], model_id: str = None, **kwargs):
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
        # 默认检查
        if model_id is None:
            model_id = self.model_id
        else:
            if model_id not in MODEL_REGISTRY:
                raise ValueError(f"Model {model_id} is not supported")

        # 获取提供商和模型
        provider, model = MODEL_REGISTRY[model_id]
        # 根据 model id 获取提供商
        self.provider = provider
        # 获取提供商实例
        model_client = self.get_or_create_client(provider)
        if not model_client:
            raise ValueError(f"Provider {provider} is not supported")

        if messages is None or not isinstance(messages, list):
            raise ValueError("Messages must be a non-empty list")
        # 调用提供商的chat方法
        # try:
        return model_client.chat(messages=messages, model_id=model_id, **kwargs)
        # except Exception as e:
        #     # 统一错误处理
        #     raise RuntimeError(f"Chat request failed: {str(e)}")

    def embed(self, texts: List[str] = [], model_id: str = None, **kwargs):
        """发送嵌入请求

        Args:
            model_id: 模型ID，如果为None则使用默认模型
            texts: 文本列表
            **kwargs: 其他参数
        Returns:
            模型响应
        Raises:
            ValueError: 如果模型或提供商不支持
        """
        if model_id is None:
            model_id = self.embed_model_id

        if model_id not in MODEL_REGISTRY:
            raise ValueError(f"Model {model_id} is not supported")

        provider, model = MODEL_REGISTRY[model_id]
        self.provider = provider

        model_client = self.get_or_create_client(provider)
        if not model_client:
            raise ValueError(f"Provider {provider} is not supported")

        try:
            return model_client.embed(model_id=model_id, texts=texts, **kwargs)
        except Exception as e:
            # 统一错误处理
            raise RuntimeError(f"Chat request failed: {str(e)}")
