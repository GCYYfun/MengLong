"""
完整工具参数格式演示

这个文件展示了如何使用改进后的 @tool 装饰器生成您提到的复杂参数格式：
{
    "type": "object",
    "properties": {
        "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA",
        },
        "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": 'The unit of temperature, either "celsius" or "fahrenheit"',
        },
    },
    "required": ["location"],
}

展示三种实现方式：
1. 完全手动定义
2. 自动生成（从类型注解和 docstring）
3. 混合方式（部分手动，部分自动）
"""

from typing import List, Dict, Any, Union, Optional, Literal
from enum import Enum
import json
from menglong.agents.component.tool_manager import tool, ToolInfo, get_global_tools


# ===================== 自动从函数获取数据的演示 =====================


# 方式A：纯自动生成（仅使用类型注解）
@tool()  # 不传任何参数，完全自动推断
def simple_calculator(expression: str, precision: int = 2) -> float:
    """
    简单计算器，支持基本数学运算

    Args:
        expression: 要计算的数学表达式，如 "2 + 3 * 4"
        precision: 结果保留的小数位数，默认为2

    Returns:
        计算结果
    """
    try:
        result = eval(expression)
        return round(result, precision)
    except Exception as e:
        return f"计算错误: {str(e)}"


# 方式B：使用枚举类型自动生成
class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@tool()  # 自动从枚举类型生成 enum 属性
def create_task(
    title: str,
    priority: Priority = Priority.MEDIUM,
    due_date: Optional[str] = None,
    tags: List[str] = None,
):
    """
    创建新任务

    Args:
        title: 任务标题
        priority: 任务优先级
        due_date: 截止日期 (YYYY-MM-DD 格式)
        tags: 任务标签列表
    """
    return {
        "id": hash(title) % 10000,
        "title": title,
        "priority": priority.value,
        "due_date": due_date,
        "tags": tags or [],
        "status": "created",
    }


# 方式C：复杂类型注解自动生成
@tool()
def search_database(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Literal["date", "relevance", "title"] = "relevance",
    limit: int = 10,
    include_metadata: bool = False,
):
    """
    搜索数据库

    Args:
        query: 搜索关键词
        filters: 搜索过滤条件，支持任意键值对
        sort_by: 排序方式
        limit: 返回结果数量限制 (1-100)
        include_metadata: 是否包含元数据信息
    """
    return {
        "query": query,
        "filters": filters or {},
        "sort_by": sort_by,
        "limit": min(max(limit, 1), 100),
        "include_metadata": include_metadata,
        "results": f"找到 {limit} 条相关结果",
    }


# 方式D：使用 Union 类型
@tool()
def process_data(
    data: Union[str, int, float, List[str]],
    operation: Literal["count", "sum", "average", "concat"] = "count",
):
    """
    处理各种类型的数据

    Args:
        data: 输入数据，可以是字符串、数字或字符串列表
        operation: 要执行的操作类型
    """
    if operation == "count":
        return len(str(data)) if isinstance(data, (str, int, float)) else len(data)
    elif operation == "sum" and isinstance(data, list):
        return sum(float(x) for x in data if str(x).replace(".", "").isdigit())
    elif operation == "concat" and isinstance(data, list):
        return " ".join(str(x) for x in data)
    else:
        return f"执行 {operation} 操作在 {type(data).__name__} 类型数据上"


# 方式E：详细的 docstring 参数描述
@tool()
def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    priority: Literal["low", "normal", "high"] = "normal",
    html: bool = False,
):
    """
    发送电子邮件

    这个函数可以发送电子邮件到指定的收件人，支持抄送、密送和不同的优先级设置。

    Args:
        to: 主要收件人的邮箱地址，格式如 "user@example.com"
        subject: 邮件主题，建议简洁明了
        body: 邮件正文内容
        cc: 抄送邮箱地址列表，可选
        bcc: 密送邮箱地址列表，可选
        priority: 邮件优先级，影响收件人的邮箱显示
        html: 是否使用 HTML 格式发送邮件

    Returns:
        发送状态信息

    Example:
        send_email("john@example.com", "会议提醒", "明天下午2点开会")
    """
    return {
        "status": "sent",
        "to": to,
        "subject": subject,
        "message_id": f"msg_{hash(to + subject) % 10000}",
        "timestamp": "2025-06-18T10:30:00Z",
    }


