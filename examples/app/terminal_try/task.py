from abc import ABC
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field
import heapq
from json import JSONDecodeError
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Callable, Tuple, Awaitable
from enum import Enum
import asyncio

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
    WAITING_REMOTE = "WaitingRemote"  # 等待远程执行结果
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELED = "Canceled"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskID:
    _id = -1

    @staticmethod
    def next():
        TaskID._id += 1
        return TaskID._id


@dataclass
class TaskContext:
    """执行上下文，保存执行过程中的状态"""

    message_context: List[Any] = field(default_factory=list)
    # file_operations: List[Dict] = field(default_factory=list)
    # command_results: List[Dict] = field(default_factory=list)
    # variables: Dict[str, Any] = field(default_factory=dict)
    # artifacts: List[str] = field(default_factory=list)
    # step_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    task_id: int = TaskID.next()
    prompt: str = ""
    tools: Optional[List[Any]] = None
    result: Optional[Dict[str, Any]] = None


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


@dataclass
class RemoteTaskRequest:
    """远程执行请求"""

    request_id: str
    task_id: int
    # command: str
    # created_at: float
    # timeout: Optional[float] = None


@dataclass
class RemoteTaskResult:
    """远程执行结果"""

    request_id: str
    # success: bool
    result: Any
    # error: Optional[str] = None
    # completed_at: Optional[float] = None


class RemoteTaskContext:
    """远程任务执行上下文"""

    def __init__(self):
        # 创建上下文变量
        # self.client_var = ContextVar("client")
        self.task_id_var = ContextVar("task_id")
        self.request_id_var = ContextVar("request_id")
        self.agent_id_var = ContextVar("agent_id")

    @contextmanager
    def context(self, task_id: int, agent_id: int, request_id: str):
        """远程任务上下文管理器"""
        task_id_token = self.task_id_var.set(task_id)
        agent_id_token = self.agent_id_var.set(agent_id)
        request_id_token = self.request_id_var.set(request_id)

        try:
            yield
        finally:
            self.task_id_var.reset(task_id_token)
            self.agent_id_var.reset(agent_id_token)
            self.request_id_var.reset(request_id_token)


class RemoteTaskManager:
    """远程执行管理器"""

    def __init__(self):
        # 存储待处理的远程执行请求
        self.pending_requests: Dict[str, RemoteTaskRequest] = {}

        # 存储任务ID到请求ID的映射
        self.task_to_request: Dict[int, str] = {}

        # 存储完成的结果，等待任务获取
        self.completed_results: Dict[str, RemoteTaskResult] = {}

        self.remote_task_context = RemoteTaskContext()

        # 任务恢复回调函数
        self.task_resume_callbacks: Dict[
            int, Callable[[RemoteTaskResult], Awaitable[None]]
        ] = {}

    def create_remote_request(self, task_id: int) -> str:
        """创建远程执行请求"""
        request_id = str(uuid.uuid4())
        request = RemoteTaskRequest(
            request_id=request_id,
            task_id=task_id,
        )

        self.pending_requests[request_id] = request
        self.task_to_request[task_id] = request_id

        return request_id

    def run_remote_task(self, client, task_id: int, agent_id: int, request_id: str):
        """运行远程任务"""
        with self.remote_task_context.context(client, task_id, agent_id, request_id):
            pass  # 这里可以添加远程任务执行的逻辑

    def handle_remote_response(
        self, request_id: str, success: bool, result: Any, error: Optional[str] = None
    ):
        """处理从WebSocket接收到的远程执行结果"""
        execution_result = RemoteTaskResult(
            request_id=request_id,
            success=success,
            result=result,
            error=error,
            completed_at=time.time(),
        )

        self.completed_results[request_id] = execution_result

        # 如果有任务恢复回调，调用它
        request = self.pending_requests.get(request_id)
        if request and request.task_id in self.task_resume_callbacks:
            callback = self.task_resume_callbacks.pop(request.task_id)
            # 异步调用回调
            asyncio.create_task(callback(execution_result))

    def register_task_resume_callback(
        self, task_id: int, callback: Callable[[RemoteTaskResult], Awaitable[None]]
    ):
        """注册任务恢复回调"""
        self.task_resume_callbacks[task_id] = callback

    def get_pending_request_by_task(self, task_id: int) -> Optional[RemoteTaskRequest]:
        """根据任务ID获取待处理的请求"""
        request_id = self.task_to_request.get(task_id)
        return self.pending_requests.get(request_id) if request_id else None


