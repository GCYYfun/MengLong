"""
工具参数解析演示

这个文件演示了如何使用 @tool 装饰器创建具有复杂参数规范的工具，
包括枚举值、描述信息、必需参数等高级特性。
"""

from typing import List, Dict, Any, Union, Literal
from enum import Enum
import json
from menglong.agents.component.tool_manager import tool, ToolInfo, get_global_tools


# 方式1：使用手动定义的参数规范
@tool(
    name="get_weather_advanced",
    description="获取指定位置的详细天气信息",
    parameters={
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "城市和州，例如 San Francisco, CA 或 北京, 中国",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "温度单位，摄氏度或华氏度",
                "default": "celsius",
            },
            "include_forecast": {
                "type": "boolean",
                "description": "是否包含未来几天的天气预报",
                "default": False,
            },
            "forecast_days": {
                "type": "integer",
                "description": "预报天数，范围 1-7",
                "minimum": 1,
                "maximum": 7,
                "default": 3,
            },
        },
        "required": ["location"],
    },
)
def get_weather_advanced(
    location: str,
    unit: str = "celsius",
    include_forecast: bool = False,
    forecast_days: int = 3,
):
    """获取指定位置的详细天气信息

    Args:
        location: 城市位置
        unit: 温度单位 (celsius/fahrenheit)
        include_forecast: 是否包含预报
        forecast_days: 预报天数
    """
    result = {
        "location": location,
        "current": {
            "temperature": 22 if unit == "celsius" else 72,
            "unit": unit,
            "description": "晴朗",
            "humidity": 65,
            "wind_speed": 10,
        },
    }

    if include_forecast:
        result["forecast"] = [
            {
                "day": f"Day {i+1}",
                "high": 25 + i if unit == "celsius" else 77 + i * 2,
                "low": 18 + i if unit == "celsius" else 64 + i * 2,
                "description": ["晴", "多云", "小雨"][i % 3],
            }
            for i in range(forecast_days)
        ]

    return result


# 方式2：使用类型注解和枚举
class TemperatureUnit(Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@tool(
    name="create_task",
    description="创建一个新的任务",
    parameters={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "任务标题",
                "minLength": 1,
                "maxLength": 100,
            },
            "description": {"type": "string", "description": "任务详细描述"},
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
                "description": "任务优先级",
                "default": "medium",
            },
            "due_date": {
                "type": "string",
                "format": "date",
                "description": "截止日期，格式: YYYY-MM-DD",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "任务标签列表",
                "default": [],
            },
            "assignees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["name", "email"],
                },
                "description": "任务分配人员列表",
            },
        },
        "required": ["title"],
    },
)
def create_task(
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str = None,
    tags: List[str] = None,
    assignees: List[Dict[str, str]] = None,
):
    """创建一个新的任务"""
    if tags is None:
        tags = []
    if assignees is None:
        assignees = []

    return {
        "task_id": "task_123",
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "tags": tags,
        "assignees": assignees,
        "created_at": "2025-06-18T10:00:00Z",
        "status": "pending",
    }


# 方式3：复杂嵌套对象
@tool(
    name="search_products",
    description="搜索商品信息",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词", "minLength": 1},
            "filters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["electronics", "clothing", "books", "home", "sports"],
                        "description": "商品分类",
                    },
                    "price_range": {
                        "type": "object",
                        "properties": {
                            "min": {
                                "type": "number",
                                "minimum": 0,
                                "description": "最低价格",
                            },
                            "max": {
                                "type": "number",
                                "minimum": 0,
                                "description": "最高价格",
                            },
                        },
                        "description": "价格范围过滤",
                    },
                    "brand": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "品牌过滤列表",
                    },
                    "in_stock": {
                        "type": "boolean",
                        "description": "是否只显示有库存商品",
                        "default": True,
                    },
                },
                "description": "搜索过滤条件",
            },
            "sort": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "enum": ["price", "rating", "popularity", "newest"],
                        "description": "排序字段",
                        "default": "popularity",
                    },
                    "order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "排序顺序",
                        "default": "desc",
                    },
                },
                "description": "排序选项",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "返回结果数量限制",
                "default": 20,
            },
        },
        "required": ["query"],
    },
)
def search_products(
    query: str, filters: Dict = None, sort: Dict = None, limit: int = 20
):
    """搜索商品信息"""
    if filters is None:
        filters = {}
    if sort is None:
        sort = {"field": "popularity", "order": "desc"}

    return {
        "query": query,
        "filters_applied": filters,
        "sort_applied": sort,
        "total_results": 156,
        "returned_count": min(limit, 156),
        "results": [
            {
                "id": f"prod_{i}",
                "name": f"商品 {i}",
                "price": 99.99 + i * 10,
                "rating": 4.5,
                "in_stock": True,
            }
            for i in range(min(limit, 5))  # 示例只返回5个
        ],
    }


def demonstrate_tool_parameters():
    """演示工具参数解析功能"""
    print("=== 工具参数解析演示 ===\n")

    # 获取所有注册的工具
    tools = get_global_tools()

    for tool_name, tool_info in tools.items():
        if tool_name in ["get_weather_advanced", "create_task", "search_products"]:
            print(f"工具名称: {tool_name}")
            print(f"描述: {tool_info.description}")
            print("参数规范:")
            print(json.dumps(tool_info.parameters, indent=2, ensure_ascii=False))
            print("-" * 60)


def test_tool_execution():
    """测试工具执行"""
    print("\n=== 工具执行测试 ===\n")

    # 测试天气工具
    print("1. 测试天气工具:")
    result1 = get_weather_advanced("北京, 中国", "celsius", True, 5)
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    print()

    # 测试任务创建工具
    print("2. 测试任务创建工具:")
    result2 = create_task(
        title="完成项目报告",
        description="准备季度项目总结报告",
        priority="high",
        due_date="2025-06-25",
        tags=["项目", "报告", "季度"],
        assignees=[
            {"name": "张三", "email": "zhangsan@example.com"},
            {"name": "李四", "email": "lisi@example.com"},
        ],
    )
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    print()

    # 测试商品搜索工具
    print("3. 测试商品搜索工具:")
    result3 = search_products(
        query="笔记本电脑",
        filters={
            "category": "electronics",
            "price_range": {"min": 3000, "max": 8000},
            "brand": ["Apple", "Dell", "Lenovo"],
            "in_stock": True,
        },
        sort={"field": "price", "order": "asc"},
        limit=3,
    )
    print(json.dumps(result3, indent=2, ensure_ascii=False))


def demonstrate_parameter_validation():
    """演示参数验证功能"""
    print("\n=== 参数验证演示 ===\n")

    # 获取工具信息
    tools = get_global_tools()
    weather_tool = tools.get("get_weather_advanced")

    if weather_tool:
        print("天气工具参数规范:")
        params = weather_tool.parameters

        # 显示参数详情
        for prop_name, prop_info in params["properties"].items():
            required = prop_name in params.get("required", [])
            print(f"- {prop_name}: {prop_info.get('description', '无描述')}")
            print(f"  类型: {prop_info['type']}")
            if "enum" in prop_info:
                print(f"  可选值: {prop_info['enum']}")
            if "default" in prop_info:
                print(f"  默认值: {prop_info['default']}")
            print(f"  必需: {'是' if required else '否'}")
            print()


if __name__ == "__main__":
    # 运行演示
    demonstrate_tool_parameters()
    test_tool_execution()
    demonstrate_parameter_validation()
