#!/usr/bin/env python3
"""
ChatAgent 自主任务执行演示
=========================

这个演示展示了如何让 ChatAgent 自主运行直到完成指定的任务：
1. 任务分解 - 将复杂任务分解为子任务
2. 自主执行 - Agent 自己决定执行步骤和使用工具
3. 进度跟踪 - 实时监控任务完成进度
4. 结果验证 - 确保任务完全完成

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
import json
import time
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from menglong.agents.chat.chat_agent import ChatAgent, ChatMode, tool
from menglong.utils.log import (
    rich_print,
    rich_print_rule,
    RichMessageType,
    configure_logger,
    get_logger,
)


def setup_logging():
    """设置日志"""
    configure_logger(log_file="autonomous_task_demo.log")
    return get_logger()


# ==================== 任务状态管理 ====================


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 待执行
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    BLOCKED = "blocked"  # 阻塞


@dataclass
class Task:
    """任务定义"""

    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = None  # 依赖的任务ID
    result: Any = None
    error: str = None
    created_at: float = None
    completed_at: float = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = time.time()


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.execution_log: List[str] = []

    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.id] = task
        self.log(f"添加任务: {task.title}")

    def complete_task(self, task_id: str, result: Any = None):
        """完成任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()
            self.log(f"完成任务: {task.title}")

    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            self.log(f"任务失败: {task.title} - {error}")

    def get_next_task(self) -> Optional[Task]:
        """获取下一个可执行的任务"""
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # 检查依赖是否完成
                if self._dependencies_completed(task):
                    return task
        return None

    def _dependencies_completed(self, task: Task) -> bool:
        """检查任务依赖是否完成"""
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                if self.tasks[dep_id].status != TaskStatus.COMPLETED:
                    return False
        return True

    def get_progress(self) -> Dict[str, int]:
        """获取任务进度"""
        total = len(self.tasks)
        completed = sum(
            1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED
        )
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        in_progress = sum(
            1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS
        )
        pending = total - completed - failed - in_progress

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "pending": pending,
            "completion_rate": completed / total if total > 0 else 0,
        }

    def is_all_completed(self) -> bool:
        """检查是否所有任务都已完成"""
        return all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for t in self.tasks.values()
        )

    def log(self, message: str):
        """记录日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_log.append(log_entry)
        rich_print(f"📋 {log_entry}", RichMessageType.INFO)


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


# ==================== 自主任务执行器 ====================


class AutonomousTaskExecutor:
    """自主任务执行器"""

    def __init__(self, max_iterations: int = 10):
        self.agent = ChatAgent(
            mode=ChatMode.AUTO,
            system="""你是一个自主任务执行助手。你的职责是：
1. 分析用户给出的任务
2. 制定执行计划
3. 逐步执行任务，使用可用的工具
4. 监控进度并调整策略
5. 确保任务完全完成

执行原则：
- 主动使用工具完成任务
- 遇到问题时寻找替代方案
- 定期检查任务完成情况
- 保持执行的连续性直到完成

请在每次响应中明确说明：
1. 当前正在执行的步骤
2. 使用的工具和原因
3. 下一步计划
4. 任务整体进度""",
            tools=None,  # 注册所有全局工具
        )
        self.task_manager = TaskManager()
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.task_context = {}

    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        """执行自主任务"""
        rich_print_rule(f"开始执行自主任务", style="green")
        rich_print(f"📋 任务描述: {task_description}", RichMessageType.INFO)

        self.current_iteration = 0
        self.task_context = {
            "original_task": task_description,
            "start_time": time.time(),
            "execution_log": [],
            "intermediate_results": [],
        }

        # 初始化任务
        initial_prompt = f"""
我需要你自主完成以下任务：

任务描述：{task_description}

请分析这个任务，制定执行计划，然后开始执行。你有以下工具可以使用：
- search_info: 搜索信息
- analyze_data: 分析数据  
- generate_report: 生成报告
- send_notification: 发送通知
- validate_completion: 验证任务完成

