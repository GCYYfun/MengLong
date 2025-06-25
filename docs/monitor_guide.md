# MengLong 监控模块使用指南

MengLong监控模块提供了灵活的监控功能，可以主动选择开启与关闭特定的监控项目，用于在需要排查问题时查看详细的verbose数据。

## 特性

- 🎯 **选择性监控**: 可以精确控制监控哪些类别的数据
- 📊 **多级别监控**: 支持 DEBUG、INFO、WARNING、ERROR 四个级别
- 🔧 **灵活配置**: 支持运行时动态开启/关闭监控
- 📝 **多种输出**: 支持控制台、文件、自定义处理器输出
- ⚡ **性能监控**: 内置性能统计和分析功能
- 🎨 **装饰器支持**: 提供便捷的装饰器进行函数监控
- 🔍 **上下文管理**: 支持上下文管理器进行代码块监控

## 监控分类

| 分类 | 说明 | 用途 |
|-----|------|------|
| `MODEL_INTERACTION` | 模型交互原始数据 | 查看请求/响应数据，排查模型相关问题 |
| `TOOL_CALLS` | 工具调用数据 | 监控工具执行情况，排查工具调用问题 |
| `CONTEXT_MANAGEMENT` | 对话上下文管理 | 跟踪上下文变化，排查对话状态问题 |
| `DATA_TRANSFORM` | 数据转换过程 | 监控数据格式转换，排查数据处理问题 |
| `ASYNC_TASKS` | 异步任务执行 | 跟踪异步任务状态，排查并发问题 |
| `WORKFLOW` | 工作流执行 | 监控工作流步骤，排查流程问题 |
| `ERROR_TRACKING` | 错误跟踪 | 收集错误信息，进行错误分析 |
| `PERFORMANCE` | 性能监控 | 分析性能瓶颈，优化执行效率 |

## 快速开始

### 基础使用

```python
from menglong.monitor import enable_monitoring, MonitorCategory, set_monitor_level, MonitorLevel

# 启用特定监控分类
enable_monitoring(MonitorCategory.MODEL_INTERACTION, MonitorCategory.TOOL_CALLS)

# 设置监控级别
set_monitor_level(MonitorLevel.DEBUG)

# 启用所有监控
enable_monitoring()
```

### 记录监控事件

```python
from menglong.monitor import log_model_interaction, log_tool_call

# 记录模型交互
log_model_interaction(
    "发送请求到模型",
    request_data={"messages": [...], "temperature": 0.7},
    response_data={"content": "响应内容"},
    model_id="gpt-4"
)

# 记录工具调用
log_tool_call(
    tool_name="get_weather", 
    arguments={"city": "北京"},
    result={"temperature": 20, "weather": "晴天"}
)
```

### 使用装饰器监控函数

```python
from menglong.monitor import monitor_performance

@monitor_performance
def expensive_function():
    # 自动监控函数执行时间和性能
    time.sleep(1)
    return "结果"
```

### 使用上下文管理器

```python
from menglong.monitor import monitor_context, MonitorCategory

with monitor_context(MonitorCategory.TOOL_CALLS, "批量处理数据") as ctx:
    ctx.add_data("batch_size", 100)
    # ... 执行代码 ...
    ctx.add_data("processed_items", 100)
```

## 在ChatAgent中集成监控

### 方法1: 继承集成

```python
from menglong.agents.chat import SimpleChatAgent
from menglong.monitor import enable_monitoring, MonitorCategory, log_model_interaction

class MonitoredChatAgent(SimpleChatAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 启用监控
        enable_monitoring(MonitorCategory.MODEL_INTERACTION, MonitorCategory.TOOL_CALLS)
    
    def chat(self, message: str, **kwargs):
        # 记录请求数据
        log_model_interaction(
            "发送请求到模型",
            request_data={"message": message},
            model_id=self.model.model_id
        )
        
        # 调用原方法
        response = super().chat(message, **kwargs)
        
        # 记录响应数据
        log_model_interaction(
            "收到模型响应",
            response_data={"content": str(response)},
            model_id=self.model.model_id
        )
        
        return response
```

### 方法2: 装饰器集成

```python
from menglong.monitor import monitor_performance

class ChatAgent:
    @monitor_performance
    def chat(self, message: str, **kwargs):
        # 原有代码...
        pass
    
    @monitor_performance  
    def _execute_tool(self, tool_name: str, arguments: dict):
        # 原有代码...
        pass
```

## 高级功能

### 自定义处理器

```python
from menglong.monitor import get_monitor

def file_handler(event):
    """将事件写入文件"""
    with open(f"{event.category.value}.log", "a") as f:
        f.write(f"{event.timestamp}: {event.message}\\n")

# 添加自定义处理器
monitor = get_monitor()
monitor.add_handler(file_handler)
```