# ===================== 原有的演示代码 =====================
# 方式1：完全手动定义（与您的示例完全相同）
@tool(
    name="get_weather_manual",
    description="获取天气信息（手动定义参数）",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": 'The unit of temperature, either "celsius" or "fahrenheit"',
            },
        },
        "required": ["location"],
    },
)
def get_weather_manual(location: str, unit: str = "celsius"):
    """手动定义参数的天气查询函数"""
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "description": "Sunny",
    }


# 方式2：完全自动生成（从类型注解和 docstring）
@tool(name="get_weather_auto", description="获取天气信息（自动生成参数）")
def get_weather_auto(location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"):
    """获取天气信息的自动生成参数版本

    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The unit of temperature, either "celsius" or "fahrenheit"
    """
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "description": "Sunny",
    }


# 方式3：更复杂的示例 - 完全覆盖您的格式需求
@tool(
    name="advanced_weather_query",
    description="高级天气查询工具",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
                "minLength": 1,
                "maxLength": 100,
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": 'The unit of temperature, either "celsius" or "fahrenheit"',
                "default": "celsius",
            },
            "include_details": {
                "type": "boolean",
                "description": "Whether to include detailed weather information",
                "default": False,
            },
            "forecast_options": {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable weather forecast",
                        "default": False,
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days",
                        "minimum": 1,
                        "maximum": 14,
                        "default": 5,
                    },
                    "include_hourly": {
                        "type": "boolean",
                        "description": "Include hourly forecast",
                        "default": False,
                    },
                },
                "description": "Forecast configuration options",
            },
            "alerts": {
                "type": "array",
                "items": {"type": "string", "enum": ["severe", "moderate", "advisory"]},
                "description": "Types of weather alerts to include",
                "default": [],
            },
        },
        "required": ["location"],
        "additionalProperties": False,
    },
)
def advanced_weather_query(
    location: str,
    unit: str = "celsius",
    include_details: bool = False,
    forecast_options: Dict = None,
    alerts: List[str] = None,
):
    """高级天气查询函数"""
    if forecast_options is None:
        forecast_options = {"enabled": False, "days": 5, "include_hourly": False}
    if alerts is None:
        alerts = []

    result = {
        "location": location,
        "current": {
            "temperature": 22 if unit == "celsius" else 72,
            "unit": unit,
            "description": "Sunny",
        },
    }

    if include_details:
        result["current"].update(
            {"humidity": 65, "wind_speed": 10, "pressure": 1013.25}
        )

    if forecast_options.get("enabled"):
        result["forecast"] = [
            {
                "day": i + 1,
                "high": 25 + i if unit == "celsius" else 77 + i * 2,
                "low": 18 + i if unit == "celsius" else 64 + i * 2,
            }
            for i in range(forecast_options.get("days", 5))
        ]

    if alerts:
        result["alerts"] = [f"{alert} weather alert" for alert in alerts]

    return result


