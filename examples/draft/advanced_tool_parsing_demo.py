"""
高级工具参数解析演示

这个文件展示了改进后的 @tool 装饰器如何：
1. 从 docstring 自动提取参数描述
2. 支持 Literal 类型注解（自动转换为 enum）
3. 支持嵌套类型注解（List[str], Dict[str, Any] 等）
4. 支持 Enum 类型
5. 自动生成完整的 JSON Schema 参数规范
"""

from typing import List, Dict, Any, Union, Optional, Literal
from enum import Enum
import json
from menglong.agents.component.tool_manager import tool, ToolInfo, get_global_tools


# 示例1：从 docstring 自动提取参数描述
@tool(name="get_weather_smart", description="智能天气查询工具")
def get_weather_smart(
    location: str,
    unit: Literal["celsius", "fahrenheit"] = "celsius",
    include_forecast: bool = False,
    forecast_days: int = 3,
):
    """获取指定位置的智能天气信息

    这个函数可以获取当前天气和未来天气预报。

    Args:
        location: 城市和州，例如 San Francisco, CA 或 北京, 中国
        unit: 温度单位，可选择摄氏度或华氏度
        include_forecast: 是否包含未来几天的天气预报
        forecast_days: 预报天数，建议 1-7 天

    Returns:
        包含天气信息的字典
    """
    result = {
        "location": location,
        "current": {
            "temperature": 22 if unit == "celsius" else 72,
            "unit": unit,
            "description": "晴朗",
            "humidity": 65,
        },
    }

    if include_forecast:
        result["forecast"] = [
            {"day": f"Day {i+1}", "temp": 25 + i} for i in range(forecast_days)
        ]

    return result


# 示例2：使用 Enum 类型
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@tool(name="update_task_status")
def update_task_status(
    task_id: str,
    status: TaskStatus,
    priority: Optional[Priority] = None,
    assigned_to: Optional[List[str]] = None,
    notes: str = "",
):
    """更新任务状态

    Args:
        task_id: 任务的唯一标识符
        status: 新的任务状态
        priority: 任务优先级（可选）
        assigned_to: 分配给的用户列表（可选）
        notes: 更新说明
    """
    return {
        "task_id": task_id,
        "status": status.value if isinstance(status, TaskStatus) else status,
        "priority": priority.value if priority else None,
        "assigned_to": assigned_to or [],
        "notes": notes,
        "updated_at": "2025-06-18T10:00:00Z",
    }


# 示例3：复杂嵌套类型
@tool(name="analyze_data")
def analyze_data(
    data_source: str,
    filters: Dict[str, Any],
    aggregations: List[str],
    output_format: Literal["json", "csv", "excel"] = "json",
    include_metadata: bool = True,
):
    """分析数据源

    对指定的数据源执行分析操作，支持过滤、聚合等功能。

    Args:
        data_source: 数据源标识符或路径
        filters: 数据过滤条件，键值对格式
        aggregations: 聚合操作列表，如 ["sum", "avg", "count"]
        output_format: 输出格式选择
        include_metadata: 是否在结果中包含元数据信息
    """
    return {
        "data_source": data_source,
        "filters_applied": filters,
        "aggregations_performed": aggregations,
        "output_format": output_format,
        "metadata": (
            {"total_rows": 1000, "processing_time": "2.5s"}
            if include_metadata
            else None
        ),
        "results": ["示例结果数据"],
    }


# 示例4：Union 类型
@tool(name="send_notification")
def send_notification(
    recipient: Union[str, List[str]],
    message: str,
    channel: Literal["email", "sms", "push"] = "email",
    priority: int = 1,
    schedule_time: Optional[str] = None,
):
    """发送通知

    Args:
        recipient: 接收者，可以是单个用户ID或用户ID列表
        message: 通知消息内容
        channel: 发送渠道选择
        priority: 优先级，1-5，数字越大优先级越高
        schedule_time: 定时发送时间，格式：YYYY-MM-DD HH:MM:SS
    """
    recipients = recipient if isinstance(recipient, list) else [recipient]

    return {
        "notification_id": "notif_123",
        "recipients": recipients,
        "message": message,
        "channel": channel,
        "priority": priority,
        "schedule_time": schedule_time,
        "status": "queued",
    }


def print_tool_schema(tool_name: str):
    """打印工具的完整 JSON Schema"""
    tools = get_global_tools()
    if tool_name in tools:
        tool_info = tools[tool_name]
        print(f"\n=== {tool_name} ===")
        print(f"描述: {tool_info.description}")
        print("参数规范:")
        print(json.dumps(tool_info.parameters, indent=2, ensure_ascii=False))
        print("-" * 80)
    else:
        print(f"工具 '{tool_name}' 未找到")


def demonstrate_advanced_parsing():
    """演示高级参数解析功能"""
    print("高级工具参数解析演示")
    print("=" * 80)

    # 演示所有注册的工具
    demo_tools = [
        "get_weather_smart",
        "update_task_status",
        "analyze_data",
        "send_notification",
    ]

    for tool_name in demo_tools:
        print_tool_schema(tool_name)


def test_enum_parameter_execution():
    """测试枚举参数的执行"""
    print("\n=== 枚举参数执行测试 ===")

    # 测试任务状态更新
    result1 = update_task_status(
        task_id="task_456",
        status=TaskStatus.IN_PROGRESS,
        priority=Priority.HIGH,
        assigned_to=["user1", "user2"],
        notes="开始执行任务",
    )
    print("任务状态更新结果:")
    print(json.dumps(result1, indent=2, ensure_ascii=False))

    # 测试数据分析
    result2 = analyze_data(
        data_source="sales_data_2025",
        filters={"region": "北京", "date_range": "2025-01-01:2025-06-18"},
        aggregations=["sum", "avg", "count"],
        output_format="json",
        include_metadata=True,
    )
    print("\n数据分析结果:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))


def validate_parameter_types():
    """验证参数类型推断的准确性"""
    print("\n=== 参数类型验证 ===")

    tools = get_global_tools()

    for tool_name, tool_info in tools.items():
        if tool_name.startswith("get_weather_smart"):
            print(f"\n工具: {tool_name}")
            params = tool_info.parameters["properties"]

            for param_name, param_info in params.items():
                print(f"  {param_name}:")
                print(f"    类型: {param_info.get('type', 'unknown')}")
                if "enum" in param_info:
                    print(f"    枚举值: {param_info['enum']}")
                if "description" in param_info:
                    print(f"    描述: {param_info['description']}")
                if "default" in param_info:
                    print(f"    默认值: {param_info['default']}")
                print()


def compare_manual_vs_auto_generation():
    """比较手动定义和自动生成的参数规范"""
    print("\n=== 手动 vs 自动生成对比 ===")

    # 手动定义的参数规范示例
    manual_schema = {
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

    print("手动定义的参数规范:")
    print(json.dumps(manual_schema, indent=2, ensure_ascii=False))

    # 自动生成的参数规范
    tools = get_global_tools()
    auto_schema = tools["get_weather_smart"].parameters

    print("\n自动生成的参数规范:")
    print(json.dumps(auto_schema, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 运行所有演示
    demonstrate_advanced_parsing()
    test_enum_parameter_execution()
    validate_parameter_types()
    compare_manual_vs_auto_generation()
