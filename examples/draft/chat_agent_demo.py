#!/usr/bin/env python3
"""
ChatAgent Demo - 演示 ChatAgent 的不同模式功能
=====================================

这个演示展示了 ChatAgent 的三种模式：
1. Normal Mode - 普通聊天模式
2. Auto Mode - 自动模式，支持工具调用
3. Workflow Mode - 工作流模式，支持多步骤任务

作者: MengLong AI Assistant
日期: 2025年6月11日
"""

import asyncio
import json
from typing import Dict, Any
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode
from menglong.ml_model import Model
from menglong.utils.log import (
    rich_print,
    rich_print_rule,
    RichMessageType,
    configure_logger,
    get_logger,
)


def setup_logging():
    """设置日志"""
    configure_logger(log_file="chat_agent_demo.log")
    return get_logger()


def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """模拟天气查询工具"""
    # 模拟天气数据
    weather_data = {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "partly cloudy",
        "humidity": "65%",
        "wind": "10 km/h",
    }
    return weather_data


def search_web(query: str) -> Dict[str, Any]:
    """模拟网络搜索工具"""
    return {
        "query": query,
        "results": [
            {"title": f"搜索结果1: {query}", "url": "https://example1.com"},
            {"title": f"搜索结果2: {query}", "url": "https://example2.com"},
        ],
        "count": 2,
    }


def calculate(expression: str) -> Dict[str, Any]:
    """简单计算工具"""
    try:
        result = eval(expression)  # 注意：在生产环境中不要使用eval
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


def get_stock_price(symbol: str) -> Dict[str, Any]:
    """模拟股票价格查询工具"""
    import random

    price = round(random.uniform(50, 500), 2)
    change = round(random.uniform(-10, 10), 2)
    return {
        "symbol": symbol,
        "price": price,
        "change": change,
        "change_percent": round((change / price) * 100, 2),
        "status": "success",
    }


def analyze_data(data: str, analysis_type: str = "trend") -> Dict[str, Any]:
    """模拟数据分析工具"""
    if analysis_type == "trend":
        return {
            "analysis_type": "趋势分析",
            "result": "数据显示上涨趋势",
            "confidence": 0.85,
            "recommendation": "建议持续观察",
        }
    elif analysis_type == "risk":
        return {
            "analysis_type": "风险分析",
            "result": "中等风险水平",
            "risk_score": 6.5,
            "recommendation": "建议适度投资",
        }
    else:
        return {
            "analysis_type": analysis_type,
            "result": "分析完成",
            "status": "success",
        }


def validate_solution(problem: str, solution: str) -> Dict[str, Any]:
    """模拟解决方案验证工具"""
    import random

    is_solved = random.choice([True, False, False])  # 模拟解决概率
    return {
        "problem": problem,
        "solution": solution,
        "is_solved": is_solved,
        "confidence": random.uniform(0.6, 0.95),
        "next_steps": "继续分析" if not is_solved else "问题已解决",
    }


def demo_normal_mode():
    """演示普通聊天模式"""
    rich_print_rule("普通聊天模式演示", style="green")

    # 创建普通模式的ChatAgent
    agent = ChatAgent(
        # model_id="deepseek-chat",  # 使用deepseek模型
        system="你是一个友好的AI助手，专门帮助用户解决问题。请用中文回复。",
        mode=ChatMode.NORMAL,
    )

    # 测试对话
    questions = [
        "你好，请介绍一下你自己",
        "今天天气怎么样？",
        "能帮我写一首关于春天的诗吗？",
    ]

    for i, question in enumerate(questions, 1):
        rich_print(f"\n用户问题 {i}: {question}", RichMessageType.USER)
        try:
            response = agent.chat(question)
            rich_print(f"助手回复: {response}", RichMessageType.AGENT, use_panel=True)
            agent.reset()  # 重置状态以避免上下文干扰
        except Exception as e:
            rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


