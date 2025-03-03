"""配置管理模块，提供统一的配置加载和访问接口。"""

import os
from typing import Any, Dict, Optional
import toml


class Config:
    """配置管理类，负责加载和管理配置信息"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._config: Dict[str, Any] = {}
            self._load_config()

    def _load_config(self, config_path: Optional[str] = None) -> None:
        """加载环境变量配置
        
        Args:
            config_path: .config文件路径，如果为None则在项目根目录查找
        """
        # 默认在项目根目录查找.config文件
        if config_path is None:
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.config')
        # 加载.config文件
        if os.path.exists(config_path):
            try:
                self._config = toml.load(config_path)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键名
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self._config[key] = value

# 全局配置实例
config = Config()