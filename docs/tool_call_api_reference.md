# Tool Call Demo API 参考文档

## 概述

本文档提供了 `tool_call.py` 示例的详细API参考，包括所有函数、参数和使用方法的完整说明。

## 模块导入

```python
from menglong.ml_model import Model
from menglong.ml_model.schema.ml_request import (
    SystemMessage as system,
    ToolMessage as tool,
    AssistantMessage as assistant,
    UserMessage as user,
)
from menglong.utils.log.logging_tool import (
    print,
    print_rule,
    print_json,
    print_table,
    MessageType,
    configure_logger,
    get_logger,
)
```

## 工具函数定义

### get_weather()

获取指定地点的天气信息（模拟实现）。

**函数签名:**
```python
def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]
```

**参数:**
- `location` (str): 城市和地区，例如 "San Francisco, CA"
- `unit` (str, 可选): 温度单位，"celsius" 或 "fahrenheit"，默认 "celsius"

**返回值:**
```python
{
    "location": str,      # 查询的地点
    "temperature": int,   # 温度值
    "unit": str,         # 温度单位
    "forecast": List[str], # 天气预报
    "humidity": int      # 湿度百分比
}
```

**示例:**
```python
result = get_weather("Beijing", "celsius")
# 返回: {
#     "location": "Beijing",
#     "temperature": 22,
#     "unit": "celsius", 
#     "forecast": ["sunny", "windy"],
#     "humidity": 60
# }
```

## 工具定义格式

### OpenAI 格式工具定义

```python
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature to use. Infer this from the user's location.",
                },
            },
            "required": ["location"],
        },
    },
}
```

### Anthropic 格式工具定义

```python
weather_tool_an = {
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "input_schema": {
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
}
```

### AWS Bedrock 格式工具定义

```python
weather_tool_aws = {
    "toolSpec": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "inputSchema": {
            "json": {
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
        },
    }
}
```

## 演示函数

### openai_tool_call_demo()

演示使用 OpenAI 模型进行工具调用的完整流程。

**函数签名:**
```python
def openai_tool_call_demo() -> None
```

**功能:**
1. 初始化 GPT-4o 模型
2. 构建包含系统消息和用户查询的消息列表
3. 调用模型并处理工具调用响应
4. 执行工具函数并获取结果
5. 将工具结果反馈给模型获取最终回复

**流程详解:**
```python
# 1. 模型初始化
model = Model(model_id="gpt-4o")

# 2. 消息构建
messages = [
    system(content="You are a helpful assistant that can use tools to answer user questions."),
    user(content="What's the weather like in Beijing?"),
]

# 3. 模型调用
response = model.chat(
    messages=messages,
    model_id="gpt-4o",
    tools=[weather_tool],
    tool_choice="auto",
)

# 4. 工具调用处理
if response.message.tool_desc:
    for tool_call in response.message.tool_desc:
        if tool_call.name == "get_weather":
            args = json.loads(tool_call.arguments)
            weather_result = get_weather(**args)
            
            # 添加消息到历史
            messages.append(response.message)
            messages.append(tool(
                tool_id=tool_call.id,
                content=json.dumps(weather_result),
            ))

# 5. 获取最终回复
final_response = model.chat(messages=messages, model_id="gpt-4o")
```

### deepseek_tool_call_demo()

演示使用 DeepSeek 模型进行工具调用。

**函数签名:**
```python
def deepseek_tool_call_demo() -> None
```

**特点:**
- 使用 DeepSeek-Chat 模型
- 工具格式与 OpenAI 兼容
- 处理流程与 OpenAI 类似

**关键差异:**
```python
model = Model(model_id="deepseek-chat")
# DeepSeek 使用相同的工具格式和处理逻辑
```

### anthropic_tool_call_demo()

演示使用 Anthropic Claude 模型进行工具调用。

**函数签名:**
```python
def anthropic_tool_call_demo() -> None
```

**特点:**
- 使用 Claude-3.5-Sonnet 模型
- 专用的 AWS Bedrock 工具格式
- 特殊的工具选择配置

**关键配置:**
```python
model = Model(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")

response = model.chat(
    messages=messages,
    temperature=0.5,
    maxTokens=1000,
    tools=[weather_tool_aws],
    tool_choice={"type": "any"},  # 强制使用工具
)
```

## 工具调用响应处理

### 工具调用检测

```python
# 检查是否有工具调用
if hasattr(response.message, "tool_desc") and response.message.tool_desc:
    # 处理工具调用
    for tool_call in response.message.tool_desc:
        print(f"工具名称: {tool_call.name}")
        print(f"调用ID: {tool_call.id}")
        print(f"参数: {tool_call.arguments}")
```

### 参数解析

