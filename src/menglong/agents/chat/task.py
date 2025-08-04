import asyncio
import heapq
import json
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

# menglong schema
from menglong.ml_model.schema import user, assistant

# log
from menglong.ml_model.schema.ml_request import ToolMessage
from menglong.utils.log import print_message, print_rule, print_json
from menglong.utils.log.common import MessageType


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


class TaskIDGenerator:
    """任务ID生成器"""

    def __init__(self):
        self._current_id = 0

    def next_id(self) -> int:
        """生成下一个任务ID"""
        self._current_id += 1
        return self._current_id


@dataclass
class TaskContext:
    """执行上下文，保存执行过程中的状态"""

    system: str = ""
    message_context: List[Any] = field(default_factory=list)
    remote_responses: List[Dict[str, Any]] = field(default_factory=list)
    temp_tool_calls: Optional[Any] = None


# 全局任务ID生成器
_task_id_generator = TaskIDGenerator()


@dataclass
class Task:
    """任务数据模型"""

    prompt: str
    tools: Optional[List[Any]] = None
    result: Optional[Any] = None
    task_id: int = field(default_factory=lambda: _task_id_generator.next_id())


@dataclass
class TaskDesc:
    task_id: int
    status: TaskStatus = TaskStatus.CREATED
    context: TaskContext = field(default_factory=TaskContext)
    priority: TaskPriority = TaskPriority.NORMAL
    parent_id: Optional[int] = None
    dependencies: Optional[List[int]] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    worker: Optional[asyncio.Task] = None
    is_first_run: bool = True


