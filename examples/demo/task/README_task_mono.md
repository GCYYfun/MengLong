# 智能任务调度终端应用

这是一个基于 `prompt_toolkit` 的高级异步任务管理终端应用，支持优先级调度和打断机制。

## 🚀 核心特性

### 智能调度系统
- **优先级队列**: 支持 4 个优先级等级（Critical > High > Normal > Low）
- **打断机制**: 关键任务可以打断所有其他任务，高优先级任务在系统繁忙时打断低优先级任务
- **并发控制**: 最多同时运行 3 个任务，智能调度等待队列
- **实时监控**: 任务状态实时更新，支持取消操作

### 交互式终端界面
- **富文本显示**: 使用表情符号和颜色区分不同状态
- **实时状态更新**: 任务执行过程中的状态变化实时显示
- **智能命令解析**: 支持多种命令格式和参数

## 📋 优先级说明

| 优先级 | 级别 | 处理时间 | 打断能力 | 使用场景 |
|--------|------|----------|----------|----------|
| **Critical** | 0 | 1秒 | 打断所有任务 | 紧急安全检查、系统故障处理 |
| **High** | 1 | 3秒 | 在繁忙时打断低优先级 | 重要业务处理、监控告警 |
| **Normal** | 2 | 5秒 | 无打断能力 | 常规数据处理、用户请求 |
| **Low** | 3 | 8秒 | 无打断能力 | 批量处理、清理任务 |

## 🎮 使用方法

### 启动应用

```bash
python examples/demo/task.py
```

### 💻 命令详解

#### 基本命令
- `help` - 显示完整帮助信息
- `clear` - 清空终端输出
- `Ctrl+C` - 退出程序
- `Ctrl+L` - 快速清空输出

#### 任务管理命令
```bash
# 发送指定优先级的任务
send critical 紧急安全检查
send high 系统监控检查
send normal 用户数据处理
send low 日志文件清理

# 快速发送普通优先级任务
处理用户订单

# 查看任务状态
status task_1

# 取消任务
cancel task_2

# 列出所有任务（美观的分组显示）
list

# 查看调度器实时状态
scheduler

# 运行演示（创建各种优先级的示例任务）
demo
```

### 🎯 演示场景

#### 场景1：优先级调度演示
```bash
1. 启动应用: python examples/demo/task.py
2. 运行演示: demo
3. 观察任务执行顺序和打断机制
4. 查看状态: list
```

#### 场景2：打断机制演示
```bash
1. 创建低优先级任务: send low 大数据分析
2. 创建普通任务: send normal 报表生成  
3. 立即创建关键任务: send critical 安全漏洞检测
4. 观察关键任务如何打断其他任务
```

#### 场景3：任务管理演示
```bash
1. 创建多个任务: send high 任务A, send normal 任务B
2. 查看状态: scheduler
3. 取消任务: cancel task_1
4. 查看结果: list
```

## 🏗️ 架构设计

### 核心组件

1. **TaskScheduler** - 智能调度器
   - 优先级队列管理
   - 并发控制
   - 打断逻辑处理

2. **AsyncTaskManager** - 任务管理器
   - 任务生命周期管理
   - 状态跟踪
   - 调度器集成

3. **AsyncTerminalApp** - 交互界面
   - 命令解析
   - 实时状态显示
   - 用户交互处理

### 关键算法

#### 优先级调度
- 使用 Python `heapq` 实现优先级队列
- 任务按优先级值排序（数值越小优先级越高）
- 相同优先级按创建时间排序

#### 打断机制
- **关键任务**: 立即取消所有正在运行的低优先级任务
- **高优先级**: 在并发任务数 > 2 时打断低优先级任务
- **优雅取消**: 使用 `asyncio.CancelledError` 安全终止任务

#### 状态管理
- **队列状态**: queued → running → completed/cancelled/failed
- **实时更新**: 0.5秒检查间隔，状态变化时立即通知
- **资源清理**: 自动清理已完成任务的资源

## 🔧 技术实现

### 异步编程
```python
# 任务执行使用异步协程
async def _execute_task(self, task_item: TaskItem) -> Dict[str, Any]:
    try:
        processing_time = self.get_processing_time(task_item.priority)
        await asyncio.sleep(processing_time)
        return self.create_success_result(task_item)
    except asyncio.CancelledError:
        return self.create_cancelled_result(task_item)
```

### 优先级队列
```python
# 使用 heapq 实现高效的优先级调度
heapq.heappush(self.priority_queue, task_item)
next_task = heapq.heappop(self.priority_queue)
```

### 实时监控
```python
# 非阻塞的任务状态监控
async def _monitor_task(self, task_id: str):
    while True:
        await asyncio.sleep(0.5)
        if status_changed:
            self.update_ui(status)
```

## 🎨 用户界面特色

- **状态图标**: ⏳ 队列中 | 🔄 运行中 | ✅ 已完成 | ❌ 已取消 | 💥 失败
- **优先级标识**: [CRITICAL] [HIGH] [NORMAL] [LOW]
- **实时时间戳**: 每条输出都有精确的时间记录
- **分组显示**: 任务按状态智能分组，便于查看

## 🔍 故障排除

### 常见问题
1. **任务不执行**: 检查调度器是否启动 (`scheduler` 命令)
2. **优先级不生效**: 确认使用正确的优先级关键词
3. **取消失败**: 任务可能已经完成或不存在

### 调试模式
- 使用 `scheduler` 命令查看队列状态
- 使用 `list` 命令查看详细的任务信息
- 观察实时状态更新信息

## 🚀 扩展可能

- 添加任务依赖关系
- 支持定时任务
- 添加任务持久化
- 支持分布式调度
- 添加性能监控和统计

---

**享受智能任务调度的强大功能！** 🎉
