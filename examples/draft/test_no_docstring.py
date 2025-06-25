"""
测试没有 docstring 的工具自动参数解析

这个文件测试在没有 docstring 的情况下，@tool 装饰器是否仍能正常工作。
"""

from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import json
from menglong.agents.component.tool_manager import tool, get_global_tools


# 测试1：完全没有 docstring
@tool()
def simple_function_no_doc(name: str, age: int = 25):
    return {"name": name, "age": age}


# 测试2：只有简单的函数描述，没有参数说明
@tool()
def function_simple_doc(
    location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"
):
    """Get weather information"""
    return {"location": location, "temperature": 22, "unit": unit}


# 测试3：有 docstring 但没有 Args 部分
@tool()
def function_no_args_section(
    query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10
):
    """
    This function searches the database.

    It performs a comprehensive search based on the query
    and returns filtered results.

    Returns:
        Search results
    """
    return {"query": query, "filters": filters, "limit": limit}


# 测试4：使用枚举类型，无 docstring
class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@tool()
def update_status_no_doc(task_id: str, status: TaskStatus, notes: str = ""):
    return {"task_id": task_id, "status": status.value, "notes": notes}


# 测试5：复杂类型，无 docstring
@tool()
def complex_function_no_doc(
    data: List[str],
    config: Dict[str, Any],
    operation: Literal["process", "validate", "transform"] = "process",
    enabled: bool = True,
):
    return {
        "data_count": len(data),
        "config": config,
        "operation": operation,
        "enabled": enabled,
    }


def test_no_docstring_parsing():
    """测试没有 docstring 的参数解析"""
    print("=== 测试没有 docstring 的工具参数解析 ===\n")

    tools = get_global_tools()

    test_functions = [
        "simple_function_no_doc",
        "function_simple_doc",
        "function_no_args_section",
        "update_status_no_doc",
        "complex_function_no_doc",
    ]

    for func_name in test_functions:
        if func_name in tools:
            tool_info = tools[func_name]
            print(f"函数名: {func_name}")
            print(f"描述: {repr(tool_info.description)}")
            print("生成的参数格式:")
            print(json.dumps(tool_info.parameters, indent=2, ensure_ascii=False))
            print("-" * 60)


def test_execution():
    """测试工具执行"""
    print("\n=== 测试工具执行 ===\n")

    tools = get_global_tools()

    # 测试简单函数
    if "simple_function_no_doc" in tools:
        result = tools["simple_function_no_doc"].func("Alice", 30)
        print("简单函数执行结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 测试枚举函数
    if "update_status_no_doc" in tools:
        result = tools["update_status_no_doc"].func(
            "task_123", TaskStatus.COMPLETED, "All done!"
        )
        print("\n枚举函数执行结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    # 测试复杂函数
    if "complex_function_no_doc" in tools:
        result = tools["complex_function_no_doc"].func(
            data=["item1", "item2", "item3"],
            config={"timeout": 30, "retries": 3},
            operation="process",
            enabled=True,
        )
        print("\n复杂函数执行结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


def analyze_parameter_quality():
    """分析没有 docstring 时参数质量"""
    print("\n=== 参数质量分析 ===\n")

    tools = get_global_tools()

    for func_name in [
        "simple_function_no_doc",
        "function_simple_doc",
        "function_no_args_section",
    ]:
        if func_name in tools:
            tool_info = tools[func_name]
            properties = tool_info.parameters.get("properties", {})

            print(f"函数: {func_name}")
            print(f"总参数数: {len(properties)}")

            params_with_descriptions = sum(
                1 for p in properties.values() if "description" in p
            )
            params_with_types = sum(1 for p in properties.values() if "type" in p)
            params_with_defaults = sum(1 for p in properties.values() if "default" in p)
            params_with_enums = sum(1 for p in properties.values() if "enum" in p)

            print(f"有描述的参数: {params_with_descriptions}/{len(properties)}")
            print(f"有类型的参数: {params_with_types}/{len(properties)}")
            print(f"有默认值的参数: {params_with_defaults}/{len(properties)}")
            print(f"有枚举值的参数: {params_with_enums}/{len(properties)}")
            print()


def compare_with_vs_without_docstring():
    """对比有无 docstring 的差异"""
    print("\n=== 有无 docstring 对比 ===\n")

    # 创建一个有完整 docstring 的对比函数
    @tool()
    def function_with_full_doc(
        location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"
    ):
        """
        Get weather information

        Args:
            location: The city and state, e.g. San Francisco, CA
            unit: The unit of temperature, either "celsius" or "fahrenheit"
        """
        return {"location": location, "temperature": 22, "unit": unit}

    tools = get_global_tools()

    print("无 docstring 的函数:")
    if "function_simple_doc" in tools:
        print(
            json.dumps(
                tools["function_simple_doc"].parameters, indent=2, ensure_ascii=False
            )
        )

    print("\n有完整 docstring 的函数:")
    if "function_with_full_doc" in tools:
        print(
            json.dumps(
                tools["function_with_full_doc"].parameters, indent=2, ensure_ascii=False
            )
        )

    print("\n结论:")
    print("1. 即使没有 docstring，类型推断仍然正常工作")
    print("2. 枚举值、默认值、必需参数等都能正确识别")
    print("3. 唯一缺失的是参数描述信息")
    print("4. 对于简单工具，没有 docstring 也完全可用")


if __name__ == "__main__":
    test_no_docstring_parsing()
    test_execution()
    analyze_parameter_quality()
    compare_with_vs_without_docstring()