def demo_auto_mode():
    """演示自动模式（工具调用）"""
    rich_print_rule("自动模式演示（工具调用）", style="blue")

    # 创建自动模式的ChatAgent
    agent = ChatAgent(
        system="你是一个智能助手，可以使用工具来帮助用户。当需要查询天气、搜索信息或进行计算时，请使用相应的工具。",
        mode=ChatMode.AUTO,
    )

    # 注册工具
    agent.register_tool(
        name="get_weather",
        func=get_weather,
        description="获取指定位置的天气信息",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，例如：北京, 上海",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位",
                },
            },
            "required": ["location"],
        },
    )

    agent.register_tool(
        name="search_web",
        func=search_web,
        description="搜索网络信息",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"],
        },
    )

    agent.register_tool(
        name="calculate",
        func=calculate,
        description="进行数学计算",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，例如：2+3*4",
                }
            },
            "required": ["expression"],
        },
    )

    # 测试工具调用
    questions = [
        "北京今天的天气怎么样？",
        "帮我搜索一下人工智能的最新发展",
        "计算一下 15 * 23 + 47 等于多少？",
    ]

    for i, question in enumerate(questions, 1):
        rich_print(f"\n用户问题 {i}: {question}", RichMessageType.USER)
        try:
            response = agent.chat(question)
            rich_print(f"助手回复: {response}", RichMessageType.AGENT, use_panel=True)
            agent.reset()  # 重置状态以避免上下文干扰
        except Exception as e:
            rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


def demo_workflow_mode():
    """演示工作流模式"""
    rich_print_rule("工作流模式演示", style="magenta")

    # 创建工作流模式的ChatAgent
    agent = ChatAgent(
        model_id="deepseek-chat",
        system="你是一个工作流助手，会按照预定义的步骤来处理任务。",
        mode=ChatMode.WORKFLOW,
    )

    # 定义工作流步骤
    def step1_analyze(input_msg, context):
        """步骤1：分析用户需求"""
        return f"分析用户需求: '{input_msg}' - 识别为信息查询任务"

    def step2_plan(input_msg, context):
        """步骤2：制定计划"""
        return "制定执行计划: 1)收集信息 2)整理数据 3)生成回复"

    def step3_execute(input_msg, context):
        """步骤3：执行任务"""
        return f"执行任务: 为用户查询 '{input_msg}' 收集相关信息"

    def step4_summarize(input_msg, context):
        """步骤4：总结结果"""
        return "总结结果: 任务执行完成，已为用户提供所需信息"

    # 添加工作流步骤
    agent.add_workflow_step("需求分析", step1_analyze)
    agent.add_workflow_step("计划制定", step2_plan)
    agent.add_workflow_step("任务执行", step3_execute)
    agent.add_workflow_step("结果总结", step4_summarize)

    # 测试工作流
    question = "我想了解一下机器学习的基础知识"
    rich_print(f"\n用户问题: {question}", RichMessageType.USER)

    try:
        # 显示工作流状态
        rich_print("工作流状态:", RichMessageType.INFO)
        rich_print(agent.get_workflow_status(), RichMessageType.SYSTEM)

        # 执行工作流
        response = agent.chat(question)
        rich_print(f"\n工作流执行结果:", RichMessageType.AGENT, use_panel=True)
        rich_print(response, RichMessageType.SUCCESS)

        # 显示更新后的工作流状态
        rich_print("\n更新后的工作流状态:", RichMessageType.INFO)
        rich_print(agent.get_workflow_status(), RichMessageType.SYSTEM)

    except Exception as e:
        rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


async def demo_async_workflow():
    """演示异步工作流"""
    rich_print_rule("异步工作流演示", style="cyan")

    agent = ChatAgent(
        system="你是一个异步工作流助手。",
        mode=ChatMode.WORKFLOW,
    )

    # 定义异步步骤
    async def async_step1(input_msg, context):
        await asyncio.sleep(1)  # 模拟异步操作
        return f"异步步骤1完成: 处理 '{input_msg}'"

    async def async_step2(input_msg, context):
        await asyncio.sleep(2)  # 模拟异步操作
        return f"异步步骤2完成: 深度分析 '{input_msg}'"

    def sync_step3(input_msg, context):
        return f"同步步骤3完成: 生成最终回复"

    # 添加异步工作流步骤
    agent.add_workflow_step("异步分析", async_step1)
    agent.add_workflow_step("异步处理", async_step2)
    agent.add_workflow_step("同步总结", sync_step3)

    question = "请帮我分析人工智能的发展趋势"
    rich_print(f"\n用户问题: {question}", RichMessageType.USER)

    try:
        rich_print("开始异步工作流执行...", RichMessageType.INFO)
        start_time = asyncio.get_event_loop().time()

        response = await agent.chat_async(question)

        end_time = asyncio.get_event_loop().time()
        rich_print(
            f"异步工作流执行完成 (耗时: {end_time - start_time:.2f}秒)",
            RichMessageType.SUCCESS,
        )
        rich_print(response, RichMessageType.AGENT, use_panel=True)

    except Exception as e:
        rich_print(f"错误: {str(e)}", RichMessageType.ERROR)
        import traceback

        rich_print(f"详细错误信息: {traceback.format_exc()}", RichMessageType.ERROR)