请开始执行，并在每步说明你的行动和理由。
"""

        last_response = ""
        task_completed = False

        while self.current_iteration < self.max_iterations and not task_completed:
            self.current_iteration += 1

            rich_print(
                f"\n🔄 执行轮次 {self.current_iteration}/{self.max_iterations}",
                RichMessageType.INFO,
            )

            try:
                # 构建当前轮次的提示
                if self.current_iteration == 1:
                    current_prompt = initial_prompt
                else:
                    current_prompt = f"""
继续执行任务。上次的执行结果：
{last_response}

请继续下一步执行，或者如果任务已完成，请进行最终验证。
当前已执行 {self.current_iteration-1} 轮，请确保任务的完整性。
"""

                # 让 Agent 执行下一步
                response = self.agent.chat(current_prompt)
                last_response = response

                # 记录执行过程
                self.task_context["execution_log"].append(
                    {
                        "iteration": self.current_iteration,
                        "response": response,
                        "timestamp": time.time(),
                    }
                )

                rich_print(f"🤖 Agent 响应:\n{response}", RichMessageType.AGENT)

                # 检查是否提到任务完成
                completion_keywords = [
                    "任务完成",
                    "已完成",
                    "执行完毕",
                    "全部完成",
                    "任务结束",
                ]
                if any(keyword in response for keyword in completion_keywords):
                    rich_print("🎯 检测到任务完成信号", RichMessageType.SUCCESS)

                    # 进行最终验证
                    final_validation = await self._perform_final_validation(
                        task_description
                    )
                    if final_validation["is_complete"]:
                        task_completed = True
                        rich_print("✅ 任务执行完成！", RichMessageType.SUCCESS)
                    else:
                        rich_print(
                            "⚠️ 任务尚未完全完成，继续执行", RichMessageType.WARNING
                        )

                # 短暂等待，避免过快执行
                await asyncio.sleep(1)

            except Exception as e:
                rich_print(f"❌ 执行出错: {str(e)}", RichMessageType.ERROR)
                break

        # 生成执行报告
        execution_report = self._generate_execution_report(task_completed)

        if not task_completed:
            rich_print("⏰ 达到最大执行轮次或任务未完成", RichMessageType.WARNING)

        return execution_report

    async def _perform_final_validation(self, task_description: str) -> Dict[str, Any]:
        """执行最终验证"""
        rich_print("🔍 执行最终任务验证...", RichMessageType.INFO)

        # 从执行日志中提取已完成的项目
        completed_items = []
        for log_entry in self.task_context["execution_log"]:
            response = log_entry["response"]
            if "搜索" in response or "信息收集" in response:
                completed_items.append("信息收集")
            if "分析" in response or "数据分析" in response:
                completed_items.append("数据分析")
            if "报告" in response or "生成" in response:
                completed_items.append("报告生成")
            if "验证" in response or "检查" in response:
                completed_items.append("结果验证")

        # 使用验证工具
        validation_prompt = f"请验证以下任务是否完成：{task_description}。已完成的项目：{completed_items}"
        validation_response = self.agent.chat(validation_prompt)

        return {
            "is_complete": len(completed_items) >= 3,  # 至少完成3个主要步骤
            "completed_items": completed_items,
            "validation_response": validation_response,
        }

    def _generate_execution_report(self, task_completed: bool) -> Dict[str, Any]:
        """生成执行报告"""
        end_time = time.time()
        execution_time = end_time - self.task_context["start_time"]

        return {
            "task_description": self.task_context["original_task"],
            "status": "completed" if task_completed else "incomplete",
            "execution_time": execution_time,
            "iterations": self.current_iteration,
            "max_iterations": self.max_iterations,
            "execution_log": self.task_context["execution_log"],
            "success_rate": (
                1.0 if task_completed else self.current_iteration / self.max_iterations
            ),
        }


# ==================== 演示场景 ====================


async def demo_simple_task():
    """演示简单任务自主执行"""
    rich_print_rule("演示1: 简单任务自主执行", style="blue")

    executor = AutonomousTaskExecutor(max_iterations=5)

    task = "请帮我研究一下人工智能在医疗领域的应用，并生成一份简要报告"

    result = await executor.execute_task(task)

    # 显示执行结果
    rich_print(f"\n📊 执行报告:", RichMessageType.SUCCESS)
    rich_print(f"任务状态: {result['status']}", RichMessageType.SYSTEM)
    rich_print(f"执行时间: {result['execution_time']:.2f}秒", RichMessageType.SYSTEM)
    rich_print(
        f"执行轮次: {result['iterations']}/{result['max_iterations']}",
        RichMessageType.SYSTEM,
    )
    rich_print(f"成功率: {result['success_rate']:.1%}", RichMessageType.SYSTEM)


async def demo_complex_task():
    """演示复杂任务自主执行"""
    rich_print_rule("演示2: 复杂任务自主执行", style="magenta")

    executor = AutonomousTaskExecutor(max_iterations=8)

    task = """请完成一个市场调研项目：
