import tomllib as toml
from typing import Any, Dict
from pathlib import Path


def load_config(config_path: str = ".configs.toml") -> Dict[str, Any]:
    """
    从指定路径加载配置文件，使用toml格式

    Args:
        config_path: 配置文件路径，默认为 .configs

    Returns:
        配置字典
    """
    config_path = Path(config_path)
    
    # 如果是相对路径，则相对于项目根目录
    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / config_path
    
    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                return toml.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    return {}


MODEL_LIST = {
    "gpt-3.5-turbo": ("openai", "gpt-3.5-turbo"),
    "gpt-4": ("openai", "gpt-4"),
    "gpt-4-32k": ("openai", "gpt-4-32k"),
}