def demo_chat_stream():
    """演示流式聊天"""
    rich_print_rule("流式聊天演示", style="yellow")

    agent = ChatAgent(
        model_id="deepseek-chat",
        system="你是一个支持流式输出的AI助手。",
        mode=ChatMode.AUTO,
    )

    question = "请详细介绍一下深度学习的发展历程"
    rich_print(f"\n用户问题: {question}", RichMessageType.USER)

    try:
        rich_print("流式响应:", RichMessageType.INFO)
        response = agent.chat_stream(question)
        rich_print(response, RichMessageType.AGENT, use_panel=True)

    except Exception as e:
        rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


def interactive_demo():
    """交互式演示"""
    rich_print_rule("交互式演示", style="red")
    rich_print(
        "输入 'quit' 退出，输入 'mode <模式>' 切换模式 (normal/auto/workflow)",
        RichMessageType.INFO,
    )

    # 默认使用自动模式
    agent = ChatAgent(
        model_id="deepseek-chat",
        system="你是一个多功能AI助手，可以根据需要使用工具或执行工作流。",
        mode=ChatMode.AUTO,
    )

    # 注册一些基础工具
    agent.register_tool("get_weather", get_weather, "获取天气信息")
    agent.register_tool("calculate", calculate, "数学计算")

    while True:
        try:
            user_input = input("\n用户: ").strip()

            if user_input.lower() == "quit":
                rich_print("再见！", RichMessageType.INFO)
                break

            if user_input.startswith("mode "):
                mode_str = user_input.split(" ", 1)[1].lower()
                if mode_str == "normal":
                    agent.mode = ChatMode.NORMAL
                elif mode_str == "auto":
                    agent.mode = ChatMode.AUTO
                elif mode_str == "workflow":
                    agent.mode = ChatMode.WORKFLOW
                else:
                    rich_print(
                        "无效模式，请使用: normal, auto, workflow",
                        RichMessageType.WARNING,
                    )
                    continue
                rich_print(f"已切换到 {mode_str} 模式", RichMessageType.SUCCESS)
                continue

            if not user_input:
                continue

            response = agent.chat(user_input)
            rich_print(f"助手: {response}", RichMessageType.AGENT)

        except KeyboardInterrupt:
            rich_print("\n用户中断，退出程序", RichMessageType.WARNING)
            break
        except Exception as e:
            rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