# 方式4：使用枚举类自动生成
class WeatherUnit(Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class AlertType(Enum):
    SEVERE = "severe"
    MODERATE = "moderate"
    ADVISORY = "advisory"


@tool(name="get_weather_with_enums", description="使用枚举类的天气查询")
def get_weather_with_enums(
    location: str,
    unit: WeatherUnit = WeatherUnit.CELSIUS,
    alert_types: Optional[List[AlertType]] = None,
):
    """使用枚举类型的天气查询函数

    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: The unit of temperature
        alert_types: Types of weather alerts to monitor
    """
    return {
        "location": location,
        "temperature": 22 if unit == WeatherUnit.CELSIUS else 72,
        "unit": unit.value,
        "alerts": [alert.value for alert in (alert_types or [])],
    }


def demonstrate_parameter_formats():
    """演示不同的参数格式生成方式"""
    print("工具参数格式演示")
    print("=" * 80)

    tools = get_global_tools()

    # 展示不同的实现方式
    demo_tools = [
        ("手动定义", "get_weather_manual"),
        ("自动生成", "get_weather_auto"),
        ("复杂示例", "advanced_weather_query"),
        ("枚举类型", "get_weather_with_enums"),
    ]

    for title, tool_name in demo_tools:
        if tool_name in tools:
            print(f"\n{title} ({tool_name}):")
            print("-" * 40)
            tool_info = tools[tool_name]
            print(json.dumps(tool_info.parameters, indent=2, ensure_ascii=False))
            print()


def test_parameter_execution():
    """测试不同参数格式的执行"""
    print("\n=== 参数执行测试 ===")

    # 测试手动定义的工具
    result1 = get_weather_manual("San Francisco, CA", "fahrenheit")
    print("手动定义工具执行结果:")
    print(json.dumps(result1, indent=2, ensure_ascii=False))

    # 测试自动生成的工具
    result2 = get_weather_auto("北京, 中国", "celsius")
    print("\n自动生成工具执行结果:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))

    # 测试复杂参数的工具
    result3 = advanced_weather_query(
        location="Tokyo, Japan",
        unit="celsius",
        include_details=True,
        forecast_options={"enabled": True, "days": 3, "include_hourly": True},
        alerts=["severe", "moderate"],
    )
    print("\n复杂参数工具执行结果:")
    print(json.dumps(result3, indent=2, ensure_ascii=False))

    # 测试枚举类型的工具
    result4 = get_weather_with_enums(
        location="London, UK",
        unit=WeatherUnit.CELSIUS,
        alert_types=[AlertType.SEVERE, AlertType.ADVISORY],
    )
    print("\n枚举类型工具执行结果:")
    print(json.dumps(result4, indent=2, ensure_ascii=False))


def show_exact_target_format():
    """展示与您的目标格式完全相同的输出"""
    print("\n=== 目标格式对比 ===")

    print("您的目标格式:")
    target_format = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": 'The unit of temperature, either "celsius" or "fahrenheit"',
            },
        },
        "required": ["location"],
    }
    print(json.dumps(target_format, indent=2, ensure_ascii=False))

    print("\n我们生成的格式 (手动定义):")
    tools = get_global_tools()
    manual_format = tools["get_weather_manual"].parameters
    print(json.dumps(manual_format, indent=2, ensure_ascii=False))

    print("\n我们生成的格式 (自动生成):")
    auto_format = tools["get_weather_auto"].parameters
    print(json.dumps(auto_format, indent=2, ensure_ascii=False))


def demonstrate_auto_parameter_generation():
    """演示自动从函数获取参数的各种方式"""
    print("\n=== 自动参数生成演示 ===")

    tools = get_global_tools()

    # 展示纯自动生成的工具
    auto_tools = [
        "simple_calculator",
        "create_task",
        "search_database",
        "process_data",
        "send_email",
    ]

    for tool_name in auto_tools:
        if tool_name in tools:
            tool_info = tools[tool_name]
            print(f"\n工具名称: {tool_name}")
            print(f"描述: {tool_info.description}")
            print("自动生成的参数格式:")
            print(json.dumps(tool_info.parameters, indent=2, ensure_ascii=False))
            print("-" * 50)