class TaskManager:
    """任务管理器"""

    DONE_TOKEN = "[DONE]"

    def __init__(self, agent):
        """初始化任务管理器"""
        self.agent = agent
        self.task_descriptions: Dict[int, TaskDesc] = {}
        self.tasks: Dict[int, Task] = {}
        self.root_task: Optional[TaskDesc] = None
        self.new_task_callback: Optional[Callable] = None

    def create_task(self, prompt: str, tools: Optional[List[Any]] = None) -> int:
        """创建新任务"""
        task = Task(
            prompt=prompt,
            tools=tools,
        )
        task_desc = TaskDesc(task_id=task.task_id)
        self.tasks[task.task_id] = task
        self.task_descriptions[task.task_id] = task_desc

        return task.task_id

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    def get_task_desc(self, task_id: int) -> Optional[TaskDesc]:
        """获取任务详情"""
        return self.task_descriptions.get(task_id)

    def _validate_task_exists(self, task_id: int) -> Tuple[Task, TaskDesc]:
        """验证任务存在并返回任务和描述"""
        task = self.get_task(task_id)
        task_desc = self.get_task_desc(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")
        if not task_desc:
            raise ValueError(f"Task description {task_id} not found")

        return task, task_desc

    def _get_dependency_status(self, task_desc: TaskDesc) -> List[Dict[str, Any]]:
        """获取任务依赖状态"""
        dependency_status = []
        for dep_id in task_desc.dependencies:
            dep_task = self.get_task(dep_id)
            if not dep_task:
                raise ValueError(f"Dependency task {dep_id} not found")
            if not dep_task.result:
                raise ValueError(f"Task depends on {dep_id} but it's not completed")

            dependency_status.append(
                {"name": dep_task.prompt, "result": dep_task.result}
            )
        return dependency_status

    def _create_task_prompt(
        self, original_prompt: str, dependency_status: List[Dict[str, Any]]
    ) -> str:
        """创建包含依赖状态的任务提示"""
        status_template = """
        当前任务依赖状态:
            {dep_status}

        任务结束:
            确认任务是否正确完成，当正确完成时，只输出任务预期输出并以{done_token}结尾，自动结束。
            如果选择plan_task工具，任务的执行结果就是plan_task工具结果，并输出{done_token}结尾，其余任务快速交给子任务执行。
        """

        return original_prompt + status_template.format(
            dep_status=dependency_status, done_token=self.DONE_TOKEN
        )

    def _check_completion(self, response) -> bool:
        """检查任务是否完成"""
        if not hasattr(response.message, "content") or not response.message.content:
            return True

        text = response.message.content.text
        if text and text.strip().endswith(self.DONE_TOKEN):
            response.message.content.text = text.rstrip(self.DONE_TOKEN).strip()
            return False
        return True

    def _has_tool_calls(self, message) -> bool:
        """检查消息是否包含工具调用"""
        return hasattr(message, "tool_descriptions") and bool(message.tool_descriptions)

    def _get_tool_names(self, tools: Optional[List[Any]]) -> List[str]:
        """获取工具名称列表"""
        if not tools:
            return []
        return [tool._tool_info.name for tool in tools]

    async def run_task(self, task_id: int) -> Any:
        """执行任务"""
        task, task_desc = self._validate_task_exists(task_id)

        print_rule(f"Running task {task_id}")
        print_message(f"Task {task_id}: {task.prompt}")

        # 准备执行环境
        dependency_status = self._get_dependency_status(task_desc)
        message_context = task_desc.context.message_context
        tools = task.tools

        # 显示工具信息
        tool_names = self._get_tool_names(tools)
        print_message(f"Tools required: {tool_names}")

        # 构建提示信息
        full_prompt = self._create_task_prompt(task.prompt, dependency_status)
        message_context.append(user(content=full_prompt))

        # 执行任务
        if not tools:
            result = await self._execute_task_without_tools(message_context)
        else:
            result = await self._execute_task_with_tools(
                task_id, message_context, tools
            )

        # 保存结果
        task.result = result
        print_message(
            result, title=f"Task {task_id} result", msg_type=MessageType.AGENT
        )

        await asyncio.sleep(0)  # 确保协程调度
        return result

    async def _execute_task_without_tools(self, message_context: List[Any]) -> str:
        """执行不需要工具的任务"""
        response = self.agent.model.chat(message_context)
        result = response.message.content.text
        message_context.append(assistant(content=str(result)))
        return result

    async def _execute_task_with_tools(
        self, task_id: int, message_context: List[Any], tools: List[Any]
    ) -> Any:
        """执行需要工具的任务"""
        continue_execution = True

        while continue_execution:
            response = self.agent.model.chat(message_context, tools=tools)

            if not self._has_tool_calls(response.message):
                # 无工具调用，处理文本响应
                result = response.message.content.text
                message_context.append(assistant(content=result))
                continue_execution = self._check_completion(response)
            else:
                # 有工具调用，执行工具
                print_json(response.message.model_dump(), title="Tool call response")
                tool_results = await self.execute_tool_call(
                    task_id, tools, response.message.tool_descriptions
                )

                message_context.append(response.message)

                # 处理工具执行结果
                for tool_result in tool_results:
                    tool_message = ToolMessage(
                        content=json.dumps(tool_result["content"], ensure_ascii=False),
                        tool_id=tool_result.get("id"),
                    )
                    print_message(tool_result["content"], title="Tool result")
                    message_context.append(tool_message)

                result = [tool_result["content"] for tool_result in tool_results]

        return result

    async def execute_tool_call(
        self, task_id: int, tools: List[Any], tool_descriptions
    ) -> List[Dict[str, Any]]:
        """执行工具调用

        Args:
            task_id: 任务ID
            tools: 可用工具列表
            tool_descriptions: 工具调用描述

        Returns:
            工具执行结果列表
        """
        tool_results = []

        for tool_call in tool_descriptions:
            tool_name = tool_call.name

            # 解析参数
            try:
                if (
                    isinstance(tool_call.arguments, str)
                    and tool_call.arguments.strip() == ""
                ):
                    arguments = {}
                else:
                    arguments = (
                        json.loads(tool_call.arguments)
                        if isinstance(tool_call.arguments, str)
                        else tool_call.arguments
                    )
            except json.JSONDecodeError:
                print_message(
                    f"Error decoding JSON for tool '{tool_name}': {tool_call.arguments}",
                    msg_type=MessageType.ERROR,
                )
                arguments = tool_call.arguments

            # 执行工具
            tool_result = await self._execute_single_tool(
                task_id, tools, tool_name, arguments
            )
            tool_results.append({"id": tool_call.id, "content": tool_result})

        return tool_results

    async def _execute_single_tool(
        self, task_id: int, tools: List[Any], tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """执行单个工具调用

        Args:
            task_id: 任务ID
            tools: 可用工具列表
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        # 构建工具字典
        tools_dict = self._build_tools_dict(tools)

        if tool_name not in tools_dict:
            return f"Error: Tool '{tool_name}' not found"

        try:
            print_json(arguments, title=f"Executing tool '{tool_name}' with arguments")

            if tool_name == "plan_task":
                return await self._execute_plan_task_tool(
                    task_id, tools_dict, tool_name, arguments
                )
            else:
                return await self._execute_regular_tool(
                    tools_dict, tool_name, arguments
                )

        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def _build_tools_dict(self, tools: List[Any]) -> Dict[str, Dict[str, Any]]:
        """构建工具字典"""
        return {
            tool._tool_info.name: {
                "function": tool._tool_info.func,
                "description": tool._tool_info.description,
                "parameters": tool._tool_info.parameters,
            }
            for tool in tools
        }

    async def _execute_plan_task_tool(
        self,
        task_id: int,
        tools_dict: Dict[str, Dict[str, Any]],
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        """执行 plan_task 工具"""
        tool_func = tools_dict[tool_name]["function"]

        # 为 plan_task 添加工具字典参数
        enhanced_args = arguments.copy()
        enhanced_args["tools"] = tools_dict

        # 执行工具
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**enhanced_args)
        else:
            result = tool_func(**enhanced_args)

        # 解析任务计划
        self.parse_task_plan(task_id, result)

        return (
            json.dumps(result, ensure_ascii=False)
            if isinstance(result, dict)
            else str(result)
        )

    async def _execute_regular_tool(
        self,
        tools_dict: Dict[str, Dict[str, Any]],
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        """执行普通工具"""
        tool_func = tools_dict[tool_name]["function"]

        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**arguments)
        else:
            result = tool_func(**arguments)

        return (
            json.dumps(result, ensure_ascii=False)
            if isinstance(result, dict)
            else str(result)
        )

    def parse_task_plan(self, current_task_id: int, task_plan: Dict[str, Any]) -> None:
        """解析任务计划并创建子任务

        Args:
            current_task_id: 当前任务ID
            task_plan: 任务计划字典
        """
        if "subtasks" not in task_plan:
            return

        # 获取根任务信息
        root_task = self.get_task(current_task_id)
        root_desc = self.get_task_desc(current_task_id)

        if not root_task or not root_task.tools:
            raise ValueError(f"Root task {current_task_id} not found or has no tools")

        # 创建工具映射
        tool_name_to_func = {tool._tool_info.name: tool for tool in root_task.tools}

        # 创建标签到ID的映射
        tag_to_id = {task_plan["task_tag"]: current_task_id}

        # 创建子任务
        created_tasks = []
        created_descs = []

        for subtask_data in task_plan["subtasks"]:
            subtask_id = _task_id_generator.next_id()
            tag_to_id[subtask_data["task_tag"]] = subtask_id

            # 映射工具
            subtask_tools = self._map_tools_for_subtask(
                subtask_data["tool_require"], tool_name_to_func
            )

            # 创建子任务
            subtask = Task(
                prompt=subtask_data["description"],
                tools=subtask_tools,
            )
            subtask.task_id = subtask_id  # 手动设置ID

            # 创建子任务描述
            subtask_desc = TaskDesc(
                task_id=subtask_id,
                parent_id=tag_to_id[subtask_data["parent"]],
                context=deepcopy(root_desc.context),
                status=TaskStatus.CREATED,
            )

            created_tasks.append((subtask, subtask_data))
            created_descs.append(subtask_desc)

        # 处理依赖关系
        for (subtask, subtask_data), task_desc in zip(created_tasks, created_descs):
            for dep_tag in subtask_data.get("dependencies", []):
                if dep_tag in tag_to_id:
                    task_desc.dependencies.append(tag_to_id[dep_tag])

        # 注册任务
        for (subtask, _), desc in zip(created_tasks, created_descs):
            self.tasks[subtask.task_id] = subtask
            self.task_descriptions[subtask.task_id] = desc

        # 通知调度器
        if self.new_task_callback and created_tasks:
            self.new_task_callback()

    def _map_tools_for_subtask(
        self, required_tool_names: List[str], tool_name_to_func: Dict[str, Any]
    ) -> List[Any]:
        """为子任务映射所需工具"""
        subtask_tools = []
        for tool_name in required_tool_names:
            if tool_name in tool_name_to_func:
                subtask_tools.append(tool_name_to_func[tool_name])
            else:
                print_message(
                    f"Warning: Tool '{tool_name}' not found in available tools"
                )
        return subtask_tools


class PriorityQueue:
    """异步优先级队列"""

    def __init__(self):
        self.queue = []

    def add(self, item: Any):
        """添加项目到队列"""
        heapq.heappush(self.queue, item)

    def get(self) -> Any:
        """从队列获取项目"""
        if self.is_empty():
            return None
        else:
            return heapq.heappop(self.queue)

    def is_empty(self) -> bool:
        """检查队列是否为空"""
        return len(self.queue) == 0

    def size(self) -> int:
        """获取队列大小"""
        return len(self.queue)


class TaskScheduler:
    """任务调度器"""

    SCHEDULER_TIMEOUT = 0.1  # 调度器超时时间（秒）

    def __init__(self, task_manager: TaskManager):
        """初始化任务调度器"""
        self.task_manager = task_manager
        self.task_queue: PriorityQueue = PriorityQueue()

        # 异步相关
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.scheduler_task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()

        # 事件通知机制
        self.task_completed_event = asyncio.Event()
        self.new_task_event = asyncio.Event()

        # 设置回调
        self.task_manager.new_task_callback = self._on_new_task_created

    async def shutdown(self) -> None:
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

    async def scheduler_loop(self) -> None:
        """调度器主循环"""
        try:
            while not self.stop_event.is_set():
                # 清理已完成的任务
                await self._cleanup_completed_tasks()

                # 查找并执行就绪任务
                await self._process_ready_tasks()

                # 检查是否应该停止
                if await self._should_stop_scheduler():
                    print_message("All tasks completed, stopping scheduler")
                    break

                # 等待事件或超时
                await self._wait_for_events()

        except Exception as e:
            print_message(f"Error in scheduler loop: {e}")
        finally:
            await self._cleanup_all_tasks()

    async def _process_ready_tasks(self) -> None:
        """处理就绪任务"""
        print_rule("Finding ready tasks")
        ready_tasks = self._find_ready_tasks()
        print_message(f"Ready tasks: {ready_tasks}")

        if not ready_tasks:
            return

        # 将就绪任务加入队列并执行
        self._add_tasks_to_queue(ready_tasks)
        print_rule("Executing ready tasks")

        while not self.task_queue.is_empty():
            task_id = self.task_queue.get()
            if task_id is not None:
                await self._start_task_execution(task_id)

    async def _start_task_execution(self, task_id: int) -> None:
        """开始执行任务"""
        print_message(f"Scheduling task {task_id}")

        task_desc = self.task_manager.get_task_desc(task_id)
        if not task_desc:
            print_message(f"Task description {task_id} not found")
            return

        # 更新任务状态
        task_desc.status = TaskStatus.RUNNING
        task_desc.start_time = asyncio.get_event_loop().time()

        # 创建并启动工作协程
        worker = asyncio.create_task(self._run_task_with_callback(task_id))
        task_desc.worker = worker
        self.running_tasks[task_id] = worker

        print_message(f"Task {task_id} started")

    async def _wait_for_events(self) -> None:
        """等待事件或超时"""
        try:
            await asyncio.wait_for(
                asyncio.wait(
                    [
                        asyncio.create_task(self.task_completed_event.wait()),
                        asyncio.create_task(self.new_task_event.wait()),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                ),
                timeout=self.SCHEDULER_TIMEOUT,
            )
            # 重置事件
            self.task_completed_event.clear()
            self.new_task_event.clear()
        except asyncio.TimeoutError:
            # 超时是正常的，继续下一轮循环
            pass

    async def _cleanup_completed_tasks(self) -> bool:
        """清理已完成的任务，返回是否有任务完成"""
        completed_task_ids = []

        for task_id, worker in self.running_tasks.items():
            if worker.done():
                completed_task_ids.append(task_id)
                await self._handle_completed_task(task_id, worker)

        # 从运行任务字典中移除已完成的任务
        for task_id in completed_task_ids:
            del self.running_tasks[task_id]

        # 如果有任务完成，触发事件
        if completed_task_ids:
            self.task_completed_event.set()

        return len(completed_task_ids) > 0

    async def _handle_completed_task(self, task_id: int, worker: asyncio.Task) -> None:
        """处理已完成的任务"""
        task_desc = self.task_manager.get_task_desc(task_id)
        if not task_desc:
            return

        if worker.exception():
            task_desc.status = TaskStatus.FAILED
            print_message(f"Task {task_id} failed: {worker.exception()}")
        else:
            task_desc.status = TaskStatus.COMPLETED
            print_message(f"Task {task_id} completed successfully")

        task_desc.end_time = asyncio.get_event_loop().time()
        task_desc.worker = None

    async def _should_stop_scheduler(self) -> bool:
        """检查是否应该停止调度器"""
        # 检查是否有运行中的任务
        if self.running_tasks:
            print_message(f"Still have {len(self.running_tasks)} running tasks")
            return False

        # 检查是否有待执行的任务
        pending_statuses = [TaskStatus.CREATED, TaskStatus.READY]
        for task_desc in self.task_manager.task_descriptions.values():
            if task_desc.status in pending_statuses:
                print_message(f"Still have pending tasks in status: {task_desc.status}")
                return False

        print_message("No running or pending tasks found")
        return True

    def _find_ready_tasks(self) -> List[int]:
        """查找所有就绪任务"""
        ready_tasks = []

        for task_id, task_desc in self.task_manager.task_descriptions.items():
            if task_desc.status == TaskStatus.CREATED and self._check_dependencies(
                task_id
            ):
                task_desc.status = TaskStatus.READY
                ready_tasks.append(task_id)

        return ready_tasks

    def _add_tasks_to_queue(self, task_ids: List[int]) -> None:
        """将就绪任务添加到调度队列"""
        for task_id in task_ids:
            self.task_queue.add(task_id)

    def _check_dependencies(self, task_id: int) -> bool:
        """检查任务依赖是否满足"""
        task_desc = self.task_manager.get_task_desc(task_id)
        if not task_desc:
            print_message(f"Task description {task_id} not found")
            return False

        for dep_id in task_desc.dependencies:
            dep_desc = self.task_manager.get_task_desc(dep_id)
            if not dep_desc or dep_desc.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _cleanup_all_tasks(self) -> None:
        """清理所有运行中的任务"""
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)

    async def cancel_task(self, task_id: int) -> None:
        """取消任务"""
        if task_id in self.running_tasks:
            worker = self.running_tasks[task_id]
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
            del self.running_tasks[task_id]

        task_desc = self.task_manager.get_task_desc(task_id)
        if task_desc:
            task_desc.status = TaskStatus.CANCELED
            task_desc.end_time = asyncio.get_event_loop().time()

    async def _run_task_with_callback(self, task_id: int) -> Any:
        """执行任务并在完成时触发事件"""
        try:
            result = await self.task_manager.run_task(task_id)
            self.task_completed_event.set()
            return result
        except Exception as e:
            self.task_completed_event.set()
            raise e

    def _on_new_task_created(self) -> None:
        """新任务创建回调"""
        self.new_task_event.set()
