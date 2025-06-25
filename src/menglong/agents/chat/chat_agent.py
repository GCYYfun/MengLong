from typing import List, Dict, Any, Optional, Callable, Union
from enum import Enum
import asyncio
import json
import inspect
import time

from ..agent import Agent
from ...ml_model.schema.ml_request import UserMessage, ToolMessage
from ..component.context_manager import ContextManager
from ...task.task_manager import AsyncTaskScheduler, TaskState

from ...utils.log import print_message, print_rule, MessageType


class ChatMode(Enum):
    """聊天模式枚举"""

    NORMAL = "normal"  # 普通聊天模式
    AUTO = "auto"  # 自动模式，支持工具调用
    WORKFLOW = "workflow"  # 工作流模式，支持多步骤任务


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


class ChatAgent(Agent):
    def __init__(
        self,
        model_id: str = None,
        system: str = None,
        mode: ChatMode = ChatMode.NORMAL,
        tools: Any = ...,  # 使用 ... 作为默认值来区分 None 和未传递
    ):
        super().__init__(model_id=model_id)
        self.context = ContextManager()
        self.mode = mode
        self.tools = {}  # 工具注册表
        self.workflow_steps = []  # 工作流步骤
        self.current_step = 0  # 当前执行的步骤
        self.task_scheduler = None  # 任务调度器

        # 自主任务执行相关属性
        self.autonomous_mode = False
        self.max_iterations = 10
        self.current_iteration = 0
        self.task_context = {}

        if system is not None:
            self.context.system = system

        # 自动注册工具
        if tools is not ...:  # 如果明确传递了tools参数（包括None）
            self.auto_register_tools(tools)

    def register_tool(
        self, name: str, func: Callable, description: str = "", parameters: Dict = None
    ):
        """注册工具函数

        Args:
            name: 工具名称
            func: 工具函数
            description: 工具描述
            parameters: 工具参数规范
        """
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": parameters or {},
        }

    def register_tools_from_functions(self, *functions):
        """
        从函数列表中注册带有 @tool 装饰器的工具

        Args:
            *functions: 函数对象列表

        Usage:
            agent.register_tools_from_functions(get_weather, calculate, search_web)
        """
        for func in functions:
            if hasattr(func, "_is_tool") and hasattr(func, "_tool_info"):
                tool_info = func._tool_info
                self.tools[tool_info.name] = {
                    "function": tool_info.func,
                    "description": tool_info.description,
                    "parameters": tool_info.parameters,
                }

    def register_tools_from_module(self, module_or_namespace):
        """
        从模块或命名空间中自动注册所有用 @tool 装饰的函数

        Args:
            module_or_namespace: 模块对象或命名空间字典

        Usage:
            import my_tools
            agent.register_tools_from_module(my_tools)

            # 或者从当前命名空间
            agent.register_tools_from_module(globals())
        """
        tools = get_tools_from_module(module_or_namespace)
        for tool_name, tool_info in tools.items():
            self.tools[tool_name] = {
                "function": tool_info.func,
                "description": tool_info.description,
                "parameters": tool_info.parameters,
            }

    def register_global_tools(self):
        """
        注册所有全局注册的工具（用 @tool 装饰器标记的）

        Usage:
            agent.register_global_tools()
        """
        global_tools = get_global_tools()
        for tool_name, tool_info in global_tools.items():
            self.tools[tool_name] = {
                "function": tool_info.func,
                "description": tool_info.description,
                "parameters": tool_info.parameters,
            }

    def auto_register_tools(self, tools=None):
        """
        智能工具注册方法，支持多种输入格式

        Args:
            tools: 可以是以下任一类型：
                - None: 自动注册全局工具
                - 模块对象: 注册模块中的工具
                - 函数列表: 注册列表中的工具
                - 字符串列表: 从全局工具中按名称注册

        Usage:
            # 注册全局工具
            agent.auto_register_tools()

            # 注册模块中的工具
            import my_tools
            agent.auto_register_tools(my_tools)

            # 注册特定函数
            agent.auto_register_tools([get_weather, calculate])

            # 按名称注册全局工具
            agent.auto_register_tools(["weather", "calculate"])
        """
        if tools is None:
            # 自动注册全局工具
            self.register_global_tools()
        elif hasattr(tools, "__dict__") or isinstance(tools, dict):
            # 模块或命名空间
            self.register_tools_from_module(tools)
        elif isinstance(tools, (list, tuple)):
            if tools and isinstance(tools[0], str):
                # 字符串列表，按名称从全局工具注册
                global_tools = get_global_tools()
                for tool_name in tools:
                    if tool_name in global_tools:
                        tool_info = global_tools[tool_name]
                        self.tools[tool_name] = {
                            "function": tool_info.func,
                            "description": tool_info.description,
                            "parameters": tool_info.parameters,
                        }
            else:
                # 函数列表
                self.register_tools_from_functions(*tools)
        else:
            raise ValueError(f"Unsupported tools type: {type(tools)}")

    def add_workflow_step(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        """添加工作流步骤

        Args:
            name: 步骤名称
            action: 执行动作
            condition: 执行条件（可选）
        """
        step = WorkflowStep(name, action, condition)
        self.workflow_steps.append(step)

    def _format_tools_for_model(self) -> List[Dict]:
        """将注册的工具格式化为模型可用的格式"""
        formatted_tools = []
        for name, tool_info in self.tools.items():
            # 根据模型类型决定工具格式
            match self.model.provider:
                case "aws":
                    # AWS模型格式
                    formatted_tools.append(
                        {
                            "toolSpec": {
                                "name": name,
                                "description": tool_info["description"],
                                "inputSchema": {"json": tool_info["parameters"]},
                            }
                        }
                    )
                case "openai" | "deepseek" | "infinigence":
                    # OpenAI/其他模型格式
                    formatted_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": name,
                                "description": tool_info["description"],
                                "parameters": tool_info["parameters"],
                            },
                        }
                    )
        return formatted_tools

    def _is_aws_model(self) -> bool:
        """判断是否为AWS模型"""
        model_id = self.model.model_id if hasattr(self.model, "model_id") else None
        if model_id and isinstance(model_id, str):
            return any(
                provider in model_id.lower()
                for provider in ["aws", "anthropic", "us.", "bedrock"]
            )
        return False

    def execute_tool_call(self, tool_descriptions) -> List:
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
            tool_result = self._execute_tool(tool_name, arguments)
            tool_results.append({"id": tool_call.id, "content": tool_result})

        return tool_results

    def _execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """执行工具调用

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"

        try:
            tool_func = self.tools[tool_name]["function"]
            result = tool_func(**arguments)
            return (
                json.dumps(result, ensure_ascii=False)
                if isinstance(result, dict)
                else str(result)
            )
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    async def async_execute_tool_call(self, tool_descriptions):
        # 异步执行工具调用并收集结果
        print("tool_descriptions:", tool_descriptions)
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

            # 异步执行工具调用
            tool_result = await self._async_execute_tool(tool_name, arguments)

            # 直接收集工具结果，不包装
            tool_results.append({"id": tool_call.id, "content": tool_result})
        return tool_results

    async def _async_execute_tool(self, tool_name: str, arguments: Dict) -> str:
        """异步执行工具调用"""
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"

        tool_func = self.tools[tool_name]["function"]

        try:
            # 检查工具函数是否是异步的
            if asyncio.iscoroutinefunction(tool_func):
                # 直接调用异步函数
                result = await tool_func(**arguments)
            else:
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: tool_func(**arguments)
                )

            return result
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    # ==================== 异步工具注册方法 ====================

    async def register_tool_async(
        self, name: str, func: Callable, description: str = "", parameters: Dict = None
    ):
        """异步注册工具函数

        Args:
            name: 工具名称
            func: 工具函数（可以是同步或异步）
            description: 工具描述
            parameters: 工具参数规范
        """
        self.tools[name] = {
            "function": func,
            "description": description,
            "parameters": parameters or {},
            "is_async": asyncio.iscoroutinefunction(func),
        }

    async def register_tools_from_functions_async(self, *functions):
        """异步注册多个工具函数

        Args:
            *functions: 函数对象列表
        """
        for func in functions:
            if hasattr(func, "_is_tool") and hasattr(func, "_tool_info"):
                tool_info = func._tool_info
                await self.register_tool_async(
                    name=tool_info.name,
                    func=tool_info.func,
                    description=tool_info.description,
                    parameters=tool_info.parameters,
                )

    # ==================== 异步批量处理 ====================

    async def batch_chat_async(self, message_list: List[str], **kwargs) -> List[str]:
        """异步批量处理多个消息"""
        tasks = []
        for message in message_list:
            # 为每个消息创建独立的上下文副本（可选）
            task = self.chat_async(message, **kwargs)
            tasks.append(task)

        # 并行执行所有聊天任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(f"Error in message {i+1}: {str(result)}")
            else:
                processed_results.append(result)

        return processed_results

    async def sequential_chat_async(
        self, message_list: List[str], **kwargs
    ) -> List[str]:
        """异步顺序处理多个消息（保持上下文连续性）"""
        results = []
        for i, message in enumerate(message_list):
            try:
                result = await self.chat_async(message, **kwargs)
                results.append(result)
            except Exception as e:
                results.append(f"Error in message {i+1}: {str(e)}")
                # 可以选择继续或中断
                break

        return results

    # ==================== 异步工作流方法 ====================

    async def _async_workflow_chat(self, input_messages, **kwargs):
        """异步工作流聊天"""
        if not self.task_scheduler:
            self.task_scheduler = AsyncTaskScheduler()

        self.context.add_user_message(input_messages)

        if not self.workflow_steps:
            response = "No workflow steps defined. Please add workflow steps first."
            self.context.add_assistant_response(response)
            return response

        # 创建异步任务来执行工作流步骤
        async def execute_step(step, step_index):
            if step.completed:
                return f"Step {step_index+1} already completed"

            if step.condition and not step.condition():
                return f"Step {step_index+1} condition not met"

            try:
                if asyncio.iscoroutinefunction(step.action):
                    result = await step.action(input_messages, self.context)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, step.action, input_messages, self.context
                    )

                step.result = result
                step.completed = True
                return f"Step {step_index+1} ({step.name}): {result}"
            except Exception as e:
                return f"Error in step {step_index+1} ({step.name}): {str(e)}"

        # 执行所有步骤（可以并行或串行）
        results = []
        for i, step in enumerate(self.workflow_steps):
            result = await execute_step(step, i)
            results.append(result)

        final_result = "\n".join(results)
        self.context.add_assistant_response(final_result)
        return final_result

    async def add_workflow_step_async(
        self, name: str, action: Callable, condition: Optional[Callable] = None
    ):
        """异步添加工作流步骤"""
        step = WorkflowStep(name, action, condition)
        self.workflow_steps.append(step)
        return step

    async def execute_workflow_async(self, input_messages=None):
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
                    result = await step.action(input_messages, self.context)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, step.action, input_messages, self.context
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

    # ==================== 异步上下文管理 ====================

    async def clear_context_async(self):
        """异步清理上下文"""
        self.context.clear()
        await asyncio.sleep(0)  # 让出控制权

    async def get_context_summary_async(self) -> str:
        """异步获取上下文摘要"""
        if not self.context.messages:
            return "Empty context"

        # 可以在这里添加AI总结逻辑
        message_count = len(self.context.messages)
        return f"Context contains {message_count} messages"

    def chat(self, input_messages, **kwargs):
        """聊天方法，根据模式决定处理方式"""
        if self.mode == ChatMode.NORMAL:
            return self._normal_chat(input_messages, **kwargs)
        elif self.mode == ChatMode.AUTO:
            return self._auto_chat(input_messages, **kwargs)
        elif self.mode == ChatMode.WORKFLOW:
            return self._workflow_chat(input_messages, **kwargs)
        else:
            raise ValueError(f"Unsupported chat mode: {self.mode}")

    def _normal_chat(self, input_messages, **kwargs):
        """普通聊天模式"""
        # 处理消息
        self.context.add_user_message(input_messages)

        # 获取消息并转换为字典格式
        messages = self.context.messages

        try:
            res = self.model.chat(messages=messages, **kwargs)

            # 处理响应内容
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
            # 发生错误时也要添加助手响应，避免上下文混乱
            error_msg = f"Error: {str(e)}"
            self.context.add_assistant_response(error_msg)
            return error_msg

    def _auto_chat(self, input_messages, **kwargs):
        """自动模式，支持工具调用"""
        self.context.add_user_message(input_messages)

        messages = self.context.messages

        # 如果有注册的工具，添加到请求中
        if self.tools:
            kwargs["tools"] = self._format_tools_for_model()
            kwargs["tool_choice"] = self._format_tool_choice()

        try:
            res = self.model.chat(messages=messages, **kwargs)

            # 检查是否有工具调用

            if self.is_use_tool(res.message):
                # 处理工具调用
                # 首先添加助手的原始消息（包含工具调用）到上下文
                self.context._messages.context.append(res.message)

                # deal tool results
                # 执行工具调用并收集结果
                tool_results = self.execute_tool_call(res.message.tool_descriptions)

                # 为AWS模型创建正确的工具结果消息格式
                # AWS要求所有工具结果必须在同一个用户消息中

                # 将所有工具结果打包到一个用户消息中
                assert (
                    len(tool_results) == len(res.message.tool_descriptions)
                    and len(tool_results) > 0
                ), "工具调用结果数量与描述不匹配"
                for tool_result in tool_results:
                    tool_results_message = ToolMessage(
                        content=json.dumps(tool_result["content"], ensure_ascii=False),
                        tool_id=tool_result.get("id"),
                    )
                    self.context._messages.context.append(tool_results_message)

                # 重新获取消息列表，确保格式统一
                messages = self.context.messages

                # 获取最终响应
                final_res = self.model.chat(
                    messages=messages, tools=kwargs.get("tools")
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
            # 发生错误时也要添加助手响应，避免上下文混乱
            error_msg = f"Error: {str(e)}"
            self.context.add_assistant_response(error_msg)
            return error_msg

    def is_use_tool(self, message):
        """检查消息是否包含工具调用"""
        if hasattr(message, "tool_descriptions") and message.tool_descriptions:
            return True
        return False

    def _workflow_chat(self, input_messages, **kwargs):
        """工作流模式，支持多步骤任务"""
        self.context.add_user_message(input_messages)

        if not self.workflow_steps:
            response = "No workflow steps defined. Please add workflow steps first."
            self.context.add_assistant_response(response)
            return response

        # 执行工作流步骤
        results = []
        for i, step in enumerate(self.workflow_steps):
            if step.completed:
                continue

            # 检查执行条件
            if step.condition and not step.condition():
                continue

            try:
                # 执行步骤
                step_result = step.action(input_messages, self.context)
                step.result = step_result
                step.completed = True
                results.append(f"Step {i+1} ({step.name}): {step_result}")

            except Exception as e:
                error_msg = f"Error in step {i+1} ({step.name}): {str(e)}"
                results.append(error_msg)
                # 出错时仍然添加助手响应
                self.context.add_assistant_response(error_msg)
                return error_msg

        # 所有步骤完成后，添加最终响应
        final_result = "\n".join(results)
        self.context.add_assistant_response(final_result)
        return final_result

    async def chat_async(self, input_messages, **kwargs):
        """异步聊天方法，根据模式决定处理方式"""
        if self.mode == ChatMode.NORMAL:
            return await self._async_normal_chat(input_messages, **kwargs)
        elif self.mode == ChatMode.AUTO:
            return await self._async_auto_chat(input_messages, **kwargs)
        elif self.mode == ChatMode.WORKFLOW:
            return await self._async_workflow_chat(input_messages, **kwargs)
        else:
            raise ValueError(f"Unsupported chat mode: {self.mode}")

    async def _async_normal_chat(self, input_messages, **kwargs):
        """异步普通聊天模式"""
        # 处理消息
        self.context.add_user_message(input_messages)

        # 获取消息并转换为字典格式
        messages = self.context.messages

        try:
            # 在线程池中执行模型调用（因为底层模型API可能是同步的）
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, lambda: self.model.chat(messages=messages, **kwargs)
            )

            # 处理响应内容
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
            # 发生错误时也要添加助手响应，避免上下文混乱
            error_msg = f"Error: {str(e)}"
            self.context.add_assistant_response(error_msg)
            return error_msg

    async def _async_auto_chat(self, input_messages, **kwargs):
        """异步自动模式，支持工具调用"""
        self.context.add_user_message(input_messages)

        messages = self.context.messages

        # 如果有注册的工具，添加到请求中
        if self.tools:
            kwargs["tools"] = self._format_tools_for_model()
            kwargs["tool_choice"] = self._format_tool_choice()

        try:
            # 在线程池中执行模型调用
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None, lambda: self.model.chat(messages=messages, **kwargs)
            )

            # 检查是否有工具调用
            if (
                hasattr(res.message, "tool_descriptions")
                and res.message.tool_descriptions
            ):
                # 处理工具调用
                # 首先添加助手的原始消息（包含工具调用）到上下文
                self.context._messages.context.append(res.message)

                tool_results = await self.async_execute_tool_call(
                    res.message.tool_descriptions
                )
                # 为AWS模型创建正确的工具结果消息格式
                # AWS要求所有工具结果必须在同一个用户消息中
                # 将所有工具结果打包到一个用户消息中
                assert (
                    len(tool_results) == len(res.message.tool_descriptions)
                    and len(tool_results) > 0
                ), "工具调用结果数量与描述不匹配"
                for tool_result in tool_results:
                    tool_results_message = ToolMessage(
                        content=json.dumps(tool_result["content"], ensure_ascii=False),
                        tool_id=tool_result.get("id"),
                    )
                    self.context._messages.context.append(tool_results_message)

                # 重新获取消息列表，确保格式统一
                messages = self.context.messages
                # 获取最终响应
                final_res = await loop.run_in_executor(
                    None,
                    lambda: self.model.chat(
                        messages=messages, tools=kwargs.get("tools")
                    ),
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
            # 发生错误时也要添加助手响应，避免上下文混乱
            error_msg = f"Error: {str(e)}"
            print_message(error_msg)
            return error_msg

    def _workflow_chat(self, input_messages, **kwargs):
        """工作流模式，支持多步骤任务"""
        self.context.add_user_message(input_messages)

        if not self.workflow_steps:
            response = "No workflow steps defined. Please add workflow steps first."
            self.context.add_assistant_response(response)
            return response

        # 执行工作流步骤
        results = []
        for i, step in enumerate(self.workflow_steps):
            if step.completed:
                continue

            # 检查执行条件
            if step.condition and not step.condition():
                continue

            try:
                # 执行步骤
                step_result = step.action(input_messages, self.context)
                step.result = step_result
                step.completed = True
                results.append(f"Step {i+1} ({step.name}): {step_result}")

            except Exception as e:
                error_msg = f"Error in step {i+1} ({step.name}): {str(e)}"
                results.append(error_msg)
                # 出错时仍然添加助手响应
                self.context.add_assistant_response(error_msg)
                return error_msg

        # 所有步骤完成后，添加最终响应
        final_result = "\n".join(results)
        self.context.add_assistant_response(final_result)
        return final_result

    async def chat_stream(self, input_messages, **kwargs):
        """流式聊天"""
        # 根据模式处理流式响应
        if self.mode == ChatMode.NORMAL:
            return self._stream_normal_chat(input_messages, **kwargs)
        elif self.mode == ChatMode.AUTO:
            return self._stream_auto_chat(input_messages, **kwargs)
        elif self.mode == ChatMode.WORKFLOW:
            return self._stream_workflow_chat(input_messages, **kwargs)

    def _stream_normal_chat(self, input_messages, **kwargs):
        """普通模式流式聊天"""
        # 这里可以实现流式响应逻辑
        # 目前简化为调用普通聊天
        return self._normal_chat(input_messages, **kwargs)

    def _stream_auto_chat(self, input_messages, **kwargs):
        """自动模式流式聊天"""
        # 实现工具调用的流式响应
        return self._auto_chat(input_messages, **kwargs)

    def _stream_workflow_chat(self, input_messages, **kwargs):
        """工作流模式流式聊天"""
        # 实现工作流的流式响应
        return self._workflow_chat(input_messages, **kwargs)

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

    def run(self, task: str = None, max_iterations: int = 10) -> Dict[str, Any]:
        """运行代理（同步版本）

        Args:
            task: 要执行的任务描述，如果提供，将启用自主执行模式
            max_iterations: 自主执行的最大迭代次数

        Returns:
            如果是自主执行模式，返回执行结果字典；否则返回None

        注意:
            此方法会创建新的事件循环，如果已在事件循环中，请使用 arun() 方法
        """
        if task:
            # 自主任务执行模式
            try:
                return asyncio.run(self._autonomous_execute_task(task, max_iterations))
            except RuntimeError as e:
                if "cannot be called from a running event loop" in str(e):
                    raise RuntimeError(
                        "Cannot use run() from within an event loop. "
                        "Please use arun() instead for async environments."
                    ) from e
                raise
        elif self.mode == ChatMode.WORKFLOW and self.task_scheduler:
            # 启动任务调度器
            self.task_scheduler.run()
        else:
            # 其他模式的运行逻辑
            pass
        return None

    async def arun(self, task: str = None, max_iterations: int = 10) -> Dict[str, Any]:
        """运行代理（异步版本）

        Args:
            task: 要执行的任务描述，如果提供，将启用自主执行模式
            max_iterations: 自主执行的最大迭代次数

        Returns:
            如果是自主执行模式，返回执行结果字典；否则返回None

        注意:
            此方法适用于已在事件循环中的异步环境
        """
        if task:
            # 自主任务执行模式
            result = await self._autonomous_execute_task(task, max_iterations)
            return result
        else:
            # 其他模式的运行逻辑
            pass
        return None

    async def _autonomous_execute_task(
        self, task_description: str, max_iterations: int = 10
    ) -> Dict[str, Any]:
        """自主执行任务的核心逻辑"""

        print_rule(f"开始自主执行任务", style="green")
        print_message(
            f" {task_description}", title="📋 任务描述:", msg_type=MessageType.INFO
        )

        # 设置自主任务模式
        self.autonomous_mode = True
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.task_context = {
            "original_task": task_description,
            "start_time": time.time(),
            "execution_log": [],
            "intermediate_results": [],
        }

        # 设置自主执行系统提示
        original_system = self.context.system
        autonomous_system = """你是一个自主任务执行助手。你的职责是：