```python
# 解析工具调用参数
if tool_call.name == "get_weather":
    # 参数可能是字符串或字典格式
    if isinstance(tool_call.arguments, str):
        args = json.loads(tool_call.arguments)
    else:
        args = tool_call.arguments
    
    # 调用实际函数
    result = get_weather(**args)
```

### 结果反馈

```python
# 将工具结果添加到消息历史
messages.append(response.message)  # 添加包含工具调用的助手消息

# OpenAI/DeepSeek 格式
messages.append(tool(
    tool_id=tool_call.id,
    content=json.dumps(result)
))

# 或者使用 UserMessage（某些提供商要求）
messages.append(user(
    tool_id=tool_call.id,
    content=result
))
```

## 日志和输出

### 日志配置

```python
# 配置日志输出到文件
configure_logger(log_file="tool_call_demo.log")
logger = get_logger()

# 记录关键事件
logger.info("启动工具调用演示")
logger.error("工具调用失败", exc_info=True)
```

### 格式化输出

```python
# 使用富文本输出
print_rule("OpenAI Demo", style="green")
print("正在处理...", MessageType.INFO)
print("工具调用成功", MessageType.SUCCESS, title="成功")
print("警告信息", MessageType.WARNING)

# 输出JSON数据
print_json(response, title="模型响应")

# 输出表格
print_table(
    [["属性", "值"], ["模型", "gpt-4o"], ["Token", "150"]],
    ["字段", "内容"],
    title="调用统计"
)
```

### 消息类型

```python
class MessageType:
    INFO = "info"           # 信息提示（蓝色）
    SUCCESS = "success"     # 成功信息（绿色）
    WARNING = "warning"     # 警告信息（黄色）
    ERROR = "error"         # 错误信息（红色）
    AGENT = "agent"         # AI回复（青色）
```

## 错误处理

### 常见错误场景

```python
def robust_tool_call_demo():
    """健壮的工具调用演示"""
    try:
        model = Model(model_id="gpt-4o")
        
        # 1. 检查模型初始化
        if not model:
            raise ValueError("模型初始化失败")
        
        # 2. 构建消息
        messages = [
            system(content="You are a helpful assistant."),
            user(content="What's the weather like?"),
        ]
        
        # 3. 模型调用
        response = model.chat(
            messages=messages,
            tools=[weather_tool],
            tool_choice="auto",
            timeout=30  # 设置超时
        )
        
        # 4. 验证响应
        if not response or not response.message:
            raise ValueError("模型响应为空")
        
        # 5. 处理工具调用
        if response.message.tool_desc:
            for tool_call in response.message.tool_desc:
                try:
                    # 验证工具调用
                    if not tool_call.name or not tool_call.arguments:
                        print(f"无效的工具调用: {tool_call}", MessageType.WARNING)
                        continue
                    
                    # 安全执行工具
                    result = execute_tool_safely(tool_call)
                    if result is None:
                        print(f"工具执行失败: {tool_call.name}", MessageType.ERROR)
                        continue
                    
                    # 添加结果到消息
                    messages.append(response.message)
                    messages.append(tool(
                        tool_id=tool_call.id,
                        content=json.dumps(result)
                    ))
                    
                except Exception as e:
                    print(f"工具调用错误: {e}", MessageType.ERROR)
                    continue
        
        # 6. 获取最终回复
        if len(messages) > 2:  # 有工具调用发生
            final_response = model.chat(messages=messages)
            print(final_response.message.content.text, MessageType.AGENT)
        else:
            print(response.message.content.text, MessageType.AGENT)
            
    except Exception as e:
        print(f"演示执行失败: {e}", MessageType.ERROR)
        logger.error("工具调用演示失败", exc_info=True)


def execute_tool_safely(tool_call: ToolDesc) -> Optional[Dict]:
    """安全执行工具函数"""
    try:
        if tool_call.name == "get_weather":
            # 参数验证
            args = json.loads(tool_call.arguments) if isinstance(tool_call.arguments, str) else tool_call.arguments
            
            if "location" not in args:
                return {"error": "缺少必需参数: location"}
            
            # 执行工具
            return get_weather(**args)
        else:
            return {"error": f"未知工具: {tool_call.name}"}
            
    except json.JSONDecodeError:
        return {"error": "参数格式错误"}
    except Exception as e:
        return {"error": f"工具执行失败: {str(e)}"}
```

## 性能优化

### 批量工具调用

