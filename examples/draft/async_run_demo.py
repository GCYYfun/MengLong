#!/usr/bin/env python3
"""
ChatAgent.arun() 异步运行演示
============================

展示如何在异步环境中使用 ChatAgent.arun(task) 方法进行自主任务执行

使用方法:
    # 在异步环境中
    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_global_tools()
    result = await agent.arun("你的任务描述", max_iterations=5)

    # 在同步环境中
    result = agent.run("你的任务描述", max_iterations=5)

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, rich_print_rule, RichMessageType
import time
from typing import Dict, Any


# ==================== 示例工具定义 ====================


@tool(name="web_search", description="使用DuckDuckGo进行网络搜索")
def web_search(query: str, max_results: int = 3) -> Dict[str, Any]:
    """使用DuckDuckGo进行真实的网络搜索"""
    try:
        from duckduckgo_search import DDGS

        rich_print(f"🔍 正在搜索: {query}", RichMessageType.INFO)

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

        rich_print(f"✅ 搜索完成，找到 {len(results)} 个结果", RichMessageType.SUCCESS)

        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "search_time": time.time(),
            "source": "DuckDuckGo",
        }

    except Exception as e:
        rich_print(f"❌ 搜索出错: {str(e)}，使用模拟搜索", RichMessageType.WARNING)
        return {
            "query": query,
            "results": [
                {
                    "title": f"模拟搜索结果: {query}",
                    "url": "https://example.com",
                    "snippet": f"关于 {query} 的信息",
                }
            ],
            "total_found": 1,
            "search_time": time.time(),
            "source": "Mock",
        }


@tool(name="data_processor", description="数据处理工具")
def data_processor(data: str, operation: str = "analyze") -> Dict[str, Any]:
    """处理数据"""
    time.sleep(1)  # 模拟处理时间

    operations = {
        "analyze": "数据分析完成，发现有趣的模式",
        "summarize": "数据摘要生成完成",
        "validate": "数据验证通过",
        "transform": "数据转换完成",
    }

    result = operations.get(operation, "未知操作")

    return {
        "operation": operation,
        "input_data": data,
        "result": result,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success",
    }


@tool(name="report_writer", description="报告撰写工具")
def report_writer(title: str, content: str, format: str = "markdown") -> Dict[str, Any]:
    """生成报告"""
    time.sleep(0.5)

    if format == "markdown":
        report = (
            f"# {title}\n\n{content}\n\n生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        report = f"标题: {title}\n内容: {content}\n生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    return {
        "title": title,
        "format": format,
        "content": report,
        "word_count": len(content.split()),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ==================== 异步演示函数 ====================


async def demo_async_research():
    """异步环境中的研究任务演示"""
    rich_print_rule("异步演示: 市场研究任务", style="blue")

    # 创建 Agent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="""你是一个专业的市场研究分析师，擅长：
- 收集市场信息和数据
- 分析行业趋势
- 撰写研究报告
- 数据验证和处理

