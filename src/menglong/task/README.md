# 高级异步任务管理系统

这是一个基于`asyncio`的高级任务调度和状态管理系统，为Python异步应用提供精细化的任务控制。

## 📋 任务状态系统

任务在其生命周期中可以处于以下状态之一：

| 状态 | 描述 | 转换条件 |
|------|------|----------|
| `UNUSED` | 默认初始化，任务被创建但尚未加入调度队列 | 创建任务后的初始状态 |
| `READY` | 准备就绪，不在运行，但随时可以被调度运行 | 从UNUSED、SUSPENDED或WAITING状态转换 |
| `RUNNING` | 运行中，当前任务正在执行 | 从READY状态开始执行 |
| `WAITING` | 等待状态，当前任务暂停等待，所依赖的任务或子任务运行 | 任务主动调用wait_task |
| `SUSPENDED` | 挂起状态，任务尚未执行完毕，但被暂停，需要等待恢复后进入READY状态 | 外部调用suspend_task |
| `CANCELED` | 已取消，任务被取消，不再进行执行 | 外部调用cancel_task |
| `COMPLETED` | 已完成，任务顺利完成 | 任务成功执行完毕 |
| `ERROR` | 错误状态，任务出现未知情况，标记为错误状态 | 任务执行过程中抛出异常 |
| `DESTROYED` | 销毁状态，任务已被销毁，资源已释放 | 调用destroy_task或任务被GC |

## 🔄 状态转换流程

```
           创建                        恢复
UNUSED ─────────> READY <───────────────┐
                   │                    │
                   │ 调度               │
                   ▼                    │
               RUNNING ────────┐        │
                │  │           │        │
  正常完成      │  │ 异常      │ 挂起    │
     │          │  │           │        │
     │          │  ▼           ▼        │
     │       ERROR      SUSPENDED ──────┘
     │          │           │
     │          │           │ 取消
     │          │           ▼
     │          └───> CANCELED
     │                   │
     ▼                   │
COMPLETED <─────────────┘
     │
     │ 资源释放/垃圾回收
     ▼
DESTROYED
```

## 🛠️ 核心组件

### 任务控制块 (TCB)

每个任务都由一个 `TCB` (Task Control Block) 对象表示，存储任务的元数据：

```python
class TCB:
    """任务控制块 (Task Control Block)
    
    存储任务的元数据和状态信息
    """
    def __init__(self, task_id, coroutine, loop=None):
        self.task_id = task_id          # 任务唯一标识符
        self.task = None                # asyncio.Task对象
        self.state = TaskState.UNUSED   # 初始状态为UNUSED
        self.coroutine = coroutine      # 协程对象
        self.created_time = ...         # 创建时间
        self.start_time = None          # 开始执行时间
        self.complete_time = None       # 完成时间
```

### 异步任务调度器 (AsyncTaskScheduler)

调度器管理任务的创建、调度、暂停和恢复：

```python
class AsyncTaskScheduler:
    """异步任务调度器
    
    负责任务的创建、调度、暂停和恢复
    """
    def __init__(self):
        self.tasks = {}                 # 任务字典，键为任务ID，值为TCB对象
        self.task_id_counter = 1        # 任务ID计数器
        self.loop = asyncio.new_event_loop()  # 事件循环
        self.current_task = None        # 当前正在执行的任务ID
```

## 📚 主要API功能

### 任务控制

- **`create_task(coroutine)`**: 创建新任务并返回task_id
  ```python
  task_id = scheduler.create_task(my_async_function())
  ```

- **`destroy_task(task_id)`**: 销毁任务并释放资源
  ```python
  scheduler.destroy_task(task_id)
  ```

- **`suspend_task(task_id)`**: 暂停任务执行
  ```python
  scheduler.suspend_task(task_id)
  ```

- **`resume_task(task_id)`**: 恢复暂停的任务
  ```python
  scheduler.resume_task(task_id)
  ```

- **`cancel_task(task_id)`**: 取消任务
  ```python
  success = scheduler.cancel_task(task_id)
  ```

- **`wait_task(task_id)`**: 等待任务完成（通常由任务自身调用）
  ```python
  await scheduler.wait_task(task_id)
  ```

### 状态查询

- **`get_task_state(task_id)`**: 获取任务当前状态
  ```python
  state = scheduler.get_task_state(task_id)
  if state == TaskState.RUNNING:
      print("任务运行中")
  ```

- **`get_task_info(task_id)`**: 获取任务详细信息
  ```python
  info = scheduler.get_task_info(task_id)
  print(f"任务已运行: {info['elapsed_time']:.2f}秒")
  ```

### 调度器控制

- **`run()`**: 启动调度器主循环
  ```python
  scheduler.run()  # 阻塞调用，直到调度器停止
  ```

- **`stop()`**: 停止调度器
  ```python
  scheduler.stop()
  ```

## 📝 使用示例

### 基本用法

