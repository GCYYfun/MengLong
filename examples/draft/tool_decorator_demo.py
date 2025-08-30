#!/usr/bin/env python3
"""
ChatAgent Tool Decorator Demo - 演示 @tool 装饰器功能
==================================================

这个演示展示了如何使用 @tool 装饰器来简化工具注册：
1. 使用 @tool 装饰器标记函数
2. 自动参数推断
3. 多种工具注册方式
4. 与传统方式的对比

作者: MengLong AI Assistant
日期: 2025年6月12日
"""

import asyncio
import json
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
    configure_logger(log_file="tool_decorator_demo.log")
    return get_logger()


# ==================== 使用 @tool 装饰器定义工具 ====================


@tool(name="weather", description="获取指定位置的天气信息")
def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """获取天气信息"""
    weather_data = {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "partly cloudy",
        "humidity": "65%",
        "wind": "10 km/h",
    }
    return weather_data


@tool()  # 使用默认名称和描述
def calculate(expression: str) -> Dict[str, Any]:
    """进行数学计算"""
    try:
        result = eval(expression)  # 注意：生产环境中不要使用eval
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


@tool(name="search", description="搜索网络信息")
def search_web(query: str, max_results: int = 3) -> Dict[str, Any]:
    """搜索网络信息"""
    return {
        "query": query,
        "results": [
            {"title": f"搜索结果{i}: {query}", "url": f"https://example{i}.com"}
            for i in range(1, max_results + 1)
        ],
        "count": max_results,
    }


@tool(description="获取股票价格信息")
def get_stock_price(symbol: str) -> Dict[str, Any]:
    """获取股票价格"""
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


@tool(name="translator")
def translate_text(text: str, target_language: str = "english") -> Dict[str, Any]:
    """翻译文本到目标语言"""
    # 模拟翻译
    translations = {
        "english": {"你好": "Hello", "世界": "World"},
        "french": {"你好": "Bonjour", "世界": "Monde"},
        "spanish": {"你好": "Hola", "世界": "Mundo"},
    }

    translated = translations.get(target_language, {}).get(
        text, f"[翻译为{target_language}]{text}"
    )
    return {
        "original": text,
        "translated": translated,
        "target_language": target_language,
    }


# 传统方式定义的工具（用于对比）
def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """发送邮件（传统方式）"""
    return {
        "to": to,
        "subject": subject,
        "body": body,
        "status": "sent",
        "timestamp": "2025-06-12 10:00:00",
    }


# ==================== 演示函数 ====================


def demo_traditional_vs_decorator():
    """演示传统方式 vs 装饰器方式"""
    rich_print_rule("传统方式 vs 装饰器方式对比", style="blue")

    # 传统方式
    rich_print("🔧 传统方式注册工具:", RichMessageType.INFO)
    agent_traditional = ChatAgent(mode=ChatMode.AUTO)

    # 需要手动注册每个工具，并定义参数
    agent_traditional.register_tool(
        name="send_email",
        func=send_email,
        description="发送邮件",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件人邮箱"},
                "subject": {"type": "string", "description": "邮件主题"},
                "body": {"type": "string", "description": "邮件内容"},
            },
            "required": ["to", "subject", "body"],
        },
    )

    rich_print("传统方式需要手动定义参数规范，比较繁琐", RichMessageType.WARNING)

    # 装饰器方式
    rich_print("\n✨ 装饰器方式注册工具:", RichMessageType.INFO)
    agent_decorator = ChatAgent(mode=ChatMode.AUTO)

    # 方式1: 自动注册全局工具
    agent_decorator.auto_register_tools()

    rich_print("装饰器方式自动推断参数，一行代码搞定！", RichMessageType.SUCCESS)

    # 显示注册的工具
    rich_print(
        f"\n传统方式注册的工具: {list(agent_traditional.tools.keys())}",
        RichMessageType.SYSTEM,
    )
    rich_print(
        f"装饰器方式注册的工具: {list(agent_decorator.tools.keys())}",
        RichMessageType.SYSTEM,
    )


