"""
简化聊天代理使用示例

这个文件展示了如何使用新的模块化聊天代理组件
"""

from menglong.agents.chat import SimpleChatAgent, ChatMode, tool


# 示例1：定义工具
@tool(description="获取天气信息")
def get_weather(location: str, unit: str = "celsius"):
    """获取指定位置的天气信息"""
    return {
        "location": location,
        "temperature": 22,
        "unit": unit,
        "description": "晴朗",
    }


@tool(description="计算数学表达式")
def calculate(expression: str):
    """安全计算数学表达式"""
    try:
        # 简单的数学表达式计算（生产环境需要更安全的实现）
        allowed_chars = "0123456789+-*/.() "
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"{expression} = {result}"
        else:
            return "表达式包含不允许的字符"
    except Exception as e:
        return f"计算错误: {str(e)}"


def example_normal_chat():
    """示例：普通聊天模式"""
    print("=== 普通聊天模式示例 ===")

    agent = SimpleChatAgent(mode=ChatMode.NORMAL, system="你是一个友善的助手")

    response = agent.chat("你好，介绍一下自己")
    print(f"Agent: {response}")


def example_auto_chat():
    """示例：自动模式（带工具）"""
    print("\n=== 自动模式示例 ===")

    agent = SimpleChatAgent(
        mode=ChatMode.AUTO, system="你是一个智能助手，可以使用工具来回答问题"
    )

    # 注册全局工具（由@tool装饰器自动注册的）
    agent.register_global_tools()

    response = agent.chat("今天北京的天气怎么样？")
    print(f"Agent: {response}")

    response = agent.chat("帮我计算 15 * 23 + 7")
    print(f"Agent: {response}")


async def example_async_chat():
    """示例：异步聊天"""
    print("\n=== 异步聊天示例 ===")

    agent = SimpleChatAgent(mode=ChatMode.AUTO, system="你是一个异步智能助手")

    agent.register_global_tools()

    response = await agent.chat_async("上海的天气如何？")
    print(f"Agent: {response}")


def example_workflow():
    """示例：工作流模式"""
    print("\n=== 工作流模式示例 ===")

    agent = SimpleChatAgent(mode=ChatMode.WORKFLOW, system="你是一个工作流执行助手")

    # 定义工作流步骤
    def step1(input_msg, context):
        return f"步骤1完成：分析输入 '{input_msg}'"

    def step2(input_msg, context):
        return f"步骤2完成：处理数据"

    def step3(input_msg, context):
        return f"步骤3完成：生成结果"

    # 添加工作流步骤
    agent.add_workflow_step("分析", step1)
    agent.add_workflow_step("处理", step2)
    agent.add_workflow_step("生成", step3)

    response = agent.chat("请执行我的工作流")
    print(f"Workflow result: {response}")

    # 查看工作流状态
    status = agent.get_workflow_status()
    print(f"Workflow status:\n{status}")


async def example_autonomous_execution():
    """示例：自主任务执行"""
    print("\n=== 自主任务执行示例 ===")

    agent = SimpleChatAgent(mode=ChatMode.AUTO, system="你是一个自主任务执行助手")

    agent.register_global_tools()

    # 执行自主任务（这里使用简单任务作为示例）
    task = "帮我分析一下北京和上海的天气差异"
    result = await agent.arun(task, max_iterations=3)

    print(f"任务执行结果:")
    print(f"状态: {result['status']}")
    print(f"执行时间: {result['execution_time']:.2f}秒")
    print(f"迭代次数: {result['iterations']}")


def example_batch_processing():
    """示例：批量处理"""
    print("\n=== 批量处理示例 ===")

    agent = SimpleChatAgent(mode=ChatMode.AUTO, system="你是一个批量处理助手")

    agent.register_global_tools()

    messages = ["北京的天气怎么样？", "计算 10 + 20", "上海的气温是多少？"]

    import asyncio

    async def run_batch():
        # 并行批量处理
        results = await agent.batch_chat_async(messages)
        print("并行处理结果:")
        for i, result in enumerate(results):
            print(f"消息 {i+1}: {result}")

        # 顺序批量处理（保持上下文）
        results = await agent.sequential_chat_async(messages)
        print("\n顺序处理结果:")
        for i, result in enumerate(results):
            print(f"消息 {i+1}: {result}")

    asyncio.run(run_batch())


if __name__ == "__main__":
    import asyncio

    # 运行同步示例
    example_normal_chat()
    example_auto_chat()
    example_workflow()

    # 运行异步示例
    asyncio.run(example_async_chat())
    asyncio.run(example_autonomous_execution())

    # 运行批量处理示例
    example_batch_processing()
