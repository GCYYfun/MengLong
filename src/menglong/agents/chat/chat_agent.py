import asyncio

from menglong.agents.agent import Agent
from menglong.agents.component.tool_manager import ToolManager
from .task import Task, TaskContext, TaskScheduler, TaskManager
from menglong.ml_model.schema.ml_request import SystemMessage as system


class ChatAgent(Agent):
    """
    ChatAgent - 用于处理聊天交互的代理
    """

    def __init__(self, model_id: str = None):
        super().__init__(model_id)
        self.tool_manager = ToolManager()
        self.task_context = TaskContext()

        self.memory = {}

        # Task
        self.task_manager = TaskManager(self)
        self.task_scheduler = TaskScheduler(self.task_manager)

    @property
    def system(self) -> str:
        """
        系统提示词
        :return: 系统提示词
        """
        return (
            self.task_context.message_context[0].get("content", "")
            if self.task_context.message_context
            else ""
        )

    @system.setter
    def system(self, value: str):
        """
        设置系统提示词
        :param value: 系统提示词
        """
        self.task_context.system = value
        if len(self.task_context.message_context) == 0 or not isinstance(
            self.task_context.message_context[0], system
        ):
            self.task_context.message_context.insert(0, system(content=value))
        else:
            self.task_context.message_context[0].content = value

    async def chat(self, task: str, tools: list = None) -> str:
        """
        聊天方法，处理用户输入并返回响应
        :param task: 用户输入的任务描述
        :param tools: 可用工具列表
        :return: 生成的响应
        """
        self.task_manager.create_task(prompt=task, tools=tools)

        # 启动调度器并等待完成
        scheduler_task = asyncio.create_task(self.task_scheduler.scheduler_loop())

        try:
            await scheduler_task
        except Exception as e:
            print(f"Scheduler error: {e}")
        finally:
            await self.task_scheduler.shutdown()

        return "Task execution completed"

    async def run(self, task: str, tools: list = None) -> str:
        """
        执行任务
        :param task: 任务描述
        :param tools: 可用工具列表
        :return: 任务执行结果
        """
        pass