def demo_multiple_registration_methods():
    """演示多种工具注册方式"""
    rich_print_rule("多种工具注册方式演示", style="green")

    # 方式1: 初始化时自动注册全局工具
    rich_print("📝 方式1: 初始化时自动注册", RichMessageType.INFO)
    agent1 = ChatAgent(mode=ChatMode.AUTO, tools=None)  # None 表示注册全局工具
    rich_print(f"注册的工具: {list(agent1.tools.keys())}", RichMessageType.SUCCESS)

    # 方式2: 按名称注册特定工具
    rich_print("\n📝 方式2: 按名称注册特定工具", RichMessageType.INFO)
    agent2 = ChatAgent(mode=ChatMode.AUTO, tools=["weather", "calculate", "search"])
    rich_print(f"注册的工具: {list(agent2.tools.keys())}", RichMessageType.SUCCESS)

    # 方式3: 从函数列表注册
    rich_print("\n📝 方式3: 从函数列表注册", RichMessageType.INFO)
    agent3 = ChatAgent(mode=ChatMode.AUTO, tools=[get_weather, calculate])
    rich_print(f"注册的工具: {list(agent3.tools.keys())}", RichMessageType.SUCCESS)

    # 方式4: 从模块注册
    rich_print("\n📝 方式4: 从当前模块注册", RichMessageType.INFO)
    agent4 = ChatAgent(mode=ChatMode.AUTO)
    agent4.register_tools_from_module(globals())
    rich_print(f"注册的工具: {list(agent4.tools.keys())}", RichMessageType.SUCCESS)

    # 方式5: 后续添加工具
    rich_print("\n📝 方式5: 后续动态添加工具", RichMessageType.INFO)
    agent5 = ChatAgent(mode=ChatMode.AUTO)
    agent5.register_tools_from_functions(get_stock_price, translate_text)
    rich_print(f"注册的工具: {list(agent5.tools.keys())}", RichMessageType.SUCCESS)


def demo_auto_parameter_inference():
    """演示自动参数推断功能"""
    rich_print_rule("自动参数推断演示", style="cyan")

    agent = ChatAgent(mode=ChatMode.AUTO, tools=["weather", "calculate"])

    # 查看自动生成的参数规范
    for tool_name, tool_info in agent.tools.items():
        rich_print(f"\n🔧 工具: {tool_name}", RichMessageType.INFO)
        rich_print(f"描述: {tool_info['description']}", RichMessageType.SYSTEM)
        rich_print(f"参数规范:", RichMessageType.SYSTEM)
        rich_print(
            json.dumps(tool_info["parameters"], indent=2, ensure_ascii=False),
            RichMessageType.SUCCESS,
        )


def demo_tool_usage():
    """演示工具实际使用"""
    rich_print_rule("工具使用演示", style="yellow")

    # 创建agent并注册工具
    agent = ChatAgent(
        mode=ChatMode.AUTO,
        system="你是一个智能助手，可以使用各种工具来帮助用户。",
        tools=["weather", "calculate", "search", "get_stock_price"],
    )

    questions = [
        "北京今天的天气怎么样？",
        "帮我计算 25 * 13 + 100",
        "搜索一下人工智能的发展趋势",
        "查询一下AAPL股票的价格",
    ]

    for i, question in enumerate(questions, 1):
        rich_print(f"\n用户问题 {i}: {question}", RichMessageType.USER)
        try:
            response = agent.chat(question)
            rich_print(f"助手回复: {response}", RichMessageType.AGENT, use_panel=True)
            agent.context.clear()  # 清空上下文避免干扰
        except Exception as e:
            rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


def demo_mixed_tools():
    """演示混合使用传统方式和装饰器方式"""
    rich_print_rule("混合工具注册演示", style="magenta")

    agent = ChatAgent(mode=ChatMode.AUTO)

    # 1. 注册装饰器工具
    agent.auto_register_tools(["weather", "calculate"])

    # 2. 传统方式注册工具
    agent.register_tool(
        name="send_email",
        func=send_email,
        description="发送邮件",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收件人邮箱"},
                "subject": {"type": "string", "description": "邮件主题"},
                "body": {"type": "string", "description": "邮件内容"},
            },
            "required": ["to", "subject", "body"],
        },
    )

    rich_print(f"混合注册的工具: {list(agent.tools.keys())}", RichMessageType.SUCCESS)

    # 测试混合工具
    question = "帮我查一下上海的天气，然后给manager@company.com发送天气报告邮件"
    rich_print(f"\n用户问题: {question}", RichMessageType.USER)
    try:
        response = agent.chat(question)
        rich_print(f"助手回复: {response}", RichMessageType.AGENT, use_panel=True)
    except Exception as e:
        rich_print(f"错误: {str(e)}", RichMessageType.ERROR)


async def main():
    """主函数"""
    logger = setup_logging()
    logger.info("开始 Tool Decorator 演示")

    rich_print_rule("@tool 装饰器功能演示", style="bold blue")
    rich_print("这个演示将展示 @tool 装饰器的各种用法", RichMessageType.INFO)

    try:
        # 传统方式 vs 装饰器方式对比
        demo_traditional_vs_decorator()

        # 多种注册方式演示
        demo_multiple_registration_methods()

        # 自动参数推断演示
        demo_auto_parameter_inference()

        # 工具实际使用演示
        demo_tool_usage()

        # 混合工具注册演示
        demo_mixed_tools()

    except Exception as e:
        rich_print(f"演示过程中发生错误: {str(e)}", RichMessageType.ERROR)
        logger.error(f"演示错误: {str(e)}")
        import traceback

        rich_print(f"详细错误信息: {traceback.format_exc()}", RichMessageType.ERROR)

    logger.info("Tool Decorator 演示完成")
    rich_print_rule("演示完成", style="bold green")


if __name__ == "__main__":
    asyncio.run(main())
