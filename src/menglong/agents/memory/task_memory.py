from typing import List, Optional, Union


class Step:
    pass


class TaskStep(Step):
    pass


class ActionStep(Step):
    pass


class PlanningStep(Step):
    pass


class ResultStep(Step):
    pass


class ObservationStep(Step):
    pass


# What - How - Why
# Chain 1
# 任务 --(观察)--> 目标 --(规划)--> 动作 --(执行)--> 结果 --(评估)--> 结论
# Chain 2
# 目的 --(量化)--> 目标 --(规划)--> 任务 --(决策)--> 动作 --(执行)--> 结果 --(评估)--> 结论


class TaskMemory:
    def __init__(self):
        self.system_prompt: str = ""
        self.step_trajectory: List[
            Union[TaskStep, ActionStep, PlanningStep, ResultStep, ObservationStep]
        ] = []

    def reset(self):
        self.step_trajectory = []
