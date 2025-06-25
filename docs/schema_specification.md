# MengLong Schema 规范文档

## 概述

本文档详细描述了 MengLong 框架中所有数据模型的Schema规范，包括请求模型、响应模型、消息格式以及工具调用相关的数据结构。这些Schema基于Pydantic库实现，提供了类型安全和数据验证功能。

## 目录

1. [Schema 设计原则](#schema-设计原则)
2. [请求模型 (Request Schema)](#请求模型-request-schema)
3. [响应模型 (Response Schema)](#响应模型-response-schema)
4. [工具调用模型](#工具调用模型)
5. [流式响应模型](#流式响应模型)
6. [嵌入模型](#嵌入模型)
7. [转换器规范](#转换器规范)
8. [验证和错误处理](#验证和错误处理)
9. [使用示例](#使用示例)

## Schema 设计原则

### 1. 类型安全
所有Schema都使用Python类型注解和Pydantic字段验证，确保数据类型的正确性。

### 2. 可扩展性
Schema设计支持向后兼容的扩展，新增字段使用可选类型。

### 3. 文档化
每个字段都包含详细的描述信息，便于理解和使用。

### 4. 标准化
统一的命名规范和数据结构，确保不同组件之间的一致性。

## 请求模型 (Request Schema)

位置: `src/menglong/ml_model/schema/ml_request.py`

### SystemMessage

系统消息用于定义AI助手的角色、行为和上下文设置。

```python
class SystemMessage(BaseModel):
    """系统消息模型
    
    用于设置AI助手的行为模式、角色定义和上下文规则。
    系统消息通常放在对话的开始，影响整个对话的风格和行为。
    """
    
    content: str = Field(
        description="系统提示内容，定义AI助手的角色和行为规则"
    )
    role: Optional[str] = Field(
        default="system", 
        description="消息角色标识，固定为'system'"
    )
```

**字段详细说明:**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `content` | `str` | ✓ | - | 系统提示文本，定义AI的行为和能力 |
| `role` | `Optional[str]` | ✗ | "system" | 消息角色，标识这是系统消息 |

**使用场景:**
- 设置AI助手的专业领域（如医生、律师、程序员）
- 定义回答风格（正式、友好、简洁）
- 设置行为约束和安全规则
- 提供背景知识和上下文

**示例:**
```python
# 专业领域设置
doctor_system = SystemMessage(
    content="你是一位经验丰富的全科医生，擅长诊断常见疾病并提供健康建议。"
)

# 行为风格设置
friendly_system = SystemMessage(
    content="你是一个友好、耐心的助手，总是用积极的语调回答问题。"
)

# 工具使用设置
tool_system = SystemMessage(
    content="你是一个智能助手，可以使用提供的工具来获取实时信息并回答用户问题。"
)
```

### UserMessage

用户消息表示来自用户的输入或者工具执行的结果反馈。

```python
class UserMessage(BaseModel):
    """用户消息模型
    
    表示用户的输入或工具执行结果。支持多种内容格式，
    包括纯文本、结构化数据和工具调用结果。
    """
    
    content: Union[str, List, Dict] = Field(
        description="消息内容，支持字符串、列表或字典格式"
    )
    role: Optional[str] = Field(
        default="user", 
        description="消息角色标识，固定为'user'"
    )
    tool_id: Optional[str] = Field(
        default=None, 
        description="工具调用ID，当消息是工具执行结果时使用"
    )
```

**字段详细说明:**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `content` | `Union[str, List, Dict]` | ✓ | - | 用户输入内容，支持多种数据类型 |
| `role` | `Optional[str]` | ✗ | "user" | 消息角色标识 |
| `tool_id` | `Optional[str]` | ✗ | None | 关联的工具调用ID |

**内容类型说明:**

1. **字符串类型** - 普通文本输入
   ```python
   UserMessage(content="今天天气怎么样？")
   ```

2. **列表类型** - 多媒体内容或结构化输入
   ```python
   UserMessage(content=[
       {"type": "text", "text": "这是什么？"},
       {"type": "image", "url": "data:image/jpeg;base64,..."}
   ])
   ```

3. **字典类型** - 结构化数据
   ```python
   UserMessage(content={
       "query": "search query",
       "filters": {"category": "tech", "date": "2024-01-01"}
   })
   ```

**使用场景:**
- 用户提问和对话输入
- 工具执行结果的反馈
- 多媒体内容上传
- 结构化查询请求

### AssistantMessage

助手消息表示AI模型生成的回复内容。

```python
class AssistantMessage(BaseModel):
    """助手消息模型
    
    表示AI助手生成的回复内容。可以包含纯文本回复
    或者包含工具调用的复合内容。
    """
    
    content: Union[str, List] = Field(
        description="助手回复内容，可以是文本或包含工具调用的列表"
    )
    role: Optional[str] = Field(
        default="assistant", 
        description="消息角色标识，固定为'assistant'"
    )
```

**字段详细说明:**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `content` | `Union[str, List]` | ✓ | - | 助手的回复内容 |
| `role` | `Optional[str]` | ✗ | "assistant" | 消息角色标识 |

### ToolMessage

专门用于工具调用结果的消息类型。

```python
class ToolMessage(BaseModel):
    """工具消息模型
    
    专门用于传递工具执行结果的消息类型。
    与UserMessage的tool_id字段功能类似，但语义更明确。
    """
    
    content: Union[str, List] = Field(
        description="工具执行结果内容"
    )
    role: Optional[str] = Field(
        default="tool", 
        description="消息角色标识，固定为'tool'"
    )
    tool_id: Optional[str] = Field(
        default=None, 
        description="对应的工具调用ID"
    )
```

**字段详细说明:**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `content` | `Union[str, List]` | ✓ | - | 工具执行的结果数据 |
| `role` | `Optional[str]` | ✗ | "tool" | 消息角色标识 |
| `tool_id` | `Optional[str]` | ✗ | None | 关联的工具调用ID |

## 响应模型 (Response Schema)

位置: `src/menglong/ml_model/schema/ml_response.py`

### Content

消息内容模型，包含AI生成的文本和推理过程。

```python
class Content(BaseModel):
    """消息内容模型
    
    包含AI生成的主要内容和可选的推理过程。
    支持具有推理能力的模型（如OpenAI o1系列）显示思考过程。
    """
    
    text: Optional[str] = Field(
        default=None, 
        description="生成的主要文本内容"
    )
    reasoning: Optional[str] = Field(
        default=None, 
        description="模型的推理思考过程（如果支持）"
    )
```

**字段详细说明:**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `text` | `Optional[str]` | ✗ | None | 主要的回复文本 |
| `reasoning` | `Optional[str]` | ✗ | None | 推理过程文本 |

**支持推理的模型:**
- OpenAI o1-preview
- OpenAI o1-mini
- 其他具有Chain-of-Thought能力的模型

### ToolDesc

工具调用描述模型，包含工具调用的完整信息。

```python
class ToolDesc(BaseModel):
    """工具调用描述模型
    
    描述AI模型请求的工具调用，包含工具标识、类型、
    函数名称和调用参数。
    """
    
    id: str = Field(
        description="工具调用的唯一标识符"
    )
    type: str = Field(
        description="工具调用类型，通常为'function'"
    )
    name: str = Field(
        description="要调用的函数名称"
    )
    arguments: Union[str, dict] = Field(
        description="函数调用参数，可以是JSON字符串或字典对象"
    )
```

**字段详细说明:**

| 字段 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `id` | `str` | ✓ | - | 工具调用的唯一ID |
| `type` | `str` | ✓ | - | 工具类型标识 |
| `name` | `str` | ✓ | - | 函数名称 |
| `arguments` | `Union[str, dict]` | ✓ | - | 函数参数 |

**参数格式说明:**
- **字符串格式**: JSON序列化的参数对象
  ```python
  arguments = '{"location": "Beijing", "unit": "celsius"}'
  ```
- **字典格式**: 直接的Python字典对象
  ```python
  arguments = {"location": "Beijing", "unit": "celsius"}
  ```

### Message

完整的消息模型，包含内容和可选的工具调用信息。

```python
class Message(BaseModel):
    """完整消息模型
    
    表示AI模型的完整响应，包括文本内容、工具调用列表
    和响应结束原因。
    """
    
    content: Content = Field(
        description="消息的文本内容"
    )
    tool_desc: Optional[List[ToolDesc]] = Field(
        default=None, 
        description="工具调用列表，如果模型决定使用工具"
    )
    finish_reason: Optional[str] = Field(
        default=None, 
        description="响应结束的原因"
    )
```

**finish_reason 可能的值:**

| 值 | 描述 |
|---|------|
| `stop` | 正常结束，模型完成了回复 |
| `length` | 由于长度限制而结束 |
| `tool_calls` | 模型请求工具调用 |
| `content_filter` | 内容被过滤器拦截 |
| `function_call` | 旧版工具调用格式 |

### Usage

Token使用统计模型，用于跟踪API调用的成本。

```python
class Usage(BaseModel):
    """Token使用统计模型
    
    记录API调用中输入、输出和总Token数量，
    用于成本计算和使用量分析。
    """
    
    input_tokens: int = Field(
        description="输入Token数量（包括系统消息、用户输入等）"
    )
    output_tokens: int = Field(
        description="输出Token数量（AI生成的内容）"
    )
    total_tokens: int = Field(
        description="总Token数量（输入+输出）"
    )
```

**Token计算说明:**
- **输入Token**: 包括所有输入的文本内容，如系统消息、用户消息、工具定义等
- **输出Token**: AI模型生成的文本内容，包括工具调用请求
- **总Token**: 输入和输出Token的总和

### ChatResponse

聊天API的完整响应模型。

```python
class ChatResponse(BaseModel):
    """聊天API响应模型
    
    表示聊天API调用的完整响应，包含消息内容、
    模型信息和使用统计。
    """
    
    message: Message = Field(
        description="响应消息内容"
    )
    model: Optional[str] = Field(
        default=None, 
        description="实际使用的模型标识符"
    )
    usage: Optional[Usage] = Field(
        default=None, 
        description="Token使用统计信息"
    )
```

## 流式响应模型

流式响应用于实时返回AI生成的内容，提供更好的用户体验。

### ContentDelta

流式响应的增量内容模型。

```python
class ContentDelta(BaseModel):
    """流式响应增量内容模型
    
    表示流式响应中的增量内容，每次只包含新生成的部分。
    """
    
    text: Optional[str] = Field(
        default=None, 
        description="增量文本内容"
    )
    reasoning: Optional[str] = Field(
        default=None, 
        description="增量推理过程内容"
    )
```

### StreamMessage

流式响应消息模型。

```python
class StreamMessage(BaseModel):
    """流式响应消息模型
    
    表示流式响应中的单个消息块，包含增量内容
    和状态信息。
    """
    
    delta: ContentDelta = Field(
        description="增量内容"
    )
    start_reason: Optional[str] = Field(
        default=None, 
        description="开始生成的原因"
    )
    finish_reason: Optional[str] = Field(
        default=None, 
        description="结束生成的原因"
    )
```

### ChatStreamResponse

流式聊天响应模型。

```python
class ChatStreamResponse(BaseModel):
    """流式聊天响应模型
    
    表示流式聊天API的响应格式。
    """
    
    message: StreamMessage = Field(
        description="流式响应消息块"
    )
    model: Optional[str] = Field(
        default=None, 
        description="使用的模型标识符"
    )
    usage: Optional[Usage] = Field(
        default=None, 
        description="Token使用统计（通常在最后一个块中）"
    )
```

## 嵌入模型

用于文本嵌入API的响应格式。

### EmbedResponse

```python
class EmbedResponse(BaseModel):
    """嵌入API响应模型
    
    表示文本嵌入API的响应，包含向量数据和元信息。
    """
    
    embeddings: List[List[float]] = Field(
        description="嵌入向量列表，每个向量对应一个输入文本"
    )
    texts: Optional[List[str]] = Field(
        default=None, 
        description="原始文本数据列表"
    )
    model: Optional[str] = Field(
        default=None, 
        description="使用的嵌入模型标识符"
    )
```

**使用说明:**
- `embeddings`: 每个子列表是一个文本的向量表示
- 向量维度取决于使用的模型（如OpenAI ada-002为1536维）
- 向量顺序与输入文本顺序对应

## 转换器规范

MengLong框架使用转换器(Converter)来适配不同AI提供商的API格式。

### 基础转换器接口

```python
class BaseConverter:
    """基础转换器接口
    
    定义了所有转换器必须实现的方法。
    """
    
    @staticmethod
    def convert_request(messages: List[Any]) -> Any:
        """将标准消息格式转换为提供商特定格式"""
        raise NotImplementedError
    
    @staticmethod
    def normalize_response(response: Any) -> ChatResponse:
        """将提供商响应转换为标准格式"""
        raise NotImplementedError
```

### 转换器实现示例

#### OpenAI转换器

```python
class OpenAIConverter(BaseConverter):
    """OpenAI API转换器"""
    
    @staticmethod
    def convert_request(messages):
        """转换为OpenAI格式"""
        formatted_messages = []
        for message in messages:
            if isinstance(message, SystemMessage):
                formatted_messages.append({
                    "role": "system",
                    "content": message.content
                })
            elif isinstance(message, UserMessage):
                formatted_messages.append({
                    "role": "user", 
                    "content": message.content
                })
            # ... 其他消息类型处理
        return formatted_messages
```

#### AWS转换器

```python
class AwsConverter(BaseConverter):
    """AWS Bedrock API转换器"""
    
    @staticmethod
    def convert_request_messages(messages):
        """转换为AWS Converse API格式"""
        system_messages = []
        prompt_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                system_messages.append({"text": message.content})
            elif isinstance(message, UserMessage):
                prompt_messages.append({
                    "role": "user",
                    "content": [{"text": message.content}]
                })
            # ... 其他处理逻辑
            
        return system_messages, prompt_messages
```

## 验证和错误处理

### 数据验证

Pydantic自动提供数据验证功能：

```python
from pydantic import ValidationError

try:
    message = SystemMessage(content="", role="invalid")
except ValidationError as e:
    print(f"验证错误: {e}")
```

### 自定义验证器

```python
from pydantic import validator

class CustomMessage(BaseModel):
    content: str
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('内容不能为空')
        return v
```

### 错误处理最佳实践

```python
def safe_message_creation(content: str) -> Optional[UserMessage]:
    """安全创建消息对象"""
    try:
        return UserMessage(content=content)
    except ValidationError as e:
        logger.error(f"创建消息失败: {e}")
        return None
```

## 使用示例

### 基础聊天对话

```python
from menglong.ml_model import Model
from menglong.ml_model.schema.ml_request import SystemMessage, UserMessage

# 创建模型实例
model = Model(model_id="gpt-4o")

# 构建消息
messages = [
    SystemMessage(content="你是一个有帮助的AI助手"),
    UserMessage(content="你好，请介绍一下你自己")
]

# 发送请求
response = model.chat(messages=messages)

# 处理响应
print(f"回复: {response.message.content.text}")
print(f"模型: {response.model}")
print(f"使用Token: {response.usage.total_tokens}")
```

### 工具调用示例

```python
import json

# 定义工具
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["location"]
        }
    }
}

# 发送带工具的请求
messages = [
    SystemMessage(content="你可以使用工具获取天气信息"),
    UserMessage(content="北京今天天气怎么样？")
]

response = model.chat(
    messages=messages,
    tools=[weather_tool],
    tool_choice="auto"
)

# 检查是否有工具调用
if response.message.tool_desc:
    for tool_call in response.message.tool_desc:
        print(f"工具调用: {tool_call.name}")
        print(f"参数: {tool_call.arguments}")
        
        # 执行工具
        if tool_call.name == "get_weather":
            args = json.loads(tool_call.arguments)
            result = get_weather(**args)
            
            # 创建工具消息
            tool_message = ToolMessage(
                tool_id=tool_call.id,
                content=json.dumps(result)
            )
            
            # 添加到消息历史
            messages.extend([response.message, tool_message])
            
            # 获取最终回复
            final_response = model.chat(messages=messages)
            print(f"最终回复: {final_response.message.content.text}")
```

### 流式响应示例

```python
# 流式聊天
for chunk in model.chat_stream(messages=messages):
    if chunk.message.delta.text:
        print(chunk.message.delta.text, end="", flush=True)
    
    if chunk.message.finish_reason:
        print(f"\n结束原因: {chunk.message.finish_reason}")
```

### 嵌入向量示例

```python
# 文本嵌入
texts = ["这是第一个文本", "这是第二个文本"]
embed_response = model.embed(texts=texts)

for i, embedding in enumerate(embed_response.embeddings):
    print(f"文本 {i+1} 的向量维度: {len(embedding)}")
    print(f"向量前5维: {embedding[:5]}")
```

## 版本兼容性

### 向后兼容性策略

1. **新增字段**: 总是使用可选类型（Optional）
2. **字段重命名**: 保留旧字段，添加别名支持
3. **类型变更**: 使用Union类型支持多种格式
4. **弃用字段**: 添加弃用警告，逐步移除

### 版本迁移指南

```python
# v1.0 -> v2.0 迁移示例
class MessageV2(BaseModel):
    # 新增可选字段
    metadata: Optional[Dict] = Field(default=None, description="元数据")
    
    # 兼容旧字段名
    content: str = Field(alias="text")  # 支持旧的"text"字段名
    
    # 支持多种类型
    user_id: Union[str, int] = Field(description="用户ID，支持字符串或数字")
```

## 总结

MengLong框架的Schema设计遵循以下核心原则：

1. **类型安全**: 使用Pydantic确保数据类型正确性
2. **可扩展性**: 支持向后兼容的功能扩展
3. **标准化**: 统一的数据结构和命名规范
4. **文档化**: 详细的字段描述和使用说明
5. **灵活性**: 支持多种AI提供商的格式差异

这些Schema为构建稳定、可维护的AI应用提供了坚实的基础，同时保持了足够的灵活性来适应不断发展的AI技术栈。

通过理解和正确使用这些Schema规范，开发者可以更好地利用MengLong框架的功能，构建出高质量的AI应用。
