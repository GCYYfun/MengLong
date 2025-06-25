"""
ChatAgent 完整异步功能演示
========================

展示 ChatAgent 的所有异步方法和功能，包括：
- arun() 自主任务执行
- chat_async() 异步聊天
- chat_stream_async() 异步流式聊天
- 异步工具注册和调用
- 异步工作流执行
- 异步批量处理

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
import time
from typing import Dict, Any, List
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, rich_print_rule, RichMessageType


# ==================== 异步工具定义 ====================


@tool(name="async_web_search", description="异步网络搜索工具")
async def async_web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """异步网络搜索"""
    rich_print(f"🔍 异步搜索: {query}", RichMessageType.INFO)

    # 模拟异步API调用
    await asyncio.sleep(1)

    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=max_results))

            for i, result in enumerate(search_results):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "relevance": 1.0 - (i * 0.1),
                    }
                )

        rich_print(
            f"✅ 异步搜索完成，找到 {len(results)} 个结果", RichMessageType.SUCCESS
        )

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": time.time(),
            "source": "DuckDuckGo_Async",
        }

    except Exception as e:
        rich_print(f"❌ 异步搜索出错，使用模拟结果: {str(e)}", RichMessageType.WARNING)
        return {
            "query": query,
            "results": [
                {
                    "title": f"异步模拟搜索结果: {query}",
                    "url": "https://example.com",
                    "snippet": f"关于 {query} 的异步搜索信息",
                }
            ],
            "total_found": 1,
            "search_time": time.time(),
            "source": "Mock_Async",
        }


@tool(name="async_data_processor", description="异步数据处理工具")
async def async_data_processor(data: str, operation: str = "analyze") -> Dict[str, Any]:
    """异步数据处理"""
    rich_print(f"📊 异步处理数据: {operation}", RichMessageType.INFO)

    # 模拟复杂的异步数据处理
    await asyncio.sleep(0.5)

    operations = {
        "analyze": "异步数据分析完成，发现重要模式",
        "summarize": "异步数据摘要生成完成",
        "validate": "异步数据验证通过",
        "transform": "异步数据转换完成",
    }

    result = operations.get(operation, "未知异步操作")

    return {
        "operation": operation,
        "input_data": data,
        "result": result,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success",
        "processing_type": "async",
    }


@tool(name="sync_calculator", description="同步计算工具")
def sync_calculator(expression: str) -> Dict[str, Any]:
    """同步计算工具（测试混合工具支持）"""
    rich_print(f"🧮 同步计算: {expression}", RichMessageType.INFO)

    try:
        # 简单的安全计算
        if all(c in "0123456789+-*/.() " for c in expression):
            result = eval(expression)
            return {
                "expression": expression,
                "result": result,
                "status": "success",
                "calculation_type": "sync",
            }
        else:
            return {
                "expression": expression,
                "error": "不安全的表达式",
                "status": "error",
            }
    except Exception as e:
        return {"expression": expression, "error": str(e), "status": "error"}


# ==================== 异步演示函数 ====================


async def demo_async_basic_chat():
    """演示基本异步聊天功能"""
    rich_print_rule("演示: 异步聊天基础功能", style="blue")

    agent = ChatAgent(mode=ChatMode.AUTO, system="你是一个专业的异步助手")

    # 注册混合工具（同步和异步）
    await agent.register_tools_from_functions_async(
        async_web_search, async_data_processor, sync_calculator
    )

    # 测试异步聊天
    messages = [
        "你好，请介绍一下你的异步能力",
        "请使用async_web_search搜索'异步编程'的相关信息",
        "使用sync_calculator计算 15 * 20 + 50",
        "用async_data_processor分析一下刚才的搜索结果",
    ]

    for i, message in enumerate(messages, 1):
        rich_print(f"\n💬 消息 {i}: {message}", RichMessageType.USER)

        start_time = time.time()
        response = await agent.chat_async(message)
        end_time = time.time()

        rich_print(
            f"🤖 响应 ({end_time - start_time:.2f}s): {response[:200]}...",
            RichMessageType.AGENT,
        )


async def demo_async_task_execution():
    """演示异步自主任务执行"""
    rich_print_rule("演示: 异步自主任务执行", style="green")

    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="""你是一个高效的异步研究助手，能够：
- 并行处理多个信息源
- 高效的数据分析和处理
- 实时搜索和信息整合

