"""
MengLong 监视器模块

提供灵活的监控功能，可以主动选择开启与关闭特定的监控项目，
用于排查问题时查看详细的verbose数据。

支持的监控项目：
- MODEL_INTERACTION: 模型交互原始数据
- TOOL_CALLS: 工具调用数据
- CONTEXT_MANAGEMENT: 对话上下文管理
- DATA_TRANSFORM: 数据转换过程
- ASYNC_TASKS: 异步任务执行
- WORKFLOW: 工作流执行
- ERROR_TRACKING: 错误跟踪
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Set
from enum import Enum
from pathlib import Path
import functools
import inspect


class MonitorLevel(Enum):
    """监控级别"""

    DEBUG = "DEBUG"  # 详细调试信息
    INFO = "INFO"  # 常规信息
    WARNING = "WARNING"  # 警告信息
    ERROR = "ERROR"  # 错误信息


class MonitorCategory(Enum):
    """监控分类"""

    MODEL_INTERACTION = "MODEL_INTERACTION"  # 模型交互
    TOOL_CALLS = "TOOL_CALLS"  # 工具调用
    CONTEXT_MANAGEMENT = "CONTEXT_MANAGEMENT"  # 上下文管理
    DATA_TRANSFORM = "DATA_TRANSFORM"  # 数据转换
    ASYNC_TASKS = "ASYNC_TASKS"  # 异步任务
    WORKFLOW = "WORKFLOW"  # 工作流
    ERROR_TRACKING = "ERROR_TRACKING"  # 错误跟踪
    PERFORMANCE = "PERFORMANCE"  # 性能监控


class MonitorEvent:
    """监控事件"""

    def __init__(
        self,
        category: MonitorCategory,
        level: MonitorLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.category = category
        self.level = level
        self.message = message
        self.data = data or {}
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.thread_id = threading.get_ident()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "level": self.level.value,
            "message": self.message,
            "data": self.data,
            "source": self.source,
            "thread_id": self.thread_id,
        }

    def __str__(self) -> str:
        """字符串表示"""
        time_str = self.timestamp.strftime("%H:%M:%S.%f")[:-3]
        return f"[{time_str}] {self.level.value} [{self.category.value}] {self.message}"


class MLMonitor:
    """MengLong 监视器"""

    def __init__(self):
        self._enabled_categories: Set[MonitorCategory] = set()
        self._enabled_levels: Set[MonitorLevel] = {
            MonitorLevel.INFO,
            MonitorLevel.WARNING,
            MonitorLevel.ERROR,
        }
        self._handlers: List[Callable[[MonitorEvent], None]] = []
        self._lock = threading.Lock()
        self._event_history: List[MonitorEvent] = []
        self._max_history = 1000  # 最大历史记录数
        self._filters: List[Callable[[MonitorEvent], bool]] = []

        # 性能统计
        self._performance_stats: Dict[str, Dict[str, Any]] = {}

        # 默认添加控制台输出处理器
        self.add_handler(self._console_handler)

    def enable_category(self, category: MonitorCategory) -> None:
        """启用监控分类"""
        with self._lock:
            self._enabled_categories.add(category)

    def disable_category(self, category: MonitorCategory) -> None:
        """禁用监控分类"""
        with self._lock:
            self._enabled_categories.discard(category)

    def enable_categories(self, categories: List[MonitorCategory]) -> None:
        """批量启用监控分类"""
        with self._lock:
            self._enabled_categories.update(categories)

    def disable_categories(self, categories: List[MonitorCategory]) -> None:
        """批量禁用监控分类"""
        with self._lock:
            for category in categories:
                self._enabled_categories.discard(category)

    def set_level(self, level: MonitorLevel) -> None:
        """设置监控级别（包含该级别及以上）"""
        level_order = {
            MonitorLevel.DEBUG: 0,
            MonitorLevel.INFO: 1,
            MonitorLevel.WARNING: 2,
            MonitorLevel.ERROR: 3,
        }

        with self._lock:
            min_level = level_order[level]
            self._enabled_levels = {
                lvl for lvl, order in level_order.items() if order >= min_level
            }

    def enable_all(self) -> None:
        """启用所有监控"""
        with self._lock:
            self._enabled_categories = set(MonitorCategory)
            self._enabled_levels = set(MonitorLevel)

    def disable_all(self) -> None:
        """禁用所有监控"""
        with self._lock:
            self._enabled_categories.clear()

    def is_enabled(self, category: MonitorCategory, level: MonitorLevel) -> bool:
        """检查是否启用了指定的监控"""
        with self._lock:
            return (
                category in self._enabled_categories and level in self._enabled_levels
            )

    def add_handler(self, handler: Callable[[MonitorEvent], None]) -> None:
        """添加事件处理器"""
        with self._lock:
            self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[MonitorEvent], None]) -> None:
        """移除事件处理器"""
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def add_filter(self, filter_func: Callable[[MonitorEvent], bool]) -> None:
        """添加事件过滤器（返回True表示通过）"""
        with self._lock:
            self._filters.append(filter_func)

    def log_event(
        self,
        category: MonitorCategory,
        level: MonitorLevel,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> None:
        """记录监控事件"""
        if not self.is_enabled(category, level):
            return

        event = MonitorEvent(category, level, message, data, source)

        # 应用过滤器
        with self._lock:
            for filter_func in self._filters:
                try:
                    if not filter_func(event):
                        return
                except Exception:
                    pass  # 过滤器错误不应影响监控

        # 添加到历史记录
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # 调用处理器
        with self._lock:
            handlers = self._handlers.copy()

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # 处理器错误不应影响监控
                pass

    def _console_handler(self, event: MonitorEvent) -> None:
        """控制台输出处理器"""
        print(f"{event}")
        if event.data and event.level in [MonitorLevel.DEBUG, MonitorLevel.ERROR]:
            try:
                data_str = json.dumps(event.data, indent=2, ensure_ascii=False)
                print(f"  Data: {data_str}")
            except Exception:
                print(f"  Data: {event.data}")

    def get_history(
        self,
        category: Optional[MonitorCategory] = None,
        level: Optional[MonitorLevel] = None,
        limit: Optional[int] = None,
    ) -> List[MonitorEvent]:
        """获取历史记录"""
        with self._lock:
            events = self._event_history.copy()

        if category:
            events = [e for e in events if e.category == category]
        if level:
            events = [e for e in events if e.level == level]

        if limit:
            events = events[-limit:]

        return events

    def clear_history(self) -> None:
        """清空历史记录"""
        with self._lock:
            self._event_history.clear()

    def export_history(self, file_path: str) -> None:
        """导出历史记录到文件"""
        with self._lock:
            events = [event.to_dict() for event in self._event_history]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)

    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        with self._lock:
            return {
                "enabled_categories": [cat.value for cat in self._enabled_categories],
                "enabled_levels": [level.value for level in self._enabled_levels],
                "handlers_count": len(self._handlers),
                "filters_count": len(self._filters),
                "history_count": len(self._event_history),
                "max_history": self._max_history,
            }

    # 便捷方法
    def log_model_interaction(
        self,
        message: str,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None,
        model_id: Optional[str] = None,
        level: MonitorLevel = MonitorLevel.DEBUG,
    ) -> None:
        """记录模型交互"""
        data = {}
        if request_data:
            data["request"] = request_data
        if response_data:
            data["response"] = response_data
        if model_id:
            data["model_id"] = model_id

        self.log_event(MonitorCategory.MODEL_INTERACTION, level, message, data)

    def log_tool_call(
        self,
        tool_name: str,
        arguments: Optional[Dict] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        level: MonitorLevel = MonitorLevel.INFO,
    ) -> None:
        """记录工具调用"""
        data = {"tool_name": tool_name}
        if arguments:
            data["arguments"] = arguments
        if result is not None:
            data["result"] = result
        if error:
            data["error"] = error
            level = MonitorLevel.ERROR

        message = f"Tool call: {tool_name}"
        if error:
            message += f" (ERROR: {error})"

        self.log_event(MonitorCategory.TOOL_CALLS, level, message, data)

    def log_context_update(
        self,
        operation: str,
        context_size: Optional[int] = None,
        details: Optional[Dict] = None,
        level: MonitorLevel = MonitorLevel.DEBUG,
    ) -> None:
        """记录上下文更新"""
        data = {"operation": operation}
        if context_size is not None:
            data["context_size"] = context_size
        if details:
            data.update(details)

        self.log_event(
            MonitorCategory.CONTEXT_MANAGEMENT, level, f"Context {operation}", data
        )

    def log_data_transform(
        self,
        transform_type: str,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        level: MonitorLevel = MonitorLevel.DEBUG,
    ) -> None:
        """记录数据转换"""
        data = {"transform_type": transform_type}
        if input_data is not None:
            data["input"] = input_data
        if output_data is not None:
            data["output"] = output_data

        self.log_event(
            MonitorCategory.DATA_TRANSFORM,
            level,
            f"Data transform: {transform_type}",
            data,
        )

    def log_performance(
        self,
        operation: str,
        duration: float,
        details: Optional[Dict] = None,
        level: MonitorLevel = MonitorLevel.INFO,
    ) -> None:
        """记录性能数据"""
        data = {"operation": operation, "duration": duration}
        if details:
            data.update(details)

        # 更新性能统计
        with self._lock:
            if operation not in self._performance_stats:
                self._performance_stats[operation] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float("inf"),
                    "max_time": 0,
                    "avg_time": 0,
                }

            stats = self._performance_stats[operation]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["min_time"] = min(stats["min_time"], duration)
            stats["max_time"] = max(stats["max_time"], duration)
            stats["avg_time"] = stats["total_time"] / stats["count"]

        self.log_event(
            MonitorCategory.PERFORMANCE,
            level,
            f"Performance: {operation} took {duration:.3f}s",
            data,
        )

    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计"""
        with self._lock:
            return self._performance_stats.copy()

    def monitor_function(
        self,
        category: MonitorCategory = MonitorCategory.PERFORMANCE,
        level: MonitorLevel = MonitorLevel.INFO,
        log_args: bool = False,
        log_result: bool = False,
    ):
        """函数监控装饰器"""

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_name = f"{func.__module__}.{func.__qualname__}"
                start_time = time.time()

                # 记录函数调用开始
                data = {"function": func_name}
                if log_args:
                    try:
                        # 获取参数信息
                        sig = inspect.signature(func)
                        bound_args = sig.bind(*args, **kwargs)
                        bound_args.apply_defaults()
                        data["arguments"] = dict(bound_args.arguments)
                    except Exception:
                        data["arguments"] = {"args": args, "kwargs": kwargs}

                self.log_event(
                    category,
                    MonitorLevel.DEBUG,
                    f"Function call started: {func_name}",
                    data,
                )

                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    # 记录成功结果
                    result_data = {"function": func_name, "duration": duration}
                    if log_result:
                        result_data["result"] = result

                    self.log_event(
                        category,
                        level,
                        f"Function completed: {func_name} ({duration:.3f}s)",
                        result_data,
                    )

                    # 记录性能数据
                    if category == MonitorCategory.PERFORMANCE:
                        self.log_performance(func_name, duration)

                    return result

                except Exception as e:
                    duration = time.time() - start_time

                    # 记录错误
                    error_data = {
                        "function": func_name,
                        "duration": duration,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }

                    self.log_event(
                        MonitorCategory.ERROR_TRACKING,
                        MonitorLevel.ERROR,
                        f"Function error: {func_name} - {e}",
                        error_data,
                    )

                    raise

            return wrapper

        return decorator