1. 调研电动汽车市场的现状和趋势
2. 分析主要竞争对手的优势劣势
3. 识别市场机会和威胁
4. 生成完整的市场调研报告
5. 发送报告给相关团队"""

    result = await executor.execute_task(task)

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


async def demo_interactive_task():
    """演示交互式任务定义"""
    rich_print_rule("演示3: 交互式任务定义", style="cyan")

    rich_print("请输入您希望ChatAgent自主完成的任务：", RichMessageType.INFO)

    # 模拟用户输入（在实际使用中可以用 input()）
    user_tasks = [
        "帮我分析区块链技术在金融行业的应用前景",
        "研究远程工作对企业文化的影响并提出建议",
        "调查可再生能源的发展趋势和投资机会",
    ]

    selected_task = user_tasks[0]  # 选择第一个任务进行演示
    rich_print(f"🎯 选定任务: {selected_task}", RichMessageType.USER)

    executor = AutonomousTaskExecutor(max_iterations=6)
    result = await executor.execute_task(selected_task)

    rich_print(
        f"\n✅ 任务执行{'成功' if result['status'] == 'completed' else '未完成'}",
        (
            RichMessageType.SUCCESS
            if result["status"] == "completed"
            else RichMessageType.WARNING
        ),
    )


async def demo_multi_agent_coordination():
    """演示多Agent协调执行"""
    rich_print_rule("演示4: 多Agent协调执行", style="yellow")

    # 创建多个专门的执行器
    research_executor = AutonomousTaskExecutor(max_iterations=4)
    analysis_executor = AutonomousTaskExecutor(max_iterations=4)

    # 定义协调任务
    main_task = "完成一个完整的产品竞争分析项目"

    # 第一阶段：研究
    research_task = "调研智能手机市场的主要品牌和产品特点"
    rich_print(f"🔍 第一阶段 - 市场调研: {research_task}", RichMessageType.INFO)
    research_result = await research_executor.execute_task(research_task)

    # 第二阶段：分析
    analysis_task = f"基于调研结果分析市场竞争格局和发展趋势"
    rich_print(f"📊 第二阶段 - 竞争分析: {analysis_task}", RichMessageType.INFO)
    analysis_result = await analysis_executor.execute_task(analysis_task)

    # 汇总结果
    rich_print(f"\n🎯 多Agent协调执行完成", RichMessageType.SUCCESS)
    rich_print(f"研究阶段: {research_result['status']}", RichMessageType.SYSTEM)
    rich_print(f"分析阶段: {analysis_result['status']}", RichMessageType.SYSTEM)


async def main():
    """主函数"""
    logger = setup_logging()
    logger.info("开始自主任务执行演示")

    rich_print_rule("ChatAgent 自主任务执行演示", style="bold blue")
    rich_print("这个演示将展示ChatAgent如何自主完成指定的任务", RichMessageType.INFO)

    try:
        # 演示1: 简单任务
        await demo_simple_task()

        # # 演示2: 复杂任务
        # await demo_complex_task()

        # # 演示3: 交互式任务
        # await demo_interactive_task()

        # # 演示4: 多Agent协调
        # await demo_multi_agent_coordination()

    except Exception as e:
        rich_print(f"演示过程中发生错误: {str(e)}", RichMessageType.ERROR)
        logger.error(f"演示错误: {str(e)}")
        import traceback

        rich_print(f"详细错误信息: {traceback.format_exc()}", RichMessageType.ERROR)

    logger.info("自主任务执行演示完成")
    rich_print_rule("演示完成", style="bold green")


if __name__ == "__main__":
    asyncio.run(main())
