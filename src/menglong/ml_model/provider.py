from abc import ABC
from typing import List, Set
from pathlib import Path
import importlib


class Provider(ABC):
    """所有厂商适配器的基类，定义统一的接口方法

    每个厂商适配器需要继承此类并实现必要的接口方法
    """

    provider_name: str

    def __init__(self, config: dict):
        """初始化提供商实例

        Args:
            config: 提供商配置信息
        """
        self.config = config


class ProviderFactory:
    """工厂类，负责根据提供商名称创建对应的客户端实例"""

    @staticmethod
    def create_provider(provider_name: str, provider_config: dict) -> Provider:
        """创建提供商实例

        Args:
            provider_name: 提供商名称
            provider_config: 提供商配置信息

        Returns:
            提供商实例

        Raises:
            ValueError: 如果提供商不支持或类未找到
        """
        # 自动构建模块路径
        # 统一开源提供商名称
        if (
            provider_name == "vllm"
            or provider_name == "ollama"
            or provider_name == "osoai"
        ):
            provider_class_name = f"OpenSourceProvider"
            provider_module_name = f"osoai_provider"
        else:
            provider_class_name = f"{provider_name.capitalize()}Provider"
            provider_module_name = f"{provider_name}_provider"
        # 根据项目结构自动确定模块路径
        module_path = f"{Path(__file__).parent.parent.name}.{Path(__file__).parent.name}.providers.{provider_module_name}"
        try:
            # 动态导入模块
            module = importlib.import_module(module_path)
            # 从模块中获取类
            provider_class = getattr(module, provider_class_name)
            # 创建类实例
            provider_instance = provider_class(provider_config)
            return provider_instance
        # except ImportError:
        # raise ValueError(f"Provider '{provider_name}' 不支持")
        except AttributeError:
            raise ValueError(f"Provider类 '{provider_class_name}' 在模块中未找到")

    @classmethod
    def list_provider(cls) -> Set[str]:
        """获取所有可用的提供商名称

        Returns:
            提供商名称集合
        """
        provider_files = (
            Path(__file__).parent.parent / Path(__file__).parent / "providers"
        ).glob("*_provider.py")
        return {file.stem.replace("_provider", "") for file in provider_files}