请按照专业的研究方法完成任务。""",
    )

    # 注册工具
    agent.register_tools_from_functions(web_search, data_processor, report_writer)

    # 定义研究任务
    task = """
    请进行一项关于"人工智能在教育领域的应用"的市场研究：
    1. 搜索相关信息和最新趋势
    2. 分析收集到的数据
    3. 生成专业的研究报告
    """

    rich_print(f"📋 任务: {task}", RichMessageType.INFO)

    try:
        # 使用异步方法执行任务
        result = await agent.arun(task, max_iterations=6)

        rich_print_rule("任务执行结果", style="green")
        rich_print(
            f"✅ 任务状态: {'完成' if result.get('task_completed') else '未完成'}",
            RichMessageType.SUCCESS,
        )
        rich_print(
            f"🔄 执行轮次: {result.get('iterations_used', 0)}", RichMessageType.INFO
        )
        rich_print(
            f"⏱️ 执行时间: {result.get('execution_time', 0):.2f}秒", RichMessageType.INFO
        )

        if result.get("final_output"):
            rich_print(
                f"📄 最终输出:\n{result['final_output']}", RichMessageType.SUCCESS
            )

        return result

    except Exception as e:
        rich_print(f"❌ 异步执行失败: {str(e)}", RichMessageType.ERROR)
        return None


async def demo_async_parallel_tasks():
    """演示并行执行多个异步任务"""
    rich_print_rule("异步演示: 并行任务执行", style="purple")

    # 创建多个 Agent
    research_agent = ChatAgent(mode=ChatMode.AUTO, system="你是研究专家")
    analysis_agent = ChatAgent(mode=ChatMode.AUTO, system="你是数据分析专家")

    # 注册工具
    research_agent.register_tools_from_functions(web_search, report_writer)
    analysis_agent.register_tools_from_functions(data_processor, report_writer)

    # 定义任务
    research_task = "搜索关于机器学习最新发展的信息并生成简要报告"
    analysis_task = "分析数据集 'AI市场趋势2024' 并生成分析报告"

    rich_print("🔄 开始并行执行任务...", RichMessageType.INFO)

    try:
        # 并行执行任务
        research_result, analysis_result = await asyncio.gather(
            research_agent.arun(research_task, max_iterations=4),
            analysis_agent.arun(analysis_task, max_iterations=4),
        )

        rich_print_rule("并行任务结果", style="green")

        rich_print("📊 研究任务结果:", RichMessageType.INFO)
        rich_print(
            f"  状态: {'完成' if research_result.get('task_completed') else '未完成'}"
        )
        rich_print(f"  轮次: {research_result.get('iterations_used', 0)}")

        rich_print("📈 分析任务结果:", RichMessageType.INFO)
        rich_print(
            f"  状态: {'完成' if analysis_result.get('task_completed') else '未完成'}"
        )
        rich_print(f"  轮次: {analysis_result.get('iterations_used', 0)}")

        return research_result, analysis_result

    except Exception as e:
        rich_print(f"❌ 并行执行失败: {str(e)}", RichMessageType.ERROR)
        return None, None


def demo_sync_vs_async():
    """演示同步和异步方法的区别"""
    rich_print_rule("对比演示: 同步 vs 异步", style="yellow")

    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_tools_from_functions(web_search, data_processor)

    task = "搜索关于量子计算的信息并进行分析"

    # 同步方法
    rich_print("🔄 使用同步方法 run()...", RichMessageType.INFO)
    start_time = time.time()
    try:
        sync_result = agent.run(task, max_iterations=3)
        sync_time = time.time() - start_time
        rich_print(f"✅ 同步执行完成，用时: {sync_time:.2f}秒", RichMessageType.SUCCESS)
    except RuntimeError as e:
        if "cannot be called from a running event loop" in str(e):
            rich_print(
                "❌ 同步方法在事件循环中失败（预期行为）", RichMessageType.WARNING
            )
            sync_result = None
            sync_time = 0
        else:
            raise

    # 异步方法 - 需要在异步函数中调用
    async def run_async():
        rich_print("🔄 使用异步方法 arun()...", RichMessageType.INFO)
        start_time = time.time()
        try:
            result = await agent.arun(task, max_iterations=3)
            async_time = time.time() - start_time
            rich_print(
                f"✅ 异步执行完成，用时: {async_time:.2f}秒", RichMessageType.SUCCESS
            )
            return result, async_time
        except Exception as e:
            rich_print(f"❌ 异步执行失败: {str(e)}", RichMessageType.ERROR)
            return None, 0

    return sync_result, sync_time, run_async


# ==================== 主程序 ====================


async def main():
    """主异步函数"""
    rich_print_rule("ChatAgent.arun() 异步运行演示", style="bold blue")

    try:
        # 演示1: 异步研究任务
        await demo_async_research()

        print("\n" + "=" * 50 + "\n")

        # 演示2: 并行任务执行
        await demo_async_parallel_tasks()

        print("\n" + "=" * 50 + "\n")

        # 演示3: 同步 vs 异步对比
        sync_result, sync_time, async_func = demo_sync_vs_async()
        async_result, async_time = await async_func()

        rich_print_rule("性能对比", style="cyan")
        rich_print(f"同步方法: {sync_time:.2f}秒 ({'成功' if sync_result else '失败'})")
        rich_print(
            f"异步方法: {async_time:.2f}秒 ({'成功' if async_result else '失败'})"
        )

    except Exception as e:
        rich_print(f"❌ 演示过程中出错: {str(e)}", RichMessageType.ERROR)

    rich_print_rule("演示完成", style="bold green")


def run_sync_demo():
    """运行同步演示（仅在没有事件循环时）"""
    rich_print_rule("同步环境演示", style="green")

    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_tools_from_functions(web_search, data_processor)

    task = "搜索关于区块链技术的信息"

    try:
        result = agent.run(task, max_iterations=3)
        rich_print("✅ 同步执行成功", RichMessageType.SUCCESS)
        return result
    except RuntimeError as e:
        rich_print(f"❌ 同步执行失败: {str(e)}", RichMessageType.ERROR)
        rich_print("💡 提示: 在异步环境中请使用 arun() 方法", RichMessageType.INFO)
        return None


if __name__ == "__main__":
    # 检查是否在事件循环中
    try:
        asyncio.get_running_loop()
        rich_print("🔄 检测到运行中的事件循环，仅演示异步模式", RichMessageType.INFO)
        rich_print(
            "💡 请在新的Python进程中运行此脚本以获得完整演示", RichMessageType.WARNING
        )
    except RuntimeError:
        # 没有事件循环，可以同时演示同步和异步
        rich_print("🔄 没有检测到事件循环，演示两种模式", RichMessageType.INFO)

        # 先运行同步演示
        run_sync_demo()

        print("\n" + "=" * 50 + "\n")

        # 再运行异步演示
        asyncio.run(main())
