"""
AsyncIO 版本的任务管理系统
相比 Threading 版本的优势：
1. 更轻量级的协程，资源消耗更少
2. 单线程执行，避免线程安全问题
3. 更好的错误处理和调试体验
4. 更适合 I/O 密集型任务（如 LLM API 调用）
5. 更精确的任务控制（暂停、恢复、取消）
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import uuid
import time
import asyncio
from collections import deque
import heapq
from dataclasses import dataclass, field
import subprocess
import os
import shlex
import json

from menglong.utils.log import (
    print_message,
    print_json,
    print_rule,
)
from menglong.agents.agent import Agent
from menglong.ml_model.schema import user, assistant, tool as ToolMessage
from menglong.agents.chat.chat_agent import tool
from menglong.utils.log import MessageType
from menglong.agents.component.tool_manager import tool, ToolManager


class TaskStatus(Enum):
    """任务状态枚举"""

    CREATED = "Created"
    PENDING = "Pending"
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELED = "Canceled"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskType(Enum):
    """任务类型"""

    SIMPLE = "simple"  # 单步任务
    COMPLEX = "complex"  # 复杂任务（需要分解）
    SUBTASK = "subtask"  # 子任务


class TaskID:
    _id = -1

    @staticmethod
    def next():
        TaskID._id += 1
        return TaskID._id


@dataclass
class Task:
    """任务描述类 - 支持多步任务"""

    prompt: str
    tools: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(init=False)

    # 多步任务支持
    task_type: TaskType = TaskType.SIMPLE
    parent_task_id: Optional[str] = None
    subtask_ids: List[str] = field(default_factory=list)
    execution_plan: Optional[Dict] = None

    def __post_init__(self):
        self.task_id = f"task_{TaskID.next()}"
        self.metadata["created_at"] = time.time()

    def add_dependency(self, task_id: str):
        """添加任务依赖"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)


@dataclass
class ExecutionContext:
    """执行上下文，保存执行过程中的状态"""

    file_operations: List[Dict] = field(default_factory=list)
    command_results: List[Dict] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    step_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAnalysis:
    """任务复杂度分析结果"""

    is_simple: bool
    complexity_score: int  # 1-10
    estimated_steps: int
    requires_tools: List[str]
    reasoning: str

    @classmethod
    def from_json(cls, json_str: str) -> "TaskAnalysis":
        """从JSON字符串创建实例"""
        try:
            # 清理可能的markdown代码块格式
            clean_json = json_str.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]  # 移除```json
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]  # 移除```
            clean_json = clean_json.strip()

            data = json.loads(clean_json)
            return cls(
                is_simple=data.get("is_simple", True),
                complexity_score=data.get("complexity_score", 1),
                estimated_steps=data.get("estimated_steps", 1),
                requires_tools=data.get("requires_tools", []),
                reasoning=data.get("reasoning", ""),
            )
        except Exception as e:
            # 默认为简单任务
            return cls(
                is_simple=True,
                complexity_score=1,
                estimated_steps=1,
                requires_tools=[],
                reasoning=f"JSON解析失败: {e}",
            )


@dataclass
class SubTaskPlan:
    """子任务计划"""

    id: str
    description: str
    tool_type: str  # terminal, analysis, file_operation
    dependencies: List[str]
    estimated_duration: int  # 秒
    validation_criteria: str


@dataclass
class ExecutionPlan:
    """执行计划"""

    subtasks: List[SubTaskPlan]
    total_estimated_time: int
    success_criteria: str

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlan":
        """从JSON字符串创建执行计划"""
        try:
            # 清理可能的markdown代码块格式
            clean_json = json_str.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]  # 移除```json
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]  # 移除```
            clean_json = clean_json.strip()

            print(f"DEBUG: Parsing JSON: {clean_json[:200]}...")  # 调试信息

            data = json.loads(clean_json)
            subtasks = []
            for st in data.get("subtasks", []):
                subtasks.append(
                    SubTaskPlan(
                        id=st.get("id", ""),
                        description=st.get("description", ""),
                        tool_type=st.get("tool_type", "analysis"),
                        dependencies=st.get("dependencies", []),
                        estimated_duration=st.get("estimated_duration", 30),
                        validation_criteria=st.get("validation_criteria", ""),
                    )
                )

            print(f"DEBUG: Created {len(subtasks)} subtasks")  # 调试信息

            return cls(
                subtasks=subtasks,
                total_estimated_time=data.get("total_estimated_time", 60),
                success_criteria=data.get("success_criteria", ""),
            )
        except Exception as e:
            print(f"DEBUG: JSON parsing failed: {e}")  # 调试信息
            # 返回空计划
            return cls(
                subtasks=[],
                total_estimated_time=0,
                success_criteria=f"计划解析失败: {e}",
            )

    def __repr__(self):
        return f"Task({self.task_id[:8]}, '{self.prompt[:20]}...')"


