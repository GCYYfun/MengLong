"""
代理工厂模块，用于创建不同类型的智能代理。
"""

from . import Agent


def create_agent(agent_type="basic", name=None):
    """
    创建一个指定类型的智能代理。

    Args:
        agent_type (str): 代理类型，目前支持 "basic"
        name (str, optional): 代理名称

    Returns:
        Agent: 创建的代理实例

    Raises:
        ValueError: 当指定的代理类型不存在时
    """
    if agent_type == "basic":
        return Agent(name=name or "基础代理")
    else:
        raise ValueError(f"不支持的代理类型: {agent_type}")
