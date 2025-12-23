import importlib
from typing import Dict, Type, Optional, List, Any
from menglong.models.providers.base import BaseProvider


class ProviderRegistry:
    """Provider 注册表"""
    
    _registry: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a provider"""
        def wrapper(provider_cls: Type[BaseProvider]):
            cls._registry[name] = provider_cls
            return provider_cls
        return wrapper

    @classmethod
    def get_provider_class(cls, provider_name: str) -> Optional[Type[BaseProvider]]:
        """Get provider class by name"""
        # 如果还没注册，尝试动态按需加载模块
        if provider_name not in cls._registry:
            try:
                # 约定：模块名必须与 provider_name 一致
                importlib.import_module(f"menglong.models.providers.{provider_name}")
            except (ImportError, ModuleNotFoundError):
                # 即使加载失败也不报错，可能该 provider 不是通过文件定义的，或者确实不存在
                pass
                
        return cls._registry.get(provider_name)
    
    @classmethod
    def get_instance(cls, provider_name: str, config_source: Any) -> BaseProvider:
        """
        工厂方法：根据名称获取 Provider 实例，支持按需加载。
        """
        from menglong.utils.config.config_type import ProviderConfig
        
        provider_cls = cls.get_provider_class(provider_name)
        if not provider_cls:
            raise ValueError(
                f"Provider '{provider_name}' not found. "
                f"Ensure 'src/menglong/models/providers/{provider_name}.py' exists "
                f"and contains a class decorated with @ProviderRegistry.register('{provider_name}')"
            )
        
        provider_config = getattr(config_source, "providers", {}).get(provider_name, ProviderConfig())
        return provider_cls(provider_config)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls._registry.keys())