@dataclass
class TCB:
    """任务控制块 - AsyncIO 版本"""

    task: Task
    status: TaskStatus = TaskStatus.CREATED
    result: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    execution_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    progress: float = 0.0
    worker_task: Optional[asyncio.Task] = None  # 关联的 asyncio.Task
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    @property
    def task_id(self) -> str:
        return self.task.task_id

    def log(self, message: str):
        """记录任务日志"""
        self.logs.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def update_progress(self, progress: float):
        """更新任务进度 (0.0 - 1.0)"""
        self.progress = max(0.0, min(1.0, progress))

    def reset(self):
        """重置任务状态（用于重试）"""
        self.status = TaskStatus.CREATED
        self.result = None
        self.start_time = None
        self.end_time = None
        self.progress = 0.0
        self.execution_count += 1
        self.cancel_event.clear()

    def get_execution_time(self) -> float:
        """获取任务执行时间（秒）"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    async def cancel(self):
        """取消任务"""
        self.cancel_event.set()
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

    def __repr__(self):
        return (
            f"TCB({self.task_id[:8]}, {self.status.name}, progress={self.progress:.0%})"
        )


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        self.root_task: Optional[Task] = None
        self.tasks: Dict[str, Task] = {}
        self.tcbs: Dict[str, TCB] = {}

    async def create_task(
        self,
        prompt: str,
        tools: List[str] = None,
        resources: Dict[str, Any] = None,
        parent_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> Tuple[Task, TCB]:
        """创建新任务及其控制块"""
        task = Task(prompt, tools or [], resources or {}, parent_id, priority)
        tcb = TCB(task)

        self.tasks[task.task_id] = task
        self.tcbs[task.task_id] = tcb

        if parent_id:
            parent = self.tasks.get(parent_id)
            if parent:
                if "children" not in parent.metadata:
                    parent.metadata["children"] = []
                parent.metadata["children"].append(task.task_id)
        elif not self.root_task:
            self.root_task = task

        tcb.log(f"Task created: {prompt}")
        return task, tcb

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_tcb(self, task_id: str) -> Optional[TCB]:
        return self.tcbs.get(task_id)

    def get_task_tree(self, task_id: str = None) -> Dict:
        """获取任务树结构"""
        task = self.tasks.get(task_id) or self.root_task
        if not task:
            return {}

        def build_tree(node_id: str):
            task = self.tasks[node_id]
            tcb = self.tcbs[node_id]
            return {
                "id": task.task_id,
                "prompt": task.prompt,
                "status": tcb.status.value,
                "progress": tcb.progress,
                "priority": task.priority.name,
                "children": [
                    build_tree(child_id)
                    for child_id in task.metadata.get("children", [])
                ],
            }

        return build_tree(task.task_id) if task else {}

    def get_task_dag(self, root_id: str = None) -> Dict[str, Dict[str, List[str]]]:
        """获取任务DAG"""
        dag = {}
        root_task = self.root_task if root_id is None else self.tasks.get(root_id)

        if not root_task:
            return {}

        all_tasks = self._collect_subtasks(root_task.task_id)

        for task in all_tasks:
            dag[task.task_id] = {
                "dependencies": task.dependencies,
                "dependent_tasks": [
                    t.task_id for t in all_tasks if task.task_id in t.dependencies
                ],
            }
        return dag

    def _collect_subtasks(self, task_id: str) -> List[Task]:
        """收集所有子任务"""
        tasks = []
        if task_id in self.tasks:
            task = self.tasks[task_id]
            tasks.append(task)
            for child_id in task.metadata.get("children", []):
                tasks.extend(self._collect_subtasks(child_id))
        return tasks


class AsyncPriorityQueue:
    """异步优先级队列"""

    def __init__(self):
        self.queue = []
        self.counter = 0
        self._condition = asyncio.Condition()

    async def put(self, item: Tuple[float, Any]):
        """添加项目到队列"""
        priority, value = item
        async with self._condition:
            heapq.heappush(self.queue, (-priority, self.counter, value))
            self.counter += 1
            self._condition.notify()

    async def get(self) -> Any:
        """从队列获取项目"""
        async with self._condition:
            while not self.queue:
                await self._condition.wait()
            _, _, value = heapq.heappop(self.queue)
            return value

    def empty(self) -> bool:
        """检查队列是否为空"""
        return len(self.queue) == 0

    def qsize(self) -> int:
        """获取队列大小"""
        return len(self.queue)


class AsyncTaskScheduler:
    """异步任务调度器"""

    def __init__(self, task_manager: AsyncTaskManager, agent: "AsyncAgent"):
        self.task_manager = task_manager
        self.agent = agent
        self.execution_policy = "priority"
        self.task_queue = AsyncPriorityQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = 10  # 最大并发任务数
        self.scheduler_task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()

    def set_execution_policy(self, policy: str):
        """设置任务执行策略"""
        self.execution_policy = policy
        self.agent.log(f"Task execution policy set to: {policy}")

    async def start(self):
        """启动调度器"""
        if not self.scheduler_task:
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def _scheduler_loop(self):
        """调度器主循环"""
        while not self.stop_event.is_set():
            try:
                # 查找就绪任务
                ready_tasks = await self._find_ready_tasks()

                # 将就绪任务加入队列
                for task_id in ready_tasks:
                    task = self.task_manager.get_task(task_id)
                    tcb = self.task_manager.get_tcb(task_id)

                    if not task or not tcb:
                        continue

                    # 计算优先级
                    if self.execution_policy == "priority":
                        priority = task.priority.value
                    elif self.execution_policy == "fifo":
                        priority = tcb.task.metadata.get("created_at", time.time())
                    else:
                        priority = 0

                    await self.task_queue.put((priority, task_id))

                # 处理任务队列
                while (
                    not self.task_queue.empty()
                    and len(self.running_tasks) < self.max_concurrent_tasks
                    and not self.stop_event.is_set()
                ):
                    task_id = await self.task_queue.get()
                    tcb = self.task_manager.get_tcb(task_id)

                    if not tcb or tcb.status != TaskStatus.READY:
                        continue

                    # 启动任务执行
                    tcb.status = TaskStatus.RUNNING
                    worker_task = asyncio.create_task(self._execute_task(task_id))
                    tcb.worker_task = worker_task
                    self.running_tasks[task_id] = worker_task

                # 清理已完成的任务
                await self._cleanup_completed_tasks()

                # 短暂休眠
                await asyncio.sleep(0.1)

            except Exception as e:
                self.agent.log(f"Scheduler error: {e}")
                await asyncio.sleep(1)

    async def _find_ready_tasks(self) -> List[str]:
        """查找所有就绪任务"""
        ready_tasks = []

        for task_id, tcb in self.task_manager.tcbs.items():
            if tcb.status == TaskStatus.CREATED and await self._check_dependencies(
                task_id
            ):
                tcb.status = TaskStatus.READY
                ready_tasks.append(task_id)

        return ready_tasks

    async def _check_dependencies(self, task_id: str) -> bool:
        """检查任务依赖是否满足"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return False

        for dep_id in task.dependencies:
            dep_tcb = self.task_manager.get_tcb(dep_id)
            if not dep_tcb or dep_tcb.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _execute_task(self, task_id: str):
        """执行单个任务"""
        task = self.task_manager.get_task(task_id)
        tcb = self.task_manager.get_tcb(task_id)

        if not task or not tcb:
            return

        try:
            tcb.start_time = time.time()
            tcb.log("Task execution started")

            # 执行任务
            result = await self._execute_llm_task(task, tcb)

            # 检查是否被取消
            if tcb.cancel_event.is_set():
                tcb.status = TaskStatus.CANCELED
                tcb.log("Task was canceled")
                return

            # 更新任务状态
            tcb.result = result
            tcb.status = TaskStatus.COMPLETED
            tcb.end_time = time.time()
            tcb.progress = 1.0
            tcb.log(f"Task completed successfully. Result: {result[:50]}...")

            # 添加到agent记忆
            self.agent.memory.append(
                {
                    "task_id": task_id,
                    "prompt": task.prompt,
                    "result": result,
                    "execution_time": tcb.get_execution_time(),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        except asyncio.CancelledError:
            tcb.status = TaskStatus.CANCELED
            tcb.log("Task was canceled")
            raise

        except Exception as e:
            tcb.status = TaskStatus.FAILED
            tcb.log(f"Task failed: {str(e)}")

        finally:
            tcb.end_time = time.time()

    async def _execute_llm_task(self, task: Task, tcb: TCB) -> str:
        """执行 LLM 任务，通过 agent 的 chat 方法"""
        # 检查取消信号
        if tcb.cancel_event.is_set():
            tcb.log("Task canceled during execution")
            return "Canceled"

        # 构建完整的任务提示，包含上下文信息
        context = f"Agent knowledge: {self.agent.self_status['knowledge']}. Environment: {self.agent.env_status['location']}"
        tools_info = (
            f"Available tools: {', '.join(task.tools)}"
            if task.tools
            else "No specific tools available"
        )

        full_prompt = f"""
Task: {task.prompt}

Context: {context}
{tools_info}

Please process this task and provide a detailed response.
"""

        tcb.log("Starting LLM interaction via agent chat")
        tcb.update_progress(0.5)

        # 使用 agent 的 chat 方法进行任务处理
        try:
            result = await self.agent.chat(full_prompt)
            tcb.log("LLM task completed successfully")
            tcb.update_progress(1.0)
            return result
        except Exception as e:
            tcb.log(f"LLM task failed: {str(e)}")
            raise

    async def _cleanup_completed_tasks(self):
        """清理已完成的任务"""
        completed_tasks = []
        for task_id, worker_task in self.running_tasks.items():
            if worker_task.done():
                completed_tasks.append(task_id)

        for task_id in completed_tasks:
            del self.running_tasks[task_id]

    def get_task_queue_size(self) -> int:
        return self.task_queue.qsize()

    def get_running_tasks(self) -> List[str]:
        return list(self.running_tasks.keys())

    async def cancel_task(self, task_id: str):
        """取消任务"""
        tcb = self.task_manager.get_tcb(task_id)
        if tcb:
            await tcb.cancel()
            if tcb.status in [TaskStatus.READY, TaskStatus.PENDING]:
                tcb.status = TaskStatus.CANCELED
                tcb.log("Task canceled by user")

    async def retry_task(self, task_id: str):
        """重试任务"""
        tcb = self.task_manager.get_tcb(task_id)
        if tcb and tcb.status in [TaskStatus.FAILED, TaskStatus.CANCELED]:
            tcb.reset()
            tcb.log("Task scheduled for retry")

    async def shutdown(self):
        """关闭调度器"""
        self.stop_event.set()

        # 取消所有运行中的任务
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)

        # 等待调度器任务完成
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

    async def schedule_complex_task(self, main_task: Task, subtasks: List[Task]) -> str:
        """调度复杂任务及其子任务"""
        self.agent.log(
            f"Scheduling complex task: {main_task.task_id} with {len(subtasks)} subtasks"
        )

        # 1. 注册主任务
        await self.add_task(main_task)

        # 2. 注册所有子任务，建立依赖关系
        for subtask in subtasks:
            subtask.parent_task_id = main_task.task_id
            main_task.subtask_ids.append(subtask.task_id)
            await self.add_task(subtask)

        # 3. 启动执行
        return await self.execute_task_tree(main_task.task_id)

    async def execute_task_tree(self, main_task_id: str) -> str:
        """执行任务树"""
        self.agent.log(f"Executing task tree for: {main_task_id}")
        context = ExecutionContext()

        main_task = self.task_manager.get_task(main_task_id)
        if not main_task:
            return "Main task not found"

        # 如果是简单任务，直接执行
        if main_task.task_type == TaskType.SIMPLE:
            return await self._execute_simple_task_direct(main_task, context)

        # 复杂任务：执行所有子任务
        final_results = []

        for subtask_id in main_task.subtask_ids:
            subtask = self.task_manager.get_task(subtask_id)
            if subtask:
                result = await self._execute_single_subtask(subtask, context)
                final_results.append(f"步骤 {subtask_id}: {result}")
                context.step_results[subtask_id] = result

        # 整合最终结果
        return await self._finalize_complex_task(main_task, context, final_results)

    async def _execute_single_subtask(
        self, subtask: Task, context: ExecutionContext
    ) -> str:
        """执行单个子任务"""
        self.agent.log(f"Executing subtask: {subtask.task_id} - {subtask.prompt}")

        try:
            # 根据工具类型选择执行方式
            if "terminal" in subtask.tools:
                result = await self.agent.chat_with_terminal_tool(subtask.prompt)
            else:
                result = await self.agent.chat(subtask.prompt)

            # 记录到上下文
            context.step_results[subtask.task_id] = result

            self.agent.log(f"Subtask {subtask.task_id} completed successfully")
            return result

        except Exception as e:
            error_msg = f"Subtask {subtask.task_id} failed: {e}"
            self.agent.log(error_msg)
            return error_msg

    async def _execute_simple_task_direct(
        self, task: Task, context: ExecutionContext
    ) -> str:
        """直接执行简单任务"""
        try:
            if "terminal" in task.tools:
                return await self.agent.chat_with_terminal_tool(task.prompt)
            else:
                return await self.agent.chat(task.prompt)
        except Exception as e:
            return f"Task execution failed: {e}"

    async def _finalize_complex_task(
        self, main_task: Task, context: ExecutionContext, results: List[str]
    ) -> str:
        """整合复杂任务的最终结果"""
        self.agent.log(f"Finalizing complex task: {main_task.task_id}")

        # 构建总结提示
        summary_prompt = f"""
基于以下多步任务的执行结果，生成最终的综合报告：

原始任务：{main_task.prompt}

执行步骤结果：
{chr(10).join(results)}

请生成一个清晰、简洁的最终报告，突出关键发现和结论。
"""

        try:
            final_summary = await self.agent.chat(summary_prompt)
            self.agent.log("Complex task finalized successfully")
            return final_summary
        except Exception as e:
            fallback_result = f"""
任务执行完成，但总结生成失败: {e}

执行步骤：
{chr(10).join(results)}
"""
            return fallback_result


class AsyncAgent(Agent):
    """异步 Agent 主体类，继承自 menglong.agents.agent.Agent"""

    def __init__(self, name: str = "Async AI Agent", model_id: str = None):
        super().__init__(model_id=model_id)
        self.name = name

        from menglong.agents.chat import ToolManager
        from menglong.agents.component import ContextManager

        # 状态相关属性
        self.context = ContextManager()

        # 工具管理器
        self.tool_manager = ToolManager()
        self.self_status: Dict[str, Any] = {
            "knowledge": "general",
            "current_action": "idle",
            "current_task": None,
        }
        self.env_status: Dict[str, Any] = {
            "time": "day",
            "location": "unknown",
            "resources": {},
        }
        self.memory: List[Dict] = []
        self.default_tool = "default_search"

        # 异步任务管理系统
        self.task_manager = AsyncTaskManager()
        self.scheduler = AsyncTaskScheduler(self.task_manager, self)

        # 任务规划器
        self.planner = TaskPlanner(self)

        # # 注册终端命令工具
        # self.register_terminal_tool()

    def log(self, message: str):
        """记录Agent日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [AsyncAgent] {message}"
        print_message(log_entry)
        self.memory.append(log_entry)

    async def chat(self, message: str) -> str:
        """简单的异步对话方法"""
        print_message(f"{message}", title="User", msg_type=MessageType.USER)

        # 使用正确的消息格式
        messages = [user(content=message)]

        try:
            # 调用模型的 chat 方法，传入消息列表
            response = await asyncio.to_thread(self.model.chat, messages)
            # 提取响应文本
            response_text = (
                response.message.content.text
                if response.message and response.message.content
                else str(response)
            )
        except Exception as e:
            self.log(f"Chat failed: {str(e)}")
            response_text = f"Error: {str(e)}"

        print_message(f"{response_text}", title="Assistant", msg_type=MessageType.AGENT)
        return response_text

    async def chat_advanced(self, input_messages, **kwargs):
        """自动模式，支持工具调用"""
        self.context.add_user_message(input_messages)
        messages = self.context.messages

        if kwargs.get("tools") is not None:
            tools = kwargs.get("tools")
            self.tool_manager.add_tools(tools)
            # kwargs["tool_choice"] = self.tool_manager.format_tool_choice(
            #     self.model.provider
            # )

        # 如果有注册的工具，添加到请求中
        # if self.tool_manager.tools:
        #     kwargs["tools"] = self.tool_manager.format_tools_for_model(
        #         self.model.provider
        #     )
        #     kwargs["tool_choice"] = self.tool_manager.format_tool_choice(
        #         self.model.provider
        #     )

        try:
            res = self.model.chat(messages=messages, **kwargs)

            # 检查是否有工具调用
            if self._is_use_tool(res.message):
                # 添加助手的原始消息到上下文
                self.context._messages.context.append(res.message)

                # 执行工具调用并收集结果
                tool_results = self.tool_manager.execute_tool_call(
                    res.message.tool_descriptions
                )

                # 将工具结果添加到上下文
                for tool_result in tool_results:
                    tool_results_message = ToolMessage(
                        content=json.dumps(tool_result["content"], ensure_ascii=False),
                        tool_id=tool_result.get("id"),
                    )
                    self.context._messages.context.append(tool_results_message)

                # 重新获取消息列表
                messages = self.context.messages

                # 获取最终响应
                final_res = self.model.chat(
                    messages=messages,
                )
                r = final_res.message.content.text
            else:
                r = res.message.content.text

            # 处理推理内容
            if res.message.content.reasoning:
                self.context.add_assistant_reasoning(
                    query=input_messages,
                    reasoning=res.message.content.reasoning,
                    answers=r,
                )

            self.context.add_assistant_response(r)
            return r

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print_message(error_msg)
            return error_msg

    async def run_async(
        self, prompt: str, tools: List[str] = None, use_scheduler: bool = False
    ) -> str:
        """异步运行Agent

        Args:
            prompt: 任务提示
            tools: 可用工具列表
            use_scheduler: 是否使用复杂的任务调度器，默认False使用简化模式
        """
        if not use_scheduler:
            # 简化模式：直接使用 chat
            return await self.execute_simple_task(prompt, tools)
        else:
            # 完整模式：使用任务调度器
            task, tcb = await self.create_task(prompt, tools)
            await self.scheduler.start()

            # 等待任务完成
            while tcb.status not in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELED,
            ]:
                await asyncio.sleep(0.1)

            return tcb.result

    def run(self, prompt: str = None, tools: List[str] = None) -> str:
        """同步运行方法，满足基类抽象方法要求，支持智能多步任务执行"""
        if prompt is None:
            prompt = "Hello, I am an AI assistant. How can I help you?"

        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，创建一个任务
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.run_intelligent_task(prompt))
                return future.result()
        except RuntimeError:
            # 没有运行的事件循环，可以直接使用 asyncio.run
            return asyncio.run(self.run_intelligent_task(prompt))

    async def create_task(
        self,
        prompt: str,
        tools: List[str] = None,
        resources: Dict[str, Any] = None,
        parent_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> Tuple[Task, TCB]:
        """创建新任务"""
        if not tools:
            tools = [self.default_tool]
        return await self.task_manager.create_task(
            prompt, tools, resources, parent_id, priority
        )

    def get_task_tree(self, task_id: str = None) -> Dict:
        return self.task_manager.get_task_tree(task_id)

    def get_task_dag(self, root_id: str = None) -> Dict[str, Dict[str, List[str]]]:
        return self.task_manager.get_task_dag(root_id)

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态信息"""
        tcb = self.task_manager.get_tcb(task_id)
        if not tcb:
            return {}

        task = self.task_manager.get_task(task_id)
        return {
            "id": task_id,
            "prompt": task.prompt if task else "Unknown",
            "status": tcb.status.value,
            "progress": tcb.progress,
            "priority": task.priority.name if task else "Normal",
            "logs": tcb.logs[-5:],
            "execution_time": tcb.get_execution_time(),
            "dependencies": task.dependencies if task else [],
        }

    async def cancel_task(self, task_id: str):
        """取消任务"""
        await self.scheduler.cancel_task(task_id)

    async def retry_task(self, task_id: str):
        """重试任务"""
        await self.scheduler.retry_task(task_id)

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "policy": self.scheduler.execution_policy,
            "queue_size": self.scheduler.get_task_queue_size(),
            "running_tasks": self.scheduler.get_running_tasks(),
            "max_concurrent": self.scheduler.max_concurrent_tasks,
        }

    async def shutdown(self):
        """关闭Agent系统"""
        await self.scheduler.shutdown()

    async def execute_simple_task(self, prompt: str, tools: List[str] = None) -> str:
        """简化的任务执行，直接使用 chat 方法，不需要调度器"""
        self.log(f"Executing simple task: {prompt}")

        # 构建任务上下文
        context = f"Agent knowledge: {self.self_status['knowledge']}. Environment: {self.env_status['location']}"
        tools_info = (
            f"Available tools: {', '.join(tools)}"
            if tools
            else "No specific tools available"
        )

        full_prompt = f"""
Task: {prompt}

Context: {context}
{tools_info}

Please process this task and provide a detailed response.
"""

        # 直接使用 chat 方法
        if tools:
            result = await self.chat(full_prompt, tools=tools)
        else:
            result = await self.chat(full_prompt)
        self.log(f"Simple task completed: {result[:50]}...")
        return result

    # def register_terminal_tool(self):
    #     """注册终端命令工具到 agent"""
    #     self.terminal_tool_schema = format_terminal_tool_for_model()
    #     self.log("Terminal command tool registered successfully")

    async def execute_terminal_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行终端工具调用"""
        try:
            # 提取参数
            arguments = tool_call.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            command = arguments.get("command")
            working_directory = arguments.get("working_directory")
            timeout = arguments.get("timeout", 30)
            safe_mode = arguments.get("safe_mode", True)

            self.log(f"Executing terminal command: {command}")

            # 执行命令
            result = await execute_terminal_command_async(
                command=command,
                working_directory=working_directory,
                timeout=timeout,
                safe_mode=safe_mode,
            )

            self.log(f"Terminal command completed: {result['success']}")
            return {
                "tool_call_id": tool_call.get("id"),
                "content": result,
                "success": result["success"],
            }

        except Exception as e:
            error_result = {
                "success": False,
                "error_message": f"Tool execution error: {str(e)}",
                "command": tool_call.get("arguments", {}).get("command", "unknown"),
            }
            return {
                "tool_call_id": tool_call.get("id"),
                "content": error_result,
                "success": False,
            }

    async def chat_with_terminal_tool(self, message: str, tools=None) -> str:
        """支持终端工具的简化聊天方法"""
        self.log(f"Received message with terminal tool support: {message}")

        try:
            # 先检查是否需要执行终端命令
            command_to_execute = self._extract_command_from_message(message)

            if command_to_execute:
                self.log(f"🔧 Detected command to execute: {command_to_execute}")
                print_message(
                    f"Executing command: {command_to_execute}",
                    title="Terminal Tool",
                    msg_type=MessageType.INFO,
                )

                # 执行命令
                cmd_result = await execute_terminal_command_async(command_to_execute)
                # 详细输出命令执行结果
                print_message(
                    "Command execution result:",
                    title="Terminal Output",
                    msg_type=MessageType.INFO,
                )
                print_json(cmd_result, title="Command Result Details")

                # 构建包含命令结果的上下文消息
                if cmd_result["success"]:
                    self.log(f"✅ Command executed successfully")
                    enhanced_message = f"""User request: {message}

