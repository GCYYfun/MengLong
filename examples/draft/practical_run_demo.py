#!/usr/bin/env python3
"""
ChatAgent.run() 实用演示
=======================

展示如何使用 ChatAgent.run(task) 方法进行自主任务执行

使用方法:
    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_global_tools()  # 或注册特定工具
    result = agent.run("你的任务描述", max_iterations=5)

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import rich_print, rich_print_rule, RichMessageType
import time
import random
from typing import Dict, Any, List


# ==================== 实用工具定义 ====================


@tool(name="web_search", description="使用DuckDuckGo进行网络搜索")
def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """使用DuckDuckGo进行真实的网络搜索"""
    try:
        from duckduckgo_search import DDGS

        rich_print(f"🔍 正在搜索: {query}", RichMessageType.INFO)

        results = []
        with DDGS() as ddgs:
            # 执行搜索，限制结果数量
            search_results = list(ddgs.text(query, max_results=max_results))

            for i, result in enumerate(search_results):
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "relevance": 1.0 - (i * 0.1),  # 按顺序递减相关性
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

    except ImportError:
        rich_print("⚠️ DuckDuckGo搜索库未安装，使用模拟搜索", RichMessageType.WARNING)
        # 回退到模拟搜索
        return _mock_web_search(query, max_results)
    except Exception as e:
        rich_print(f"❌ 搜索出错: {str(e)}，使用模拟搜索", RichMessageType.WARNING)
        return _mock_web_search(query, max_results)


def _mock_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """模拟网络搜索（回退方案）"""
    time.sleep(1)  # 模拟搜索延迟

    # 模拟搜索结果
    results = []
    for i in range(min(max_results, 3)):
        results.append(
            {
                "title": f"搜索结果 {i+1}: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"这是关于 {query} 的搜索结果片段 {i+1}",
                "relevance": random.uniform(0.7, 1.0),
            }
        )

    return {
        "query": query,
        "results": results,
        "total_found": len(results),
        "search_time": time.time(),
        "source": "Mock",
    }


@tool(name="data_analysis", description="数据分析工具")
def data_analysis(data: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """模拟数据分析"""
    time.sleep(2)  # 模拟分析时间

    analysis_types = {
        "summary": {
            "insights": ["数据趋势稳定", "存在季节性变化", "整体增长良好"],
            "key_metrics": {
                "growth_rate": "12%",
                "variance": "0.15",
                "confidence": "85%",
            },
        },
        "trend": {
            "insights": ["上升趋势明显", "周期性波动", "预测值积极"],
            "key_metrics": {
                "trend_slope": "0.8",
                "correlation": "0.92",
                "r_squared": "0.84",
            },
        },
        "comparison": {
            "insights": ["显著差异存在", "群组A表现更佳", "需要进一步验证"],
            "key_metrics": {
                "p_value": "0.03",
                "effect_size": "0.7",
                "sample_size": "1000",
            },
        },
    }

    result = analysis_types.get(analysis_type, analysis_types["summary"])
    result.update(
        {
            "data_processed": data,
            "analysis_type": analysis_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )

    return result


@tool(name="report_generator", description="报告生成工具")
def report_generator(
    title: str, sections: List[str], format: str = "markdown"
) -> Dict[str, Any]:
    """生成结构化报告"""
    time.sleep(1.5)  # 模拟生成时间

    if format == "markdown":
        content = f"# {title}\n\n"
        content += f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        for i, section in enumerate(sections, 1):
            content += f"## {i}. {section}\n\n"
            content += f"这是 {section} 的详细内容。\n\n"
    else:
        content = f"标题: {title}\n"
        content += f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for i, section in enumerate(sections, 1):
            content += f"{i}. {section}\n"

    return {
        "title": title,
        "format": format,
        "content": content,
        "sections": sections,
        "word_count": len(content.split()),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@tool(name="file_manager", description="文件管理工具")
def file_manager(action: str, filename: str, content: str = "") -> Dict[str, Any]:
    """模拟文件操作"""
    time.sleep(0.5)  # 模拟文件操作时间

    if action == "save":
        return {
            "action": "save",
            "filename": filename,
            "size": len(content),
            "status": "success",
            "message": f"文件 {filename} 保存成功",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    elif action == "read":
        return {
            "action": "read",
            "filename": filename,
            "content": f"这是文件 {filename} 的模拟内容",
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    elif action == "delete":
        return {
            "action": "delete",
            "filename": filename,
            "status": "success",
            "message": f"文件 {filename} 删除成功",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    else:
        return {
            "action": action,
            "status": "error",
            "message": f"不支持的操作: {action}",
        }


# ==================== 演示场景 ====================


def demo_research_task():
    """演示研究任务"""
    rich_print_rule("演示: 自主研究任务", style="blue")

    # 创建研究型 Agent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="""你是一个专业的研究助手，擅长：
- 信息收集和搜索
- 数据分析和解读
- 报告撰写和总结
- 文件管理和组织

请按照科学严谨的方法完成研究任务。""",
    )

    # 注册工具
    agent.register_tools_from_functions(
        web_search, data_analysis, report_generator, file_manager
    )

    # 定义研究任务
    task = """请完成一个关于人工智能在医疗领域应用的研究：