1. 分析用户给出的任务
2. 制定执行计划
3. 逐步执行任务，使用可用的工具
4. 监控进度并调整策略
5. 确保任务完全完成

执行原则：
- 主动使用工具完成任务
- 遇到问题时寻找替代方案
- 定期检查任务完成情况
- 保持执行的连续性直到完成

请在每次响应中明确说明：
1. 当前正在执行的步骤
2. 使用的工具和原因
3. 下一步计划
4. 任务整体进度"""

        if original_system:
            self.context.system = f"{original_system}\n\n{autonomous_system}"
        else:
            self.context.system = autonomous_system

        # 确保在AUTO模式下执行
        original_mode = self.mode
        self.mode = ChatMode.AUTO

        try:
            # 初始化任务
            initial_prompt = f"""
我需要你自主完成以下任务：

任务描述：{task_description}

请分析这个任务，制定执行计划，然后开始执行。你有以下可用工具：
{self._get_available_tools_description()}

请开始执行，并在每步说明你的行动和理由。
"""

            last_response = ""
            task_completed = False

            while self.current_iteration < self.max_iterations and not task_completed:
                self.current_iteration += 1

                print_message(
                    f"{self.current_iteration}/{self.max_iterations}",
                    title="🔄 当前轮次:",
                    msg_type=MessageType.INFO,
                )

                # try:
                # 构建当前轮次的提示
                if self.current_iteration == 1:
                    current_prompt = initial_prompt
                else:
                    current_prompt = f"""
