"""
监控集成示例

展示如何在ChatAgent中集成监控功能来追踪模型交互、工具调用等数据。
"""

from menglong.monitor import (
    enable_monitoring,
    MonitorCategory,
    MonitorLevel,
    set_monitor_level,
    log_model_interaction,
    log_tool_call,
    log_context_update,
    monitor_context,
    get_monitor,
)


def integrate_monitoring_to_chat_agent():
    """演示如何集成监控到ChatAgent"""

    # 1. 启用需要的监控分类
    enable_monitoring(
        MonitorCategory.MODEL_INTERACTION,
        MonitorCategory.TOOL_CALLS,
        MonitorCategory.CONTEXT_MANAGEMENT,
        MonitorCategory.PERFORMANCE,
    )

    # 2. 设置监控级别
    set_monitor_level(MonitorLevel.DEBUG)

    print("监控已启用，可以在ChatAgent中添加以下代码：")

    # 在ChatAgent的chat方法中添加监控
    example_chat_method = '''
    def chat(self, message: str, **kwargs):
        """带监控的聊天方法示例"""
        from menglong.monitor import log_model_interaction, monitor_context
        
        with monitor_context(MonitorCategory.MODEL_INTERACTION, "chat_request") as ctx:
            # 添加请求数据到监控上下文
            ctx.add_data("user_message", message)
            ctx.add_data("model_id", self.model.model_id)
            
            # 记录原始请求数据
            request_data = {
                "messages": self.context.get_messages(),
                "model_config": kwargs
            }
            log_model_interaction(
                "Sending request to model",
                request_data=request_data,
                model_id=self.model.model_id
            )
            
            # 调用模型
            response = self.model.chat(messages=self.context.get_messages(), **kwargs)
            
            # 记录响应数据
            log_model_interaction(
                "Received response from model", 
                response_data=response.dict() if hasattr(response, 'dict') else response,
                model_id=self.model.model_id
            )
            
            # 添加响应数据到监控上下文
            ctx.add_data("response_content", getattr(response, 'content', str(response)))
            
            return response
    '''

    # 在工具调用中添加监控
    example_tool_call = '''
    def _execute_tool_call(self, tool_name: str, arguments: dict):
        """带监控的工具调用示例"""
        from menglong.monitor import log_tool_call
        
        try:
            # 记录工具调用开始
            log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                level=MonitorLevel.INFO
            )
            
            # 执行工具
            tool_func = self.tools[tool_name]["function"]
            result = tool_func(**arguments)
            
            # 记录成功结果
            log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                level=MonitorLevel.INFO
            )
            
            return result
            
        except Exception as e:
            # 记录错误
            log_tool_call(
                tool_name=tool_name,
                arguments=arguments,
                error=str(e),
                level=MonitorLevel.ERROR
            )
            raise
    '''

    print("示例聊天方法代码：")
    print(example_chat_method)
    print("\n示例工具调用代码：")
    print(example_tool_call)


def demonstrate_monitoring_usage():
    """演示监控功能的使用"""

    print("=== 监控功能演示 ===\n")

    # 启用监控
    enable_monitoring(MonitorCategory.MODEL_INTERACTION, MonitorCategory.TOOL_CALLS)
    set_monitor_level(MonitorLevel.DEBUG)

    # 模拟模型交互
    log_model_interaction(
        "模拟模型请求",
        request_data={
            "messages": [{"role": "user", "content": "你好"}],
            "model": "gpt-4",
            "temperature": 0.7,
        },
        model_id="gpt-4",
    )

    log_model_interaction(
        "模拟模型响应",
        response_data={
            "content": "你好！我是AI助手，有什么可以帮助您的吗？",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        },
        model_id="gpt-4",
    )

    # 模拟工具调用
    log_tool_call(
        tool_name="get_weather",
        arguments={"city": "北京"},
        result={"temperature": 20, "weather": "晴天"},
        level=MonitorLevel.INFO,
    )

    # 模拟工具调用错误
    log_tool_call(
        tool_name="invalid_tool",
        arguments={"param": "value"},
        error="工具不存在",
        level=MonitorLevel.ERROR,
    )

    # 使用上下文管理器
    with monitor_context(MonitorCategory.TOOL_CALLS, "批量处理") as ctx:
        ctx.add_data("batch_size", 10)
        # 模拟一些处理
        import time

        time.sleep(0.1)
        ctx.add_data("processed_items", 10)

    # 查看监控状态
    monitor = get_monitor()
    print(f"\n监控状态: {monitor.get_status()}")

    # 查看最近的事件
    recent_events = monitor.get_history(limit=5)
    print(f"\n最近 {len(recent_events)} 个事件:")
    for event in recent_events:
        print(f"  {event}")


def create_file_handler_example():
    """创建文件输出处理器示例"""

    def file_handler(event):
        """将监控事件写入文件"""
        import json
        from pathlib import Path

        log_dir = Path("./monitor_logs")
        log_dir.mkdir(exist_ok=True)

        # 按分类创建不同的日志文件
        log_file = log_dir / f"{event.category.value}.log"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    # 添加文件处理器
    monitor = get_monitor()
    monitor.add_handler(file_handler)

    print("已添加文件处理器，监控日志将保存到 ./monitor_logs/ 目录")


def demonstrate_selective_monitoring():
    """演示选择性监控"""

    print("=== 选择性监控演示 ===\n")

    monitor = get_monitor()

    # 清空之前的状态
    monitor.disable_all()

    print("1. 只监控模型交互...")
    monitor.enable_category(MonitorCategory.MODEL_INTERACTION)

    log_model_interaction("这条会显示", model_id="test")
    log_tool_call(tool_name="test")

    print("\n2. 添加工具调用监控...")
    monitor.enable_category(MonitorCategory.TOOL_CALLS)

    log_model_interaction("这条会显示", model_id="test")
    log_tool_call(tool_name="test")

    print("\n3. 设置只显示ERROR级别...")
    monitor.set_level(MonitorLevel.ERROR)

    log_model_interaction(
        "这条不会显示 (INFO)", level=MonitorLevel.INFO, model_id="test"
    )
    log_model_interaction(
        "这条会显示 (ERROR)", level=MonitorLevel.ERROR, model_id="test"
    )

    print("\n4. 恢复所有监控...")
    monitor.enable_all()
    monitor.set_level(MonitorLevel.DEBUG)


if __name__ == "__main__":
    print("MengLong 监控模块示例\n")

    # 基础使用演示
    demonstrate_monitoring_usage()

    print("\n" + "=" * 50 + "\n")

    # 选择性监控演示
    demonstrate_selective_monitoring()

    print("\n" + "=" * 50 + "\n")

    # ChatAgent集成说明
    integrate_monitoring_to_chat_agent()

    print("\n" + "=" * 50 + "\n")

    # 文件处理器示例
    create_file_handler_example()
