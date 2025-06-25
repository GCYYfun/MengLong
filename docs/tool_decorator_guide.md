# @tool 装饰器使用指南

## 概述

`@tool` 装饰器为 ChatAgent 提供了一种更简洁、更优雅的工具注册方式。相比传统的手动注册方法，装饰器方式可以自动推断参数类型、自动生成工具描述，让工具注册变得更加简单。

## 基本用法

### 1. 使用 @tool 装饰器定义工具

```python
from menglong.agents.chat.chat_agent import tool, ChatAgent, ChatMode

@tool(name="weather", description="获取指定位置的天气信息")
def get_weather(location: str, unit: str = "celsius"):
    """获取天气信息"""
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "condition": "sunny"
    }

@tool()  # 使用默认名称和描述
def calculate(expression: str):
    """进行数学计算"""
    try:
        return {"result": eval(expression)}
    except Exception as e:
        return {"error": str(e)}
```

### 2. 自动参数推断

装饰器会根据函数签名自动生成参数规范：

- **类型推断**: 从类型注解推断参数类型（str → string, int → integer, float → number, bool → boolean）
- **必需参数**: 没有默认值的参数自动标记为必需
- **可选参数**: 有默认值的参数自动标记为可选，并包含默认值

```python
@tool()
def search_web(query: str, max_results: int = 3, include_images: bool = False):
    """搜索网络信息"""
    # 自动生成的参数规范：
    # {
    #   "type": "object",
    #   "properties": {
    #     "query": {"type": "string"},
    #     "max_results": {"type": "integer", "default": 3},
    #     "include_images": {"type": "boolean", "default": false}
    #   },
    #   "required": ["query"]
    # }
    pass
```

## 工具注册方式

### 方式1: 初始化时自动注册

```python
# 注册所有全局工具（用 @tool 装饰的函数）
agent = ChatAgent(mode=ChatMode.AUTO, tools=None)

# 按名称注册特定工具
agent = ChatAgent(mode=ChatMode.AUTO, tools=["weather", "calculate"])

# 从函数列表注册
agent = ChatAgent(mode=ChatMode.AUTO, tools=[get_weather, calculate])
```

### 方式2: 后续动态注册

```python
agent = ChatAgent(mode=ChatMode.AUTO)

# 注册全局工具
agent.auto_register_tools()

# 注册特定工具
agent.auto_register_tools(["weather", "calculate"])

# 从函数注册
agent.register_tools_from_functions(get_weather, calculate)

# 从模块注册
import my_tools_module
agent.register_tools_from_module(my_tools_module)
```

### 方式3: 混合使用

```python
agent = ChatAgent(mode=ChatMode.AUTO)

# 1. 注册装饰器工具
agent.auto_register_tools(["weather", "calculate"])

# 2. 传统方式注册工具
agent.register_tool(
    name="send_email",
    func=send_email_func,
    description="发送邮件",
    parameters={...}  # 手动定义参数规范
)
```

## 装饰器参数

### @tool() 参数说明

```python
@tool(
    name="custom_name",           # 可选：工具名称，默认使用函数名
    description="工具描述",        # 可选：工具描述，默认使用文档字符串
    parameters={...}              # 可选：手动指定参数规范，默认自动推断
)
def my_tool():
    pass
```

### 示例

```python
# 最简单的用法
@tool()
def simple_tool(param: str):
    """这是工具描述"""
    pass

# 自定义名称和描述
@tool(name="weather_api", description="获取实时天气数据")
def get_weather_info(city: str):
    pass

# 手动指定参数（高级用法）
@tool(parameters={
    "type": "object",
    "properties": {
        "data": {"type": "string", "description": "要处理的数据"},
        "format": {"type": "string", "enum": ["json", "xml", "csv"]}
    },
    "required": ["data"]
})
def process_data(data: str, format: str = "json"):
    pass
```

## 实际使用示例

```python
# 定义工具
@tool(name="weather", description="获取天气信息")
def get_weather(location: str, unit: str = "celsius"):
    return {"location": location, "temperature": 22}

@tool()
def calculate(expression: str):
    """计算数学表达式"""
    return {"result": eval(expression)}

# 创建 Agent 并使用工具
agent = ChatAgent(
    mode=ChatMode.AUTO,
    system="你是一个智能助手，可以使用工具帮助用户。",
    tools=["weather", "calculate"]  # 按名称注册
)

# 聊天测试
response1 = agent.chat("北京今天天气怎么样？")
response2 = agent.chat("计算 15 * 23 + 47")
```

## 对比：传统方式 vs 装饰器方式

### 传统方式
```python
# 需要手动定义每个工具和参数规范
agent = ChatAgent(mode=ChatMode.AUTO)
agent.register_tool(
    name="weather",
    func=get_weather,
    description="获取天气信息",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "城市名称"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location"]
    }
)
```

### 装饰器方式
```python
# 简洁明了，自动推断参数
@tool(name="weather", description="获取天气信息")
def get_weather(location: str, unit: str = "celsius"):
    pass

agent = ChatAgent(mode=ChatMode.AUTO, tools=["weather"])
```

## 高级特性

### 1. 全局工具管理
所有用 `@tool` 装饰的函数都会自动注册到全局工具表中，可以在不同的 Agent 实例间共享。

### 2. 模块化工具组织
可以将工具分组到不同的模块中，然后按模块注册：

```python
# tools/weather_tools.py
@tool()
def get_weather(location: str):
    pass

@tool() 
def get_forecast(location: str, days: int = 7):
    pass

# main.py
import tools.weather_tools
agent.register_tools_from_module(tools.weather_tools)
```

### 3. 动态工具加载
可以根据需要动态加载和注册工具：

```python
# 根据用户权限注册不同的工具
if user.is_admin:
    agent.auto_register_tools(["admin_tool1", "admin_tool2"])
else:
    agent.auto_register_tools(["basic_tool1", "basic_tool2"])
```

## 注意事项

1. **类型注解**: 建议为函数参数添加类型注解，以便自动推断正确的参数类型
2. **文档字符串**: 如果不指定 description，会使用函数的文档字符串作为工具描述
3. **参数验证**: 装饰器会根据函数签名生成基本的参数规范，但复杂的验证逻辑仍需手动指定
4. **兼容性**: 装饰器方式与传统注册方式完全兼容，可以混合使用

## 总结

`@tool` 装饰器大大简化了工具的定义和注册过程：

- ✅ **简洁**: 一行装饰器替代多行注册代码
- ✅ **智能**: 自动推断参数类型和必需性
- ✅ **灵活**: 支持多种注册方式
- ✅ **兼容**: 与传统方式完全兼容
- ✅ **可维护**: 工具定义与使用位置更近，便于维护

这使得开发者可以更专注于工具的核心逻辑，而不需要花费时间在繁琐的注册配置上。
