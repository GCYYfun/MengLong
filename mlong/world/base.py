from abc import ABC, abstractmethod
from typing import Any, Dict, List, Callable


class World(ABC):
    """环境交互基类"""

    @abstractmethod
    def init(self, config: Dict[str, Any]) -> None:
        """环境初始化方法"""
        pass

    @abstractmethod
    def step(self, actions: List[Dict]) -> Dict[str, Any]:
        """执行环境步进，返回新状态/奖励/终止标志"""
        pass

    @abstractmethod
    def validate_action(self, action: Dict) -> bool:
        """验证动作合法性"""
        pass

    @abstractmethod
    def reset(self, seed: int) -> Dict[str, Any]:
        """重置环境到初始混沌状态

        Args:
            seed: 随机种子用于状态复现
        """
        pass

    @property
    @abstractmethod
    def current_state(self) -> Dict[str, Any]:
        """获取当前环境状态"""
        pass

    # 事件订阅系统
    def __init__(self):
        self._observers: List[Callable[[str, Dict], None]] = []

    def subscribe_event(self, callback: Callable[[str, Dict], None]) -> None:
        """注册环境事件监听"""
        self._observers.append(callback)

    def trigger_event(self, event_type: str, data: Dict) -> None:
        """触发环境事件"""
        for observer in self._observers:
            observer(event_type, data)