1. 搜索相关信息和最新发展
2. 分析收集到的数据和趋势
3. 生成一份结构化的研究报告
4. 保存报告到文件系统"""

    rich_print(f"🎯 研究任务: {task}", RichMessageType.INFO)

    # 执行任务
    result = agent.run(task=task, max_iterations=6)

    # 显示结果
    rich_print(f"\n📊 执行结果:", RichMessageType.SUCCESS)
    rich_print(f"状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"用时: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )

    return result


def demo_data_processing_task():
    """演示数据处理任务"""
    rich_print_rule("演示: 自主数据处理任务", style="green")

    # 创建数据分析型 Agent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="""你是一个数据科学专家，精通：
- 数据收集和清理
- 统计分析和建模
- 可视化和报告
- 结果验证和解释

请用科学的方法处理数据任务。""",
    )

    # 注册工具
    agent.register_tools_from_functions(
        web_search, data_analysis, report_generator, file_manager
    )

    # 定义数据处理任务
    task = """分析电商平台的销售数据：
1. 搜索行业基准数据进行对比
2. 对销售数据进行趋势分析
3. 生成包含洞察和建议的分析报告
4. 保存分析结果和报告"""

    rich_print(f"🎯 数据任务: {task}", RichMessageType.INFO)

    # 执行任务
    result = agent.run(task=task, max_iterations=5)

    # 显示结果
    rich_print(f"\n📊 执行结果:", RichMessageType.SUCCESS)
    rich_print(f"状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"用时: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )

    return result


def demo_content_creation_task():
    """演示内容创作任务"""
    rich_print_rule("演示: 自主内容创作任务", style="magenta")

    # 创建内容创作型 Agent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="""你是一个专业的内容创作者，专长包括：
- 市场调研和分析
- 创意内容策划
- 多格式内容生成
- 质量控制和优化

请创作高质量、有价值的内容。""",
    )

    # 注册工具
    agent.register_tools_from_functions(
        web_search, data_analysis, report_generator, file_manager
    )

    # 定义内容创作任务
    task = """为科技公司创作一篇关于区块链技术的白皮书：
1. 研究区块链的最新发展和应用案例
2. 分析技术优势和市场机会
3. 生成专业的白皮书文档
4. 保存最终文档"""

    rich_print(f"🎯 创作任务: {task}", RichMessageType.INFO)

    # 执行任务
    result = agent.run(task=task, max_iterations=6)

    # 显示结果
    rich_print(f"\n📊 执行结果:", RichMessageType.SUCCESS)
    rich_print(f"状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"用时: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )

    return result


def demo_quick_task():
    """演示快速任务"""
    rich_print_rule("演示: 快速任务执行", style="cyan")

    # 创建通用 Agent
    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_tools_from_functions(web_search, report_generator)

    # 简单快速任务
    task = "搜索一下'Python编程最佳实践'，然后生成一个简短的总结报告"

    rich_print(f"🎯 快速任务: {task}", RichMessageType.INFO)

    # 快速执行（限制轮次）
    result = agent.run(task=task, max_iterations=3)

    # 显示结果
    rich_print(f"\n📊 执行结果:", RichMessageType.SUCCESS)
    rich_print(f"状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"用时: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )

    return result


def main():
    """主演示函数"""
    rich_print_rule("ChatAgent.run() 实用演示", style="bold blue")
    rich_print(
        "展示如何使用 ChatAgent.run(task) 进行各种自主任务执行", RichMessageType.INFO
    )

    try:
        # 演示1: 研究任务
        demo_research_task()

        # 演示2: 数据处理任务
        demo_data_processing_task()

        # 演示3: 内容创作任务
        demo_content_creation_task()

        # 演示4: 快速任务
        demo_quick_task()

        # 使用说明
        rich_print_rule("使用说明", style="yellow")
        rich_print(
            """
📝 使用 ChatAgent.run() 的基本步骤：

1. 创建 ChatAgent 实例：
   agent = ChatAgent(mode=ChatMode.AUTO, system="你的系统提示")

2. 注册工具：
   agent.register_global_tools()  # 注册全局工具
   # 或
   agent.register_tools_from_functions(tool1, tool2, ...)  # 注册特定工具

3. 执行任务：
   result = agent.run(task="你的任务描述", max_iterations=10)

4. 检查结果：
   print(f"状态: {result['status']}")
   print(f"执行时间: {result['execution_time']}")
   print(f"轮次: {result['iterations']}")

✨ 特性：
- 自动任务分解和执行
- 智能工具选择和使用
- 进度跟踪和状态监控
- 错误处理和重试机制
- 详细的执行日志记录
""",
            RichMessageType.INFO,
        )

    except Exception as e:
        rich_print(f"演示过程中发生错误: {str(e)}", RichMessageType.ERROR)
        import traceback

        rich_print(f"详细错误信息: {traceback.format_exc()}", RichMessageType.ERROR)

    rich_print_rule("演示完成", style="bold green")


if __name__ == "__main__":
    main()
