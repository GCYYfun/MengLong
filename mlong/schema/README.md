# Schema 数据模式

数据模式模块定义了朦胧框架中使用的核心数据结构和接口，确保系统各组件之间的一致性和互操作性。

## 模块结构

- **__init__.py**: 模式系统初始化
- **context_manager.py**: 上下文管理器，负责管理对话上下文
- **model_registry.py**: 模型注册表，管理支持的模型及其提供商
- **response/**: 响应类型目录
  - **base.py**: 基础消息类型定义
  - **chat.py**: 聊天相关响应类型

## 核心类型

### 响应类型 (response/)

定义了各种响应相关的数据结构：

- **Message**: 基础消息类型，包含内容和推理内容
- **Choice**: 选择类型，包含消息内容
- **ChatResponse**: 聊天响应类型
- **ChatStreamResponse**: 流式聊天响应类型

### 上下文管理 (context_manager.py)

- **ContextManager**: 上下文管理器，负责管理对话上下文，包括系统消息、用户消息和助手响应

### 模型注册 (model_registry.py)

- **MODEL_REGISTRY**: 全局模型注册表
- **register_model**: 注册新模型
- **get_model_info**: 获取模型信息
- **list_models**: 列出所有模型
- **list_models_by_provider**: 获取指定提供商的模型

## 使用方式

数据模式主要用于：
1. 定义接口规范
2. 数据结构验证
3. 确保系统各组件间的一致性

代码示例：

```python
from mlong.schema import ContextManager, Message

# 创建上下文管理器
context_manager = ContextManager()

# 设置系统消息
context_manager.system = "你是一个友好的AI助手"

# 添加用户消息
context_manager.add_user_message("你好，能帮我解答一个问题吗？")

# 获取当前对话上下文
context = context_manager.messages
```

## 模式扩展

如需扩展数据模式，可以：
1. 在现有模式文件中添加新的数据结构
2. 创建新的模式定义文件
3. 在 `__init__.py` 中导出新的数据结构

请确保新的数据结构与现有系统保持一致，并提供适当的文档说明。