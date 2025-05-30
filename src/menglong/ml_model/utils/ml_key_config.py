import tomllib as toml

import yaml
import os
from typing import Any, Dict
from pathlib import Path
from ...utils.log import rich_print, RichMessageType


def load_config(config_path: str = ".configs.toml") -> Dict[str, Any]:
    """
    从指定路径加载配置文件，使用toml或yaml格式

    Args:
        config_path: 配置文件路径，默认为 .configs.toml

    Returns:
        配置字典
    """
    # 使用Path对象处理路径
    config_path = Path(config_path)

    # 如果是相对路径，则相对于项目根目录
    if not config_path.is_absolute():
        # 获取当前文件的路径
        current_file = Path(__file__).resolve()

        # 项目根目录：找到包含src目录的父级目录
        project_root = current_file.parent
        while project_root.name != "src" and project_root.parent != project_root:
            project_root = project_root.parent

        # 如果找到了src目录，再上一级就是项目根目录
        if project_root.name == "src":
            project_root = project_root.parent

        config_path = project_root / config_path

    rich_print(f"{config_path}", RichMessageType.INFO, title="尝试加载配置文件")

    if config_path.exists():
        try:
            # # 根据文件扩展名确定使用哪种解析器
            # if config_path.suffix.lower() in [".yaml", ".yml"]:
            #     with open(config_path, "r", encoding="utf-8") as f:
            #         return yaml.safe_load(f)
            # else:  # 默认使用toml
            with open(config_path, "rb") as f:
                return toml.load(f)
        except Exception as e:
            rich_print(f"加载配置文件失败: {e}", RichMessageType.ERROR)
            return {}
    else:
        rich_print(f"配置文件不存在: {config_path}", RichMessageType.WARNING)
        return {}


MODEL_LIST = {
    "gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),
    "gpt-4": ("openai", "gpt-4"),
    "gpt-4-32k": ("openai", "gpt-4-32k"),
}