I executed the command '{command_to_execute}' and got the following result:

Command output:
{cmd_result['stdout']}

Please provide a helpful response based on this information."""
                else:
                    self.log(
                        f"❌ Command execution failed: {cmd_result.get('error_message', 'Unknown error')}"
                    )
                    enhanced_message = f"""User request: {message}

I tried to execute the command '{command_to_execute}' but encountered an error:
Error: {cmd_result.get('error_message', 'Unknown error')}

Please provide a helpful response explaining what went wrong."""
            else:
                self.log("No command detected, proceeding with normal chat")
                enhanced_message = message

            # 调用模型获取响应
            self.log("🤖 Sending request to LLM...")
            messages = [user(content=enhanced_message)]
            if tools:
                # 如果有工具，添加到消息中
                response = await asyncio.to_thread(
                    self.model.chat, messages, tools=tools
                )
            else:
                response = await asyncio.to_thread(self.model.chat, messages)

            print_message(
                f"response: {response}",
                title="LLM Response",
                msg_type=MessageType.AGENT,
            )
            response_text = (
                response.message.content.text
                if response.message and response.message.content
                else str(response)
            )

            self.log("✅ Received response from LLM")

        except Exception as e:
            self.log(f"❌ Chat with terminal tool failed: {str(e)}")
            response_text = f"Error: {str(e)}"

        self.log(f"Responding with: {response_text[:100]}...")
        return response_text

    def _extract_command_from_message(self, message: str) -> Optional[str]:
        """从用户消息中提取需要执行的命令"""
        message_lower = message.lower()

        # 简单的命令匹配
        if "ls" in message_lower and (
            "directory" in message_lower or "files" in message_lower
        ):
            return "ls -la"
        elif "python" in message_lower and "version" in message_lower:
            return "python --version"
        elif "disk usage" in message_lower or "du command" in message_lower:
            return "du -sh ."
        elif "current directory" in message_lower and "pwd" not in message_lower:
            return "pwd"
        elif "git status" in message_lower:
            return "git status"
        elif "git log" in message_lower:
            return "git log --oneline -5"

        return None

    async def run_intelligent_task(self, task_description: str, tools: list) -> str:
        """智能任务执行：自动判断单步/多步执行"""
        self.log(f"Received task: {task_description}")

        try:
            # 1. LLM判断任务复杂度
            task_analysis = self.planner.analyze_task_complexity(task_description)

            self.log(
                f"Task analysis: complexity_score={task_analysis.complexity_score}, "
                f"is_simple={task_analysis.is_simple}, reasoning={task_analysis.reasoning}"
            )

            if task_analysis.is_simple:
                return await self._execute_simple_task(task_description, tools)
            else:
                return await self._execute_complex_task(
                    task_description, task_analysis, tools
                )

        except Exception as e:
            error_msg = f"Task execution failed: {e}"
            self.log(error_msg)
            return error_msg

    async def _execute_simple_task(self, description: str, tools) -> str:
        """执行简单任务"""
        self.log("Executing as simple task")

        # 判断是否需要终端工具
        if any(
            keyword in description.lower()
            for keyword in [
                "command",
                "terminal",
                "run",
                "execute",
                "check",
                "list",
                "version",
            ]
        ):
            result = await self.chat_with_terminal_tool(description)
        else:
            result = await self.chat(description)

        self.log(f"Simple task completed: {result[:100]}...")
        return result

    async def _execute_complex_task(
        self, description: str, analysis: TaskAnalysis, tools
    ) -> str:
        """执行复杂的多步任务"""
        self.log(f"Executing as complex task with {analysis.estimated_steps} steps")

        try:
            # 1. 生成执行计划
            execution_plan = self.planner.generate_execution_plan(description)

            self.log(
                f"Generated execution plan with {len(execution_plan.subtasks)} subtasks"
            )

            if not execution_plan.subtasks:
                self.log("No subtasks generated, falling back to simple execution")
                return await self._execute_simple_task(description)

            # 2. 创建主任务
            main_task = Task(
                prompt=description,
                task_type=TaskType.COMPLEX,
                execution_plan=execution_plan.__dict__,
                priority=TaskPriority.HIGH,
            )

            # 3. 创建子任务
            subtasks = []
            for i, subtask_plan in enumerate(execution_plan.subtasks):
                tools = []
                if subtask_plan.tool_type == "terminal":
                    tools = ["terminal"]

                subtask = Task(
                    prompt=subtask_plan.description,
                    task_type=TaskType.SUBTASK,
                    tools=tools,
                    dependencies=subtask_plan.dependencies,
                    priority=TaskPriority.NORMAL,
                    metadata={
                        "step_order": i + 1,
                        "validation_criteria": subtask_plan.validation_criteria,
                        "estimated_duration": subtask_plan.estimated_duration,
                    },
                )
                subtasks.append(subtask)

            # 4. 提交到调度器执行
            self.log(
                f"Submitting complex task with {len(subtasks)} subtasks to scheduler"
            )
            result = await self.scheduler.schedule_complex_task(main_task, subtasks)

            return result

        except Exception as e:
            error_msg = f"Complex task execution failed: {e}"
            self.log(error_msg)
            # 回退到简单任务执行
            return await self._execute_simple_task(description)


@dataclass
class SubTaskPlan:
    """子任务计划"""

    id: str
    description: str
    tool_type: str  # terminal, analysis, file_operation
    dependencies: List[str]
    estimated_duration: int  # 秒
    validation_criteria: str


@dataclass
class ExecutionPlan:
    """执行计划"""

    subtasks: List[SubTaskPlan]
    total_estimated_time: int
    success_criteria: str

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionPlan":
        """从JSON字符串创建执行计划"""
        try:
            data = json.loads(json_str)
            subtasks = []
            for st in data.get("subtasks", []):
                subtasks.append(
                    SubTaskPlan(
                        id=st.get("id", ""),
                        description=st.get("description", ""),
                        tool_type=st.get("tool_type", "analysis"),
                        dependencies=st.get("dependencies", []),
                        estimated_duration=st.get("estimated_duration", 30),
                        validation_criteria=st.get("validation_criteria", ""),
                    )
                )

            return cls(
                subtasks=subtasks,
                total_estimated_time=data.get("total_estimated_time", 60),
                success_criteria=data.get("success_criteria", ""),
            )
        except Exception as e:
            # 返回空计划
            return cls(
                subtasks=[],
                total_estimated_time=0,
                success_criteria=f"计划解析失败: {e}",
            )


# 示例使用
async def main():
    """异步主函数示例"""
    # 创建异步Agent
    agent = AsyncAgent("Async Research Assistant")

    # 设置Agent状态
    agent.self_status["knowledge"] = "AI research"
    agent.env_status["location"] = "research lab"
    agent.env_status["resources"] = {"datasets": ["Climate Data", "AI Publications"]}

    try:
        # 启动调度器
        await agent.scheduler.start()

        # 创建主任务
        main_task, main_tcb = await agent.create_task(
            "Research the impact of AI on climate change",
            tools=["web_search", "data_analysis"],
            resources={"priority": "high"},
            priority=TaskPriority.HIGH,
        )

        # 创建子任务
        data_task, data_tcb = await agent.create_task(
            "Gather climate data from reliable sources",
            parent_id=main_task.task_id,
            priority=TaskPriority.NORMAL,
        )

        analysis_task, analysis_tcb = await agent.create_task(
            "Analyze AI energy consumption patterns",
            tools=["data_visualization"],
            parent_id=main_task.task_id,
            priority=TaskPriority.HIGH,
        )

        # 创建有依赖关系的任务
        report_task, report_tcb = await agent.create_task(
            "Prepare final research report",
            parent_id=main_task.task_id,
            priority=TaskPriority.CRITICAL,
        )
        report_task.add_dependency(data_task.task_id)
        report_task.add_dependency(analysis_task.task_id)

        # 查看任务树
        print_rule("Async Task Tree Structure:")
        print_json(agent.get_task_tree())

        print("\nAsync Task DAG:")
        print_json(agent.get_task_dag(main_task.task_id))

        print("\nAsync Scheduler Status:")
        print_json(agent.get_scheduler_status())

        # 监控任务执行
        print_message("\nMonitoring async task execution...")
        while True:
            # 显示任务状态
            print_message("\nCurrent Async Task Status:")
            for task_id in agent.task_manager.tcbs:
                status = agent.get_task_status(task_id)
                print_message(
                    f"{task_id[:8]}: {status['status']} - {status['progress']:.0%} - {status['prompt'][:30]}..."
                )

            # 检查所有任务是否完成
            all_completed = all(
                tcb.status
                in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]
                for tcb in agent.task_manager.tcbs.values()
            )

            if all_completed:
                break

            await asyncio.sleep(2)

        # 显示最终结果
        print_message("\nFinal Async Task Status:")
        for task_id, tcb in agent.task_manager.tcbs.items():
            print_message(
                f"{task_id[:8]}: {tcb.status.name} - Result: {tcb.result[:50] if tcb.result else 'None'}"
            )

        print_message("\nFinal Async Task Tree:")
        print_json(agent.get_task_tree())

    except KeyboardInterrupt:
        print_message("\nInterrupted by user")

    finally:
        # 关闭系统
        await agent.shutdown()


# 简单测试示例
async def simple_test():
    """简单测试，展示修正后的agent使用"""
    print_rule("Simple AsyncAgent Test")

    # 创建agent
    agent = AsyncAgent("Test Assistant")

    # 简单聊天测试
    print_rule("Testing simple chat...")
    response = await agent.chat("Hello, how are you?")
    # print_message(f"Chat response: {response}", msg_type=MessageType.AGENT)

    # 简单任务执行测试
    print_rule("Testing simple task execution...")
    result = await agent.execute_simple_task(
        "Explain what is machine learning", ["research", "analysis"]
    )
    # print_message(f"Task result: {result}", msg_type=MessageType.AGENT)

    # 测试同步接口
    print_rule("Testing sync interface...")
    sync_result = agent.run("What is the weather like today?")
    # print_message(f"Sync result: {sync_result}", msg_type=MessageType.AGENT)


# 终端工具测试示例
async def terminal_tool_test():
    """测试终端工具功能"""
    print_rule("Terminal Tool Test")

    # 测试基础终端命令功能
    print_message("Testing basic terminal command functions...")
    test_terminal_command_tool()

    # 测试与 Agent 的集成
    print_message("Testing terminal tool integration with AsyncAgent...")
    agent = AsyncAgent("Terminal Test Agent")

    # 测试1: 让模型执行简单命令
    print_message("\nTest 1: Ask model to check current directory")
    response1 = await agent.chat_with_terminal_tool(
        "Please check what files are in the current directory using the ls command",
        tools=[execute_terminal_command],
    )
    print_message(f"Response: {response1}")

    # 测试2: 让模型检查Python版本
    print_message("\nTest 2: Ask model to check Python version")
    response2 = await agent.chat_with_terminal_tool(
        "Can you check what version of Python is installed on this system?",
        tools=[execute_terminal_command],
    )
    print_message(f"Response: {response2}")

    # 测试3: 让模型执行一些文件操作
    print_message("\nTest 3: Ask model to check disk usage")
    response3 = await agent.chat_with_terminal_tool(
        "Please check the disk usage of the current directory using the du command",
        tools=[execute_terminal_command],
    )
    print_message(f"Response: {response3}")


@tool
def execute_terminal_command(
    command: str,
    working_directory: Optional[str] = None,
    timeout: int = 30,
    capture_output: bool = True,
    safe_mode: bool = True,
) -> Dict[str, Any]:
    """
    执行终端命令的工具函数，可以被模型调用

    Args:
        command: 要执行的命令
        working_directory: 工作目录，默认为当前目录
        timeout: 超时时间（秒），默认30秒
        capture_output: 是否捕获输出，默认True
        safe_mode: 安全模式，限制危险命令，默认True

    Returns:
        Dict包含：
        - success: 是否成功执行
        - returncode: 返回码
        - stdout: 标准输出
        - stderr: 标准错误
        - command: 执行的命令
        - error_message: 错误信息（如果有）
    """

    # 安全检查：禁止危险命令
    dangerous_commands = [
        "rm -rf",
        "rm -f",
        "format",
        "del /f",
        "del /q",
        "sudo rm",
        "sudo dd",
        "sudo mkfs",
        "shutdown",
        "reboot",
        "kill -9",
        "killall",
        "pkill",
        ">>",
        "> /",
        "chmod 777",
        "chown",
        "passwd",
        "su -",
        "sudo su",
        "fdisk",
        "crontab",
    ]

    if safe_mode:
        command_lower = command.lower()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return {
                    "success": False,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Dangerous command blocked: {dangerous}",
                    "command": command,
                    "error_message": f"Command contains dangerous operation: {dangerous}",
                }

    # 设置工作目录
    if working_directory and not os.path.exists(working_directory):
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Working directory does not exist: {working_directory}",
            "command": command,
            "error_message": f"Invalid working directory: {working_directory}",
        }

    cwd = working_directory or os.getcwd()

    try:
        # 解析命令，安全地处理参数
        if isinstance(command, str):
            # 使用 shlex.split 安全地分割命令
            cmd_args = shlex.split(command)
        else:
            cmd_args = command

        # 执行命令
        result = subprocess.run(
            cmd_args,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            check=False,  # 不自动抛出异常，我们手动处理返回码
        )

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip() if result.stdout else "",
            "stderr": result.stderr.strip() if result.stderr else "",
            "command": command,
            "error_message": (
                None
                if result.returncode == 0
                else f"Command failed with return code {result.returncode}"
            ),
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "command": command,
            "error_message": f"Command execution timed out after {timeout} seconds",
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command not found: {str(e)}",
            "command": command,
            "error_message": f"Command or program not found: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "command": command,
            "error_message": f"Unexpected error during command execution: {str(e)}",
        }


async def execute_terminal_command_async(
    command: str,
    working_directory: Optional[str] = None,
    timeout: int = 30,
    capture_output: bool = True,
    safe_mode: bool = True,
) -> Dict[str, Any]:
    """
    异步版本的终端命令执行工具函数

    Args:
        command: 要执行的命令
        working_directory: 工作目录，默认为当前目录
        timeout: 超时时间（秒），默认30秒
        capture_output: 是否捕获输出，默认True
        safe_mode: 安全模式，限制危险命令，默认True

    Returns:
        Dict包含执行结果信息
    """
    # 在线程池中执行同步版本
    return await asyncio.to_thread(
        execute_terminal_command,
        command,
        working_directory,
        timeout,
        capture_output,
        safe_mode,
    )


def format_terminal_tool_for_model() -> Dict[str, Any]:
    """
    格式化终端命令工具的描述，供模型调用

    Returns:
        工具的JSON Schema描述
    """
    return {
        "type": "function",
        "function": {
            "name": "execute_terminal_command",
            "description": "Execute terminal/shell commands and return the results. Useful for running system commands, checking file contents, running scripts, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The terminal command to execute (e.g., 'ls -la', 'python script.py', 'git status')",
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Optional working directory where to execute the command. If not specified, uses current directory.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds for command execution. Default is 30 seconds.",
                        "default": 30,
                    },
                    "safe_mode": {
                        "type": "boolean",
                        "description": "Enable safe mode to block dangerous commands. Default is true.",
                        "default": True,
                    },
                },
                "required": ["command"],
            },
        },
    }


# 测试函数
def test_terminal_command_tool():
    """测试终端命令工具函数"""
    print_rule("Terminal Command Tool Test")

    # 测试1: 简单的ls命令
    print_message("Test 1: List current directory")
    result1 = execute_terminal_command("ls -la")
    print_json(result1, title="Result 1")

    # 测试2: Python命令
    print_message("Test 2: Python version")
    result2 = execute_terminal_command("python --version")
    print_json(result2, title="Result 2")

    # 测试3: 危险命令测试（应该被阻止）
    print_message("Test 3: Dangerous command (should be blocked)")
    result3 = execute_terminal_command("rm -rf /tmp/test", safe_mode=True)
    print_json(result3, title="Result 3")

    # 测试4: 无效命令
    print_message("Test 4: Invalid command")
    result4 = execute_terminal_command("nonexistentcommand123")
    print_json(result4, title="Result 4")

    # 测试5: 工作目录
    print_message("Test 5: Custom working directory")
    result5 = execute_terminal_command("pwd", working_directory="/tmp")
    print_json(result5, title="Result 5")


class TaskPlanner:
    """基于LLM的任务规划器"""

    def __init__(self, agent):
        self.agent = agent

    def analyze_task_complexity(self, description: str) -> TaskAnalysis:
        """LLM分析任务复杂度"""
        prompt = f"""
