from typing import List, Optional
from logging import getLogger
import time

from .agent import Agent
from .memory.task_memory import TaskMemory, TaskStep


class EnvAgent(Agent):
    def __init__(
        self,
        tools: List[Tool],
        prompt_templates: str,
        model_id: str = None,
        max_steps: int = 10,
    ):
        """
        Initialize the EnvAgent with a list of tools.

        Args:
            tools (List[Tool]): A list of tools that the agent can use.
            prompt_templates (str): A prompt template for the agent.
            model_id (str, optional): An optional identifier for the model.
            max_steps (int, optional): Maximum number of steps for the agent to take.
        """
        super().__init__()
        self.tools = tools
        self.prompt_templates = prompt_templates
        self.model_id = model_id
        self.max_steps = max_steps

        self.logger = getLogger("EnvAgent")

    def step(self):
        # Get the current state of the environment
        state = self.env.get_state()

        # Use the agent to decide on an action based on the current state
        action = self.agent.act(state)

        # Take the action in the environment and get the next state and reward
        next_state, reward, done = self.env.step(action)

        # Return the next state, reward, and done flag
        return next_state, reward, done

    def run(
        self,
        task: str,
        stream: bool = False,
        reset: bool = True,
        max_steps: Optional[int] = None,
    ):
        max_steps = max_steps or self.max_steps
        self.task = task

        if reset:
            self.task_memory.reset()
            self.monitor.reset()

        self.logger.info(f"Running task: {task}")

        self.task_memory.steps.append(TaskStep(task=task))
        if stream:
            return self._run_stream(task, max_steps)
        return self._run(task, max_steps)

    def _run(self, task: str, max_steps: int):
        done = False
        self.step_index = 0
        while not done and self.step_index < max_steps:
            step_start_time = time.time()
            # Get the current state of the environment
            state = self.env.get_state()

            # Use the agent to decide on an action based on the current state
            action = self.plan(state)

            # Take the action in the environment and get the next state and reward
            next_state, reward, done = self.env.step(action)

            # Store the step in memory
            self.task_memory.steps.append(TaskStep(task=task))

            if done or len(self.task_memory.steps) >= max_steps:
                break

    def plan(self, state: str, first: bool = False):
        """
        Plan the next action based on the current state.
        """
        # 初次规划，进行目的确认
        if first:
            message = ""
            self.model.chat(messages=message, stop_sequences=["<end_plan>"])
            self.task_memory.steps.append(TaskStep(action="confirm"))
        else:
            self.task_memory.steps.append(TaskStep(action="plan"))
        # Use the agent to decide on an action based on the current state
        action = self.agent.act(state)

        # Store the action in memory
        self.task_memory.steps.append(TaskStep(action=action))

        return action
