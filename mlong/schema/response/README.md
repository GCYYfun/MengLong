# Response 响应类型

响应类型模块定义了朦胧框架中所有输出响应的数据结构，确保系统输出的一致性和规范性。

## 模块结构

- **__init__.py**: 响应类型模块初始化，导出所有响应类型
- **base.py**: 基础响应类型定义
  - `Message`: 基础消息类型，包含内容和推理内容
  - `Choice`: 选择类型，包含消息内容
- **chat.py**: 聊天相关响应类型
  - `ChatResponse`: 聊天响应类型
  - `ChatStreamResponse`: 流式聊天响应类型

## 详细说明

### 基础响应类型 (base.py)

#### Message

基础消息类型，用于表示单条消息内容。

```python
@dataclass
class Message:
    content: str                      # 消息内容
    reasoning_content: Optional[str]  # 推理内容（可选）
```

#### Choice

选择类型，包含消息内容，通常作为响应的一部分。

```python
@dataclass
class Choice:
    message: Message  # 消息对象
```

### 聊天响应类型 (chat.py)

#### ChatResponse

标准聊天响应类型，包含一个或多个选择。

```python
@dataclass
class ChatResponse:
    choices: List[Choice]  # 选择列表
    
    @property
    def text(self) -> str:  # 便捷访问第一个选择的内容
        return self.choices[0].message.content
```

#### ChatStreamResponse

流式聊天响应类型，用于支持流式输出。

```python
@dataclass
class ChatStreamResponse:
    id: Optional[str]    # 响应ID
    stream: Optional[bool]  # 是否为流式响应
```

## 使用示例

```python
from mlong.schema.response import Message, Choice, ChatResponse

# 创建消息
message = Message(content="这是一条回复", reasoning_content="这是推理过程")

# 创建选择
choice = Choice(message=message)

# 创建聊天响应
response = ChatResponse(choices=[choice])

# 获取响应文本
text = response.text  # "这是一条回复"
```

## 扩展指南

如需扩展响应类型，可以：

1. 在现有文件中添加新的响应类型
2. 创建新的响应类型文件（如 `completion.py`、`embedding.py` 等）
3. 在 `__init__.py` 中导出新的响应类型

新的响应类型应当遵循现有的设计模式，并提供清晰的文档说明。