# 全局监控器实例
_global_monitor = MLMonitor()


def get_monitor() -> MLMonitor:
    """获取全局监控器实例"""
    return _global_monitor


def enable_monitoring(*categories: MonitorCategory) -> None:
    """快速启用监控分类"""
    if not categories:
        get_monitor().enable_all()
    else:
        get_monitor().enable_categories(list(categories))


def disable_monitoring(*categories: MonitorCategory) -> None:
    """快速禁用监控分类"""
    if not categories:
        get_monitor().disable_all()
    else:
        get_monitor().disable_categories(list(categories))


def set_monitor_level(level: MonitorLevel) -> None:
    """设置监控级别"""
    get_monitor().set_level(level)


def log_event(
    category: MonitorCategory,
    level: MonitorLevel,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
) -> None:
    """记录监控事件"""
    get_monitor().log_event(category, level, message, data, source)


# 便捷函数
def log_model_interaction(message: str, **kwargs) -> None:
    """记录模型交互"""
    get_monitor().log_model_interaction(message, **kwargs)


def log_tool_call(tool_name: str, **kwargs) -> None:
    """记录工具调用"""
    get_monitor().log_tool_call(tool_name, **kwargs)


def log_context_update(operation: str, **kwargs) -> None:
    """记录上下文更新"""
    get_monitor().log_context_update(operation, **kwargs)


