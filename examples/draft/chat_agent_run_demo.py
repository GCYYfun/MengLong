#!/usr/bin/env python3
"""
ChatAgent.run() 自主任务执行演示
================================

这个演示展示了如何使用 ChatAgent.run(task) 方法让 Agent 自主执行任务，
直到完成为止。

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
import json
import time
import random
from typing import Dict, Any, List

from menglong.agents.task.task_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import (
    rich_print,
    rich_print_rule,
    RichMessageType,
    configure_logger,
    get_logger,
)


def setup_logging():
    """设置日志"""
    configure_logger(log_file="chat_agent_run_demo.log")
    return get_logger()


# ==================== 工具定义 ====================


@tool(name="search_info", description="搜索信息")
def search_information(query: str, category: str = "general") -> Dict[str, Any]:
    """搜索相关信息"""
    time.sleep(1)  # 模拟搜索延迟

    # 模拟搜索结果
    mock_results = {
        "market": {
            "query": query,
            "results": [
                {
                    "title": f"市场分析: {query}",
                    "summary": f"关于{query}的市场趋势分析",
                },
                {
                    "title": f"行业报告: {query}",
                    "summary": f"{query}行业的最新发展报告",
                },
            ],
        },
        "technology": {
            "query": query,
            "results": [
                {"title": f"技术文档: {query}", "summary": f"{query}的技术实现方案"},
                {"title": f"最佳实践: {query}", "summary": f"{query}的行业最佳实践"},
            ],
        },
        "general": {
            "query": query,
            "results": [
                {"title": f"综合信息: {query}", "summary": f"关于{query}的综合信息"},
                {"title": f"相关资源: {query}", "summary": f"{query}相关的有用资源"},
            ],
        },
    }

    return mock_results.get(category, mock_results["general"])


@tool(name="analyze_data", description="分析数据")
def analyze_data(data: str, analysis_type: str = "general") -> Dict[str, Any]:
    """分析数据并提供洞察"""
    time.sleep(2)  # 模拟分析延迟

    insights = {
        "market": ["市场规模增长稳定", "竞争激烈", "存在细分机会"],
        "technology": ["技术成熟度较高", "存在创新空间", "需要关注兼容性"],
        "financial": ["投资回报率良好", "风险可控", "现金流稳定"],
        "general": ["数据质量良好", "趋势明显", "需要进一步验证"],
    }

    return {
        "data": data,
        "analysis_type": analysis_type,
        "insights": insights.get(analysis_type, insights["general"]),
        "confidence": random.uniform(0.7, 0.95),
        "recommendations": [
            f"建议1: 基于{data}的分析",
            f"建议2: 考虑{analysis_type}因素",
        ],
    }


@tool(name="generate_report", description="生成报告")
def generate_report(
    title: str, content: List[str], format: str = "markdown"
) -> Dict[str, Any]:
    """生成报告文档"""
    time.sleep(1.5)  # 模拟生成延迟

    if format == "markdown":
        report = f"# {title}\n\n"
        for i, section in enumerate(content, 1):
            report += f"## {i}. {section}\n\n"
    else:
        report = f"报告标题: {title}\n" + "\n".join(
            f"{i}. {section}" for i, section in enumerate(content, 1)
        )

    return {
        "title": title,
        "format": format,
        "content": report,
        "word_count": len(report.split()),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@tool(name="send_notification", description="发送通知")
def send_notification(recipient: str, subject: str, message: str) -> Dict[str, Any]:
    """发送通知消息"""
    time.sleep(0.5)  # 模拟发送延迟

    return {
        "recipient": recipient,
        "subject": subject,
        "message": message,
        "status": "sent",
        "sent_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message_id": f"msg_{random.randint(1000, 9999)}",
    }


@tool(name="validate_completion", description="验证任务完成情况")
def validate_task_completion(
    task_description: str, completed_items: List[str]
) -> Dict[str, Any]:
    """验证任务是否完成"""
    time.sleep(1)  # 模拟验证延迟

    # 模拟验证逻辑
    total_items = len(completed_items)
    required_items = ["信息收集", "数据分析", "报告生成", "结果验证"]

    completed_required = sum(
        1 for item in required_items if any(req in item for req in completed_items)
    )

    completion_rate = completed_required / len(required_items)
    is_complete = completion_rate >= 0.8  # 80%以上认为完成

    return {
        "task_description": task_description,
        "completed_items": completed_items,
        "required_items": required_items,
        "completion_rate": completion_rate,
        "is_complete": is_complete,
        "missing_items": [
            item
            for item in required_items
            if not any(req in item for req in completed_items)
        ],
        "quality_score": (
            random.uniform(0.7, 0.95) if is_complete else random.uniform(0.4, 0.7)
        ),
    }


# ==================== 演示函数 ====================


def demo_simple_autonomous_task():
    """演示简单的自主任务执行"""
    rich_print_rule("演示1: 使用 ChatAgent.run() 执行简单任务", style="blue")

    # 创建 ChatAgent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="你是一个专业的研究助手，能够自主完成各种调研和分析任务。",
    )

    # 自动注册全局工具
    agent.register_global_tools()

    # 定义任务
    task = "请帮我研究一下人工智能在医疗领域的应用，并生成一份简要报告"

    rich_print(f"🎯 要执行的任务: {task}", RichMessageType.INFO)

    # 使用 run 方法自主执行任务
    result = agent.run(task=task, max_iterations=5)

    # 显示执行结果
    rich_print(f"\n📊 执行结果:", RichMessageType.SUCCESS)
    rich_print(f"任务状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"执行时间: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"执行轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )
    rich_print(f"成功率: {result['success_rate']:.1%}", RichMessageType.SYSTEM)

    return result


def demo_complex_autonomous_task():
    """演示复杂的自主任务执行"""
    rich_print_rule("演示2: 使用 ChatAgent.run() 执行复杂任务", style="magenta")

    # 创建专门的市场调研 Agent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="""你是一个专业的市场调研分析师，具备以下能力：
