# ChatAgent 异步运行完整指南

## 概述

ChatAgent 现在提供了完整的异步支持，包括：
- `run(task)` - 同步版本，适用于普通Python环境
- `arun(task)` - 异步版本，适用于异步环境（如 FastAPI、asyncio 应用等）
- 完整的异步工具调用支持
- 异步批量处理能力
- 异步工作流执行

## 核心异步方法

### 基础异步方法

| 方法名 | 描述 | 用途 |
|--------|------|------|
| `arun(task)` | 异步自主任务执行 | 替代 `run()` 在异步环境中使用 |
| `chat_async(message)` | 异步聊天 | 替代 `chat()` 在异步环境中使用 |
| `register_tools_from_functions_async(*funcs)` | 异步工具注册 | 注册同步和异步工具 |
| `batch_chat_async(messages)` | 异步批量聊天 | 并行处理多个消息 |
| `sequential_chat_async(messages)` | 异步顺序聊天 | 顺序处理多个消息 |

### 异步工具支持

ChatAgent 现在支持混合工具调用：
- **同步工具**: 在线程池中异步执行
- **异步工具**: 直接异步调用
- **自动检测**: 根据函数类型自动选择执行方式

## 问题背景

在异步环境中（如已有事件循环运行时），使用 `asyncio.run()` 会引发以下错误：
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

这是因为 `asyncio.run()` 会尝试创建新的事件循环，但在已有事件循环的环境中这是不被允许的。

## 解决方案

### 1. 同步环境使用 `run()`

```python
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode

# 在普通Python脚本中
agent = ChatAgent(mode=ChatMode.AUTO)
agent.register_global_tools()

# 同步执行
result = agent.run("搜索人工智能最新进展", max_iterations=5)
print(f"任务完成: {result['task_completed']}")
```

### 2. 异步环境使用 `arun()`

```python
import asyncio
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode

async def main():
    agent = ChatAgent(mode=ChatMode.AUTO)
    agent.register_global_tools()
    
    # 异步执行
    result = await agent.arun("分析市场数据并生成报告", max_iterations=5)
    print(f"任务完成: {result['task_completed']}")

# 运行异步函数
asyncio.run(main())
```

### 3. FastAPI 中使用

```python
from fastapi import FastAPI
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode

app = FastAPI()
agent = ChatAgent(mode=ChatMode.AUTO)
agent.register_global_tools()

@app.post("/execute_task")
async def execute_task(task: str):
    # 在 FastAPI 路由中使用 arun()
    result = await agent.arun(task, max_iterations=5)
    return {
        "success": result['task_completed'],
        "iterations": result['iterations_used'],
        "execution_time": result['execution_time']
    }
```

### 4. 并行执行多个任务

```python
import asyncio
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode

async def parallel_execution():
    # 创建多个 agent
    research_agent = ChatAgent(mode=ChatMode.AUTO, system="研究专家")
    analysis_agent = ChatAgent(mode=ChatMode.AUTO, system="分析专家")
    
    # 注册工具
    research_agent.register_global_tools()
    analysis_agent.register_global_tools()
    
    # 并行执行不同任务
    research_task = "研究量子计算的最新发展"
    analysis_task = "分析区块链市场趋势"
    
    research_result, analysis_result = await asyncio.gather(
        research_agent.arun(research_task, max_iterations=4),
        analysis_agent.arun(analysis_task, max_iterations=4)
    )
    
    return research_result, analysis_result

# 运行并行任务
asyncio.run(parallel_execution())
```

## 方法对比

| 特性 | `run(task)` | `arun(task)` |
|------|-------------|--------------|
| 执行环境 | 同步环境 | 异步环境 |
| 事件循环 | 创建新循环 | 使用现有循环 |
| 并发支持 | 不支持 | 支持并行执行 |
| 适用场景 | 脚本、命令行 | Web应用、API服务 |

## 错误处理

### 检测运行环境

```python
import asyncio
from menglong.agents.chat.chat_agent import ChatAgent, ChatMode

def smart_run(agent, task, max_iterations=5):
    """智能选择运行方式"""
    try:
        # 检查是否在事件循环中
        asyncio.get_running_loop()
        # 在事件循环中，提示使用异步方式
        print("检测到事件循环，请使用 arun() 方法")
        return None
    except RuntimeError:
        # 没有事件循环，使用同步方式
        return agent.run(task, max_iterations)

async def smart_arun(agent, task, max_iterations=5):
    """异步执行"""
    return await agent.arun(task, max_iterations)
```

### 错误提示改进

`run()` 方法现在会提供更清晰的错误提示：

```python
try:
    result = agent.run(task)
except RuntimeError as e:
    if "cannot be called from a running event loop" in str(e):
        print("错误：在事件循环中调用了 run()，请使用 arun() 代替")
    else:
        raise
```

## 最佳实践

### 1. 选择正确的方法

- **Web 应用 (FastAPI, Django)**: 使用 `arun()`
- **命令行脚本**: 使用 `run()`
- **Jupyter Notebook**: 使用 `arun()`（现代Jupyter支持异步）
- **普通Python脚本**: 使用 `run()`

### 2. 工具注册

```python
# 推荐：在创建agent时注册工具
agent = ChatAgent(mode=ChatMode.AUTO)
agent.register_global_tools()  # 注册所有全局工具

# 或者注册特定工具
from your_tools import web_search, data_analysis
agent.register_tools_from_functions(web_search, data_analysis)
```

### 3. 错误处理

```python
async def robust_execution(agent, task):
    try:
        result = await agent.arun(task, max_iterations=5)
        return result
    except Exception as e:
        print(f"执行失败: {e}")
        return {"task_completed": False, "error": str(e)}
```

### 4. 性能监控

```python
import time

async def timed_execution(agent, task):
    start_time = time.time()
    result = await agent.arun(task)
    execution_time = time.time() - start_time
    
    print(f"执行时间: {execution_time:.2f}秒")
    print(f"迭代次数: {result.get('iterations_used', 0)}")
    
    return result
```

## 示例项目结构

```
your_project/
├── main.py              # 主应用入口
├── agents/
│   ├── __init__.py
│   └── specialized_agents.py
├── tools/
│   ├── __init__.py
│   ├── web_search.py
│   └── data_processing.py
└── async_examples/
    ├── fastapi_app.py   # FastAPI 示例
    ├── parallel_tasks.py # 并行任务示例
    └── jupyter_demo.ipynb # Jupyter 示例
```

## 常见问题

### Q: 何时使用 `run()` vs `arun()`？
A: 如果你的代码已经在异步环境中运行（如 FastAPI 路由），使用 `arun()`。否则使用 `run()`。

### Q: 可以在同一个程序中混用两种方法吗？
A: 不建议。选择一种方式并保持一致。

### Q: `arun()` 是否支持所有 `run()` 的功能？
A: 是的，两个方法功能完全相同，只是执行环境不同。

### Q: 如何调试异步执行？
A: 使用相同的日志系统，异步执行的日志会正常输出。

## 迁移指南

### 从 `run()` 迁移到 `arun()`

1. 将调用代码包装在异步函数中
2. 在函数调用前添加 `await`
3. 使用 `asyncio.run()` 运行主函数

```python
# 之前
result = agent.run(task)

# 之后
async def main():
    result = await agent.arun(task)

asyncio.run(main())
```

这个指南应该能帮助用户正确选择和使用同步或异步版本的 ChatAgent 运行方法。
