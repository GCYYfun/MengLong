# 远程工具执行集成指南

## 概述

这个系统允许您将远程执行的工具与本地任务系统集成，支持任务的挂起(suspend)和恢复(resume)机制。

## 核心组件

### 1. 新增任务状态

- `WAITING_REMOTE`: 表示任务正在等待远程执行结果

### 2. RemoteExecutionManager

管理远程执行请求和响应的核心组件：

```python
# 创建远程执行请求
request_id = remote_manager.create_remote_request(task_id, command, timeout)

# 处理远程响应
remote_manager.handle_remote_response(request_id, success, result, error)

# 等待远程结果
result = await remote_manager.wait_for_remote_result(request_id, timeout)
```

### 3. 任务挂起和恢复方法

在TaskManager中新增的方法：

```python
# 挂起任务等待远程结果
request_id = await task_manager.suspend_task_for_remote(task_id, command, timeout)

# 恢复任务
await task_manager.resume_task_with_result(task_id, remote_result)

# 处理WebSocket响应
task_manager.handle_websocket_response(request_id, success, result, error)
```

## 使用步骤

### 步骤1: 创建远程工具

```python
@tool
def remote_execute(command: str, timeout: int = 30):
    \"\"\"远程执行工具\"\"\"
    # 获取当前任务ID（需要通过上下文传递）
    current_task_id = get_current_task_id()  # 您需要实现这个函数
    
    # 获取任务管理器实例
    task_manager = get_task_manager()  # 您需要实现这个函数
    
    # 挂起任务并发送远程请求
    request_id = await task_manager.suspend_task_for_remote(
        current_task_id, command, timeout
    )
    
    # 发送到远程服务器（通过WebSocket或其他方式）
    await send_to_remote_server(request_id, command)
    
    return {
        "status": "pending_remote",
        "request_id": request_id,
        "message": f"Command sent to remote server: {command}"
    }
```

### 步骤2: 设置WebSocket监听器

```python
class RemoteExecutionHandler:
    def __init__(self, task_manager):
        self.task_manager = task_manager
    
    async def on_websocket_message(self, message):
        \"\"\"WebSocket消息处理器\"\"\"
        data = json.loads(message)
        
        request_id = data.get("request_id")
        success = data.get("success", False)
        result = data.get("result")
        error = data.get("error")
        
        # 这是关键：将远程结果传递给任务系统
        self.task_manager.handle_websocket_response(
            request_id, success, result, error
        )

# 设置WebSocket监听
handler = RemoteExecutionHandler(task_manager)
websocket.on_message = handler.on_websocket_message
```

### 步骤3: 调度器自动处理

调度器已经自动支持`WAITING_REMOTE`状态：

- 等待远程结果的任务不会被重复调度
- 收到远程结果后，任务自动恢复执行
- 支持超时处理和错误处理

## 实际集成示例

### 场景：远程服务器执行命令

```python
# 1. 在您的agent中添加远程工具
tools = [remote_execute, other_tools...]
agent = ChatAgent()
agent.task_manager.remote_manager  # 远程执行管理器已就绪

# 2. 任务执行中调用远程工具
task_id = agent.task_manager.create_task(
    prompt="在远程服务器上执行 'docker ps' 命令",
    tools=[remote_execute]
)

# 3. 任务执行时会自动挂起等待远程结果
# 当WebSocket收到响应时，任务自动恢复

# 4. WebSocket响应处理（在您的WebSocket事件监听器中）
def on_websocket_message(message):
    data = json.loads(message)
    agent.task_manager.handle_websocket_response(
        data["request_id"],
        data["success"], 
        data["result"],
        data.get("error")
    )
```

## 关键特性

### 1. 自动状态管理
- 任务自动从`RUNNING` → `WAITING_REMOTE` → `RUNNING`或`FAILED`
- 调度器智能处理等待状态的任务

### 2. 超时支持
```python
# 支持超时设置
request_id = await task_manager.suspend_task_for_remote(
    task_id, command, timeout=30  # 30秒超时
)
```

### 3. 错误处理
```python
# 远程执行失败时，任务自动标记为FAILED
task_manager.handle_websocket_response(
    request_id, 
    success=False, 
    result=None, 
    error="Remote server connection failed"
)
```

### 4. 上下文保持
- 远程执行结果自动添加到任务的消息上下文
- 支持后续的工具调用和LLM交互

## 注意事项

1. **任务ID传递**: 需要在工具中获取当前任务ID
2. **WebSocket集成**: 需要将远程响应正确路由到任务系统
3. **超时处理**: 设置合理的超时时间避免任务永久挂起
4. **错误恢复**: 处理网络断开、远程服务器故障等情况

这个系统让您可以无缝地将异步远程执行集成到同步的任务流程中，同时保持良好的并发性能和错误处理能力。
