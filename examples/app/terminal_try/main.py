import asyncio
from task_agent import ChatAgent
from tool import (
    terminal_command,
    plan_task,
    brave_web_search,
    recall_experience,
    summarize_and_save_experience,
    abstract_experience,
)


async def chat_with_terminal():
    agent = ChatAgent()
    complex_task = """
    统计下当前目录下src/menglong目录下的python文件数、函数数量、代码行数。
    如果做过参考经验获得更好的结果，
    如果运行成果总结下经验
    """
    # complex_task = """
    # 对经验库抽象与反思下。
    # """
    tools = [
        plan_task,
        # brave_web_search,
        terminal_command,
        recall_experience,
        summarize_and_save_experience,
        abstract_experience,
    ]
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