### 事件过滤器

```python
def error_only_filter(event):
    """只通过错误级别的事件"""
    return event.level == MonitorLevel.ERROR

monitor.add_filter(error_only_filter)
```

### 性能统计

```python
from menglong.monitor import get_monitor

monitor = get_monitor()

# 获取性能统计
stats = monitor.get_performance_stats()
print(f"平均执行时间: {stats['my_function']['avg_time']:.3f}s")
```

### 导出历史记录

```python
# 导出所有历史记录
monitor.export_history("monitor_history.json")

# 获取特定类别的历史
history = monitor.get_history(category=MonitorCategory.MODEL_INTERACTION, limit=50)
```

## 最佳实践

### 1. 分环境配置

```python
import os
from menglong.monitor import enable_monitoring, MonitorCategory, set_monitor_level, MonitorLevel

# 根据环境配置监控
if os.getenv("ENV") == "development":
    enable_monitoring()  # 开发环境启用所有监控
    set_monitor_level(MonitorLevel.DEBUG)
elif os.getenv("ENV") == "production":
    enable_monitoring(MonitorCategory.ERROR_TRACKING)  # 生产环境只监控错误
    set_monitor_level(MonitorLevel.ERROR)
```

### 2. 关键路径监控

```python
# 在关键业务逻辑中添加监控
with monitor_context(MonitorCategory.WORKFLOW, "用户查询处理") as ctx:
    ctx.add_data("user_id", user_id)
    ctx.add_data("query_type", query_type)
    
    # 执行业务逻辑
    result = process_user_query(query)
    
    ctx.add_data("result_count", len(result))
```

### 3. 错误排查

```python
# 开启详细监控进行错误排查
enable_monitoring(
    MonitorCategory.MODEL_INTERACTION,
    MonitorCategory.TOOL_CALLS, 
    MonitorCategory.CONTEXT_MANAGEMENT
)
set_monitor_level(MonitorLevel.DEBUG)

# 执行可能有问题的代码
try:
    agent.chat("用户消息")
except Exception:
    # 查看监控历史排查问题
    history = get_monitor().get_history(level=MonitorLevel.ERROR)
    for event in history:
        print(f"错误: {event.message}")
        print(f"数据: {event.data}")
```

### 4. 性能优化

```python
# 启用性能监控
enable_monitoring(MonitorCategory.PERFORMANCE)

@monitor_performance
def slow_function():
    # 函数执行时间会被自动记录
    pass

# 分析性能数据
stats = get_monitor().get_performance_stats()
for func_name, data in stats.items():
    if data['avg_time'] > 1.0:  # 找出执行时间超过1秒的函数
        print(f"慢函数: {func_name}, 平均时间: {data['avg_time']:.3f}s")
```

## 配置选项

### 环境变量配置

```bash
# 设置默认监控级别
export ML_MONITOR_LEVEL=DEBUG

# 设置默认监控分类
export ML_MONITOR_CATEGORIES=MODEL_INTERACTION,TOOL_CALLS

# 设置日志输出目录
export ML_MONITOR_LOG_DIR=./logs
```

### 配置文件

```yaml
# monitor_config.yaml
monitor:
  enabled: true
  level: INFO
  categories:
    - MODEL_INTERACTION
    - TOOL_CALLS
    - ERROR_TRACKING
  handlers:
    - console
    - file
  file_output:
    directory: "./logs"
    max_size: "10MB"
    backup_count: 5
```

## 故障排查

### 常见问题

1. **监控不生效**
   ```python
   # 检查监控状态
   from menglong.monitor import get_monitor
   print(get_monitor().get_status())
   ```

2. **输出过多信息**
   ```python
   # 调整监控级别
   set_monitor_level(MonitorLevel.WARNING)
   ```

3. **性能影响**
   ```python
   # 选择性启用监控
   enable_monitoring(MonitorCategory.ERROR_TRACKING)
   ```

### 调试技巧

```python
# 临时启用详细监控
def debug_chat_issue():
    monitor = get_monitor()
    
    # 保存当前状态
    old_categories = monitor._enabled_categories.copy()
    old_level = monitor._enabled_levels.copy()
    
    try:
        # 启用详细监控
        enable_monitoring()
        set_monitor_level(MonitorLevel.DEBUG)
        
        # 执行有问题的代码
        agent.chat("测试消息")
        
    finally:
        # 恢复原状态
        monitor._enabled_categories = old_categories
        monitor._enabled_levels = old_level
```

## 示例代码

完整的示例代码请参考：
- `examples/monitor_example.py` - 基础使用示例
- `examples/monitored_chat_agent.py` - ChatAgent集成示例

## API参考

详细的API文档请参考源码中的docstring注释。
