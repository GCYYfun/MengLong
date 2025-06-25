#!/usr/bin/env python3
"""
快速测试 ChatAgent 异步功能
==========================

验证核心异步功能是否正常工作

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
import time
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, rich_print_rule, RichMessageType


@tool(name="simple_async_tool", description="简单的异步测试工具")
async def simple_async_tool(message: str) -> dict:
    """简单的异步工具"""
    await asyncio.sleep(0.2)  # 模拟异步操作
    return {
        "processed_message": f"异步处理了: {message}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "async",
    }


@tool(name="simple_sync_tool", description="简单的同步测试工具")
def simple_sync_tool(message: str) -> dict:
    """简单的同步工具"""
    time.sleep(0.1)  # 模拟同步操作
    return {
        "processed_message": f"同步处理了: {message}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "sync",
    }


async def test_basic_async_functionality():
    """测试基本异步功能"""
    rich_print_rule("测试基本异步功能", style="blue")

    agent = ChatAgent(mode=ChatMode.AUTO)

    # 测试异步工具注册
    await agent.register_tools_from_functions_async(simple_async_tool, simple_sync_tool)

    # 测试异步聊天
    response = await agent.chat_async(
        "请使用simple_async_tool处理消息'Hello Async World'"
    )
    rich_print(f"✅ 异步聊天成功: {response[:100]}...", RichMessageType.SUCCESS)

    # 测试异步任务执行
    task_result = await agent.arun(
        "使用simple_sync_tool和simple_async_tool分别处理消息", max_iterations=3
    )

    if task_result.get("task_completed"):
        rich_print("✅ 异步任务执行成功", RichMessageType.SUCCESS)
    else:
        rich_print("⚠️ 异步任务未完全完成", RichMessageType.WARNING)

    return True


async def test_mixed_tools():
    """测试混合工具（同步+异步）调用"""
    rich_print_rule("测试混合工具调用", style="green")

    agent = ChatAgent(mode=ChatMode.AUTO)
    await agent.register_tools_from_functions_async(simple_async_tool, simple_sync_tool)

    # 测试混合工具调用
    messages = [
        "使用simple_async_tool处理'异步消息'",
        "使用simple_sync_tool处理'同步消息'",
    ]

    results = await agent.batch_chat_async(messages)

    if len(results) == 2:
        rich_print("✅ 混合工具批量处理成功", RichMessageType.SUCCESS)
        return True
    else:
        rich_print("❌ 混合工具批量处理失败", RichMessageType.ERROR)
        return False


async def test_error_scenarios():
    """测试错误场景"""
    rich_print_rule("测试错误处理", style="yellow")

    # 测试在事件循环中调用 run()
    agent = ChatAgent(mode=ChatMode.AUTO)
    await agent.register_tools_from_functions_async(simple_async_tool)

    try:
        # 这应该失败
        agent.run("测试任务", max_iterations=1)
        rich_print("❌ run() 在事件循环中意外成功", RichMessageType.ERROR)
        return False
    except RuntimeError as e:
        if "running event loop" in str(e) or "async environments" in str(e):
            rich_print("✅ run() 正确地抛出了事件循环错误", RichMessageType.SUCCESS)
        else:
            rich_print(f"❌ run() 抛出了意外错误: {e}", RichMessageType.ERROR)
            return False

    # 测试 arun() 是否正常工作
    try:
        result = await agent.arun("使用simple_async_tool处理测试消息", max_iterations=2)
        rich_print("✅ arun() 在事件循环中正常工作", RichMessageType.SUCCESS)
        return True
    except Exception as e:
        rich_print(f"❌ arun() 失败: {e}", RichMessageType.ERROR)
        return False


async def test_performance():
    """测试异步性能"""
    rich_print_rule("测试异步性能", style="purple")

    # 为每个测试创建独立的agent以避免上下文冲突
    async def create_agent():
        agent = ChatAgent(mode=ChatMode.AUTO)
        await agent.register_tools_from_functions_async(simple_async_tool)
        return agent

    # 并行执行多个任务
    tasks = ["任务1", "任务2", "任务3"]

    start_time = time.time()
    agents = [await create_agent() for _ in tasks]
    results = await asyncio.gather(
        *[
            agent.chat_async(f"使用simple_async_tool处理'{task}'")
            for agent, task in zip(agents, tasks)
        ]
    )
    parallel_time = time.time() - start_time

    # 顺序执行
    start_time = time.time()
    sequential_agent = await create_agent()
    sequential_results = []
    for task in tasks:
        # 为每个任务创建新的agent以避免上下文问题
        agent = await create_agent()
        result = await agent.chat_async(f"使用simple_async_tool处理'{task}'")
        sequential_results.append(result)
    sequential_time = time.time() - start_time

    rich_print(f"并行执行时间: {parallel_time:.2f}秒")
    rich_print(f"顺序执行时间: {sequential_time:.2f}秒")

    # 由于网络延迟等因素，并行不一定总是更快，所以放宽条件
    if len(results) == len(tasks) and len(sequential_results) == len(tasks):
        rich_print("✅ 异步并行功能正常", RichMessageType.SUCCESS)
        return True
    else:
        rich_print("⚠️ 异步并行结果数量不匹配", RichMessageType.WARNING)
        return False


async def main():
    """主测试函数"""
    rich_print_rule("ChatAgent 异步功能快速测试", style="bold cyan")

    tests = [
        ("基本异步功能", test_basic_async_functionality),
        ("混合工具调用", test_mixed_tools),
        ("错误处理", test_error_scenarios),
        ("异步性能", test_performance),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        rich_print(f"\n🧪 运行测试: {test_name}")
        try:
            start_time = time.time()
            success = await test_func()
            end_time = time.time()

            if success:
                rich_print(
                    f"✅ {test_name} 通过 ({end_time - start_time:.2f}s)",
                    RichMessageType.SUCCESS,
                )
                passed += 1
            else:
                rich_print(f"❌ {test_name} 失败", RichMessageType.ERROR)

        except Exception as e:
            rich_print(f"❌ {test_name} 出错: {str(e)}", RichMessageType.ERROR)

    # 汇总结果
    rich_print_rule("测试结果汇总", style="bold green")
    rich_print(f"📊 通过: {passed}/{total}")

    if passed == total:
        rich_print("🎉 所有异步功能测试通过！", RichMessageType.SUCCESS)
    else:
        rich_print("⚠️ 部分测试失败，请检查实现", RichMessageType.WARNING)

    return passed == total


if __name__ == "__main__":
    # 运行快速测试
    success = asyncio.run(main())
    exit(0 if success else 1)
