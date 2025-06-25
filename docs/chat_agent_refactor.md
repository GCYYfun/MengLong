# ChatAgent 模块化重构说明

## 概述

为了提高代码的可维护性和模块化程度，我们将原本复杂的 `ChatAgent` 拆分成了三个独立的模块：

1. **ToolManager** (`tool_manager.py`) - 工具管理器
2. **WorkflowManager** (`workflow_manager.py`) - 工作流管理器  
3. **SimpleChatAgent** (`simple_chat_agent.py`) - 简化的聊天代理

## 模块说明

### 1. ToolManager (工具管理器)

负责工具的定义、注册、格式化和执行。

**主要功能：**
- 工具注册和管理
- 支持多种工具注册方式（函数列表、模块、全局工具等）
- 根据不同模型提供商格式化工具描述
- 同步和异步工具执行

**核心类：**
- `ToolManager`: 工具管理器主类
- `ToolInfo`: 工具信息存储类
- `@tool`: 工具装饰器

### 2. WorkflowManager (工作流管理器)

负责工作流的定义和执行。

**主要功能：**
- 工作流步骤管理
- 同步和异步工作流执行
- 工作流状态跟踪
- 条件执行支持

**核心类：**
- `WorkflowManager`: 工作流管理器主类
- `WorkflowStep`: 工作流步骤类

### 3. SimpleChatAgent (简化聊天代理)

专注于核心聊天功能，通过组合 ToolManager 和 WorkflowManager 提供完整功能。

**主要功能：**
- 三种聊天模式（NORMAL、AUTO、WORKFLOW）
- 同步和异步聊天
- 自主任务执行
- 批量消息处理
- 上下文管理

## 使用示例

### 基本使用

```python
from menglong.agents.chat import SimpleChatAgent, ChatMode, tool

# 定义工具
@tool(description="获取天气信息")
def get_weather(location: str):
    return f"{location}的天气很好"

# 创建代理
agent = SimpleChatAgent(mode=ChatMode.AUTO)
agent.register_global_tools()

# 聊天
response = agent.chat("今天北京的天气怎么样？")
```

### 异步使用

```python
# 异步聊天
response = await agent.chat_async("今天北京的天气怎么样？")

# 自主任务执行
result = await agent.arun("帮我研究一下人工智能的最新发展")
```

### 工作流模式

```python
agent = SimpleChatAgent(mode=ChatMode.WORKFLOW)

# 定义工作流步骤
def analyze_step(input_msg, context):
    return "分析完成"

def process_step(input_msg, context):
    return "处理完成"

# 添加步骤
agent.add_workflow_step("分析", analyze_step)
agent.add_workflow_step("处理", process_step)

# 执行工作流
result = agent.chat("执行工作流")
```

## 向后兼容性

原本的 `ChatAgent` 类仍然保留，确保现有代码不受影响。新的模块化组件可以逐步迁移使用。

```python
# 原有方式仍然可用
from menglong.agents.chat import ChatAgent

# 新的模块化方式
from menglong.agents.chat import SimpleChatAgent
```

## 优势

1. **模块化**: 每个模块职责单一，便于理解和维护
2. **可重用性**: 工具管理器和工作流管理器可以独立使用
3. **可扩展性**: 更容易添加新功能而不影响其他模块
4. **测试友好**: 每个模块可以独立测试
5. **向后兼容**: 保持现有API不变

## 文件结构

```
src/menglong/agents/chat/
├── __init__.py                 # 模块导入
├── chat_agent.py              # 原始复杂实现（保留）
├── tool_manager.py            # 工具管理器
├── workflow_manager.py        # 工作流管理器
└── simple_chat_agent.py       # 简化聊天代理
```

## 示例文件

参考 `examples/simple_chat_agent_example.py` 获取详细的使用示例。
