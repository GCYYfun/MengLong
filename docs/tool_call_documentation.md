# Tool Call Documentation

## 概述

这份文档详细说明了 MengLong 框架中工具调用（Tool Call）功能的实现，包括不同AI模型提供商的工具格式差异、模式规范以及使用示例。

## 目录

1. [工具调用基础概念](#工具调用基础概念)
2. [不同厂商工具格式对比](#不同厂商工具格式对比)
3. [Schema 规范文档](#schema-规范文档)
4. [使用示例](#使用示例)
5. [最佳实践](#最佳实践)

## 工具调用基础概念

工具调用（Tool Call）是现代AI模型的一项重要功能，它允许模型在对话过程中调用外部函数或API来获取实时信息、执行计算或与外部系统交互。

### 工具调用流程

1. **定义工具**: 开发者定义可用的工具函数和其参数schema
2. **模型推理**: AI模型根据用户输入决定是否需要使用工具
3. **工具调用**: 模型生成工具调用请求，包含函数名和参数
4. **执行工具**: 系统执行相应的工具函数
5. **返回结果**: 将工具执行结果返回给模型
6. **生成回复**: 模型基于工具结果生成最终回复

## 不同厂商工具格式对比

### 1. OpenAI 格式

OpenAI 使用标准的 JSON Schema 格式定义工具，这也是目前最广泛采用的格式。

```python
openai_tool = {
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
                    "description": "The unit of temperature to use."
                }
            },
            "required": ["location"]
        }
    }
}
```

**特点:**
- 使用 `type: "function"` 声明工具类型
- 参数定义使用标准 JSON Schema
- 支持复杂的参数验证（enum、required等）
- 广泛兼容性

### 2. AWS Bedrock 格式

AWS Bedrock 使用 `toolSpec` 结构，参数定义放在 `inputSchema.json` 中。

```python
aws_tool = {
    "toolSpec": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The unit of temperature"
                    }
                },
                "required": ["location"]
            }
        }
    }
}
```

**特点:**
- 使用 `toolSpec` 作为顶层结构
- 参数定义嵌套在 `inputSchema.json` 中
- 支持多种输入格式（json、text等）
- 适配 AWS 生态系统

### 3. Anthropic 格式

Anthropic Claude 使用简化的工具定义格式，直接使用 `input_schema`。

```python
anthropic_tool = {
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The unit of temperature"
            }
        },
        "required": ["location"]
    }
}
```

**特点:**
- 扁平化的结构，没有嵌套的 `function` 对象
- 直接使用 `input_schema` 定义参数
- 简洁明了的格式
- 与 Claude 模型紧密集成

### 4. DeepSeek 格式

DeepSeek 兼容 OpenAI 格式，使用相同的工具定义结构。

```python
deepseek_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature"
                }
            },
            "required": ["location"]
        }
    }
}
```

**特点:**
- 完全兼容 OpenAI 格式
- 支持相同的 JSON Schema 规范
- 便于从 OpenAI 迁移

### 格式对比总结

| 厂商 | 顶层结构 | 参数位置 | 特点 |
|------|----------|----------|------|
| OpenAI | `type: "function"` + `function` | `function.parameters` | 标准格式，广泛兼容 |
| AWS Bedrock | `toolSpec` | `toolSpec.inputSchema.json` | AWS 生态集成 |
| Anthropic | 扁平结构 | `input_schema` | 简洁直观 |
| DeepSeek | 兼容 OpenAI | `function.parameters` | OpenAI 兼容 |

## Schema 规范文档

### 消息模式 (Message Schema)

#### SystemMessage
系统消息用于设置AI助手的行为和上下文。

```python
class SystemMessage(BaseModel):
    """系统消息模型"""
    content: str = Field(description="系统提示内容")
    role: Optional[str] = Field(default="system", description="消息角色")
```

**字段说明:**
- `content`: 系统提示文本，定义AI的角色和行为
- `role`: 固定为 "system"

**使用示例:**
```python
system_msg = SystemMessage(
    content="You are a helpful assistant that can use tools to answer questions."
)
```

#### UserMessage
用户消息表示来自用户的输入或工具执行结果。

```python
class UserMessage(BaseModel):
    """用户消息模型"""
    content: Union[str, List, Dict] = Field(description="消息内容")
    role: Optional[str] = Field(default="user", description="消息角色")
    tool_id: Optional[str] = Field(default=None, description="工具调用ID")
```

**字段说明:**
- `content`: 用户输入内容，支持字符串、列表或字典格式
- `role`: 固定为 "user"
- `tool_id`: 当消息是工具执行结果时，标识对应的工具调用ID

**使用示例:**
```python
# 普通用户消息
user_msg = UserMessage(content="What's the weather like in Beijing?")

# 工具结果消息
tool_result = UserMessage(
    content='{"temperature": 22, "weather": "sunny"}',
    tool_id="call_123"
)
```

#### AssistantMessage
助手消息表示AI模型的回复。

```python
class AssistantMessage(BaseModel):
    """助手消息模型"""
    content: Union[str, List] = Field(description="回复内容")
    role: Optional[str] = Field(default="assistant", description="消息角色")
```

**字段说明:**
- `content`: AI的回复内容
- `role`: 固定为 "assistant"

#### ToolMessage
专门用于工具调用结果的消息类型。

```python
class ToolMessage(BaseModel):
    """工具消息模型"""
    content: Union[str, List] = Field(description="工具执行结果")
    role: Optional[str] = Field(default="tool", description="消息角色")
    tool_id: Optional[str] = Field(default=None, description="工具调用ID")
```

**字段说明:**
- `content`: 工具执行的结果数据
- `role`: 固定为 "tool"
- `tool_id`: 对应的工具调用ID

### 响应模式 (Response Schema)

#### Content
消息内容模型，包含文本和推理过程。

```python
class Content(BaseModel):
    """消息内容模型"""
    text: Optional[str] = Field(default=None, description="生成的文本内容")
    reasoning: Optional[str] = Field(default=None, description="思考过程内容")
```

**字段说明:**
- `text`: 主要的回复文本内容
- `reasoning`: 模型的推理过程（如果模型支持）

#### ToolDesc
工具调用描述模型。

```python
class ToolDesc(BaseModel):
    """工具调用模型"""
    id: str = Field(description="工具调用ID")
    type: str = Field(description="工具调用类型")
    name: str = Field(description="函数名称")
    arguments: Union[str, dict] = Field(description="函数参数")
```

**字段说明:**
- `id`: 唯一的工具调用标识符
- `type`: 工具类型，通常为 "function"
- `name`: 要调用的函数名称
- `arguments`: 函数参数，可以是JSON字符串或字典

#### Message
完整的消息模型，包含内容和工具调用信息。

```python
class Message(BaseModel):
    """消息模型"""
    content: Content = Field(description="消息内容")
    tool_desc: Optional[List[ToolDesc]] = Field(default=None, description="工具调用列表")
    finish_reason: Optional[str] = Field(default=None, description="结束原因")
```

**字段说明:**
- `content`: 消息的文本内容
- `tool_desc`: 工具调用列表（如果有）
- `finish_reason`: 响应结束的原因

#### Usage
Token使用统计模型。

```python
class Usage(BaseModel):
    """token使用统计模型"""
    input_tokens: int = Field(description="输入token数量")
    output_tokens: int = Field(description="输出token数量")
    total_tokens: int = Field(description="总token数量")
```

#### ChatResponse
聊天API的完整响应模型。

```python
class ChatResponse(BaseModel):
    """聊天响应模型"""
    message: Message = Field(description="响应消息")
    model: Optional[str] = Field(default=None, description="使用的模型标识符")
    usage: Optional[Usage] = Field(default=None, description="token使用统计")
```

### 工具定义规范

#### 标准工具定义结构

```python
tool_definition = {
    "type": "function",
    "function": {
        "name": "function_name",
        "description": "功能描述",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "参数描述",
                    "enum": ["value1", "value2"]  # 可选
                },
                "param2": {
                    "type": "number",
                    "description": "数值参数",
                    "minimum": 0,  # 可选
                    "maximum": 100  # 可选
                }
            },
            "required": ["param1"]
        }
    }
}
```

#### 参数类型支持

| JSON类型 | 描述 | 验证属性 |
|----------|------|----------|
| `string` | 字符串类型 | `enum`, `pattern`, `minLength`, `maxLength` |
| `number` | 数值类型 | `minimum`, `maximum`, `multipleOf` |
| `integer` | 整数类型 | `minimum`, `maximum`, `multipleOf` |
| `boolean` | 布尔类型 | 无 |
| `array` | 数组类型 | `items`, `minItems`, `maxItems` |
| `object` | 对象类型 | `properties`, `required`, `additionalProperties` |

## 使用示例

### 基础工具调用示例

```python
from menglong.ml_model import Model
from menglong.ml_model.schema.ml_request import SystemMessage, UserMessage, ToolMessage

# 定义工具
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定地点的天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，如：北京、上海"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["location"]
        }
    }
}

# 初始化模型
model = Model(model_id="gpt-4o")

# 构建消息
messages = [
    SystemMessage(content="你是一个可以使用工具的智能助手"),
    UserMessage(content="北京今天天气怎么样？")
]

# 调用模型
response = model.chat(
    messages=messages,
    tools=[weather_tool],
    tool_choice="auto"
)

# 处理工具调用
if response.message.tool_desc:
    for tool_call in response.message.tool_desc:
        if tool_call.name == "get_weather":
            # 执行工具函数
            result = get_weather(**json.loads(tool_call.arguments))
            
            # 添加工具结果到消息历史
            messages.append(response.message)
            messages.append(ToolMessage(
                tool_id=tool_call.id,
                content=json.dumps(result)
            ))
    
    # 获取最终回复
    final_response = model.chat(messages=messages)
    print(final_response.message.content.text)
```

### 多工具协作示例

```python
# 定义多个工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "地点"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "search_flights",
            "description": "搜索航班信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "出发地"},
                    "destination": {"type": "string", "description": "目的地"},
                    "date": {"type": "string", "description": "出发日期"}
                },
                "required": ["origin", "destination", "date"]
            }
        }
    }
]

# 复杂查询
messages = [
    SystemMessage(content="你是一个旅行助手，可以查询天气和航班信息"),
    UserMessage(content="我想从北京飞往上海，明天出发，帮我查一下明天上海的天气和可用的航班")
]

response = model.chat(messages=messages, tools=tools, tool_choice="auto")
```

## 最佳实践

### 1. 工具设计原则

- **单一职责**: 每个工具应该只完成一个特定的任务
- **清晰描述**: 提供详细的功能描述和参数说明
- **参数验证**: 使用JSON Schema的验证功能确保参数正确性
- **错误处理**: 工具函数应该优雅地处理错误情况

### 2. 参数设计建议

- **必需参数**: 只将真正必需的参数标记为required
- **默认值**: 为可选参数提供合理的默认值
- **枚举限制**: 对于有限选项的参数使用enum限制
- **数值范围**: 为数值参数设置合理的最小值和最大值

### 3. 错误处理

```python
def robust_tool_function(param1: str, param2: int = 10) -> dict:
    """
    健壮的工具函数示例
    """
    try:
        # 参数验证
        if not param1:
            raise ValueError("param1 cannot be empty")
        
        if param2 < 0:
            raise ValueError("param2 must be non-negative")
        
        # 执行实际功能
        result = perform_operation(param1, param2)
        
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### 4. 性能优化

- **缓存结果**: 对于重复调用的工具，实现结果缓存
- **异步执行**: 对于耗时操作，考虑使用异步执行
- **超时控制**: 为工具调用设置合理的超时时间
- **批量处理**: 支持批量参数处理以减少调用次数

### 5. 安全考虑

- **输入验证**: 严格验证所有输入参数
- **权限控制**: 实现适当的权限检查机制
- **敏感信息**: 避免在工具定义中暴露敏感信息
- **日志记录**: 记录工具调用的关键信息用于审计

## 故障排除

### 常见问题

1. **工具未被调用**
   - 检查工具描述是否清晰
   - 确认参数定义是否正确
   - 验证tool_choice设置

2. **参数解析错误**
   - 检查JSON Schema定义
   - 确认参数类型匹配
   - 验证required字段设置

3. **工具执行失败**
   - 添加错误处理逻辑
   - 检查函数实现
   - 验证返回值格式

### 调试技巧

```python
# 启用详细日志记录
import logging
logging.basicConfig(level=logging.DEBUG)

# 打印工具调用信息
def debug_tool_call(tool_call):
    print(f"Tool: {tool_call.name}")
    print(f"Arguments: {tool_call.arguments}")
    print(f"ID: {tool_call.id}")
```

## 总结

MengLong 框架提供了统一的工具调用接口，支持多种AI模型提供商的不同格式。通过标准化的Schema定义和转换器机制，开发者可以轻松地在不同模型之间切换，同时保持代码的一致性和可维护性。

正确理解和使用工具调用功能，能够极大地扩展AI应用的能力边界，实现更加智能和实用的AI助手系统。