def test_auto_generated_tools():
    """测试自动生成的工具执行"""
    print("\n=== 自动生成工具执行测试 ===")

    tools = get_global_tools()

    # 测试计算器
    if "simple_calculator" in tools:
        calc_tool = tools["simple_calculator"]
        result = calc_tool.func("2 + 3 * 4", precision=3)
        print(f"计算器测试: 2 + 3 * 4 = {result}")

    # 测试任务创建
    if "create_task" in tools:
        task_tool = tools["create_task"]
        result = task_tool.func(
            title="完成项目文档",
            priority=Priority.HIGH,
            due_date="2025-06-25",
            tags=["文档", "urgent"],
        )
        print(f"\n任务创建测试:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 测试数据库搜索
    if "search_database" in tools:
        search_tool = tools["search_database"]
        result = search_tool.func(
            query="Python 教程",
            filters={"category": "programming", "level": "beginner"},
            sort_by="relevance",
            limit=5,
            include_metadata=True,
        )
        print(f"\n数据库搜索测试:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 测试数据处理
    if "process_data" in tools:
        process_tool = tools["process_data"]
        result1 = process_tool.func(["apple", "banana", "cherry"], "concat")
        result2 = process_tool.func([1, 2, 3, 4, 5], "sum")
        print(f"\n数据处理测试:")
        print(f"字符串连接: {result1}")
        print(f"数字求和: {result2}")

    # 测试邮件发送
    if "send_email" in tools:
        email_tool = tools["send_email"]
        result = email_tool.func(
            to="john@example.com",
            subject="会议提醒",
            body="明天下午2点开会，请准时参加。",
            cc=["manager@example.com"],
            priority="high",
            html=False,
        )
        print(f"\n邮件发送测试:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


def compare_manual_vs_auto():
    """对比手动定义和自动生成的参数格式"""
    print("\n=== 手动 vs 自动参数生成对比 ===")

    tools = get_global_tools()

    # 对比天气查询工具
    manual_tool = tools.get("get_weather_manual")
    auto_tool = tools.get("get_weather_auto")

    if manual_tool and auto_tool:
        print("手动定义的天气工具参数:")
        print(json.dumps(manual_tool.parameters, indent=2, ensure_ascii=False))

        print("\n自动生成的天气工具参数:")
        print(json.dumps(auto_tool.parameters, indent=2, ensure_ascii=False))

        print("\n主要差异:")
        print("1. 手动定义可以添加更详细的约束（如 minLength, maxLength）")
        print("2. 自动生成更简洁，但同样支持 enum 和描述")
        print("3. 自动生成会从 docstring 中提取参数描述")
        print("4. 两种方式都能生成符合标准的 JSON Schema 格式")


def show_complex_auto_examples():
    """展示复杂的自动生成示例"""
    print("\n=== 复杂自动生成示例 ===")

    tools = get_global_tools()

    # 展示包含枚举、可选参数、列表等复杂类型的工具
    complex_tools = ["create_task", "search_database", "send_email"]

    for tool_name in complex_tools:
        if tool_name in tools:
            tool_info = tools[tool_name]
            print(f"\n=== {tool_name} ===")
            print(f"描述: {tool_info.description}")

            params = tool_info.parameters
            properties = params.get("properties", {})
            required = params.get("required", [])

            print("参数详情:")
            for param_name, param_info in properties.items():
                status = "必需" if param_name in required else "可选"
                param_type = param_info.get("type", "unknown")
                description = param_info.get("description", "无描述")

                print(f"  - {param_name} ({param_type}, {status}): {description}")

                # 显示特殊属性
                if "enum" in param_info:
                    print(f"    可选值: {param_info['enum']}")
                if "default" in param_info:
                    print(f"    默认值: {param_info['default']}")
                if param_info.get("type") == "array" and "items" in param_info:
                    print(f"    数组元素类型: {param_info['items']}")

            print(f"\n完整 JSON Schema:")
            print(json.dumps(params, indent=2, ensure_ascii=False))
            print("-" * 70)


# 在主函数中添加新的演示
if __name__ == "__main__":
    print("🚀 完整工具参数格式演示")
    print("=" * 60)

    # 1. 基础参数格式演示
    demonstrate_parameter_formats()

    # 2. 自动参数生成演示
    demonstrate_auto_parameter_generation()

    # 3. 自动生成工具执行测试
    test_auto_generated_tools()

    # 4. 手动 vs 自动对比
    compare_manual_vs_auto()

    # 5. 复杂自动生成示例
    show_complex_auto_examples()

    # 6. 工具执行测试
    test_parameter_execution()

    # 7. 目标格式对比
    show_exact_target_format()

    print("\n🎉 演示完成！")
    print("=" * 60)
    demonstrate_auto_parameter_generation()
    test_auto_generated_tools()
    compare_manual_vs_auto()
    show_complex_auto_examples()
