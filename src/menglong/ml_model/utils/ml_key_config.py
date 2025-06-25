import tomllib as toml

import yaml
import os
from typing import Any, Dict
from pathlib import Path
from ...utils.log import print_message, MessageType


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

    # 如果是相对路径，则尝试多种策略来定位配置文件
    if not config_path.is_absolute():
        # 1. 首先，尝试从当前工作目录加载（适用于作为库被其他项目使用的情况）
        cwd_config = Path.cwd() / config_path
        if cwd_config.exists():
            print_message(f"在当前工作目录找到配置文件: {cwd_config}", MessageType.INFO)
            config_path = cwd_config
        else:
            # 2. 获取当前文件的路径
            current_file = Path(__file__).resolve()

            # 3. 尝试查找原项目的根目录：找到包含src目录的父级目录
            project_root = current_file.parent
            while project_root.name != "src" and project_root.parent != project_root:
                project_root = project_root.parent

            # 如果找到了src目录，再上一级就是项目根目录
            if project_root.name == "src":
                project_root = project_root.parent
                lib_config_path = project_root / config_path

                if lib_config_path.exists():
                    print_message(
                        f"在库项目根目录找到配置文件: {lib_config_path}",
                        MessageType.INFO,
                    )
                    config_path = lib_config_path
                else:
                    # 4. 如果库项目根目录也没有找到，保持原始路径（可能之后会提示不存在）
                    print_message(
                        f"未找到配置文件，将使用原始路径: {config_path}",
                        MessageType.WARNING,
                    )

    print_message(f"{config_path}", MessageType.INFO, title="尝试加载配置文件")

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
            print_message(f"加载配置文件失败: {e}", MessageType.ERROR)
            return {}
    else:
        print_message(f"配置文件不存在: {config_path}", MessageType.WARNING)
        return {}
