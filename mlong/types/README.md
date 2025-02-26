# Types 类型系统

类型系统模块定义了朦胧框架中使用的核心数据类型和接口，确保系统各组件之间的一致性和互操作性。

## 模块结构

- **__init__.py**: 类型系统初始化
- **type_chat.py**: 聊天相关的类型定义
- **type_model.py**: 模型相关的类型定义

## 核心类型

### 聊天类型 (type_chat.py)

定义了与聊天功能相关的数据结构和类型：

- **Message**: 消息类型，包含角色、内容等属性
- **ChatHistory**: 聊天历史记录类型
- **ChatOptions**: 聊天选项配置
- **ChatResponse**: 聊天响应类型

### 模型类型 (type_model.py)

定义了与模型功能相关的数据结构和类型：

- **ModelConfig**: 模型配置类型
- **ModelResponse**: 模型响应类型
- **ModelMetadata**: 模型元数据
- **GenerationOptions**: 生成选项配置

## 使用方式

类型系统主要用于：
1. 定义接口规范
2. 类型检查和验证
3. 确保系统各组件间的一致性

代码示例：

```python
from mlong.types.type_chat import Message

# 创建消息对象
user_message = Message(
    role="user",
    content="你好，能帮我解答一个问题吗？",
    id="msg_1234"
)

# 消息可以被用于各种智能体和模型接口中
```

## 类型扩展

如需扩展类型系统，可以：
1. 在现有类型文件中添加新类型
2. 创建新的类型定义文件
3. 在 `__init__.py` 中导出新类型

请确保新类型与现有系统保持一致，并提供适当的文档说明。