分析以下任务的复杂度和执行方式：

任务：{description}

请返回JSON格式：
{{
    "is_simple": boolean,
    "complexity_score": 1-10,
    "estimated_steps": number,
    "requires_tools": ["terminal", "file_operations", "analysis"],
    "reasoning": "为什么这样判断"
}}

判断标准：
- 简单任务(1-3分)：单一操作，如查看文件、执行命令、简单分析
- 复杂任务(4-10分)：需要多步骤，如项目分析、环境设置、综合报告生成

只返回JSON，不要其他解释。
"""

        try:
            response = self.agent.model.chat([user(content=prompt)])
            response_text = (
                response.message.content.text
                if response.message and response.message.content
                else str(response)
            )
            self.agent.log(f"Task complexity analysis: {response_text}")
            return TaskAnalysis.from_json(response_text)
        except Exception as e:
            self.agent.log(f"Failed to analyze task complexity: {e}")
            # 默认为简单任务
            return TaskAnalysis(
                is_simple=True,
                complexity_score=1,
                estimated_steps=1,
                requires_tools=["terminal"],
                reasoning=f"分析失败，默认为简单任务: {e}",
            )

    def generate_execution_plan(self, description: str) -> ExecutionPlan:
        """LLM生成详细执行计划"""
        prompt = f"""