def log_data_transform(transform_type: str, **kwargs) -> None:
    """记录数据转换"""
    get_monitor().log_data_transform(transform_type, **kwargs)


def monitor_performance(func=None, **kwargs):
    """性能监控装饰器"""
    if func is None:
        return lambda f: get_monitor().monitor_function(**kwargs)(f)
    return get_monitor().monitor_function()(func)


# 上下文管理器
class MonitorContext:
    """监控上下文管理器"""

    def __init__(
        self,
        category: MonitorCategory,
        operation: str,
        level: MonitorLevel = MonitorLevel.INFO,
        log_data: bool = True,
    ):
        self.category = category
        self.operation = operation
        self.level = level
        self.log_data = log_data
        self.start_time = None
        self.data = {}

    def __enter__(self):
        self.start_time = time.time()
        get_monitor().log_event(
            self.category,
            MonitorLevel.DEBUG,
            f"Started: {self.operation}",
            {"operation": self.operation},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.data["duration"] = duration

        if exc_type is None:
            # 成功完成
            get_monitor().log_event(
                self.category,
                self.level,
                f"Completed: {self.operation} ({duration:.3f}s)",
                (
                    self.data
                    if self.log_data
                    else {"operation": self.operation, "duration": duration}
                ),
            )
        else:
            # 发生错误
            error_data = self.data.copy()
            error_data.update({"error": str(exc_val), "error_type": exc_type.__name__})
            get_monitor().log_event(
                MonitorCategory.ERROR_TRACKING,
                MonitorLevel.ERROR,
                f"Failed: {self.operation} - {exc_val}",
                (
                    error_data
                    if self.log_data
                    else {"operation": self.operation, "error": str(exc_val)}
                ),
            )

    def add_data(self, key: str, value: Any) -> None:
        """添加数据到监控上下文"""
        self.data[key] = value


def monitor_context(
    category: MonitorCategory,
    operation: str,
    level: MonitorLevel = MonitorLevel.INFO,
    log_data: bool = True,
) -> MonitorContext:
    """创建监控上下文"""
    return MonitorContext(category, operation, level, log_data)
