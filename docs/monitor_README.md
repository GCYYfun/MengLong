# MengLong 监控模块

## 概述

MengLong监控模块是一个功能强大、灵活可配置的监控系统，专门为排查Agent系统问题而设计。它能够主动选择开启与关闭特定的监控项目，在需要排查问题时提供详细的verbose数据。

## 🎯 核心特性

- **🔧 选择性监控**: 精确控制监控哪些类别的数据
- **📊 多级别监控**: 支持 DEBUG、INFO、WARNING、ERROR 四个级别
- **⚙️ 灵活配置**: 支持配置文件、环境变量、代码配置
- **📝 多种输出**: 控制台、文件、自定义处理器
- **⚡ 性能监控**: 内置性能统计和分析
- **🎨 装饰器支持**: 便捷的函数监控装饰器
- **🔍 上下文管理**: 代码块级别的监控
- **📈 实时统计**: 事件统计和历史记录
- **🛠️ 零侵入集成**: 可轻松集成到现有代码

## 📋 监控分类

| 分类 | 说明 | 应用场景 |
|-----|------|----------|
| `MODEL_INTERACTION` | 模型交互原始数据 | 调试模型请求/响应，排查模型相关问题 |
| `TOOL_CALLS` | 工具调用数据 | 监控工具执行情况，排查工具调用问题 |
| `CONTEXT_MANAGEMENT` | 对话上下文管理 | 跟踪上下文变化，排查对话状态问题 |
| `DATA_TRANSFORM` | 数据转换过程 | 监控数据格式转换，排查数据处理问题 |
| `ASYNC_TASKS` | 异步任务执行 | 跟踪异步任务状态，排查并发问题 |
| `WORKFLOW` | 工作流执行 | 监控工作流步骤，排查流程问题 |
| `ERROR_TRACKING` | 错误跟踪 | 收集错误信息，进行错误分析 |
| `PERFORMANCE` | 性能监控 | 分析性能瓶颈，优化执行效率 |

## 🚀 快速开始

### 基础使用

```python
from menglong.monitor import enable_monitoring, MonitorCategory, set_monitor_level, MonitorLevel

# 启用特定监控
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

### 使用装饰器

```python
from menglong.monitor import monitor_performance

@monitor_performance
def expensive_function():
    # 自动监控函数执行时间
    time.sleep(1)
    return "结果"
```

### 使用上下文管理器

```python
from menglong.monitor import monitor_context, MonitorCategory

with monitor_context(MonitorCategory.TOOL_CALLS, "批量处理") as ctx:
    ctx.add_data("batch_size", 100)
    # ... 执行代码 ...
    ctx.add_data("processed_items", 100)
```

## ⚙️ 配置方式

### 1. 配置文件 (推荐)

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
    console:
      enabled: true
    file:
      enabled: true
      directory: "./logs"
```

```python
from menglong.monitor import init_monitoring
init_monitoring("monitor_config.yaml")
```

### 2. 环境变量

```bash
export ML_MONITOR_ENABLED=true
export ML_MONITOR_LEVEL=DEBUG
export ML_MONITOR_CATEGORIES=MODEL_INTERACTION,TOOL_CALLS
```

### 3. 代码配置

```python
from menglong.monitor import enable_debug_monitoring, enable_production_monitoring

# 开发环境
enable_debug_monitoring()

# 生产环境
enable_production_monitoring()
```

## 🔧 ChatAgent集成

### 继承方式集成

```python
from menglong.agents.chat import SimpleChatAgent
from menglong.monitor import enable_monitoring, MonitorCategory, log_model_interaction

class MonitoredChatAgent(SimpleChatAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_monitoring(MonitorCategory.MODEL_INTERACTION, MonitorCategory.TOOL_CALLS)
    
    def chat(self, message: str, **kwargs):
        # 记录请求
        log_model_interaction("发送请求", request_data={"message": message})
        
        # 调用原方法
        response = super().chat(message, **kwargs)
        
        # 记录响应
        log_model_interaction("收到响应", response_data={"content": str(response)})
        
        return response
```

### 装饰器方式集成