为以下复杂任务制定详细的执行计划：

任务：{description}

要求：
1. 分解为具体的子任务
2. 明确每个子任务的依赖关系
3. 指定执行工具（terminal, analysis, file_operation）
4. 预估执行时间

返回JSON格式：
{{
    "subtasks": [
        {{
            "id": "step_1",
            "description": "具体操作描述",
            "tool_type": "terminal|analysis|file_operation",
            "dependencies": [],
            "estimated_duration": 30,
            "validation_criteria": "如何验证完成"
        }}
    ],
    "total_estimated_time": 180,
    "success_criteria": "整体任务完成标准"
}}

只返回JSON，不要其他解释。
"""

        try:
            response = self.agent.model.chat([user(content=prompt)])
            response_text = (
                response.message.content.text
                if response.message and response.message.content
                else str(response)
            )
            self.agent.log(f"Execution plan generated: {response_text}")

            # 添加调试信息
            execution_plan = ExecutionPlan.from_json(response_text)
            self.agent.log(
                f"Parsed execution plan: {len(execution_plan.subtasks)} subtasks, success_criteria: {execution_plan.success_criteria}"
            )
            return execution_plan
        except Exception as e:
            self.agent.log(f"Failed to generate execution plan: {e}")
            # 返回空计划
            return ExecutionPlan(
                subtasks=[],
                total_estimated_time=0,
                success_criteria=f"计划生成失败: {e}",
            )


# 多步任务测试
async def multi_step_test():
    """测试多步任务执行功能"""
    print_rule("Multi-Step Task Execution Test")

    agent = AsyncAgent("Multi-Step Agent")

    # 测试1: 简单任务（应该直接执行）
    print_message("\n=== Test 1: Simple Task ===")
    simple_result = agent.run("检查当前目录的文件列表")
    print_message(f"Simple task result: {simple_result[:200]}...")

    # 测试2: 复杂任务（应该分解为多步）
    print_message("\n=== Test 2: Complex Task ===")
    complex_result = agent.run(
        """
    分析当前Python项目的基本情况，包括：
    1. 检查项目结构和主要文件
    2. 查看Python版本和依赖
    3. 检查是否有虚拟环境
    4. 生成项目基本信息报告
    """
    )
    print_message(f"Complex task result: {complex_result}")

    # 测试3: 中等复杂度任务
    print_message("\n=== Test 3: Medium Complexity Task ===")
    medium_result = agent.run(
        """
    检查系统环境并验证开发环境配置，包括检查Python版本、
    查看当前目录内容，并确认项目是否可以正常运行
    """
    )
    print_message(f"Medium task result: {medium_result}")


# 运行入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "simple":
            # 运行简单测试
            asyncio.run(simple_test())
        elif sys.argv[1] == "terminal":
            # 运行终端工具测试
            asyncio.run(terminal_tool_test())
        elif sys.argv[1] == "multi":
            # 运行多步任务测试
            asyncio.run(multi_step_test())
        elif sys.argv[1] == "main":
            # 运行完整的调度器测试
            asyncio.run(main())
        else:
            print("Usage: python async_task_test.py [simple|terminal|multi|main]")
            print("  simple   - Run simple chat tests")
            print("  terminal - Run terminal tool tests")
            print("  multi    - Run multi-step task tests")
            print("  main     - Run full task scheduler tests")
    else:
        # 默认运行多步任务测试
        asyncio.run(multi_step_test())
