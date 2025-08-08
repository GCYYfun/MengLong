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

        # Control state
        self._is_running = False
        self._current_scheduler_task = None

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

    async def raw_chat(self, messages: list) -> str:
        """
        处理原始聊天消息
        :param messages: 消息列表
        :return: 生成的响应
        """
        res = self.model.chat(messages)
        return res.message.content.text

    async def chat(self, task: str, tools: list = None, auto_end: bool = False) -> str:
        """
        聊天方法，处理用户输入并返回响应
        :param task: 用户输入的任务描述
        :param tools: 可用工具列表
        :return: 生成的响应
        """
        if self._is_running:
            return "Agent is already running. Please stop the current task first."

        self._is_running = True

        try:
            self.task_manager.create_task(prompt=task, tools=tools)

            # 启动调度器并等待完成
            self._current_scheduler_task = asyncio.create_task(
                self.task_scheduler.scheduler_loop(auto_end=auto_end)
            )

            await self._current_scheduler_task
            return "Task execution completed"

        except asyncio.CancelledError:
            return "Task execution was stopped"
        except Exception as e:
            return f"Task execution failed: {e}"
        finally:
            self._is_running = False
            self._current_scheduler_task = None
            await self.task_scheduler.shutdown()

    async def run(self, task: str, tools: list = None) -> str:
        """
        执行任务
        :param task: 任务描述
        :param tools: 可用工具列表
        :return: 任务执行结果
        """
        return await self.chat(task, tools)

    async def stop(self) -> str:
        """
        停止当前正在运行的任务和调度器
        :return: 停止状态信息
        """
        if not self._is_running:
            return "No task is currently running"

        try:
            # 停止调度器
            if self._current_scheduler_task and not self._current_scheduler_task.done():
                self._current_scheduler_task.cancel()

            # 停止任务调度器
            await self.task_scheduler.shutdown()

            self._is_running = False
            self._current_scheduler_task = None

            return "Agent stopped successfully"

        except Exception as e:
            return f"Error stopping agent: {e}"

    def is_running(self) -> bool:
        """
        检查代理是否正在运行
        :return: 运行状态
        """
        return self._is_running

    async def force_stop(self) -> str:
        """
        强制停止所有任务和调度器
        :return: 停止状态信息
        """
        try:
            # 强制停止调度器
            if self._current_scheduler_task:
                self._current_scheduler_task.cancel()
                try:
                    await self._current_scheduler_task
                except asyncio.CancelledError:
                    pass

            # 强制关闭任务调度器
            await self.task_scheduler.shutdown()

            # 重置状态
            self._is_running = False
            self._current_scheduler_task = None

            # 清理任务管理器状态
            self.task_manager.task_descriptions.clear()
            self.task_manager.tasks.clear()
            self.task_manager.root_task = None

            return "Agent force stopped and reset successfully"

        except Exception as e:
            # 即使出错也要重置状态
            self._is_running = False
            self._current_scheduler_task = None
            return f"Agent force stopped with errors: {e}"