- 深度市场分析
- 竞争对手研究
- 趋势预测
- 报告撰写
- 数据验证

请以专业的态度完成分配的任务，确保分析的全面性和准确性。""",
    )

    # 注册工具
    agent.register_global_tools()

    # 定义复杂任务
    task = """请完成一个电动汽车市场调研项目：
1. 调研当前电动汽车市场的规模和增长趋势
2. 分析主要品牌（特斯拉、比亚迪、蔚来等）的市场地位
3. 识别市场机会和潜在威胁
4. 预测未来3年的发展趋势
5. 生成完整的市场调研报告
6. 验证报告的完整性和准确性"""

    rich_print(f"🎯 要执行的复杂任务: {task}", RichMessageType.INFO)

    # 使用 run 方法自主执行任务
    result = agent.run(task=task, max_iterations=8)

    # 显示详细执行过程
    rich_print(f"\n📊 详细执行报告:", RichMessageType.SUCCESS)
    rich_print(f"任务状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"执行时间: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"执行轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )

    rich_print("\n📝 执行过程详情:", RichMessageType.INFO)
    for i, log in enumerate(result["execution_log"], 1):
        rich_print(f"  轮次 {i}: {log['response'][:100]}...", RichMessageType.SYSTEM)

    return result


def demo_interactive_task_definition():
    """演示交互式任务定义"""
    rich_print_rule("演示3: 交互式任务定义", style="cyan")

    # 预定义一些示例任务供选择
    sample_tasks = [
        "分析区块链技术在金融行业的应用前景和挑战",
        "研究远程工作对企业效率和员工满意度的影响",
        "调查可再生能源的技术发展和投资机会",
        "分析元宇宙概念的商业化进展和市场潜力",
    ]

    rich_print("可选的任务示例：", RichMessageType.INFO)
    for i, task in enumerate(sample_tasks, 1):
        rich_print(f"{i}. {task}", RichMessageType.SYSTEM)

    # 选择一个任务进行演示
    selected_task = sample_tasks[0]  # 默认选择第一个
    rich_print(f"\n🎯 选定任务: {selected_task}", RichMessageType.USER)

    # 创建通用研究 Agent
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="你是一个全能的研究分析师，能够处理各种领域的研究任务。",
    )
    agent.register_global_tools()

    # 执行任务
    result = agent.run(task=selected_task, max_iterations=6)

    rich_print(
        f"\n✅ 任务执行{'成功' if result['status'] == 'completed' else '未完成'}",
        (
            RichMessageType.SUCCESS
            if result["status"] == "completed"
            else RichMessageType.WARNING
        ),
    )

    return result


def demo_comparison_different_agents():
    """演示不同配置的 Agent 执行同一任务的对比"""
    rich_print_rule("演示4: 不同 Agent 配置的执行对比", style="yellow")

    # 同一个任务
    task = "研究人工智能在教育领域的应用现状和发展前景"

    # Agent 1: 快速执行型
    rich_print("🚀 Agent 1: 快速执行型 (3轮)", RichMessageType.INFO)
    agent1 = ChatAgent(
        mode=ChatMode.AUTO, system="你是一个高效的研究助手，追求快速完成任务。"
    )
    agent1.register_global_tools()
    result1 = agent1.run(task=task, max_iterations=3)

    # Agent 2: 深度分析型
    rich_print("\n🔍 Agent 2: 深度分析型 (7轮)", RichMessageType.INFO)
    agent2 = ChatAgent(
        mode=ChatMode.AUTO, system="你是一个注重细节的研究专家，追求深度和全面性。"
    )
    agent2.register_global_tools()
    result2 = agent2.run(task=task, max_iterations=7)

    # 对比结果
    rich_print(f"\n📊 执行对比:", RichMessageType.SUCCESS)
    rich_print(
        f"Agent 1 - 状态: {result1['status']}, 用时: {result1['execution_time']:.1f}s, 轮次: {result1['iterations']}",
        RichMessageType.SYSTEM,
    )
    rich_print(
        f"Agent 2 - 状态: {result2['status']}, 用时: {result2['execution_time']:.1f}s, 轮次: {result2['iterations']}",
        RichMessageType.SYSTEM,
    )

    return result1, result2


def main():
    """主函数"""
    logger = setup_logging()
    logger.info("开始 ChatAgent.run() 自主任务执行演示")

    rich_print_rule("ChatAgent.run() 自主任务执行演示", style="bold blue")
    rich_print("演示 ChatAgent.run(task) 方法的自主任务执行功能", RichMessageType.INFO)

    try:
        # 演示1: 简单任务
        demo_simple_autonomous_task()

        # # 演示2: 复杂任务
        # demo_complex_autonomous_task()

        # # 演示3: 交互式任务
        # demo_interactive_task_definition()

        # # 演示4: 不同配置对比
        # demo_comparison_different_agents()

    except Exception as e:
        rich_print(f"演示过程中发生错误: {str(e)}", RichMessageType.ERROR)
        logger.error(f"演示错误: {str(e)}")
        import traceback

        rich_print(f"详细错误信息: {traceback.format_exc()}", RichMessageType.ERROR)

    logger.info("ChatAgent.run() 自主任务执行演示完成")
    rich_print_rule("演示完成", style="bold green")


if __name__ == "__main__":
    main()
