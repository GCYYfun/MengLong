"""
监控配置模块

提供通过配置文件控制监控行为的功能。
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .ml_monitor import (
    get_monitor,
    enable_monitoring,
    disable_monitoring,
    set_monitor_level,
    MonitorCategory,
    MonitorLevel,
)


class MonitorConfig:
    """监控配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = {}

        # 默认配置
        self.default_config = {
            "monitor": {
                "enabled": True,
                "level": "INFO",
                "categories": ["ERROR_TRACKING"],
                "max_history": 1000,
                "handlers": {
                    "console": {"enabled": True, "format": "simple"},
                    "file": {
                        "enabled": False,
                        "directory": "./logs",
                        "max_size": "10MB",
                        "backup_count": 5,
                    },
                },
                "filters": {
                    "min_level": "INFO",
                    "exclude_categories": [],
                    "include_sources": [],
                },
            }
        }

        # 加载配置
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        # 1. 尝试从指定路径加载
        if self.config_path and os.path.exists(self.config_path):
            self._load_from_file(self.config_path)
            return

        # 2. 尝试从常见位置加载
        possible_paths = [
            "monitor_config.yaml",
            "monitor_config.json",
            ".monitor.yaml",
            ".monitor.json",
            "config/monitor.yaml",
            "config/monitor.json",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                self._load_from_file(path)
                return

        # 3. 尝试从环境变量加载
        self._load_from_env()

        # 4. 使用默认配置
        self.config = self.default_config.copy()

    def _load_from_file(self, file_path: str) -> None:
        """从文件加载配置"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.endswith((".yaml", ".yml")):
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)

            # 合并默认配置
            self._merge_with_defaults()

        except Exception as e:
            print(f"警告: 无法加载配置文件 {file_path}: {e}")
            self.config = self.default_config.copy()

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        config = {"monitor": {}}

        # 基础配置
        if os.getenv("ML_MONITOR_ENABLED"):
            config["monitor"]["enabled"] = (
                os.getenv("ML_MONITOR_ENABLED").lower() == "true"
            )

        if os.getenv("ML_MONITOR_LEVEL"):
            config["monitor"]["level"] = os.getenv("ML_MONITOR_LEVEL")

        if os.getenv("ML_MONITOR_CATEGORIES"):
            categories = os.getenv("ML_MONITOR_CATEGORIES").split(",")
            config["monitor"]["categories"] = [cat.strip() for cat in categories]

        if os.getenv("ML_MONITOR_MAX_HISTORY"):
            config["monitor"]["max_history"] = int(os.getenv("ML_MONITOR_MAX_HISTORY"))

        # 文件输出配置
        if os.getenv("ML_MONITOR_LOG_DIR"):
            config["monitor"]["handlers"] = {
                "file": {"enabled": True, "directory": os.getenv("ML_MONITOR_LOG_DIR")}
            }

        if config["monitor"]:
            self.config = config
            self._merge_with_defaults()
        else:
            self.config = self.default_config.copy()

    def _merge_with_defaults(self) -> None:
        """合并默认配置"""

        def merge_dict(base: dict, update: dict) -> dict:
            result = base.copy()
            for key, value in update.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = merge_dict(self.default_config, self.config)

    def apply_config(self) -> None:
        """应用配置到监控器"""
        monitor_config = self.config.get("monitor", {})

        # 启用/禁用监控
        if not monitor_config.get("enabled", True):
            disable_monitoring()
            return

        # 设置监控级别
        level_str = monitor_config.get("level", "INFO")
        try:
            level = MonitorLevel(level_str)
            set_monitor_level(level)
        except ValueError:
            print(f"警告: 无效的监控级别 {level_str}")

        # 启用监控分类
        categories_str = monitor_config.get("categories", [])
        if categories_str:
            try:
                categories = [MonitorCategory(cat) for cat in categories_str]
                enable_monitoring(*categories)
            except ValueError as e:
                print(f"警告: 无效的监控分类: {e}")
        else:
            enable_monitoring()  # 启用所有

        # 设置最大历史记录数
        max_history = monitor_config.get("max_history", 1000)
        get_monitor()._max_history = max_history

        # 配置处理器
        self._setup_handlers(monitor_config.get("handlers", {}))

    def _setup_handlers(self, handlers_config: Dict[str, Any]) -> None:
        """设置处理器"""
        monitor = get_monitor()

        # 文件处理器
        file_config = handlers_config.get("file", {})
        if file_config.get("enabled", False):
            log_dir = Path(file_config.get("directory", "./logs"))
            log_dir.mkdir(exist_ok=True)

            def file_handler(event):
                log_file = log_dir / f"{event.category.value}.log"
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

            monitor.add_handler(file_handler)

    def save_config(self, file_path: Optional[str] = None) -> None:
        """保存当前配置到文件"""
        if not file_path:
            file_path = self.config_path or "monitor_config.yaml"

        with open(file_path, "w", encoding="utf-8") as f:
            if file_path.endswith((".yaml", ".yml")):
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()

    def update_config(self, updates: Dict[str, Any]) -> None:
        """更新配置"""

        def update_dict(base: dict, updates: dict) -> dict:
            for key, value in updates.items():
                if (
                    key in base
                    and isinstance(base[key], dict)
                    and isinstance(value, dict)
                ):
                    update_dict(base[key], value)
                else:
                    base[key] = value

        update_dict(self.config, updates)


# 全局配置实例
_global_config = None


def get_config() -> MonitorConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = MonitorConfig()
    return _global_config


def init_monitoring(config_path: Optional[str] = None) -> None:
    """初始化监控系统"""
    global _global_config
    _global_config = MonitorConfig(config_path)
    _global_config.apply_config()


def create_default_config(file_path: str = "monitor_config.yaml") -> None:
    """创建默认配置文件"""
    config = MonitorConfig()
    config.save_config(file_path)
    print(f"默认配置文件已创建: {file_path}")


def load_config_from_dict(config_dict: Dict[str, Any]) -> None:
    """从字典加载配置"""
    config = get_config()
    config.config = config_dict
    config._merge_with_defaults()
    config.apply_config()


# 便捷配置函数
def enable_debug_monitoring() -> None:
    """启用调试监控配置"""
    load_config_from_dict(
        {
            "monitor": {
                "enabled": True,
                "level": "DEBUG",
                "categories": [
                    "MODEL_INTERACTION",
                    "TOOL_CALLS",
                    "CONTEXT_MANAGEMENT",
                    "PERFORMANCE",
                    "ERROR_TRACKING",
                ],
            }
        }
    )


def enable_production_monitoring() -> None:
    """启用生产环境监控配置"""
    load_config_from_dict(
        {
            "monitor": {
                "enabled": True,
                "level": "ERROR",
                "categories": ["ERROR_TRACKING", "PERFORMANCE"],
                "handlers": {
                    "console": {"enabled": False},
                    "file": {"enabled": True, "directory": "./logs"},
                },
            }
        }
    )


def enable_tool_debugging() -> None:
    """启用工具调试监控配置"""
    load_config_from_dict(
        {
            "monitor": {
                "enabled": True,
                "level": "DEBUG",
                "categories": ["TOOL_CALLS", "ERROR_TRACKING"],
            }
        }
    )


def enable_model_debugging() -> None:
    """启用模型调试监控配置"""
    load_config_from_dict(
        {
            "monitor": {
                "enabled": True,
                "level": "DEBUG",
                "categories": ["MODEL_INTERACTION", "ERROR_TRACKING"],
            }
        }
    )