```python
def batch_tool_call_demo():
    """批量工具调用演示"""
    # 多个查询
    locations = ["Beijing", "Shanghai", "Guangzhou"]
    
    # 构建批量查询消息
    query = f"请告诉我这些城市的天气：{', '.join(locations)}"
    messages = [
        system(content="你可以使用工具获取多个城市的天气信息"),
        user(content=query)
    ]
    
    response = model.chat(
        messages=messages,
        tools=[weather_tool],
        tool_choice="auto"
    )
    
    # 处理多个工具调用
    if response.message.tool_desc:
        results = []
        for tool_call in response.message.tool_desc:
            if tool_call.name == "get_weather":
                args = json.loads(tool_call.arguments)
                result = get_weather(**args)
                results.append(result)
                
                # 添加每个工具结果
                messages.append(tool(
                    tool_id=tool_call.id,
                    content=json.dumps(result)
                ))
        
        # 汇总回复
        messages.insert(-len(results), response.message)
        final_response = model.chat(messages=messages)
        print(final_response.message.content.text)
```

### 缓存优化

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_get_weather(location: str, unit: str = "celsius") -> str:
    """带缓存的天气查询"""
    print(f"正在查询 {location} 的天气...", MessageType.INFO)
    time.sleep(0.1)  # 模拟API延迟
    
    result = get_weather(location, unit)
    return json.dumps(result)

# 使用缓存版本
def optimized_tool_call_demo():
    """优化的工具调用演示"""
    # 第一次调用
    result1 = cached_get_weather("Beijing")
    
    # 第二次调用相同参数（将使用缓存）
    result2 = cached_get_weather("Beijing")
    
    print(f"缓存命中: {result1 == result2}")
```

## 主函数

### main()

程序入口函数，依次执行所有演示。

**函数签名:**
```python
def main() -> None
```

**执行流程:**
1. 配置日志系统
2. 执行 OpenAI 工具调用演示
3. 执行 DeepSeek 工具调用演示  
4. 执行 Anthropic 工具调用演示
5. 记录完成状态

**完整实现:**
```python
def main():
    """主函数：执行所有工具调用演示"""
    # 配置日志
    configure_logger(log_file="tool_call_demo.log")
    logger = get_logger()

    logger.info("启动工具调用演示")
    print("Starting Tool Call Demo...", MessageType.INFO)

    try:
        # OpenAI 演示
        print_rule("OpenAI Demo", style="green")
        logger.info("开始 OpenAI 工具调用演示")
        openai_tool_call_demo()

        # DeepSeek 演示
        print_rule("DeepSeek Demo", style="blue")
        logger.info("开始 DeepSeek 工具调用演示")
        deepseek_tool_call_demo()

        # Anthropic 演示
        print_rule("Anthropic Demo", style="magenta")
        logger.info("开始 Anthropic 工具调用演示")
        anthropic_tool_call_demo()

        logger.info("工具调用演示完成")
        print("Tool Call Demo completed.", MessageType.SUCCESS, title="Completed")
        
    except Exception as e:
        logger.error(f"演示执行失败: {e}", exc_info=True)
        print(f"演示执行失败: {e}", MessageType.ERROR)


if __name__ == "__main__":
    main()
```

## 使用指南

### 环境准备

1. **安装依赖**
   ```bash
   pip install menglong
   ```

2. **配置API密钥**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export DEEPSEEK_API_KEY="your-deepseek-key"
   export AWS_ACCESS_KEY_ID="your-aws-key"
   export AWS_SECRET_ACCESS_KEY="your-aws-secret"
   ```

3. **运行演示**
   ```bash
   python tool_call.py
   ```

### 自定义工具

```python
# 定义新的工具函数
def calculate_math(expression: str) -> Dict[str, Any]:
    """计算数学表达式"""
    try:
        result = eval(expression)  # 注意：生产环境中应使用安全的计算方法
        return {
            "expression": expression,
            "result": result,
            "success": True
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "success": False
        }

# 定义工具schema
math_tool = {
    "type": "function",
    "function": {
        "name": "calculate_math",
        "description": "计算数学表达式",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "要计算的数学表达式，如 '2 + 3 * 4'"
                }
            },
            "required": ["expression"]
        }
    }
}

# 在演示中使用
def custom_tool_demo():
    """自定义工具演示"""
    model = Model(model_id="gpt-4o")
    
    messages = [
        system(content="你是一个数学助手，可以使用工具进行计算"),
        user(content="请计算 (10 + 5) * 3 - 8 的结果")
    ]
    
    response = model.chat(
        messages=messages,
        tools=[math_tool],
        tool_choice="auto"
    )
    
    # 处理工具调用...
```

## 总结

这个工具调用演示提供了完整的AI工具调用实现，涵盖了：

1. **多厂商支持**: OpenAI、DeepSeek、Anthropic等
2. **标准化接口**: 统一的调用方式和错误处理
3. **丰富的输出**: 格式化日志和用户友好的显示
4. **错误处理**: 健壮的异常处理和恢复机制
5. **可扩展性**: 易于添加新工具和新厂商支持

通过学习这个演示，开发者可以快速掌握如何在自己的应用中集成AI工具调用功能。
