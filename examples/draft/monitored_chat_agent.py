"""
集成监控功能的ChatAgent示例

这个示例展示了如何在现有的ChatAgent中集成监控功能，
以便在排查问题时查看详细的verbose数据。
"""

import time
from typing import Dict, Any, Optional
from menglong.agents.chat import SimpleChatAgent, ChatMode
from menglong.monitor import (
    enable_monitoring,
    MonitorCategory,
    MonitorLevel,
    set_monitor_level,
    log_model_interaction,
    log_tool_call,
    log_context_update,
    log_data_transform,
    monitor_context,
    monitor_performance,
    get_monitor,
)


class MonitoredChatAgent(SimpleChatAgent):
    """集成了监控功能的ChatAgent"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 启用默认监控
        self._setup_default_monitoring()

    def _setup_default_monitoring(self):
        """设置默认监控配置"""
        # 可以通过环境变量或配置文件控制
        enable_monitoring(
            MonitorCategory.MODEL_INTERACTION,
            MonitorCategory.TOOL_CALLS,
            MonitorCategory.CONTEXT_MANAGEMENT,
            MonitorCategory.PERFORMANCE,
        )
        set_monitor_level(MonitorLevel.INFO)

    @monitor_performance
    def chat(self, message: str, **kwargs) -> Any:
        """带监控的聊天方法"""

        with monitor_context(MonitorCategory.MODEL_INTERACTION, "chat_session") as ctx:
            # 记录输入信息
            ctx.add_data("user_message", message)
            ctx.add_data("model_id", getattr(self.model, "model_id", "unknown"))

            # 更新上下文
            log_context_update(
                "add_user_message",
                context_size=len(self.context.messages),
                details={"message_length": len(message)},
            )

            # 准备请求数据
            messages = self.context.get_messages()
            request_data = {
                "messages": [
                    msg.dict() if hasattr(msg, "dict") else msg for msg in messages
                ],
                "model_config": kwargs,
                "context_length": len(messages),
            }

            # 记录模型交互开始
            log_model_interaction(
                "发送请求到模型",
                request_data=request_data,
                model_id=getattr(self.model, "model_id", "unknown"),
                level=MonitorLevel.DEBUG,
            )

            try:
                # 调用父类方法
                response = super().chat(message, **kwargs)

                # 记录成功响应
                response_data = {
                    "content": getattr(response, "content", str(response)),
                    "response_type": type(response).__name__,
                }

                log_model_interaction(
                    "收到模型响应",
                    response_data=response_data,
                    model_id=getattr(self.model, "model_id", "unknown"),
                    level=MonitorLevel.INFO,
                )

                # 更新上下文监控
                log_context_update(
                    "add_assistant_message",
                    context_size=len(self.context.messages),
                    details={"response_length": len(str(response))},
                )

                ctx.add_data(
                    "response_content", str(response)[:200]
                )  # 截取前200字符避免过长

                return response

            except Exception as e:
                # 记录错误
                log_model_interaction(
                    "模型调用失败",
                    model_id=getattr(self.model, "model_id", "unknown"),
                    level=MonitorLevel.ERROR,
                )
                ctx.add_data("error", str(e))
                raise

    def register_tool(
        self, name: str, func: callable, description: str = None, **kwargs
    ):
        """带监控的工具注册"""

        log_context_update(
            "register_tool",
            details={
                "tool_name": name,
                "description": description,
                "function": func.__name__ if hasattr(func, "__name__") else str(func),
            },
        )

        # 包装工具函数以添加监控
        original_func = func

        def monitored_tool(*args, **kwargs):
            """监控工具调用的包装器"""
            with monitor_context(MonitorCategory.TOOL_CALLS, f"tool_{name}") as ctx:
                ctx.add_data("tool_name", name)
                ctx.add_data("arguments", {"args": args, "kwargs": kwargs})

                try:
                    result = original_func(*args, **kwargs)

                    log_tool_call(
                        tool_name=name,
                        arguments=kwargs,
                        result=result,
                        level=MonitorLevel.INFO,
                    )

                    ctx.add_data("result", result)
                    return result

                except Exception as e:
                    log_tool_call(
                        tool_name=name,
                        arguments=kwargs,
                        error=str(e),
                        level=MonitorLevel.ERROR,
                    )
                    ctx.add_data("error", str(e))
                    raise

        # 保持原函数的元数据
        monitored_tool.__name__ = getattr(original_func, "__name__", name)
        monitored_tool.__doc__ = getattr(original_func, "__doc__", description)

        # 调用父类方法注册监控后的工具
        return super().register_tool(name, monitored_tool, description, **kwargs)


def demonstrate_monitored_chat():
    """演示监控功能的ChatAgent"""

    print("=== 监控式ChatAgent演示 ===\n")

    # 创建监控式代理
    agent = MonitoredChatAgent(system="你是一个带监控功能的AI助手")

    # 注册一些示例工具
    def get_weather(city: str) -> dict:
        """获取天气信息"""
        time.sleep(0.1)  # 模拟网络请求
        return {"city": city, "temperature": 20, "weather": "晴天", "humidity": "60%"}

    def calculate(expression: str) -> float:
        """计算数学表达式"""
        try:
            # 简单的安全计算
            result = eval(expression)
            return result
        except Exception as e:
            raise ValueError(f"无法计算表达式: {expression}")

    # 注册工具（会自动添加监控）
    agent.register_tool("get_weather", get_weather, "获取城市天气信息")
    agent.register_tool("calculate", calculate, "计算数学表达式")

    print("工具注册完成，开始对话测试...\n")

    # 模拟一些对话
    test_messages = ["你好！", "北京今天天气怎么样？", "计算 2 + 3 * 4", "再见！"]

    for i, message in enumerate(test_messages, 1):
        print(f"用户 {i}: {message}")
        try:
            # 这里实际上不会调用真实模型，仅用于演示监控
            print(f"助手 {i}: [模拟响应] 收到您的消息: {message}")

            # 手动触发一些监控事件来演示
            if "天气" in message:
                get_weather("北京")  # 触发工具调用监控
            elif "计算" in message:
                calculate("2 + 3 * 4")  # 触发工具调用监控

        except Exception as e:
            print(f"错误: {e}")

        print()

    # 显示监控统计
    monitor = get_monitor()
    print("=== 监控统计 ===")
    print(f"监控状态: {monitor.get_status()}")

    # 显示最近的事件
    print("\n=== 最近的监控事件 ===")
    recent_events = monitor.get_history(limit=10)
    for event in recent_events:
        print(
            f"[{event.timestamp.strftime('%H:%M:%S')}] {event.category.value}: {event.message}"
        )


def demonstrate_selective_monitoring():
    """演示选择性监控功能"""

    print("=== 选择性监控演示 ===\n")

    monitor = get_monitor()

    # 场景1: 只监控工具调用
    print("场景1: 只监控工具调用")
    monitor.disable_all()
    monitor.enable_category(MonitorCategory.TOOL_CALLS)

    agent = MonitoredChatAgent()

    def test_tool():
        return "工具执行结果"

    agent.register_tool("test_tool", test_tool)
    test_tool()  # 这个会被监控

    log_model_interaction("这个不会被监控", model_id="test")

    print()

    # 场景2: 只监控错误
    print("场景2: 只监控错误级别")
    monitor.enable_all()
    monitor.set_level(MonitorLevel.ERROR)

    log_model_interaction(
        "这个不会显示 (INFO)", level=MonitorLevel.INFO, model_id="test"
    )
    log_tool_call("test_tool", error="这个会显示 (ERROR)")

    print()

    # 场景3: 性能监控
    print("场景3: 性能监控")
    monitor.set_level(MonitorLevel.INFO)
    monitor.enable_category(MonitorCategory.PERFORMANCE)

    @monitor_performance
    def slow_function():
        time.sleep(0.1)
        return "完成"

    slow_function()

    # 显示性能统计
    stats = monitor.get_performance_stats()
    print(f"性能统计: {stats}")


def demonstrate_custom_handlers():
    """演示自定义处理器"""

    print("=== 自定义处理器演示 ===\n")

    monitor = get_monitor()

    # 创建一个简单的统计处理器
    class StatisticsHandler:
        def __init__(self):
            self.event_counts = {}
            self.error_count = 0

        def __call__(self, event):
            # 统计事件数量
            category = event.category.value
            self.event_counts[category] = self.event_counts.get(category, 0) + 1

            if event.level == MonitorLevel.ERROR:
                self.error_count += 1

        def get_stats(self):
            return {
                "event_counts": self.event_counts,
                "error_count": self.error_count,
                "total_events": sum(self.event_counts.values()),
            }

    # 添加统计处理器
    stats_handler = StatisticsHandler()
    monitor.add_handler(stats_handler)

    # 生成一些事件
    log_model_interaction("测试事件1", model_id="test")
    log_tool_call("tool1", arguments={"arg": "value"})
    log_tool_call("tool2", error="测试错误")
    log_context_update("test_operation")

    # 显示统计
    print(f"事件统计: {stats_handler.get_stats()}")


if __name__ == "__main__":
    print("MengLong 监控集成示例\n")

    # 基础监控演示
    demonstrate_monitored_chat()

    print("\n" + "=" * 60 + "\n")

    # 选择性监控演示
    demonstrate_selective_monitoring()

    print("\n" + "=" * 60 + "\n")

    # 自定义处理器演示
    demonstrate_custom_handlers()
