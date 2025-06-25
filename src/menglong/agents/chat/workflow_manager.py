from typing import List, Dict, Any, Optional, Callable
import asyncio

from ...task.task_manager import AsyncTaskScheduler, TaskState


class WorkflowStep:
    """工作流步骤"""

    def __init__(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        self.name = name
        self.action = action
        self.condition = condition
        self.completed = False
        self.result = None


class WorkflowManager:
    """工作流管理器，负责工作流的定义和执行"""

    def __init__(self):
        self.workflow_steps = []  # 工作流步骤
        self.current_step = 0  # 当前执行的步骤
        self.task_scheduler = None  # 任务调度器

    def add_workflow_step(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        """添加工作流步骤"""
        step = WorkflowStep(name, action, condition)
        self.workflow_steps.append(step)
        return step

    async def add_workflow_step_async(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        """异步添加工作流步骤"""
        step = WorkflowStep(name, action, condition)
        self.workflow_steps.append(step)
        return step

    def execute_workflow(self, input_messages, context):
        """执行工作流（同步版本）"""
        if not self.workflow_steps:
            return "No workflow steps defined. Please add workflow steps first."

        results = []
        for i, step in enumerate(self.workflow_steps):
            if step.completed:
                results.append(f"Step {i+1}: {step.name} - Already completed")
                continue

            # 检查执行条件
            if step.condition and not step.condition():
                results.append(f"Step {i+1}: {step.name} - Condition not met")
                continue

            try:
                # 执行步骤
                step_result = step.action(input_messages, context)
                step.result = step_result
                step.completed = True
                results.append(f"Step {i+1} ({step.name}): {step_result}")

            except Exception as e:
                error_msg = f"Error in step {i+1} ({step.name}): {str(e)}"
                results.append(error_msg)
                return error_msg

        return "\n".join(results)

    async def execute_workflow_async(self, input_messages=None, context=None):
        """异步执行完整工作流"""
        if not self.workflow_steps:
            return "No workflow steps defined"

        results = []
        for i, step in enumerate(self.workflow_steps):
            if step.completed:
                results.append(f"Step {i+1}: {step.name} - Already completed")
                continue

            if step.condition and not await self._async_call_if_needed(step.condition):
                results.append(f"Step {i+1}: {step.name} - Condition not met")
                continue

            try:
                if asyncio.iscoroutinefunction(step.action):
                    result = await step.action(input_messages, context)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, step.action, input_messages, context
                    )

                step.result = result
                step.completed = True
                results.append(f"Step {i+1}: {step.name} - Completed: {result}")
            except Exception as e:
                results.append(f"Step {i+1}: {step.name} - Error: {str(e)}")

        return "\n".join(results)

    async def _async_call_if_needed(self, func, *args, **kwargs):
        """根据函数类型异步或同步调用"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)

    def reset_workflow(self):
        """重置工作流状态"""
        for step in self.workflow_steps:
            step.completed = False
            step.result = None
        self.current_step = 0

    def get_workflow_status(self):
        """获取工作流状态"""
        if not self.workflow_steps:
            return "No workflow steps defined"

        status = []
        for i, step in enumerate(self.workflow_steps):
            state = "✅ Completed" if step.completed else "⏳ Pending"
            status.append(f"Step {i+1}: {step.name} - {state}")

        return "\n".join(status)

    def clear_workflow(self):
        """清空工作流"""
        self.workflow_steps.clear()
        self.current_step = 0

    def get_step_count(self):
        """获取步骤总数"""
        return len(self.workflow_steps)

    def get_completed_steps(self):
        """获取已完成的步骤数量"""
        return sum(1 for step in self.workflow_steps if step.completed)

    def get_progress(self):
        """获取工作流进度"""
        if not self.workflow_steps:
            return 0.0
        return self.get_completed_steps() / len(self.workflow_steps)

    def is_workflow_complete(self):
        """检查工作流是否完成"""
        return all(step.completed for step in self.workflow_steps)

    def get_next_step(self):
        """获取下一个未完成的步骤"""
        for step in self.workflow_steps:
            if not step.completed:
                return step
        return None
