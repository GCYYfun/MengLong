"""
Agent模块，包含智能代理相关的类和函数。
"""


class Agent:
    """
    基本的智能代理类。

    Attributes:
        name (str): 代理的名称
    """

    def __init__(self, name="Default Agent"):
        """
        初始化一个新的智能代理实例。

        Args:
            name (str): 代理的名称，默认为"Default Agent"
        """
        self.name = name

    def run(self):
        """
        运行智能代理。

        Returns:
            str: 代理的运行状态信息
        """
        return f"{self.name} is running!"
