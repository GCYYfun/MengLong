# Agent 模块

Agent模块包含各种智能体的实现，用于处理不同类型的任务和场景。

## 模块结构

- **agent.py**: 基础智能体类，实现了智能体的核心功能
- **code_agent.py**: 代码智能体，专注于代码生成、理解和修改任务

## 核心功能

### 基础智能体 (agent.py)

基础智能体提供了智能体所需的通用功能，包括：
- 消息处理与管理
- 上下文管理
- 会话历史记录
- 工具调用接口

### 代码智能体 (code_agent.py)

代码智能体扩展了基础智能体的功能，专注于代码相关任务：
- 代码生成与补全
- 代码解释与分析
- 错误修复
- 代码优化建议
- 集成开发环境辅助功能

## 子目录说明

- **role_play/**: 角色扮演相关的智能体实现，支持单角色与多角色交互场景

## 使用示例

### 基础智能体

```python
from mlong.model import Model
from mlong.agent.agent import Agent

# 创建模型
model = Model()

# 创建基础智能体
agent = Agent(model=model)

# 与智能体对话
response = agent.chat("如何提高编程效率？")
print(response)
```

### 代码智能体

```python
from mlong.model import Model
from mlong.agent.code_agent import CodeAgent

# 创建模型
model = Model()

# 创建代码智能体
code_agent = CodeAgent(model=model)

# 请求代码生成
code = code_agent.generate_code("创建一个简单的Flask Web应用")
print(code)

