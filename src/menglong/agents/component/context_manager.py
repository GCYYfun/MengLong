from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ...ml_model.schema import user, assistant, system, tool, res_message


@dataclass
class MessagesContext:
    """对话消息上下文"""

    context: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ReasoningCache:
    """推理内容数据结构"""

    context: List[Dict[str, Any]] = field(default_factory=list)


class ContextManager:
    """上下文管理器，负责管理对话上下文"""

    def __init__(self):
        """初始化上下文管理器"""
        self._messages = MessagesContext()
        self._reasoning = ReasoningCache()
        self.tokens = 0
        self.total_price = 0.0

    def reset(self):
        """重置对话上下文"""
        self._messages.context = []
        self._reasoning.context = []

    def clear(self):
        """清除对话上下文，但保留系统消息"""
        if len(self._messages.context) != 0 and isinstance(
            self._messages.context[0], system
        ):
            self._messages.context = self._messages.context[:1]

    @property
    def system(self) -> Optional[str]:
        """获取系统消息内容"""
        if len(self._messages.context) != 0:
            if isinstance(self._messages.context[0], system):
                return self._messages.context[0].content
        return None

    @property
    def messages(self) -> List[Dict[str, Any]]:
        """获取当前对话上下文"""
        return self._messages.context

    @system.setter
    def system(self, message: str):
        """设置系统消息"""
        if len(self._messages.context) != 0:
            if isinstance(self._messages.context[0], system):
                self._messages.context[0].content = message
        else:
            self._messages.context.append(system(content=message))

    def add_user_message(self, message: str):
        """添加用户消息

        Args:
            message: 用户消息内容

        Raises:
            ValueError: 如果用户消息不符合对话规则
        """
        # 检查是否有连续的用户消息
        if len(self._messages.context) == 0:
            self._messages.context.append(user(content=message))
        elif (
            isinstance(self._messages.context[-1], assistant)
            or isinstance(self._messages.context[-1], system)
            or isinstance(self._messages.context[-1], res_message)
        ):
            self._messages.context.append(user(content=message))
        else:
            raise ValueError(
                f"User message must follow system or assistant message,now you context is {self._messages.context},message is {message}"
            )

    def add_assistant_response(self, message: str, reasoning: Optional[str] = None):
        """添加助手响应

        Args:
            message: 助手响应内容

        Raises:
            ValueError: 如果助手响应不符合对话规则
        """
        if self._messages.context and (
            isinstance(self._messages.context[-1], user)
            or isinstance(self._messages.context[-1], tool)
        ):
            self._messages.context.append(assistant(content=message))
        else:
            raise ValueError("Assistant response must follow user message")

    def add_assistant_reasoning(self, query: str, reasoning: str, answers: str):
        """添加助手推理消息

        Args:
            query: 用户查询内容
            reasoning: 助手推理内容

        Raises:
            ValueError: 如果助手推理不符合对话规则
        """
        if self._reasoning.context:
            self._reasoning.context.append(
                {"query": query, "reasoning": reasoning, "answers": answers}
            )
        else:
            raise ValueError("Assistant reasoning must follow assistant response")

    def pop(self) -> Dict[str, Any]:
        """移除并返回最后一条消息"""
        if not self._messages.context:
            raise IndexError("pop from empty context")
        return self._messages.context.pop()


class ATAContextManager:
    """Agent to Agent 上下文管理器"""

    def __init__(self):
        """初始化上下文管理器"""
        self.context_manager = {
            "active": ContextManager(),
            "passive": ContextManager(),
            "topic": ContextManager(),
        }

    def reset(self):
        """重置上下文管理器"""
        for key in self.context_manager:
            self.context_manager[key].reset()

    def clear(self):
        """清除上下文管理器"""
        for key in self.context_manager:
            self.context_manager[key].clear()

    def get_context(self, key: str) -> List[Dict[str, Any]]:
        """获取指定角色的上下文
        Args:
            key: 角色名称
        Returns:
            上下文列表
        """
        return self.context_manager[key].messages

    def get_system(self, key: str) -> Optional[str]:
        """获取指定角色的系统消息
        Args:
            key: 角色名称
        Returns:
            系统消息内容
        """
        return self.context_manager[key].system

    @property
    def active(self) -> ContextManager:
        """获取主动角色的上下文管理器"""
        return self.context_manager["active"]

    @property
    def passive(self) -> ContextManager:
        """获取被动角色的上下文管理器"""
        return self.context_manager["passive"]

    @property
    def topic(self) -> ContextManager:
        """获取话题的上下文管理器"""
        return self.context_manager["topic"]

    @active.setter
    def active(self, context: ContextManager):
        """设置主动角色的系统消息"""
        self.context_manager["active"] = context

    @passive.setter
    def passive(self, context: ContextManager):
        """设置被动角色的系统消息"""
        self.context_manager["passive"] = context

    @topic.setter
    def topic(self, context: ContextManager):
        """设置话题的系统消息"""
        self.context_manager["topic"] = context