def demo_multi_step_problem_solving():
    """演示多步工具调用解决复杂问题"""
    rich_print_rule("多步工具调用问题解决演示", style="red")

    # 创建自动模式的ChatAgent
    agent = ChatAgent(
        system="""你是一个智能问题解决助手。当收到复杂问题时，你需要：
1. 首先分析问题，制定解决计划
2. 逐步调用相关工具收集信息
3. 分析收集到的数据
4. 验证解决方案是否完整
5. 如果问题未完全解决，继续重复上述步骤直到解决

请一步一步地解决问题，并在每个步骤后检查是否需要更多信息。""",
        mode=ChatMode.AUTO,
    )

    # 注册工具
    agent.register_tool(
        name="get_stock_price",
        func=get_stock_price,
        description="获取股票实时价格信息",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，例如：AAPL, TSLA, MSFT",
                }
            },
            "required": ["symbol"],
        },
    )

    agent.register_tool(
        name="search_web",
        func=search_web,
        description="搜索网络信息",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"],
        },
    )

    agent.register_tool(
        name="analyze_data",
        func=analyze_data,
        description="分析数据并提供洞察",
        parameters={
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "要分析的数据"},
                "analysis_type": {
                    "type": "string",
                    "enum": ["trend", "risk", "performance"],
                    "description": "分析类型",
                },
            },
            "required": ["data"],
        },
    )

    agent.register_tool(
        name="validate_solution",
        func=validate_solution,
        description="验证解决方案是否完整和正确",
        parameters={
            "type": "object",
            "properties": {
                "problem": {"type": "string", "description": "原始问题"},
                "solution": {"type": "string", "description": "提出的解决方案"},
            },
            "required": ["problem", "solution"],
        },
    )

    # 复杂问题示例
    complex_problem = "我想投资科技股，请帮我分析AAPL和TSLA这两只股票，给出投资建议并确保分析全面完整。"

    rich_print(f"\n🎯 复杂问题: {complex_problem}", RichMessageType.USER)
    rich_print("\n📋 开始多步骤问题解决过程...", RichMessageType.INFO)

    max_iterations = 5  # 最大迭代次数，防止无限循环
    iteration = 0
    problem_solved = False

    try:
        while not problem_solved and iteration < max_iterations:
            iteration += 1
            rich_print(f"\n🔄 第 {iteration} 轮分析", RichMessageType.INFO)

            # 构建当前轮次的提示
            if iteration == 1:
                current_prompt = complex_problem
            else:
                current_prompt = f"""继续分析问题: {complex_problem}

这是第{iteration}轮分析，请根据之前收集的信息继续完善分析，
如果信息不够充分，请继续调用工具获取更多数据。
最后请验证解决方案是否完整。"""

            # 让Agent处理问题
            response = agent.chat(current_prompt)

            rich_print(
                f"\n📝 第 {iteration} 轮分析结果:",
                RichMessageType.AGENT,
                use_panel=True,
            )
            rich_print(response, RichMessageType.SUCCESS)

            # 检查是否需要验证解决方案
            if iteration >= 2:  # 从第2轮开始可以验证
                rich_print(f"\n🔍 验证解决方案...", RichMessageType.INFO)
                validation_prompt = (
                    f"请验证当前的分析和建议是否完整解决了这个问题: {complex_problem}"
                )
                validation_response = agent.chat(validation_prompt)

                rich_print(f"验证结果: {validation_response}", RichMessageType.SYSTEM)

                # 简单检查是否包含"完整"、"解决"等关键词
                if any(
                    keyword in validation_response.lower()
                    for keyword in ["完整", "解决", "充分", "满足"]
                ):
                    problem_solved = True
                    rich_print("✅ 问题已完整解决！", RichMessageType.SUCCESS)
                else:
                    rich_print("⚠️ 解决方案需要进一步完善", RichMessageType.WARNING)

            rich_print("-" * 80, RichMessageType.SYSTEM)

        if not problem_solved:
            rich_print(
                f"⚠️ 达到最大迭代次数({max_iterations})，分析结束",
                RichMessageType.WARNING,
            )

        # 总结
        rich_print(f"\n📊 问题解决总结:", RichMessageType.INFO)
        rich_print(f"• 总迭代次数: {iteration}", RichMessageType.SYSTEM)
        rich_print(
            f"• 问题状态: {'✅ 已解决' if problem_solved else '⚠️ 需进一步分析'}",
            RichMessageType.SYSTEM,
        )
        rich_print(f"• 调用的工具: {list(agent.tools.keys())}", RichMessageType.SYSTEM)

    except Exception as e:
        rich_print(f"❌ 多步问题解决过程中发生错误: {str(e)}", RichMessageType.ERROR)


async def main():
    """主函数"""
    logger = setup_logging()
    logger.info("开始 ChatAgent 演示")

    rich_print_rule("ChatAgent 功能演示", style="bold blue")
    rich_print("这个演示将展示 ChatAgent 的三种模式功能", RichMessageType.INFO)

    try:
        # # 普通模式演示
        # demo_normal_mode()

        # # 自动模式演示
        # demo_auto_mode()

        # # 多步工具调用问题解决演示
        demo_multi_step_problem_solving()

        # 工作流模式演示
        # demo_workflow_mode()

        # # 异步工作流演示
        # await demo_async_workflow()

        # # 流式聊天演示
        # demo_chat_stream()

        # 交互式演示（注释掉，因为这会阻塞自动测试）
        # interactive_demo()

    except Exception as e:
        rich_print(f"演示过程中发生错误: {str(e)}", RichMessageType.ERROR)
        logger.error(f"演示错误: {str(e)}")
        import traceback

        rich_print(f"详细错误信息: {traceback.format_exc()}", RichMessageType.ERROR)

    logger.info("ChatAgent 演示完成")
    rich_print_rule("演示完成", style="bold green")


if __name__ == "__main__":
    asyncio.run(main())