请充分利用异步能力完成任务。""",
    )

    # 注册异步工具
    await agent.register_tools_from_functions_async(
        async_web_search, async_data_processor, sync_calculator
    )

    # 复杂的研究任务
    task = """
    请进行一项关于"Python异步编程"的深度研究：
    1. 搜索Python异步编程的核心概念和最佳实践
    2. 分析异步编程的性能优势
    3. 整理研究结果并生成摘要报告
    
    要求：充分利用异步工具的并发能力
    """

    rich_print(f"📋 异步任务: {task}", RichMessageType.INFO)

    start_time = time.time()
    result = await agent.arun(task, max_iterations=6)
    end_time = time.time()

    rich_print_rule("异步任务执行结果", style="cyan")
    rich_print(f"✅ 任务状态: {'完成' if result.get('task_completed') else '未完成'}")
    rich_print(f"🔄 执行轮次: {result.get('iterations_used', 0)}")
    rich_print(f"⏱️ 总执行时间: {end_time - start_time:.2f}秒")

    if result.get("final_output"):
        rich_print(f"📄 最终输出:\n{result['final_output'][:300]}...")


async def demo_async_parallel_processing():
    """演示异步并行处理"""
    rich_print_rule("演示: 异步并行处理", style="purple")

    # 创建多个专门的异步代理
    agents = {
        "researcher": ChatAgent(mode=ChatMode.AUTO, system="专门的异步研究员"),
        "analyzer": ChatAgent(mode=ChatMode.AUTO, system="专门的异步数据分析师"),
        "calculator": ChatAgent(mode=ChatMode.AUTO, system="专门的异步计算专家"),
    }

    # 为每个代理注册工具
    for agent in agents.values():
        await agent.register_tools_from_functions_async(
            async_web_search, async_data_processor, sync_calculator
        )

    # 并行任务
    tasks = {
        "research": "搜索机器学习的最新发展趋势",
        "analysis": "分析数据集'AI市场预测2024'的关键指标",
        "calculation": "计算投资回报率：初始投资100000，年收益15000，投资期限5年",
    }

    rich_print("🚀 启动并行任务执行...", RichMessageType.INFO)

    # 使用 asyncio.gather 并行执行
    start_time = time.time()
    results = await asyncio.gather(
        *[
            agents[agent_type].arun(task, max_iterations=3)
            for agent_type, task in tasks.items()
        ],
        return_exceptions=True,
    )
    end_time = time.time()

    rich_print_rule("并行执行结果", style="yellow")
    rich_print(f"⏱️ 并行执行总时间: {end_time - start_time:.2f}秒")

    for (agent_type, task), result in zip(tasks.items(), results):
        if isinstance(result, Exception):
            rich_print(f"❌ {agent_type} 任务失败: {str(result)}")
        else:
            status = "✅ 完成" if result.get("task_completed") else "⚠️ 未完成"
            iterations = result.get("iterations_used", 0)
            rich_print(f"{status} {agent_type}: {iterations} 轮次")


async def demo_async_batch_processing():
    """演示异步批量处理"""
    rich_print_rule("演示: 异步批量处理", style="orange")

    agent = ChatAgent(mode=ChatMode.AUTO)
    await agent.register_tools_from_functions_async(async_web_search, sync_calculator)

    # 批量消息
    messages = [
        "搜索'深度学习'相关信息",
        "计算 25 * 16",
        "搜索'区块链技术'的应用",
        "计算 (100 + 200) * 3",
        "搜索'量子计算'的发展现状",
    ]

    rich_print("📦 批量处理消息...", RichMessageType.INFO)

    # 并行批量处理
    start_time = time.time()
    results = await agent.batch_chat_async(messages)
    parallel_time = time.time() - start_time

    rich_print(f"⚡ 并行处理完成，用时: {parallel_time:.2f}秒")

    # 顺序批量处理（对比）
    agent2 = ChatAgent(mode=ChatMode.AUTO)
    await agent2.register_tools_from_functions_async(async_web_search, sync_calculator)

    start_time = time.time()
    sequential_results = await agent2.sequential_chat_async(messages)
    sequential_time = time.time() - start_time

    rich_print(f"🔄 顺序处理完成，用时: {sequential_time:.2f}秒")

    # 性能对比
    rich_print_rule("批量处理性能对比", style="cyan")
    rich_print(f"并行处理: {parallel_time:.2f}秒")
    rich_print(f"顺序处理: {sequential_time:.2f}秒")
    rich_print(f"性能提升: {sequential_time/parallel_time:.1f}x")


async def demo_async_workflow():
    """演示异步工作流"""
    rich_print_rule("演示: 异步工作流", style="magenta")

    agent = ChatAgent(mode=ChatMode.WORKFLOW)
    await agent.register_tools_from_functions_async(
        async_web_search, async_data_processor, sync_calculator
    )

    # 定义异步工作流步骤
    async def research_step(input_msg, context):
        await asyncio.sleep(0.5)
        return "研究步骤完成：收集了相关资料"

    async def analysis_step(input_msg, context):
        await asyncio.sleep(0.3)
        return "分析步骤完成：提取了关键信息"

    def report_step(input_msg, context):
        time.sleep(0.2)  # 同步步骤
        return "报告步骤完成：生成了最终报告"

    # 添加工作流步骤
    await agent.add_workflow_step_async("research", research_step)
    await agent.add_workflow_step_async("analysis", analysis_step)
    await agent.add_workflow_step_async("report", report_step)

    # 执行工作流
    rich_print("🔄 执行异步工作流...", RichMessageType.INFO)

    start_time = time.time()
    result = await agent.execute_workflow_async("执行完整的研究工作流")
    end_time = time.time()

    rich_print(f"✅ 工作流执行完成，用时: {end_time - start_time:.2f}秒")
    rich_print(f"📊 执行结果:\n{result}")


async def demo_error_handling():
    """演示异步错误处理"""
    rich_print_rule("演示: 异步错误处理", style="red")

    agent = ChatAgent(mode=ChatMode.AUTO)

    @tool(name="error_tool", description="会出错的工具")
    async def error_tool(should_error: bool = True):
        await asyncio.sleep(0.1)
        if should_error:
            raise ValueError("这是一个测试错误")
        return {"status": "success"}

    await agent.register_tools_from_functions_async(error_tool)

    # 测试错误处理
    try:
        response = await agent.chat_async("请使用error_tool并设置should_error为true")
        rich_print(f"🤖 响应: {response}", RichMessageType.AGENT)
    except Exception as e:
        rich_print(f"❌ 捕获到异常: {str(e)}", RichMessageType.ERROR)

    # 测试正常情况
    try:
        response = await agent.chat_async("请使用error_tool并设置should_error为false")
        rich_print(f"✅ 正常响应: {response[:100]}...", RichMessageType.SUCCESS)
    except Exception as e:
        rich_print(f"❌ 意外异常: {str(e)}", RichMessageType.ERROR)


# ==================== 主程序 ====================


async def main():
    """主异步演示程序"""
    rich_print_rule("ChatAgent 完整异步功能演示", style="bold blue")

    demos = [
        ("基础异步聊天", demo_async_basic_chat),
        ("异步任务执行", demo_async_task_execution),
        ("异步并行处理", demo_async_parallel_processing),
        ("异步批量处理", demo_async_batch_processing),
        ("异步工作流", demo_async_workflow),
        ("异步错误处理", demo_error_handling),
    ]

    total_start_time = time.time()

    for demo_name, demo_func in demos:
        rich_print(f"\n🚀 开始演示: {demo_name}")
        try:
            start_time = time.time()
            await demo_func()
            end_time = time.time()
            rich_print(
                f"✅ {demo_name} 完成，用时: {end_time - start_time:.2f}秒",
                RichMessageType.SUCCESS,
            )
        except Exception as e:
            rich_print(f"❌ {demo_name} 失败: {str(e)}", RichMessageType.ERROR)

        print("\n" + "=" * 50 + "\n")

    total_end_time = time.time()

    rich_print_rule("演示完成", style="bold green")
    rich_print(
        f"🎉 所有演示完成，总用时: {total_end_time - total_start_time:.2f}秒",
        RichMessageType.SUCCESS,
    )

    # 性能统计
    rich_print_rule("性能总结", style="bold cyan")
    rich_print("✨ ChatAgent 异步功能特点:")
    rich_print("  • 支持同步和异步工具的混合使用")
    rich_print("  • 真正的异步并发处理能力")
    rich_print("  • 完整的异步工作流支持")
    rich_print("  • 高效的批量处理机制")
    rich_print("  • 良好的错误处理和恢复")


if __name__ == "__main__":
    # 运行完整的异步演示
    asyncio.run(main())