class TaskManager:
    """任务管理器接口"""

    def __init__(self, agent):
        """初始化任务管理器"""
        self.agent = agent
        self.task_descriptions: Dict[int, TaskDesc] = {}
        self.tasks: Dict[int, Task] = {}

        self.root_task: Optional[TaskDesc] = None

        self.ex_components = {
            "websocket_client": ContextVar("remote_client", default=None),
        }
        self.remote_temp_context = {
            "task_id": ContextVar("remote_task_id", default=None),
            "agent_id": ContextVar("remote_agent_id", default=None),
            "request_id": ContextVar("remote_request_id", default=None),
        }

        # 新任务创建回调函数
        self.new_task_callback: Optional[Callable] = None

        # 远程执行管理器
        self.remote_manager = RemoteTaskManager()

    def create_task(self, prompt: str, tools: Optional[List[Any]] = None) -> int:
        """创建新任务"""
        task = Task(
            task_id=TaskID.next(),
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

    # Local Task
    async def run_task(self, task_id: int) -> Any:
        """执行任务"""
        task = self.get_task(task_id)
        task_desc = self.get_task_desc(task_id)
        print_rule(f"Running task {task_id}")
        if not task:
            raise ValueError(f"Task {task_id} not found")
        print_message(f"Task {task_id} found,{task}")
        prompt = task.prompt
        tools = task.tools
        mc = task_desc.context.message_context

        print_message(f"{prompt}")
        d = [tool._tool_info.name for tool in tools] if tools else []
        print_message(f"Tools required: {d}")

        # 检查任务依赖的结果
        dep_status = []
        for dep in task_desc.dependencies:
            t = self.get_task(dep)
            dep_name = t.prompt
            dep_result = t.result
            dep_status.append({"name": dep_name, "result": dep_result})
            if not dep_result:
                raise ValueError(
                    f"Task {task_id} depends on {dep} but it's not completed"
                )
        # 任务状态信息
        done_token = "[DONE]"
        status = """
        当前任务依赖状态:
            {dep_status}

        任务结束:
            确认任务是否正确完成，当正确完成时，只输出任务预期输出并以{done_token}结尾，自动结束。
            如果选择plan_task工具，任务的执行结果就是plan_task工具结果，并输出{done_token}结尾，其余任务快速交给子任务执行。
"""

        mc.append(
            user(
                content=prompt
                + status.format(dep_status=dep_status, done_token=done_token)
            )
        )
        print("---------user-----------")
        print(mc)
        print("--------------------")
        if tools is None or tools is []:
            res = self.agent.model.chat(mc)
            r = res.message.content.text
            mc.append(assistant(content=str(r)))
        else:
            done = True
            need_break = False

            def check_done(res):
                text = res.message.content.text
                if text and text.strip().endswith(done_token):
                    res.message.content.text = text.strip(done_token)
                    return False
                return True

            while done:
                res = self.agent.model.chat(
                    mc,
                    tools=tools,
                )

                if not self.is_use_tool(res.message):
                    r = res.message.content.text
                    mc.append(assistant(content=r))
                    done = check_done(res)
                else:
                    print_json(res.message.model_dump(), title="Tool call response")
                    tool_results = await self.execute_tool_call(
                        task_id, tools, res.message.tool_descriptions
                    )

                    mc.append(res.message)
                    for tool_result in tool_results:
                        tool_results_message = ToolMessage(
                            content=json.dumps(
                                tool_result["content"], ensure_ascii=False
                            ),
                            tool_id=tool_result.get("id"),
                        )
                        print_message(tool_result["content"], title="Tool result")
                        mc.append(tool_results_message)

                    # step_res = self.agent.model.chat(messages=mc, tools=tools)

                    # if not done:
                    #     mc.append()
                    # r = step_res.message.content.text
                    r = [tool_result["content"] for tool_result in tool_results]
                    task_desc.is_first_run = False

        print_message(r, title=f"Task {task_id} result", msg_type=MessageType.AGENT)
        task.result = r

        print("---------assistant-----------")
        print(mc)
        print("--------------------")
        # task_desc = self.get_task_desc(task_id)
        # task_desc.status = TaskStatus.COMPLETED
        # task_desc.end_time = asyncio.get_event_loop().time()
        # task_desc.worker = None  # 清理worker引用
        await asyncio.sleep(0)  # 确保协程调度

    async def run_task_async(self, task_id: int) -> Any:
        """执行任务"""
        task = self.get_task(task_id)
        task_desc = self.get_task_desc(task_id)

        if task_desc.is_first_run:
            print_rule(f"Running task {task_id}")
            if not task:
                raise ValueError(f"Task {task_id} not found")
            print_message(f"Task {task_id} found,{task}")
            prompt = task.prompt
            tools = task.tools
            mc = task_desc.context.message_context

            print_message(f"{prompt}")
            d = [tool._tool_info.name for tool in tools] if tools else []
            print_message(f"Tools required: {d}")

            # 检查任务依赖的结果
            dep_status = []
            for dep in task_desc.dependencies:
                t = self.get_task(dep)
                dep_name = t.prompt
                dep_result = t.result
                dep_status.append({"name": dep_name, "result": dep_result})
                if not dep_result:
                    raise ValueError(
                        f"Task {task_id} depends on {dep} but it's not completed"
                    )
            # 任务状态信息
            done_token = "[DONE]"
            status = """
            当前任务依赖状态:
                {dep_status}

            任务结束:
                确认任务是否正确完成，当正确完成时，只输出任务预期输出并以{done_token}结尾，自动结束。
                如果选择plan_task工具，任务的执行结果就是plan_task工具结果，并输出{done_token}结尾，其余任务快速交给子任务执行。
    """

            mc.append(
                user(
                    content=prompt
                    + status.format(dep_status=dep_status, done_token=done_token)
                )
            )
            print("---------user-----------")
            print(mc)
            print("--------------------")
            if tools is None or tools is []:
                res = self.agent.model.chat(mc)
                r = res.message.content.text
                mc.append(assistant(content=str(r)))
            else:
                done = True
                need_break = False

                def check_done(res):
                    text = res.message.content.text
                    if text and text.strip().endswith(done_token):
                        res.message.content.text = text.strip(done_token)
                        return False
                    return True

                while done:
                    res = self.agent.model.chat(
                        mc,
                        tools=tools,
                    )

                    if not self.is_use_tool(res.message):
                        r = res.message.content.text
                        mc.append(assistant(content=r))
                        done = check_done(res)
                    else:
                        print_json(res.message.model_dump(), title="Tool call response")
                        tool_results = self.execute_tool_call(
                            task_id, tools, res.message.tool_descriptions
                        )
                        for tool_results in tool_results:
                            if tool_results.get("remote", False):
                                need_break = True

                        if need_break:
                            task_desc.is_first_run = False
                            break
                        mc.append(res.message)
                        for tool_result in tool_results:
                            tool_results_message = ToolMessage(
                                content=json.dumps(
                                    tool_result["content"], ensure_ascii=False
                                ),
                                tool_id=tool_result.get("id"),
                            )
                            print_message(tool_result["content"], title="Tool result")
                            mc.append(tool_results_message)

                        # step_res = self.agent.model.chat(messages=mc, tools=tools)

                        # if not done:
                        #     mc.append()
                        # r = step_res.message.content.text
                        r = [tool_result["content"] for tool_result in tool_results]
                        task_desc.is_first_run = False

            print_message(r, title=f"Task {task_id} result", msg_type=MessageType.AGENT)
            task.result = r

            print("---------assistant-----------")
            print(mc)
            print("--------------------")
            # task_desc = self.get_task_desc(task_id)
            # task_desc.status = TaskStatus.COMPLETED
            # task_desc.end_time = asyncio.get_event_loop().time()
            # task_desc.worker = None  # 清理worker引用
            await asyncio.sleep(0)  # 确保协程调度
        else:
            responses = task_desc.context.remote_responses
            mc = task_desc.context.message_context
            temp_tool_calls = task_desc.context.temp_tool_calls
            mc.append(temp_tool_calls)
            for tool_result in responses:
                tool_results_message = ToolMessage(
                    content=json.dumps(tool_result["content"], ensure_ascii=False),
                    tool_id=tool_result.get("id"),
                )
                print_message(tool_result["content"], title="Tool result")
                mc.append(tool_results_message)
            r = [tool_result["content"] for tool_result in tool_results]

            done = True
            need_break = False

            def check_done(res):
                text = res.message.content.text
                if text and text.strip().endswith(done_token):
                    res.message.content.text = text.strip(done_token)
                    return False
                return True

            while done:
                res = self.agent.model.chat(
                    mc,
                    tools=tools,
                )

                if not self.is_use_tool(res.message):
                    r = res.message.content.text
                    mc.append(assistant(content=r))
                    done = check_done(res)
                else:
                    print_json(res.message.model_dump(), title="Tool call response")
                    tool_results = await self.execute_tool_call(
                        task_id, tools, res.message.tool_descriptions
                    )
                    for tool_results in tool_results:
                        if tool_results.get("remote", False):
                            need_break = True

                    if need_break:
                        break
                    mc.append(res.message)
                    for tool_result in tool_results:
                        tool_results_message = ToolMessage(
                            content=json.dumps(
                                tool_result["content"], ensure_ascii=False
                            ),
                            tool_id=tool_result.get("id"),
                        )
                        print_message(tool_result["content"], title="Tool result")
                        mc.append(tool_results_message)

                    # step_res = self.agent.model.chat(messages=mc, tools=tools)

                    # if not done:
                    #     mc.append()
                    # r = step_res.message.content.text
                    r = [tool_result["content"] for tool_result in tool_results]

            print_message(r, title=f"Task {task_id} result", msg_type=MessageType.AGENT)
            task.result = r

            print("---------assistant-----------")
            print(mc)
            print("--------------------")
            pass

    def is_use_tool(self, message):
        """检查消息是否包含工具调用"""
        if hasattr(message, "tool_descriptions") and message.tool_descriptions:
            return True
        return False

    async def execute_tool_call(
        self, task_id: int, tools: Dict, tool_descriptions
    ) -> List:
        """执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        tool_results = []
        for tool_call in tool_descriptions:
            tool_name = tool_call.name

            try:
                arguments = (
                    json.loads(tool_call.arguments)
                    if isinstance(tool_call.arguments, str)
                    else tool_call.arguments
                )
            except json.JSONDecodeError:
                arguments = tool_call.arguments

            # 执行工具调用
            tool_result = await self._execute_tool(task_id, tools, tool_name, arguments)

            tool_results.append({"id": tool_call.id, "content": tool_result})

        return tool_results

    async def _execute_tool(
        self, task_id: int, tools: List, tool_name: str, arguments: Dict
    ) -> Tuple[str, bool]:
        """执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        tools_dict = {
            tool._tool_info.name: {
                "function": tool._tool_info.func,
                "description": tool._tool_info.description,
                "parameters": tool._tool_info.parameters,
                # "remote": tool._tool_info.remote,
            }
            for tool in tools
        }
        if tool_name not in tools_dict:
            return f"Error: Tool '{tool_name}' not found", False

        try:
            match tool_name:
                case "plan_task":
                    # 特殊处理 plan_task 工具
                    tool_func = tools_dict[tool_name]["function"]
                    print_json(
                        arguments, title=f"Executing tool '{tool_name}' with arguments"
                    )
                    args = {}  # 不修改arguments
                    args.update(arguments)
                    args.update({"tools": tools_dict})
                    result = tool_func(**args)
                    self.parse_task_plan(task_id, result)
                    return (
                        (
                            json.dumps(result, ensure_ascii=False)
                            if isinstance(result, dict)
                            else str(result)
                        ),
                        False,
                    )
                case _:
                    # if tools_dict[tool_name].get("remote", False):
                    #     tool_func = tools_dict[tool_name]["function"]
                    #     print_json(
                    #         arguments,
                    #         title=f"Executing tool '{tool_name}' with arguments",
                    #     )
                    #     result = tool_func(**arguments)
                    #     return (
                    #         (
                    #             json.dumps(result, ensure_ascii=False)
                    #             if isinstance(result, dict)
                    #             else str(result)
                    #         ),
                    #         True,
                    #     )
                    # else:
                    tool_func = tools_dict[tool_name]["function"]
                    print_json(
                        arguments,
                        title=f"Executing tool '{tool_name}' with arguments",
                    )
                    result = tool_func(**arguments)
                    return (
                        (
                            json.dumps(result, ensure_ascii=False)
                            if isinstance(result, dict)
                            else str(result)
                        ),
                        False,
                    )
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}", False

    def _execute_remote_tool(
        self, task_id: int, tools: List, tool_name: str, arguments: Dict
    ) -> str:
        """执行远程工具调用

        Args:

            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        tools_dict = {
            tool._tool_info.name: {
                "function": tool._tool_info.func,
                "description": tool._tool_info.description,
                "parameters": tool._tool_info.parameters,
            }
            for tool in tools
        }
        if tool_name not in tools_dict:
            return f"Error: Tool '{tool_name}' not found"

        try:
            match tool_name:
                case "plan_task":
                    # 特殊处理 plan_task 工具
                    tool_func = tools_dict[tool_name]["function"]
                    print_json(
                        arguments, title=f"Executing tool '{tool_name}' with arguments"
                    )
                    args = {}  # 不修改arguments
                    args.update(arguments)
                    args.update({"tools": tools_dict})
                    result = tool_func(**args)
                    self.parse_task_plan(task_id, result)
                    return (
                        json.dumps(result, ensure_ascii=False)
                        if isinstance(result, dict)
                        else str(result)
                    )
                case _:
                    tool_func = tools_dict[tool_name]["function"]
                    print_json(
                        arguments, title=f"Executing tool '{tool_name}' with arguments"
                    )
                    result = tool_func(**arguments)
                    # 根据结果判断
                    # 1. 如果需要等待远程结果，挂起任务，等待远程结果返回后恢复
                    # 2. 否则直接返回结果
                    return (
                        json.dumps(result, ensure_ascii=False)
                        if isinstance(result, dict)
                        else str(result)
                    )
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def parse_task_plan(self, current_task_id: int, task_plan: Dict) -> tuple:
        """
        解析任务
        """
        # 创建映射字典
        tag_to_id = {}
        tasks = []
        task_descs = []

        tag_to_id[task_plan["task_tag"]] = current_task_id

        root_desc = self.task_descriptions.get(current_task_id)

        # 获取根任务的工具，用于映射工具名称到实际工具函数
        root_task = self.get_task(current_task_id)
        if not root_task or not root_task.tools:
            raise ValueError(f"Root task {current_task_id} not found or has no tools")

        # 创建工具名称到工具函数的映射
        tool_name_to_func = {tool._tool_info.name: tool for tool in root_task.tools}

        # 处理子任务
        for subtask_data in task_plan["subtasks"]:
            # 创建子任务
            subtask_id = TaskID.next()
            tag_to_id[subtask_data["task_tag"]] = subtask_id

            # 将工具名称映射回工具函数
            subtask_tools = []
            for tool_name in subtask_data["tool_require"]:
                if tool_name in tool_name_to_func:
                    subtask_tools.append(tool_name_to_func[tool_name])
                else:
                    print_message(
                        f"Warning: Tool '{tool_name}' not found in available tools"
                    )

            subtask = Task(
                task_id=subtask_id,
                prompt=subtask_data["description"],
                tools=subtask_tools,
            )
            tasks.append(subtask)

            # 创建任务描述
            subtask_desc = TaskDesc(
                task_id=subtask_id,
                parent_id=tag_to_id[subtask_data["parent"]],  # 设置父任务ID
                context=deepcopy(root_desc.context),  # fork上下文
                status=TaskStatus.CREATED,
            )
            task_descs.append(subtask_desc)

        # 第二遍处理依赖关系
        for subtask, task_desc in zip(task_plan["subtasks"], task_descs):
            if task_desc.task_id == current_task_id:
                continue
            # 转换依赖项ID
            for dep_tag in subtask.get("dependencies", []):
                if dep_tag in tag_to_id:
                    task_desc.dependencies.append(tag_to_id[dep_tag])

        # 设置根任务的依赖 - 依赖所有子任务
        # root_desc.dependencies = [
        #     t.task_id
        #     for t in all_tasks
        #     if t.task_id != root_task_id
        #     and any(
        #         d
        #         for d in all_descs
        #         if d.task_id == t.task_id and d.parent_id == root_task_id
        #     )
        # ]

        for task, desc in zip(tasks, task_descs):
            self.tasks[task.task_id] = task
            self.task_descriptions[task.task_id] = desc

        # 通知调度器有新任务创建
        if self.new_task_callback and tasks:
            self.new_task_callback()

    async def suspend_task_for_remote(
        self, task_id: int, command: str, timeout: Optional[float] = None
    ) -> str:
        """挂起任务，等待远程执行结果"""
        task_desc = self.get_task_desc(task_id)
        if not task_desc:
            raise ValueError(f"Task {task_id} not found")

        # 创建远程执行请求
        request_id = self.remote_manager.create_remote_request(
            task_id, command, timeout
        )

        # 设置任务状态为等待远程结果
        task_desc.status = TaskStatus.WAITING_REMOTE

        print_message(
            f"Task {task_id} suspended, waiting for remote execution: {request_id}"
        )

        return request_id

    async def resume_task_with_result(
        self, task_id: int, remote_result: RemoteTaskResult
    ):
        """使用远程执行结果恢复任务"""
        task_desc = self.get_task_desc(task_id)
        if not task_desc:
            print_message(f"Warning: Task {task_id} not found for resume")
            return

        if task_desc.status != TaskStatus.WAITING_REMOTE:
            print_message(
                f"Warning: Task {task_id} is not in WAITING_REMOTE status, current: {task_desc.status}"
            )
            return

        # 将远程结果添加到任务上下文
        if remote_result.success:
            # 成功结果
            result_message = assistant(content=f"远程执行成功: {remote_result.result}")
            task_desc.context.message_context.append(result_message)

            # 恢复任务状态
            task_desc.status = TaskStatus.RUNNING
            print_message(f"Task {task_id} resumed with successful remote result")
        else:
            # 失败结果
            error_message = assistant(content=f"远程执行失败: {remote_result.error}")
            task_desc.context.message_context.append(error_message)

            # 标记任务失败
            task_desc.status = TaskStatus.FAILED
            print_message(
                f"Task {task_id} failed due to remote execution error: {remote_result.error}"
            )


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
    """任务调度器接口"""

    def __init__(self, task_manager: TaskManager):
        """初始化任务调度器"""
        self.task_manager = task_manager
        self.task_queue: PriorityQueue = PriorityQueue()

        # --- asyncio 相关 ---
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.scheduler_task: Optional[asyncio.Task] = None
        self.stop_event = asyncio.Event()

        # 添加事件通知机制
        self.task_completed_event = asyncio.Event()  # 任务完成事件
        self.new_task_event = asyncio.Event()  # 新任务创建事件

        # 设置新任务创建回调
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
        """
        调度循环
        step1: 清理已完成的任务
        step2: 获取就绪任务
        step3: 执行就绪任务
        step4: 检查是否需要继续运行
        """
        try:
            while not self.stop_event.is_set():
                # 1. 清理已完成的任务
                has_completed_tasks = await self._cleanup_completed_tasks()

                # 2. 获取就绪任务
                print_rule("find ready task")
                ready_tasks = self.find_ready_tasks()
                print_message(ready_tasks)

                # 3. 执行就绪任务
                if ready_tasks:
                    self.add_to_queue(ready_tasks)
                    print_rule("Executing ready tasks")
                    while not self.task_queue.is_empty():
                        task_id = self.task_queue.get()
                        print_message(f"Scheduling task {task_id}")
                        if task_id is not None:
                            desc = self.task_manager.get_task_desc(task_id)

                            desc.status = TaskStatus.RUNNING
                            desc.start_time = asyncio.get_event_loop().time()
                            worker = asyncio.create_task(
                                self._run_task_with_callback(task_id)
                            )
                            print_message(f"Task {task_id} started")
                            desc.worker = worker
                            print_message(desc)
                            self.running_tasks[task_id] = worker

                # 4. 检查是否需要继续运行
                # 只有当没有运行中的任务且没有待执行任务时才退出
                if await self._should_stop_scheduler():
                    print_message("All tasks completed, stopping scheduler")
                    break

                # 5. 等待事件或超时
                # 使用事件驱动 + 短间隔轮询的混合策略
                try:
                    await asyncio.wait_for(
                        asyncio.wait(
                            [
                                asyncio.create_task(self.task_completed_event.wait()),
                                asyncio.create_task(self.new_task_event.wait()),
                            ],
                            return_when=asyncio.FIRST_COMPLETED,
                        ),
                        timeout=0.1,  # 100ms 超时，确保定期检查
                    )
                    # 重置事件
                    self.task_completed_event.clear()
                    self.new_task_event.clear()
                except asyncio.TimeoutError:
                    # 超时是正常的，继续下一轮循环
                    pass
        except Exception as e:
            print_message(f"Error in scheduler loop: {e}")
        finally:
            # 清理所有运行中的任务
            await self._cleanup_all_tasks()

    async def _cleanup_completed_tasks(self) -> bool:
        """清理已完成的任务，返回是否有任务完成"""
        completed_task_ids = []

        for task_id, worker in self.running_tasks.items():
            if worker.done():
                completed_task_ids.append(task_id)
                desc = self.task_manager.get_task_desc(task_id)
                if desc:
                    if worker.exception():
                        desc.status = TaskStatus.FAILED
                        print_message(f"Task {task_id} failed: {worker.exception()}")
                    else:
                        desc.status = TaskStatus.COMPLETED
                        print_message(f"Task {task_id} completed successfully")
                    desc.end_time = asyncio.get_event_loop().time()
                    desc.worker = None

        # 从运行任务字典中移除已完成的任务
        for task_id in completed_task_ids:
            del self.running_tasks[task_id]

        # 如果有任务完成，触发事件
        if completed_task_ids:
            self.task_completed_event.set()

        return len(completed_task_ids) > 0

    async def _all_tasks_completed(self) -> bool:
        """检查是否所有任务都已完成"""
        # 检查是否还有未完成的任务
        for desc in self.task_manager.task_descriptions.values():
            if desc.status in [
                TaskStatus.CREATED,
                TaskStatus.READY,
                TaskStatus.RUNNING,
            ]:
                return False
        return True

    async def _cleanup_all_tasks(self) -> None:
        """清理所有运行中的任务"""
        for task_id in list(self.running_tasks.keys()):
            await self.cancel_task(task_id)

    async def _should_stop_scheduler(self) -> bool:
        """
        检查是否应该停止调度器
        停止条件：
        1. 没有运行中的任务
        2. 没有待执行的任务（CREATED, READY状态的任务）
        """
        # 检查是否有运行中的任务
        if self.running_tasks:
            print_message(f"Still have {len(self.running_tasks)} running tasks")
            return False

        # 检查是否有待执行的任务
        for desc in self.task_manager.task_descriptions.values():
            if desc.status in [
                TaskStatus.CREATED,
                TaskStatus.READY,
                TaskStatus.WAITING_REMOTE,
            ]:
                print_message(f"Still have pending tasks in status: {desc.status}")
                return False

        print_message("No running or pending tasks found")
        return True

    def find_ready_tasks(self) -> List[int]:
        """查找所有就绪任务"""
        ready_tasks = []

        for task_id, desc in self.task_manager.task_descriptions.items():
            if desc.status == TaskStatus.CREATED and self.check_dependencies(task_id):
                desc.status = TaskStatus.READY
                ready_tasks.append(task_id)

        return ready_tasks

    def add_to_queue(self, task_ids: List[int]) -> None:
        """将就绪任务添加到调度队列"""
        for task_id in task_ids:
            # desc = self.get_task_desc(task_id)  # 确保任务描述存在

            # # 计算优先级
            # if desc:
            #     priority = self._calculate_priority(desc)
            # else:
            #     priority = 0

            self.task_queue.add(task_id)

    def check_dependencies(self, task_id: int) -> bool:
        """检查任务依赖是否满足"""
        desc = self.task_manager.get_task_desc(task_id)
        if not desc:
            raise ValueError(f"Task {task_id} description not found")
            return False

        for dep_id in desc.dependencies:
            dep_desc = self.task_manager.get_task_desc(dep_id)
            if not dep_desc or dep_desc.status != TaskStatus.COMPLETED:
                return False

        return True

    def get_task_desc(self, task_id: str) -> Optional[TaskDesc]:
        """获取任务信息"""
        return self.task_manager.get_task_desc(task_id)

    async def cancel_task(self, task_id: int) -> None:
        """取消任务"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.running_tasks[task_id]

        desc = self.task_manager.get_task_desc(task_id)
        if desc:
            desc.status = TaskStatus.CANCELED
            desc.end_time = asyncio.get_event_loop().time()

    async def _run_task_with_callback(self, task_id: int):
        """执行任务并在完成时触发事件"""
        try:
            result = await self.task_manager.run_task(task_id)
            # 任务完成，触发事件通知调度器
            self.task_completed_event.set()
            return result
        except Exception as e:
            # 任务失败也要触发事件
            self.task_completed_event.set()
            raise e

    def _on_new_task_created(self):
        """新任务创建回调"""
        self.new_task_event.set()