```python
from menglong.monitor import monitor_performance

class ChatAgent:
    @monitor_performance
    def chat(self, message: str, **kwargs):
        # 原有代码保持不变
        pass
```

## 📊 监控输出示例

```
[14:30:15.123] INFO [model_interaction] 发送请求到模型
  Data: {
    "request": {
      "messages": [{"role": "user", "content": "你好"}],
      "model": "gpt-4"
    },
    "model_id": "gpt-4"
  }

[14:30:15.456] INFO [tool_calls] Tool call: get_weather
  Data: {
    "tool_name": "get_weather",
    "arguments": {"city": "北京"},
    "result": {"temperature": 20, "weather": "晴天"}
  }

[14:30:15.789] ERROR [error_tracking] Function error: process_data - 数据格式错误
  Data: {
    "function": "process_data",
    "error": "数据格式错误",
    "error_type": "ValueError"
  }
```

## 🎭 使用场景

### 1. 问题排查

```python
# 临时启用详细监控进行问题排查
from menglong.monitor import enable_debug_monitoring

enable_debug_monitoring()

# 执行有问题的代码
agent.chat("用户消息")

# 查看监控历史
history = get_monitor().get_history(level=MonitorLevel.ERROR)
for event in history:
    print(f"错误: {event.message}")
```

### 2. 性能优化

```python
# 启用性能监控
enable_monitoring(MonitorCategory.PERFORMANCE)

@monitor_performance
def slow_function():
    pass

# 查看性能统计
stats = get_monitor().get_performance_stats()
for func_name, data in stats.items():
    if data['avg_time'] > 1.0:
        print(f"慢函数: {func_name}, 平均时间: {data['avg_time']:.3f}s")
```

### 3. 生产监控

```python
# 生产环境只监控错误
enable_production_monitoring()

# 所有错误会被自动记录到日志文件
```

## 📁 项目结构

```
src/menglong/monitor/
├── __init__.py          # 模块导出
├── ml_monitor.py        # 核心监控器
└── config.py           # 配置管理

examples/
├── monitor_example.py           # 基础使用示例
├── monitored_chat_agent.py     # ChatAgent集成示例
├── monitor_config_example.py   # 配置使用示例
└── monitor_config.yaml         # 配置文件示例

docs/
└── monitor_guide.md            # 详细使用指南
```

## 📖 文档

- [详细使用指南](docs/monitor_guide.md)
- [API参考](src/menglong/monitor/)
- [示例代码](examples/)

## 🔧 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ML_MONITOR_ENABLED` | 是否启用监控 | `true` |
| `ML_MONITOR_LEVEL` | 监控级别 | `DEBUG` |
| `ML_MONITOR_CATEGORIES` | 监控分类 | `MODEL_INTERACTION,TOOL_CALLS` |
| `ML_MONITOR_LOG_DIR` | 日志目录 | `./logs` |

## 🎨 高级功能

### 自定义处理器

```python
def custom_handler(event):
    # 自定义处理逻辑
    print(f"自定义处理: {event.message}")

get_monitor().add_handler(custom_handler)
```

### 事件过滤器

```python
def error_filter(event):
    return event.level == MonitorLevel.ERROR

get_monitor().add_filter(error_filter)
```

### 历史记录导出

```python
# 导出历史记录
get_monitor().export_history("monitor_history.json")

# 获取特定事件
history = get_monitor().get_history(
    category=MonitorCategory.MODEL_INTERACTION,
    limit=50
)
```

## 🔧 最佳实践

1. **分环境配置**: 开发环境启用详细监控，生产环境只监控错误
2. **选择性监控**: 根据需要启用特定分类，避免信息过载
3. **性能考虑**: 监控本身有开销，合理配置级别和分类
4. **日志管理**: 配置日志轮转，避免日志文件过大
5. **错误处理**: 监控器错误不应影响主业务逻辑

## 🚫 注意事项

- 监控功能会有一定的性能开销，请根据需要合理配置
- 敏感数据在记录时需要注意脱敏处理
- 生产环境建议使用文件输出而非控制台输出
- 定期清理历史记录和日志文件

## 🤝 贡献

欢迎提交Issue和Pull Request来改进监控模块！

## 📄 许可证

本项目遵循 MIT 许可证。
