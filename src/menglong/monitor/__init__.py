"""
MengLong 监控模块

提供可控制的监控功能，支持以下监控分类：
- MODEL_INTERACTION: 模型交互原始数据
- TOOL_CALLS: 工具调用数据
- CONTEXT_MANAGEMENT: 对话上下文管理
- DATA_TRANSFORM: 数据转换过程
- ASYNC_TASKS: 异步任务执行
- WORKFLOW: 工作流执行
- ERROR_TRACKING: 错误跟踪
- PERFORMANCE: 性能监控

快速使用：
```python
from menglong.monitor import enable_monitoring, MonitorCategory, set_monitor_level, MonitorLevel

# 启用模型交互监控
enable_monitoring(MonitorCategory.MODEL_INTERACTION)

# 启用所有监控
enable_monitoring()

# 设置监控级别
set_monitor_level(MonitorLevel.DEBUG)

# 使用装饰器监控函数
from menglong.monitor import monitor_performance

@monitor_performance
def my_function():
    pass

# 使用上下文管理器
from menglong.monitor import monitor_context, MonitorCategory

with monitor_context(MonitorCategory.TOOL_CALLS, "process_data") as ctx:
    ctx.add_data("input_size", 100)
    # ... 执行代码 ...
```
"""

from .ml_monitor import (
    # 核心类
    MLMonitor,
    MonitorEvent,
    MonitorLevel,
    MonitorCategory,
    MonitorContext,
    # 全局监控器
    get_monitor,
    # 便捷控制函数
    enable_monitoring,
    disable_monitoring,
    set_monitor_level,
    # 日志记录函数
    log_event,
    log_model_interaction,
    log_tool_call,
    log_context_update,
    log_data_transform,
    # 装饰器和上下文管理器
    monitor_performance,
    monitor_context,
)

from .config import (
    # 配置类
    MonitorConfig,
    # 全局配置
    get_config,
    init_monitoring,
    create_default_config,
    load_config_from_dict,
    # 便捷配置函数
    enable_debug_monitoring,
    enable_production_monitoring,
    enable_tool_debugging,
    enable_model_debugging,
)

__all__ = [
    # 核心类
    "MLMonitor",
    "MonitorEvent",
    "MonitorLevel",
    "MonitorCategory",
    "MonitorContext",
    # 全局监控器
    "get_monitor",
    # 便捷控制函数
    "enable_monitoring",
    "disable_monitoring",
    "set_monitor_level",
    # 日志记录函数
    "log_event",
    "log_model_interaction",
    "log_tool_call",
    "log_context_update",
    "log_data_transform",
    # 装饰器和上下文管理器
    "monitor_performance",
    "monitor_context",
    # 配置类
    "MonitorConfig",
    # 全局配置
    "get_config",
    "init_monitoring",
    "create_default_config",
    "load_config_from_dict",
    # 便捷配置函数
    "enable_debug_monitoring",
    "enable_production_monitoring",
    "enable_tool_debugging",
    "enable_model_debugging",
]
