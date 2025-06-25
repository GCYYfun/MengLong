import asyncio
from task_agent import ChatAgent
from tool import terminal_command, plan_task, brave_web_search


async def chat_with_terminal():
    agent = ChatAgent()
    complex_task = """
    9.11 与 9.8 哪个大？,可以用工具来辅助
    """
    tools = [plan_task, brave_web_search, terminal_command]
    res = await agent.chat(complex_task, tools)  # 添加 await
    await asyncio.sleep(0)  # 模拟异步等待
    return res


# async def run_with_terminal():
#     agent = ChatAgent()
#     task = "请执行以下命令：ls -l"
#     tools = [terminal_command]
#     res = agent.run(task, tools)
#     return res


async def main():

    await chat_with_terminal()

    # await run_with_terminal()


if __name__ == "__main__":
    asyncio.run(main())
