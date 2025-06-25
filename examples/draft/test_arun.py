#!/usr/bin/env python3
"""
测试 ChatAgent.arun() 异步功能
=============================

验证在异步环境中使用 ChatAgent.arun() 方法的正确性

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, rich_print_rule, RichMessageType
import time
from typing import Dict, Any


@tool(name="simple_tool", description="简单的测试工具")
def simple_tool(message: str) -> Dict[str, Any]:
    """简单的测试工具"""
    time.sleep(0.5)  # 模拟工作
    return {
        "message": f"处理了消息: {message}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success",
    }


async def test_arun_basic():
    """测试基本异步功能"""
    rich_print_rule("测试 arun() 基本功能", style="blue")

    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_tools_from_functions(simple_tool)

    task = "请使用simple_tool处理消息'Hello World'"

    try:
        result = await agent.arun(task, max_iterations=3)

        rich_print("✅ arun() 测试成功", RichMessageType.SUCCESS)
        rich_print(f"任务完成: {result.get('task_completed', False)}")
        rich_print(f"执行轮次: {result.get('iterations_used', 0)}")

        return True
    except Exception as e:
        rich_print(f"❌ arun() 测试失败: {str(e)}", RichMessageType.ERROR)
        return False


async def test_arun_vs_run_in_loop():
    """测试在事件循环中调用 run() 和 arun() 的差异"""
    rich_print_rule("测试事件循环中的方法差异", style="yellow")

    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_tools_from_functions(simple_tool)

    task = "使用simple_tool处理测试消息"

    # 测试 run() 方法（应该失败）
    rich_print("🔍 测试 run() 方法在事件循环中...", RichMessageType.INFO)
    try:
        result = agent.run(task, max_iterations=2)
        rich_print("❌ run() 方法意外成功（这不应该发生）", RichMessageType.WARNING)
        run_success = True
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            rich_print("✅ run() 方法正确地抛出了事件循环错误", RichMessageType.SUCCESS)
            run_success = False
        else:
            rich_print(f"❌ run() 方法抛出了意外错误: {str(e)}", RichMessageType.ERROR)
            run_success = False

    # 测试 arun() 方法（应该成功）
    rich_print("🔍 测试 arun() 方法在事件循环中...", RichMessageType.INFO)
    try:
        result = await agent.arun(task, max_iterations=2)
        rich_print("✅ arun() 方法成功执行", RichMessageType.SUCCESS)
        arun_success = True
    except Exception as e:
        rich_print(f"❌ arun() 方法失败: {str(e)}", RichMessageType.ERROR)
        arun_success = False

    return not run_success and arun_success  # run应该失败，arun应该成功


async def test_multiple_arun_parallel():
    """测试并行执行多个 arun() 任务"""
    rich_print_rule("测试并行执行 arun()", style="purple")

    # 创建多个 agent
    agents = []
    for i in range(3):
        agent = ChatAgent(mode=ChatMode.AUTO, system=f"你是助手 {i+1}")
        agent.register_tools_from_functions(simple_tool)
        agents.append(agent)

    # 创建不同任务
    tasks = [
        "使用simple_tool处理消息'任务1'",
        "使用simple_tool处理消息'任务2'",
        "使用simple_tool处理消息'任务3'",
    ]

    try:
        # 并行执行
        start_time = time.time()
        results = await asyncio.gather(
            *[agent.arun(task, max_iterations=2) for agent, task in zip(agents, tasks)]
        )
        end_time = time.time()

        rich_print(
            f"✅ 并行执行成功，用时: {end_time - start_time:.2f}秒",
            RichMessageType.SUCCESS,
        )

        success_count = sum(
            1 for result in results if result.get("task_completed", False)
        )
        rich_print(f"成功任务: {success_count}/{len(results)}")

        return success_count == len(results)

    except Exception as e:
        rich_print(f"❌ 并行执行失败: {str(e)}", RichMessageType.ERROR)
        return False


async def main():
    """主测试函数"""
    rich_print_rule("ChatAgent.arun() 异步功能测试", style="bold green")

    tests = [
        ("基本功能测试", test_arun_basic),
        ("事件循环差异测试", test_arun_vs_run_in_loop),
        ("并行执行测试", test_multiple_arun_parallel),
    ]

    results = []

    for test_name, test_func in tests:
        rich_print(f"\n🧪 运行测试: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            if success:
                rich_print(f"✅ {test_name} 通过", RichMessageType.SUCCESS)
            else:
                rich_print(f"❌ {test_name} 失败", RichMessageType.ERROR)
        except Exception as e:
            rich_print(f"❌ {test_name} 出错: {str(e)}", RichMessageType.ERROR)
            results.append((test_name, False))

    # 汇总结果
    rich_print_rule("测试结果汇总", style="cyan")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        rich_print(f"{test_name}: {status}")

    rich_print(
        f"\n📊 总计: {passed}/{total} 测试通过",
        RichMessageType.SUCCESS if passed == total else RichMessageType.WARNING,
    )

    if passed == total:
        rich_print("🎉 所有测试通过！arun() 功能正常", RichMessageType.SUCCESS)
    else:
        rich_print("⚠️ 部分测试失败，请检查实现", RichMessageType.WARNING)


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main())