```python
import asyncio
from task_manager import AsyncTaskScheduler, TaskState

async def my_task(scheduler, task_name):
    print(f"{task_name} 开始运行")
    await asyncio.sleep(1)  # 模拟工作
    print(f"{task_name} 完成")

# 创建调度器
scheduler = AsyncTaskScheduler()

# 创建任务管理函数
async def manage_tasks(scheduler):
    # 创建几个任务
    task1 = scheduler.create_task(my_task(scheduler, "Task 1"))
    task2 = scheduler.create_task(my_task(scheduler, "Task 2"))
    
    # 等待所有任务完成
    await asyncio.sleep(2)
    
    # 创建另一个任务
    task3 = scheduler.create_task(my_task(scheduler, "Task 3"))
    
    # 取消一个任务（假设它还未完成）
    scheduler.cancel_task(task3)
    
    # 停止调度器
    scheduler.stop()

# 启动管理任务
scheduler.loop.call_soon(lambda: scheduler.create_task(manage_tasks(scheduler)))

# 运行调度器
print("开始任务调度...")
scheduler.run()
print("任务调度完成")
```

### 等待和恢复示例

```python
async def waiting_task(scheduler):
    print("任务开始等待")
    await scheduler.wait_task(scheduler.current_task)
    print("任务从等待中恢复")

async def control_task(scheduler, task_to_resume):
    await asyncio.sleep(2)  # 等待一段时间
    print(f"恢复任务 {task_to_resume}")
    scheduler.resume_task(task_to_resume)
```

### 任务依赖管理

```python
async def dependent_task(scheduler, dependency_id):
    print(f"等待任务 {dependency_id} 完成")
    
    # 监控依赖任务状态
    while True:
        state = scheduler.get_task_state(dependency_id)
        if state == TaskState.COMPLETED:
            break
        elif state in (TaskState.ERROR, TaskState.CANCELED, TaskState.DESTROYED):
            print(f"依赖任务 {dependency_id} 未正常完成: {state}")
            return
        await asyncio.sleep(0.5)
    
    print(f"依赖任务已完成，继续执行")
    # 执行后续操作
```

## 🚀 高级功能与扩展

### 周期性任务

```python
async def periodic_task(scheduler, interval=1.0):
    """每隔指定秒数执行一次的周期性任务"""
    while True:
        # 执行任务逻辑
        print(f"执行周期性任务 - {asyncio.get_running_loop().time():.2f}")
        
        # 等待指定间隔
        await asyncio.sleep(interval)
```

### 优先级任务

可以通过扩展 `TCB` 类来实现任务优先级：

```python
class PrioritizedTCB(TCB):
    def __init__(self, task_id, coroutine, priority=0, loop=None):
        super().__init__(task_id, coroutine, loop)
        self.priority = priority  # 优先级，数值越小优先级越高
```

然后在调度器中实现优先级排序：

```python
def _get_next_ready_task(self):
    """选择优先级最高的就绪任务"""
    ready_tasks = [tcb for tcb in self.tasks.values() 
                  if tcb.state == TaskState.READY]
    if not ready_tasks:
        return None
    
    # 按优先级排序（如果支持优先级）
    if hasattr(ready_tasks[0], 'priority'):
        ready_tasks.sort(key=lambda tcb: tcb.priority)
    
    return ready_tasks[0]
```

### 任务分组

```python
class TaskGroup:
    """任务分组，管理一组相关任务"""
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.tasks = set()
    
    def add_task(self, coroutine):
        """添加任务到组中"""
        task_id = self.scheduler.create_task(coroutine)
        self.tasks.add(task_id)
        return task_id
    
    def cancel_all(self):
        """取消组中所有任务"""
        for task_id in self.tasks:
            self.scheduler.cancel_task(task_id)
```

## 📊 监控与调试

### 任务状态监控器

```python
async def monitor_task(scheduler, task_id, interval=0.5):
    """监控任务状态变化"""
    last_state = None
    start_time = asyncio.get_running_loop().time()
    
    while True:
        # 获取当前状态
        current_state = scheduler.get_task_state(task_id)
        
        # 状态变化时输出
        if current_state != last_state:
            elapsed = asyncio.get_running_loop().time() - start_time
            print(f"任务 {task_id} 状态变化: {last_state} -> {current_state} ({elapsed:.2f}s)")
            last_state = current_state
        
        # 任务结束，退出监控
        if current_state in (TaskState.COMPLETED, TaskState.CANCELED, 
                            TaskState.ERROR, TaskState.DESTROYED):
            break
        
        await asyncio.sleep(interval)
```

### 性能统计

可以通过扩展 `AsyncTaskScheduler` 类来收集性能指标：

```python
class MonitoredTaskScheduler(AsyncTaskScheduler):
    def __init__(self):
        super().__init__()
        self.stats = {
            "created": 0,
            "completed": 0,
            "canceled": 0,
            "errors": 0,
            "avg_run_time": 0,
            "total_tasks": 0
        }
    
    def create_task(self, coroutine):
        task_id = super().create_task(coroutine)
        self.stats["created"] += 1
        self.stats["total_tasks"] += 1
        return task_id
    
    # 重写其他方法，在相应状态变化时更新统计信息
```

## 🔍 最佳实践

1. **资源管理**: 确保长时间运行的任务能够正确响应取消请求
2. **错误处理**: 总是包装任务执行代码在try/except中以避免未处理异常
3. **状态跟踪**: 使用 `get_task_info` 定期检查任务状态
4. **避免死锁**: 小心设计任务间的等待关系，避免循环依赖
5. **合理调用stop()**: 在程序结束前确保调用 `scheduler.stop()` 清理资源

---

**享受高效的异步任务管理！** 🚀