"""
Remote Command 依赖注入最佳实践
===============================

## 快速开始 🚀

### 1. 推荐方案：ContextVar（适用于 99% 的场景）

```python
# 在 TaskManager 的 run_task 方法中设置上下文
from remote_tool import DependencyInjector

class TaskManager:
    async def run_task(self, task_id: int):
        # 设置依赖注入上下文
        DependencyInjector.set_task_context(
            task_manager=self,
            task_id=task_id,
            remote_executor=self.remote_executor  # 如果有的话
        )
        
        # 执行任务逻辑...
        # 现在所有工具都可以通过依赖注入获取这些实例

# 在工具中获取外部实例
@tool
async def remote_command(command: str):
    task_manager = DependencyInjector.get_task_manager()
    task_id = DependencyInjector.get_current_task_id()
    executor = DependencyInjector.get_remote_executor()
    
    # 使用获取到的实例...
```

### 2. 为什么选择 ContextVar？

✅ **异步安全**: 每个协程都有独立的上下文，不会相互干扰
✅ **自动清理**: 协程结束时自动清理，无内存泄漏
✅ **嵌套支持**: 支持嵌套调用和递归
✅ **线程安全**: 在多线程环境下也能正常工作
✅ **零配置**: 不需要复杂的设置和管理

## 实际集成步骤 📋

### 步骤 1: 修改 TaskManager

```python
# 在现有的 TaskManager 类中添加依赖注入支持
from remote_tool import DependencyInjector

class TaskManager:
    def __init__(self):
        # 现有代码...
        self.remote_executor = None  # 添加远程执行器属性
    
    def set_remote_executor(self, executor):
        \"\"\"设置远程执行器\"\"\"
        self.remote_executor = executor
    
    async def run_task(self, task_id: int):
        # 在任务执行前设置依赖注入上下文
        DependencyInjector.set_task_context(
            task_manager=self,
            task_id=task_id,
            remote_executor=self.remote_executor
        )
        
        # 调用原有的任务执行逻辑
        return await self._original_run_task_logic(task_id)
```

### 步骤 2: 创建远程执行器

```python
from remote_tool import WebSocketRemoteExecutor

# 创建远程执行器
remote_executor = WebSocketRemoteExecutor(task_manager)
await remote_executor.connect("ws://your-remote-server")

# 设置到 TaskManager
task_manager.set_remote_executor(remote_executor)
```

### 步骤 3: 创建支持依赖注入的工具

```python
from remote_tool import DependencyInjector
from menglong.agents.component.tool_manager import tool

@tool
async def enhanced_remote_command(command: str, timeout: int = 30):
    \"\"\"支持依赖注入的远程命令工具\"\"\"
    
    # 获取注入的依赖
    task_manager = DependencyInjector.get_task_manager()
    task_id = DependencyInjector.get_current_task_id()
    executor = DependencyInjector.get_remote_executor()
    
    # 验证依赖
    if not task_manager:
        return {"error": "TaskManager 不可用"}
    
    if task_id is None:
        return {"error": "任务 ID 不可用"}
    
    if not executor:
        # 降级处理：如果没有远程执行器，使用本地执行
        return await fallback_to_local_execution(command)
    
    # 发送远程命令
    try:
        request_id = await executor.send_command(task_id, command, timeout)
        return {
            "status": "remote_pending",
            "request_id": request_id,
            "command": command,
            "message": f"远程命令已发送: {request_id}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "command": command
        }

async def fallback_to_local_execution(command: str):
    \"\"\"降级到本地执行\"\"\"
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "status": "local_executed",
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message": "远程执行器不可用，已降级为本地执行"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

## 高级用法 🎯

### 1. 条件性依赖注入

```python
@tool
async def smart_command(command: str):
    \"\"\"智能命令：自动选择本地或远程执行\"\"\"
    
    task_manager = DependencyInjector.get_task_manager()
    executor = DependencyInjector.get_remote_executor()
    
    # 根据可用性选择执行方式
    if executor and await executor.is_available():
        # 远程执行
        return await remote_execution(command, executor)
    else:
        # 本地执行
        return await local_execution(command)
```

### 2. 多重依赖获取

```python
@tool
async def task_info():
    \"\"\"获取当前任务的详细信息\"\"\"
    
    task_manager = DependencyInjector.get_task_manager()
    task_id = DependencyInjector.get_current_task_id()
    
    if not task_manager or task_id is None:
        return {"error": "依赖注入上下文不可用"}
    
    # 获取任务详细信息
    task = task_manager.get_task(task_id)
    task_desc = task_manager.get_task_desc(task_id)
    
    return {
        "task_id": task_id,
        "prompt": task.prompt if task else None,
        "status": task_desc.status.value if task_desc else None,
        "dependencies": task_desc.dependencies if task_desc else [],
        "tools_count": len(task.tools) if task and task.tools else 0
    }
```

### 3. 错误处理和降级策略

```python
@tool
async def robust_remote_command(command: str):
    \"\"\"具有完整错误处理的远程命令\"\"\"
    
    try:
        # 尝试获取依赖
        task_manager = DependencyInjector.get_task_manager()
        task_id = DependencyInjector.get_current_task_id()
        executor = DependencyInjector.get_remote_executor()
        
        # 多层降级策略
        if executor:
            try:
                # 优先使用远程执行
                return await executor.send_command(task_id, command, 30)
            except Exception as remote_error:
                print(f"远程执行失败: {remote_error}")
                # 降级到本地执行
                return await local_execution(command)
        else:
            # 直接本地执行
            return await local_execution(command)
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "command": command,
            "message": "命令执行完全失败"
        }
```

## 性能优化建议 ⚡

### 1. 缓存依赖引用

```python
class OptimizedTool:
    def __init__(self):
        self._task_manager_cache = None
        self._executor_cache = None
    
    def get_cached_dependencies(self):
        if self._task_manager_cache is None:
            self._task_manager_cache = DependencyInjector.get_task_manager()
            self._executor_cache = DependencyInjector.get_remote_executor()
        
        return self._task_manager_cache, self._executor_cache
```

### 2. 惰性初始化

```python
@tool
async def lazy_remote_command(command: str):
    \"\"\"惰性初始化的远程命令\"\"\"
    
    # 只在需要时获取依赖
    def get_executor():
        return DependencyInjector.get_remote_executor()
    
    def get_task_manager():
        return DependencyInjector.get_task_manager()
    
    # 根据命令类型决定是否需要远程执行
    if command.startswith("local:"):
        return await local_execution(command[6:])
    
    # 只有远程命令才获取远程执行器
    executor = get_executor()
    if executor:
        task_manager = get_task_manager()
        task_id = DependencyInjector.get_current_task_id()
        return await executor.send_command(task_id, command, 30)
    
    return await local_execution(command)
```

## 调试技巧 🔍

### 1. 依赖可用性检查

```python
@tool
async def debug_dependencies():
    \"\"\"调试工具：检查依赖注入状态\"\"\"
    
    task_manager = DependencyInjector.get_task_manager()
    task_id = DependencyInjector.get_current_task_id()
    executor = DependencyInjector.get_remote_executor()
    
    return {
        "dependency_status": {
            "task_manager": "✅ 可用" if task_manager else "❌ 不可用",
            "task_id": f"✅ {task_id}" if task_id is not None else "❌ 不可用",
            "remote_executor": "✅ 可用" if executor else "❌ 不可用",
        },
        "task_manager_type": type(task_manager).__name__ if task_manager else None,
        "executor_type": type(executor).__name__ if executor else None,
    }
```

### 2. 上下文追踪

```python
import logging

logger = logging.getLogger(__name__)

@tool
async def traced_remote_command(command: str):
    \"\"\"带追踪的远程命令\"\"\"
    
    task_id = DependencyInjector.get_current_task_id()
    logger.info(f"执行远程命令 - 任务 ID: {task_id}, 命令: {command}")
    
    task_manager = DependencyInjector.get_task_manager()
    executor = DependencyInjector.get_remote_executor()
    
    logger.debug(f"依赖状态 - TaskManager: {bool(task_manager)}, Executor: {bool(executor)}")
    
    # 执行命令逻辑...
```

## 常见问题解决 ❓

### Q1: 工具中获取不到 TaskManager 怎么办？

**A**: 确保在 TaskManager 的 `run_task` 方法开始时调用了 `DependencyInjector.set_task_context()`

### Q2: 在嵌套工具调用中依赖丢失了？

**A**: ContextVar 自动支持嵌套，检查是否在某个地方错误地清理了上下文

### Q3: 如何在工具外部（如测试）中使用依赖注入？

**A**: 手动设置上下文：
```python
DependencyInjector.set_task_context(mock_task_manager, 123, mock_executor)
await your_tool("test command")
```

### Q4: 多个 TaskManager 实例的依赖冲突？

**A**: ContextVar 是协程隔离的，每个协程都有独立的上下文，不会冲突

## 总结 🎉

依赖注入让 `remote_command` 工具能够：

1. **获取 TaskManager**: 访问任务状态、管理任务生命周期
2. **获取当前任务 ID**: 知道自己在哪个任务中执行
3. **获取远程执行器**: 发送命令到远程服务器
4. **实现降级策略**: 在远程不可用时自动降级到本地执行
5. **支持复杂交互**: 挂起任务、等待远程响应、恢复任务

通过 ContextVar 方案，您可以轻松地让任何工具获取到所需的外部实例，无需破坏现有代码结构。
"""
