"""
演示 @tool 和 @tool() 的区别

这个文件展示了我们的装饰器现在同时支持两种使用方式：
1. @tool (不带括号)
2. @tool() (带括号)
"""

from typing import Literal
import json
from menglong.agents.component.tool_manager import tool, get_global_tools


# ========== 方式1：@tool (不带括号) ==========


@tool  # 不带括号，直接装饰
def simple_weather(location: str, unit: Literal["celsius", "fahrenheit"] = "celsius"):
    """
    简单天气查询

    Args:
        location: 城市名称
        unit: 温度单位
    """
    return {"location": location, "temperature": 22, "unit": unit}


@tool  # 不带括号，没有docstring
def calculator(
    a: int, b: int, operation: Literal["add", "subtract", "multiply"] = "add"
):
    return (
        a + b if operation == "add" else (a - b if operation == "subtract" else a * b)
    )


# ========== 方式2：@tool() (带括号) ==========


@tool()  # 带括号，但不传参数
def database_search(query: str, limit: int = 10, include_metadata: bool = False):
    """
    数据库搜索

    Args:
        query: 搜索关键词
        limit: 结果数量限制
        include_metadata: 是否包含元数据
    """
    return {"query": query, "results": f"找到 {limit} 条结果"}


@tool(description="发送邮件工具")  # 带括号，指定描述
def send_email(to: str, subject: str, body: str):
    """发送邮件到指定地址"""
    return {"status": "sent", "to": to, "subject": subject}


@tool("custom_name", description="自定义名称的工具")  # 带括号，指定名称和描述
def some_function(text: str, count: int = 1):
    """重复文本的函数"""
    return text * count


def demonstrate_decorator_differences():
    """演示两种装饰器形式的区别"""
    print("@tool 装饰器形式对比演示")
    print("=" * 60)

    tools = get_global_tools()

    test_tools = [
        ("@tool (不带括号)", "simple_weather"),
        ("@tool (不带括号，无docstring)", "calculator"),
        ("@tool() (带括号，无参数)", "database_search"),
        ("@tool(description=...) (带描述)", "send_email"),
        ("@tool(name, description) (自定义名称)", "custom_name"),
    ]

    for title, tool_name in test_tools:
        if tool_name in tools:
            tool_info = tools[tool_name]
            print(f"\n{title}:")
            print(f"工具名称: {tool_info.name}")
            print(f"原函数名: {tool_info.func.__name__}")
            print(f"描述: {tool_info.description}")
            print("参数规范:")
            print(json.dumps(tool_info.parameters, indent=2, ensure_ascii=False))
            print("-" * 40)


def test_decorator_execution():
    """测试不同装饰器形式的执行"""
    print("\n装饰器执行测试")
    print("=" * 60)

    # 测试 @tool 形式
    result1 = simple_weather("北京", "celsius")
    print(f"@tool 形式执行结果: {result1}")

    # 测试 @tool() 形式
    result2 = database_search("Python教程", limit=5, include_metadata=True)
    print(f"@tool() 形式执行结果: {result2}")

    # 测试无docstring的工具
    result3 = calculator(10, 5, "multiply")
    print(f"无docstring工具执行结果: {result3}")


def explain_differences():
    """解释两种形式的技术差异"""
    print("\n技术原理解释")
    print("=" * 60)

    print(
        """
1. @tool (不带括号):
   - 这是直接装饰器形式
   - Python 直接将函数传递给 tool() 函数
   - 相当于: tool(my_function)
   
2. @tool() (带括号):
   - 这是装饰器工厂形式  
   - Python 先调用 tool()，返回一个装饰器
   - 然后这个装饰器再装饰函数
   - 相当于: decorator = tool(); decorator(my_function)
   
3. 我们的实现同时支持两种形式:
   - 通过检查第一个参数是否为callable来区分
   - 如果是函数对象，直接装饰
   - 如果不是，返回装饰器函数
   
4. 使用建议:
   - 简单情况用 @tool (更简洁)
   - 需要自定义参数时用 @tool(...)
   - 两种形式功能完全相同
    """
    )


def show_parameter_differences():
    """展示参数生成的差异"""
    print("\n参数生成差异对比")
    print("=" * 60)

    tools = get_global_tools()

    # 有docstring vs 无docstring
    with_doc = tools.get("simple_weather")
    without_doc = tools.get("calculator")

    if with_doc and without_doc:
        print("有docstring的工具参数:")
        props1 = with_doc.parameters["properties"]
        for name, info in props1.items():
            desc = info.get("description", "无描述")
            print(f"  {name}: {desc}")

        print("\n无docstring的工具参数:")
        props2 = without_doc.parameters["properties"]
        for name, info in props2.items():
            desc = info.get("description", "无描述")
            print(f"  {name}: {desc}")

        print("\n结论:")
        print("- 有docstring时：参数有详细描述")
        print("- 无docstring时：参数无描述，但类型推断正常工作")
        print("- 两种情况都能正确生成JSON Schema格式")


if __name__ == "__main__":
    # 运行演示
    demonstrate_decorator_differences()
    test_decorator_execution()
    explain_differences()
    show_parameter_differences()