继续执行任务。上次的执行结果：
{last_response}

请继续下一步执行，或者如果任务已完成，请进行最终验证。
当前已执行 {self.current_iteration-1} 轮，请确保任务的完整性。
"""

                # 让 Agent 执行下一步（使用异步方法）
                response = await self.chat_async(current_prompt)
                print("---------------执行完一次----------------")
                last_response = response

                # 记录执行过程
                self.task_context["execution_log"].append(
                    {
                        "iteration": self.current_iteration,
                        "response": response,
                        "timestamp": time.time(),
                    }
                )

                print_message(
                    f"{response}", title="🤖 Agent 响应:", msg_type=MessageType.AGENT
                )

                # 检查是否提到任务完成
                completion_keywords = [
                    "任务完成",
                    "已完成",
                    "执行完毕",
                    "全部完成",
                    "任务结束",
                ]
                if any(keyword in response for keyword in completion_keywords):
                    print("🎯 检测到任务完成信号", MessageType.SUCCESS)

                    # 进行最终验证
                    final_validation = await self._perform_final_validation(
                        task_description
                    )
                    if final_validation["is_complete"]:
                        task_completed = True
                        print_message("✅ 任务执行完成！", MessageType.SUCCESS)
                    else:
                        print_message(
                            "⚠️ 任务尚未完全完成，继续执行", MessageType.WARNING
                        )

                    # 短暂等待，避免过快执行
                await asyncio.sleep(1)

                # except Exception as e:
                #     rich_print(f"❌ 执行出错: {str(e)}", RichMessageType.ERROR)
                #     break

            # 生成执行报告
            execution_report = self._generate_execution_report(task_completed)

            if not task_completed:
                print_message("⏰ 达到最大执行轮次或任务未完成", MessageType.WARNING)

            return execution_report

        finally:
            # 恢复原始设置
            self.context.system = original_system
            self.mode = original_mode
            self.autonomous_mode = False

    def _get_available_tools_description(self) -> str:
        """获取可用工具的描述"""
        if not self.tools:
            return "当前没有可用的工具"

        tool_descriptions = []
        for name, tool in self.tools.items():
            desc = tool.get("description", "无描述")
            tool_descriptions.append(f"- {name}: {desc}")

        return "\n".join(tool_descriptions)

    async def _perform_final_validation(self, task_description: str) -> Dict[str, Any]:
        """执行最终验证"""

        print_message("🔍 执行最终任务验证...", MessageType.INFO)

        # 从执行日志中提取已完成的项目
        completed_items = []
        for log_entry in self.task_context["execution_log"]:
            response = log_entry["response"]
            if "搜索" in response or "信息收集" in response:
                completed_items.append("信息收集")
            if "分析" in response or "数据分析" in response:
                completed_items.append("数据分析")
            if "报告" in response or "生成" in response:
                completed_items.append("报告生成")
            if "验证" in response or "检查" in response:
                completed_items.append("结果验证")

        # 使用验证提示（异步调用）
        validation_prompt = f"请验证以下任务是否完成：{task_description}。已完成的项目：{completed_items}"
        validation_response = await self.chat_async(validation_prompt)

        return {
            "is_complete": len(completed_items) >= 3,  # 至少完成3个主要步骤
            "completed_items": completed_items,
            "validation_response": validation_response,
        }

    def _generate_execution_report(self, task_completed: bool) -> Dict[str, Any]:
        """生成执行报告"""
        end_time = time.time()
        execution_time = end_time - self.task_context["start_time"]

        return {
            "task_description": self.task_context["original_task"],
            "status": "completed" if task_completed else "incomplete",
            "execution_time": execution_time,
            "iterations": self.current_iteration,
            "max_iterations": self.max_iterations,
            "execution_log": self.task_context["execution_log"],
            "success_rate": (
                1.0 if task_completed else self.current_iteration / self.max_iterations
            ),
        }

    def reset(self):
        """重置代理状态"""
        self.context.clear()
        self.workflow_steps.clear()
        self.current_step = 0
        self.task_scheduler = None

    def _format_tool_choice(self) -> Union[Dict, str]:
        """根据模型类型格式化tool_choice"""
        match self.model.provider:
            case "aws":
                return {"type": "any"}
            case "openai" | "deepseek" | "infinigence":
                return "required"

    def _handle_tool_response(self, messages: List, tool_call, tool_result: str):
        """处理工具调用响应，根据模型类型格式化"""
        from ...ml_model.schema.ml_request import ToolMessage

        # 统一使用ToolMessage，让底层转换器处理格式化
        tool_msg = ToolMessage(
            tool_id=tool_call.id,
            content=(
                json.dumps(tool_result)
                if isinstance(tool_result, dict)
                else str(tool_result)
            ),
        )
        messages.append(tool_msg)
        return messages


# 全局工具注册表，用于存储所有用 @tool 装饰的函数
_GLOBAL_TOOLS = {}


class ToolInfo:
    """工具信息类，存储工具的元数据"""

    def __init__(
        self,
        func: Callable,
        name: str = None,
        description: str = "",
        parameters: Dict = None,
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self.parameters = parameters or self._auto_generate_parameters()

    def _auto_generate_parameters(self) -> Dict:
        """自动从函数签名生成参数规范"""
        sig = inspect.signature(self.func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            # 跳过 self 参数
            if param_name == "self":
                continue

            param_info = {"type": "string"}  # 默认类型

            # 尝试从类型注解推断类型
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif (
                    hasattr(param.annotation, "__origin__")
                    and param.annotation.__origin__ == list
                ):
                    param_info["type"] = "array"
                elif (
                    hasattr(param.annotation, "__origin__")
                    and param.annotation.__origin__ == dict
                ):
                    param_info["type"] = "object"

            # 从默认值推断是否必需
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                param_info["default"] = param.default

            properties[param_name] = param_info

        return {"type": "object", "properties": properties, "required": required}


def tool(name: str = None, description: str = None, parameters: Dict = None):
    """
    工具装饰器，用于标记函数为可用工具

    Args:
        name: 工具名称，默认使用函数名
        description: 工具描述，默认使用函数文档字符串
        parameters: 工具参数规范，默认自动从函数签名生成

    Usage:
        @tool(name="weather", description="获取天气信息")
        def get_weather(location: str, unit: str = "celsius"):
            '''获取指定位置的天气信息'''
            return {"location": location, "temperature": 22}

        @tool()  # 使用默认值
        def calculate(expression: str):
            '''计算数学表达式'''
            return eval(expression)
    """

    def decorator(func: Callable) -> Callable:
        # 创建工具信息
        tool_info = ToolInfo(
            func=func, name=name, description=description, parameters=parameters
        )

        # 注册到全局工具表
        tool_name = tool_info.name
        _GLOBAL_TOOLS[tool_name] = tool_info

        # 在函数上添加标记
        func._is_tool = True
        func._tool_info = tool_info

        return func

    return decorator


def get_tools_from_module(module_or_namespace) -> Dict[str, ToolInfo]:
    """
    从模块或命名空间中提取所有用 @tool 装饰的函数

    Args:
        module_or_namespace: 模块对象或命名空间字典

    Returns:
        工具名称到 ToolInfo 的映射
    """
    tools = {}

    if hasattr(module_or_namespace, "__dict__"):
        # 处理模块对象
        namespace = module_or_namespace.__dict__
    elif isinstance(module_or_namespace, dict):
        # 处理命名空间字典
        namespace = module_or_namespace
    else:
        return tools

    for name, obj in namespace.items():
        if callable(obj) and hasattr(obj, "_is_tool") and hasattr(obj, "_tool_info"):
            tool_info = obj._tool_info
            tools[tool_info.name] = tool_info

    return tools


def get_global_tools() -> Dict[str, ToolInfo]:
    """获取全局注册的所有工具"""
    return _GLOBAL_TOOLS.copy()
