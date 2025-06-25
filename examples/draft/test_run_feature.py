#!/usr/bin/env python3
"""
ChatAgent.run() 功能测试
=======================
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, RichMessageType


@tool(name="test_tool", description="测试工具")
def test_tool(message: str) -> str:
    """简单的测试工具"""
    return f"工具收到消息: {message}"


def test_basic_run():
    """测试基本的 run 功能"""
    rich_print("🧪 测试 ChatAgent.run() 基本功能", RichMessageType.INFO)

    # 创建 Agent
    agent = ChatAgent(mode=ChatMode.AUTO, system="你是一个测试助手。")

    # 注册工具
    agent.register_tools_from_functions(test_tool)

    # 测试任务
    task = "请使用 test_tool 发送一条消息'Hello World'"

    rich_print(f"📋 任务: {task}", RichMessageType.INFO)

    try:
        # 执行任务
        result = agent.run(task=task, max_iterations=2)

        rich_print("✅ 执行成功!", RichMessageType.SUCCESS)
        rich_print(f"状态: {result['status']}", RichMessageType.SYSTEM)
        rich_print(f"轮次: {result['iterations']}", RichMessageType.SYSTEM)
        rich_print(f"用时: {result['execution_time']:.2f}s", RichMessageType.SYSTEM)

        return True

    except Exception as e:
        rich_print(f"❌ 执行失败: {str(e)}", RichMessageType.ERROR)
        import traceback

        rich_print(f"错误详情: {traceback.format_exc()}", RichMessageType.ERROR)
        return False


if __name__ == "__main__":
    success = test_basic_run()
    if success:
        rich_print("🎉 测试通过!", RichMessageType.SUCCESS)
    else:
        rich_print("💥 测试失败!", RichMessageType.ERROR)
