import time
from logging import getLogger
from typing import List, Optional
from mlong.tools import Tool


logger = getLogger(__name__)


class RecursionAgent:

    def __init__(
        self,
        tools: List[Tool],
        model_id: Optional[str],
    ):
        self.agent_name = self.__class__.__name__
        self.memory = []
        self.logger = None
        self.monitor = None

    def step(self):
        pass

    def run(
        self,
        task: str,
        stream=False,
        max_step: Optional[int] = None,
    ):
        """
        执行给定的任务
        Args:
            task: 任务描述
            stream: 是否使用流式输出
            max_step: 最大执行步数
        """
        # 初始化任务
        self.task = task
        max_step = max_step or self.max_step

        self.system_prompt = "This is the system prompt."
        self.memory.append(self.system_prompt)

        self.logger.info(f"Running task: {task}")

        if stream:
            self.logger.info("Streaming output enabled.")
            return self._run_stream(task, max_step)
        else:
            self.logger.info("Streaming output disabled.")
            return self._run(task, max_step)

    def _run_stream(self, task: str, max_step: Optional[int] = None):
        """
        执行给定的任务，使用流式输出
        Args:
            task: 任务描述
        """
        result = None
        self.step_count = 1
        while result is None and self.step_count < max_step:
            step_start_time = time.time()

            # base task gen planning
            planning_step = self.planning_step(task)

            # base planning gen action
            action_step = self.generate_action_step()

            # execute action
            result = self.execute_action(task, action_step)
            yield action_step
            self.step_count += 1
        yield result

    def _run(self, task: str, max_step: Optional[int] = None):
        """
        执行给定的任务
        Args:
            task: 任务描述
        """

        pass

    def planning_step(self, task: str):
        pass

    # === visualization ===
    def visualize(self):
        pass
