"""
聊天代理模块

这个模块包含三个主要组件：
1. ToolManager - 工具管理器，负责工具的定义、注册和执行
2. WorkflowManager - 工作流管理器，负责工作流的定义和执行
3. SimpleChatAgent - 简化的聊天代理，专注于核心聊天功能

使用示例：
    # 使用简化的聊天代理
    from menglong.agents.chat import SimpleChatAgent, tool, ChatMode

    # 定义工具
    @tool(description="获取天气信息")
    def get_weather(location: str):
        return f"{location}的天气很好"

    # 创建代理
    agent = SimpleChatAgent(mode=ChatMode.AUTO)

    # 聊天
    response = agent.chat("今天北京的天气怎么样？")

    # 异步聊天
    response = await agent.chat_async("今天北京的天气怎么样？")

    # 自主任务执行
    result = await agent.arun("帮我研究一下人工智能的最新发展")
"""

# 新的模块化组件
from ..component.tool_manager import ToolManager, ToolInfo, tool
from .workflow_manager import WorkflowManager, WorkflowStep
from .chat_agent import ChatAgent
from .tool import plan_task

__all__ = [
    # 工具相关
    "ToolManager",
    "ToolInfo",
    "tool",
    # 工作流相关
    "WorkflowManager",
    "WorkflowStep",
    # 聊天代理
    "ChatAgent",
    "plan_task",
]
